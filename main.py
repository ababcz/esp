import network
import urequests
import time
import machine
import os
import urandom
from machine import Pin
from neopixel import NeoPixel

# Nastavení RGB LED na GPIO 8 (1 LED)
pin_rgb = Pin(8, Pin.OUT)
np = NeoPixel(pin_rgb, 1)

# Definice barev
RED = (8, 0, 0)
GREEN = (0, 8, 0)
BLUE = (0, 0, 8)
YELLOW = (8, 8, 0)
OFF = (0, 0, 0)

def indikace_stavu(barva):
    np[0] = barva
    np.write()

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Připojování k WiFi...')
        indikace_stavu(BLUE)  # Indikace připojování pomocí modré barvy
        wlan.connect(ssid, password)
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            time.sleep(1)
    if wlan.isconnected():
        print('WiFi připojeno:', wlan.ifconfig())
        indikace_stavu(GREEN)  # Indikace úspěšného připojení pomocí zelené barvy
        return True
    else:
        print('Připojení k WiFi selhalo')
        indikace_stavu(RED)  # Indikace selhání připojení pomocí červené barvy
        return False

def check_and_update_code():
    base_url = "https://raw.githubusercontent.com/ababcz/esp/refs/heads/main/c6.py"
    
    # Generování náhodného anti-cache tokenu
    random_token = urandom.getrandbits(32)
    url = f"{base_url}?rnd={random_token}"
    
    try:
        indikace_stavu(YELLOW)  # Indikace zahájení stahování nového kódu pomocí žluté barvy
        response = urequests.get(url)
        if response.status_code == 200:
            new_code = response.text
            try:
                with open('c6.py', 'r') as f:
                    current_code = f.read()
                if current_code == new_code:
                    print('Kód je aktuální')
                    indikace_stavu(GREEN)  # Indikace, že kód je aktuální pomocí zelené barvy
                    return False
            except:
                pass
            
            with open('c6.py', 'w') as f:
                f.write(new_code)
            print('Nový kód uložen')
            indikace_stavu(BLUE)  # Indikace úspěšného stažení nového kódu pomocí modré barvy
            return True
        else:
            print('Chyba HTTP:', response.status_code)
            indikace_stavu(RED)  # Indikace chyby HTTP pomocí červené barvy
            return False
    except Exception as e:
        print('Chyba spojení:', e)
        indikace_stavu(RED)  # Indikace chyby spojení pomocí červené barvy
        return False

def execute_new_code():
    try:
        print('Spouštím c6.py...')
        indikace_stavu(BLUE)  # Indikace spuštění nového kódu pomocí modré barvy
        with open('c6.py', 'r') as f:
            exec(f.read())
    except Exception as e:
        print('Chyba spouštění:', e)
        indikace_stavu(RED)  # Indikace chyby spuštění pomocí červené barvy
        if 'main.py' in os.listdir():
            print('Fallback na main.py')
            with open('main.py', 'r') as f:
                exec(f.read())

def main():
    ssid = ""
    password = ""
    
    if connect_wifi(ssid, password):
        if check_and_update_code():
            execute_new_code()
        else:
            if 'c6.py' in os.listdir():
                execute_new_code()
            else:
                print('Chybějící spustitelný soubor')
    indikace_stavu(OFF)  # Vypnutí LED po dokončení

if __name__ == "__main__":
    main()
    # Udržovat připojení
    #while True:
    #    time.sleep(3600)  # Snižte frekvenci připojování
