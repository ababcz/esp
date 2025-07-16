# main.py - Finální, funkční updater pro ESP32
# Tento skript správně komunikuje s GitHub API, včetně povinné User-Agent hlavičky.

import network
import urequests
import time
import os
import json
import gc
from machine import Pin
from neopixel import NeoPixel

# --- UŽIVATELSKÁ KONFIGURACE ---
WIFI_SSID    = ""
WIFI_PASSWORD = ""

GITHUB_USER  = "ababcz"
GITHUB_REPO  = "esp"
GITHUB_FILE  = "c6.py"

# VOLITELNÉ: Pro zvýšení limitu API dotazů (z 60 na 5000/hod)
GITHUB_TOKEN = "" # Např. "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# --- INTERNÍ NASTAVENÍ ---
SHA_FILENAME = "c6_version.json"
LED_PIN      = 8
np           = NeoPixel(Pin(LED_PIN, Pin.OUT), 1)

# Barvy pro LED indikaci
RED, GREEN, BLUE, YELLOW, OFF = (8,0,0), (0,8,0), (0,0,8), (8,8,0), (0,0,0)

# --- FUNKCE ---

def led_status(color):
    """Zobrazí stav pomocí NeoPixel LED."""
    np[0] = color
    np.write()

def connect_to_wifi():
    """Připojí zařízení k Wi-Fi síti."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return True

    print("Připojování k Wi-Fi...")
    led_status(BLUE)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(15):
        if wlan.isconnected():
            print(f"Wi-Fi připojeno, IP adresa: {wlan.ifconfig()[0]}")
            led_status(GREEN)
            return True
        time.sleep(1)

    print("Připojení k Wi-Fi selhalo.")
    led_status(RED)
    return False

def get_local_sha():
    """Načte SHA posledního staženého souboru z interní paměti."""
    try:
        with open(SHA_FILENAME, 'r') as f:
            return json.load(f).get('sha')
    except (OSError, ValueError):
        return None

def get_remote_sha():
    """Získá nejnovější SHA commitu z GitHubu."""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/git/refs/heads/main"
    
    # --- DŮLEŽITÁ ZMĚNA ZDE ---
    # Všechny požadavky musí mít User-Agent hlavičku.
    headers = {
        'User-Agent': 'ESP32-Updater-Script'
    }
    # -------------------------

    if GITHUB_TOKEN:
        headers['Authorization'] = f"token {GITHUB_TOKEN}"

    print(f"Získávání remote SHA z: {url}")
    response = None
    try:
        response = urequests.get(url, headers=headers)
        if response.status_code == 200:
            sha = response.json()['object']['sha']
            return sha
        else:
            print(f"Chyba při komunikaci s GitHub API: Status {response.status_code}")
            print(f"Odpověď serveru: {response.text}")
            return None
    except Exception as e:
        print(f"Chyba sítě při získávání SHA: {e}")
        return None
    finally:
        if response:
            response.close()
        gc.collect()

def download_and_save(sha):
    """Stáhne soubor podle SHA a uloží ho."""
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{sha}/{GITHUB_FILE}"
    print(f"Stahování nové verze: {url}")
    response = None
    try:
        # Pro stahování raw souboru není User-Agent obvykle potřeba, ale neuškodí.
        headers = {'User-Agent': 'ESP32-Updater-Script'}
        response = urequests.get(url, headers=headers)
        if response.status_code == 200:
            with open(GITHUB_FILE, 'w') as f:
                f.write(response.text)
            with open(SHA_FILENAME, 'w') as f:
                json.dump({'sha': sha}, f)
            print("Soubor úspěšně aktualizován.")
            return True
        else:
            print(f"Chyba při stahování souboru: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"Chyba sítě při stahování souboru: {e}")
        return False
    finally:
        if response:
            response.close()
        gc.collect()

def run_script():
    """Spustí stažený skript 'c6.py'."""
    print(f"\n--- Spouštění skriptu '{GITHUB_FILE}' ---")
    try:
        with open(GITHUB_FILE, 'r') as f:
            exec(f.read(), globals())
    except OSError:
        print(f"Chyba: Skript '{GITHUB_FILE}' nenalezen.")
        led_status(RED)
    except Exception as e:
        print(f"Chyba při spouštění '{GITHUB_FILE}': {e}")
        led_status(RED)

# --- HLAVNÍ ČÁST PROGRAMU ---

def main():
    if not connect_to_wifi():
        return

    print("\n--- Kontrola aktualizací ---")
    led_status(YELLOW)
    
    local_sha = get_local_sha()
    remote_sha = get_remote_sha()

    if remote_sha and local_sha != remote_sha:
        print(f"Nalezena nová verze. Stahuji...")
        if download_and_save(remote_sha):
            led_status(BLUE)
        else:
            led_status(RED)
    elif remote_sha:
        print("Máte nejnovější verzi.")
        led_status(GREEN)
    else:
        print("Nepodařilo se zkontrolovat aktualizace.")

    if GITHUB_FILE in os.listdir():
        run_script()
    else:
        print(f"Soubor '{GITHUB_FILE}' není k dispozici pro spuštění.")

    print("\nProgram dokončen.")
    time.sleep(1)
    led_status(OFF)

if __name__ == "__main__":
    main()

