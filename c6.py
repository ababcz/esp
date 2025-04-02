from machine import Pin
from neopixel import NeoPixel
from time import sleep

# Nastavení RGB LED na GPIO 8 (1 LED)
pin_rgb = Pin(8, Pin.OUT)
np = NeoPixel(pin_rgb, 1)

# Definice barev
RED = (255, 0, 0)
BLUE = (0, 0, 255)
OFF = (0, 0, 0)

def blikani_majaku(pocet_opakovani=10):
    for _ in range(pocet_opakovani):
        # Dvakrát rychle červená
        for _ in range(2):
            np[0] = RED
            np.write()
            sleep(0.1)
            np[0] = OFF
            np.write()
            sleep(0.1)

        sleep(0.2)

        # Dvakrát rychle modrá
        for _ in range(3):
            np[0] = BLUE
            np.write()
            sleep(0.05)
            np[0] = OFF
            np.write()
            sleep(0.05)

        sleep(0.2)

    # Po ukončení zhasni LED
    np[0] = OFF
    np.write()

# Spuštění blikání majáku s 10 opakováními
blikani_majaku()

