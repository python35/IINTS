import machine
import utime


button_1 = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP)
button_2 = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)
button_3 = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_UP)

print("GP16 GP17 GP18")
print("los = 1, ingedrukt = 0")

for _ in range(15):
    print(button_1.value(), button_2.value(), button_3.value())
    utime.sleep(1)
