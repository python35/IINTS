import machine
import utime


button_1 = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP)
button_2 = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)
button_3 = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_UP)

buttons = (
    ("Button 1 / GP16", button_1),
    ("Button 2 / GP17", button_2),
    ("Button 3 / GP18", button_3),
)

last_values = [pin.value() for _, pin in buttons]

print("Button test gestart")
print("Niet ingedrukt = 1, ingedrukt = 0")
print("Druk elke knop om de beurt in.")

while True:
    for index, (name, pin) in enumerate(buttons):
        value = pin.value()
        if value != last_values[index]:
            state = "INGEDRUKT" if value == 0 else "los"
            print("{}: {} ({})".format(name, state, value))
            last_values[index] = value
    utime.sleep_ms(30)
