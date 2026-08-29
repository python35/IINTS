import machine
import utime


# Veilige scan: motorpinnen GP4/5/6/9 en DRV EEP GP28 worden niet aangeraakt.
scan_gpios = [
    0, 1, 2, 3,
    7, 8,
    10, 11, 12, 13, 14, 15,
    16, 17, 18, 19, 20, 21, 22,
    26, 27,
]

pins = [(gpio, machine.Pin(gpio, machine.Pin.IN, machine.Pin.PULL_UP)) for gpio in scan_gpios]
last = {gpio: pin.value() for gpio, pin in pins}

print("Veilige knopscan gestart")
print("Druk elke knop 1-2 seconden in.")
print("Een knop naar GND verschijnt als: GPxx INGEDRUKT")

start = utime.ticks_ms()
while utime.ticks_diff(utime.ticks_ms(), start) < 25000:
    for gpio, pin in pins:
        value = pin.value()
        if value != last[gpio]:
            state = "INGEDRUKT" if value == 0 else "los"
            print("GP{} {}".format(gpio, state))
            last[gpio] = value
    utime.sleep_ms(20)

print("Scan klaar")
