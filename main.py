import network
import urequests
import time
import machine
import os
import urandom

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Připojování k WiFi...')
        wlan.connect(ssid, password)
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            time.sleep(1)
    if wlan.isconnected():
        print('WiFi připojeno:', wlan.ifconfig())
        return True
    else:
        print('Připojení k WiFi selhalo')
        return False

def check_and_update_code():
    base_url = "https://raw.githubusercontent.com/ababcz/esp/refs/heads/main/c6.py"
    
    # Generování náhodného anti-cache tokenu
    random_token = urandom.getrandbits(32)
    url = f"{base_url}?rnd={random_token}"
    
    try:
        response = urequests.get(url)
        if response.status_code == 200:
            new_code = response.text
            try:
                with open('c6.py', 'r') as f:
                    current_code = f.read()
                if current_code == new_code:
                    print('Kód je aktuální')
                    return False
            except:
                pass
            
            with open('c6.py', 'w') as f:
                f.write(new_code)
            print('Nový kód uložen')
            return True
        else:
            print('Chyba HTTP:', response.status_code)
            return False
    except Exception as e:
        print('Chyba spojení:', e)
        return False

def execute_new_code():
    try:
        print('Spouštím c6.py...')
        with open('c6.py', 'r') as f:
            exec(f.read())
    except Exception as e:
        print('Chyba spouštění:', e)
        if 'main.py' in os.listdir():
            print('Fallback na main.py')
            with open('main.py', 'r') as f:
                exec(f.read())

def main():
    ssid = "XXX"
    password = "XXX"
    
    if connect_wifi(ssid, password):
        if check_and_update_code():
            execute_new_code()
        else:
            if 'c6.py' in os.listdir():
                execute_new_code()
            else:
                print('Chybějící spustitelný soubor')

if __name__ == "__main__":
    main()
    # Udržovat připojení
    #while True:
      #  time.sleep(3600)  # Snižte frekvenci připojování

