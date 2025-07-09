import machine
import utime
import framebuf
from st7789 import ST7789

# --- Scherminitialisatie ---
spi = machine.SPI(1, baudrate=40000000, polarity=1, phase=1,
                   sck=machine.Pin(10), mosi=machine.Pin(11))
dc = machine.Pin(13, machine.Pin.OUT)
reset = machine.Pin(12, machine.Pin.OUT)
bl = machine.Pin(17, machine.Pin.OUT)

display = ST7789(spi, 240, 240, reset=reset, dc=dc)
display.init()
bl.value(1)

# --- Tekstfunctie ---
buffer = bytearray(240 * 240 * 2)
fb = framebuf.FrameBuffer(buffer, 240, 240, framebuf.RGB565)


def draw_text_centered(text, color=0xFFFF):
    fb.fill(0x0000)
    text_width = len(text) * 8
    text_x = (240 - text_width) // 2
    text_y = 100
    fb.text(text, text_x, text_y, color)
    display.blit_buffer(buffer, 0, 0, 240, 240)

# --- Startup-scherm functie ---
def show_startup_screen():
    try:
        with open("start.bmp", "rb") as f:
            f.seek(18)
            bmp_width = int.from_bytes(f.read(4), 'little')
            bmp_height = int.from_bytes(f.read(4), 'little')
            f.seek(54)  # Begin van de pixeldata

            # Bereken positie: gecentreerd en iets naar links verschoven
            x_offset = ((240 - bmp_width) // 2) - 40
            y_offset = (240 - bmp_height) // 2

            row_buffer = bytearray(bmp_width * 2)

            display.fill(0x22C5)
            for y in range(bmp_height):
                f.seek(54 + (bmp_height - 1 - y) * bmp_width * 2)
                f.readinto(row_buffer)
                for i in range(0, len(row_buffer), 2):
                    row_buffer[i], row_buffer[i + 1] = row_buffer[i + 1], row_buffer[i]
                display.blit_buffer(row_buffer, x_offset, y + y_offset, bmp_width, 1)
            utime.sleep(5)  # Afbeelding 5 seconden zichtbaar
    except OSError:
        draw_text_centered("BMP niet gevonden", color=0xFFFF)
        utime.sleep(3)
    display.fill(0x000000)

# --- Knopconfiguratie ---
happy_button = machine.Pin(9, machine.Pin.IN, machine.Pin.PULL_UP)
# De sad-button is defect, dus we negeren deze
sad_button = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)
angry_button = machine.Pin(28, machine.Pin.IN, machine.Pin.PULL_UP)

# We gaan geen wacht-for-release gebruiken, maar continu de knopstatus checken.
def button_held(button, delay=0.2):
    """Return True als de knop ingedrukt blijft gedurende 'delay' seconden."""
    if button.value() == 0:
        utime.sleep(delay)
        if button.value() == 0:
            return True
    return False

# --- Motorconfiguratie ---
in1 = machine.Pin(2, machine.Pin.OUT)
in2 = machine.Pin(3, machine.Pin.OUT)
in3 = machine.Pin(4, machine.Pin.OUT)
in4 = machine.Pin(6, machine.Pin.OUT)

def disable_motor():
    in1.value(0)
    in2.value(0)
    in3.value(0)
    in4.value(0)

disable_motor()

# --- Full-step sequentie (volgens testcode) ---
full_step_sequence = [
    (1, 0, 1, 0),  # Stap 1
    (0, 1, 1, 0),  # Stap 2
    (0, 1, 0, 1),  # Stap 3
    (1, 0, 0, 1)   # Stap 4
]

def step_motor(delay, steps, direction=1):
    """
    Draait de motor met de full-step sequentie.
      - Voor injectie: we gebruiken nu direction=-1 (omgekeerd ten opzichte van testcode)
      - Voor terugdraaien: direction=1
    """
    sequence = full_step_sequence if direction == 1 else full_step_sequence[::-1]
    for _ in range(steps):
        for step in sequence:
            in1.value(step[0])
            in2.value(step[1])
            in3.value(step[2])
            in4.value(step[3])
            utime.sleep_ms(delay)
    disable_motor()

def continuous_step_motor(delay, steps, direction=1):
    """
    Draait de motor continu (zonder uit te schakelen) in kleine stapjes,
    zodat deze blijft draaien zolang de knop ingedrukt is.
    """
    sequence = full_step_sequence if direction == 1 else full_step_sequence[::-1]
    for _ in range(steps):
        for step in sequence:
            in1.value(step[0])
            in2.value(step[1])
            in3.value(step[2])
            in4.value(step[3])
            utime.sleep_ms(delay)
    # Geen disable_motor() hier zodat de motor blijft draaien

# --- Variabelen ---
totale_dagdosis = 0
gram_koolhydraten = 0
stap = 0

def verander_waarde(waarde, richting, stap_grootte=1):
    if richting == 'omhoog':
        waarde += stap_grootte
    elif richting == 'omlaag' and waarde > 0:
        waarde -= stap_grootte
    return waarde

# --- Hoofdprogramma ---
show_startup_screen()

while True:
    # Stap 0: Stel totale dagdosis in
    if stap == 0:
        draw_text_centered(f"Dagdos: {totale_dagdosis}U")
        utime.sleep(1)
        if button_held(happy_button, delay=0.3):
            totale_dagdosis = verander_waarde(totale_dagdosis, 'omhoog')
            draw_text_centered(f"Dagdos: {totale_dagdosis}U")
        # sad_button is defect, dus geen verlagen
        if button_held(angry_button, delay=0.3) and totale_dagdosis > 0:
            stap = 1
            utime.sleep(0.3)
    
    # Stap 1: Stel gram koolhydraten in
    elif stap == 1:
        draw_text_centered(f"Koolhydr: {gram_koolhydraten}g")
        if button_held(happy_button, delay=0.3):
            gram_koolhydraten = verander_waarde(gram_koolhydraten, 'omhoog')
            draw_text_centered(f"Koolhydr: {gram_koolhydraten}g")
        # sad_button is defect, dus geen verlagen
        if button_held(angry_button, delay=0.3) and gram_koolhydraten > 0:
            stap = 2
            utime.sleep(0.3)
    
    # Stap 2: Bereken insuline, injecteer, en laat motor terugdraaien
    elif stap == 2:
        kh_ratio = 500 / totale_dagdosis
        eenheden_insuline = gram_koolhydraten / kh_ratio
        steps_per_revolution = 200
        insuline_per_revolution = 1.0
        steps_per_unit_insuline = steps_per_revolution / insuline_per_revolution
        total_steps = int(eenheden_insuline * steps_per_unit_insuline)
        
        # Injectie: Gebruik direction=-1 zodat de motor draait in jouw gewenste "vooruit" richting.
        step_motor(5, total_steps, direction=-1)
        draw_text_centered(f"Insuline: {eenheden_insuline:.2f}U")
        utime.sleep(2)
        
        draw_text_centered("terugdraaien?")
        utime.sleep(1)
        # Terugdraaien: Gebruik direction=1 en blijf draaien zolang de knop ingedrukt is.
        while angry_button.value() == 0:
            continuous_step_motor(5, 10, direction=1)
            utime.sleep(0.1)
        disable_motor()
        draw_text_centered("Motor teruggedraaid")
        utime.sleep(2)
        
        # Reset de waarden en ga terug naar stap 0
        totale_dagdosis = 0
        gram_koolhydraten = 0
        stap = 0

