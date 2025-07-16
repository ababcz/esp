import network
import urequests
import time
import os
import json
import gc
from machine import Pin
from neopixel import NeoPixel

# --- Konfigurace ---
SSID       = ""
PASSWORD   = ""
USERNAME   = "ababcz"
REPO       = "esp"
FILEPATH   = "c6.py"
SHA_STORE  = "last_sha.json"

# Pin pro RGB LED (NeoPixel)
LED_PIN    = 8
np         = NeoPixel(Pin(LED_PIN, Pin.OUT), 1)

# Barvy
RED, GREEN, BLUE, YELLOW, OFF = (8,0,0), (0,8,0), (0,0,8), (8,8,0), (0,0,0)

# --- Pomocné funkce ---
def blik(barva):
    np[0] = barva
    np.write()

def WiFi_connect(ssid, pwd):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        blik(BLUE)
        wlan.connect(ssid, pwd)
        for _ in range(10):
            if wlan.isconnected(): break
            time.sleep(1)
    if wlan.isconnected():
        blik(GREEN)
        return True
    blik(RED)
    return False

def load_sha():
    try:
        with open(SHA_STORE) as f:
            return json.load(f).get("sha")
    except:
        return None

def save_sha(sha):
    with open(SHA_STORE, "w") as f:
        json.dump({"sha": sha}, f)

def fetch_sha():
    url = f"https://api.github.com/repos/{USERNAME}/{REPO}/git/refs/heads/main"
    resp = urequests.get(url)
    if resp.status_code == 200:
        sha = resp.json()["object"]["sha"]
        resp.close(); gc.collect()
        return sha
    resp.close(); gc.collect()
    return None

def fetch_code(sha):
    url = f"https://raw.githubusercontent.com/{USERNAME}/{REPO}/{sha}/{FILEPATH}"
    resp = urequests.get(url)
    if resp.status_code == 200:
        code = resp.text
        resp.close(); gc.collect()
        return code
    resp.close(); gc.collect()
    return None

def update_once():
    blik(YELLOW)
    old = load_sha()
    new = fetch_sha()
    if not new or new == old:
        # nic ke stažení, nebo stejné SHA
        blik(GREEN)
        return False
    code = fetch_code(new)
    if code:
        with open(FILEPATH, "w") as f:
            f.write(code)
        save_sha(new)
        blik(BLUE)
        return True
    blik(RED)
    return False

def run_script():
    blik(BLUE)
    with open(FILEPATH) as f:
        exec(f.read(), globals())

# --- Hlavní program ---
def main():
    if WiFi_connect(SSID, PASSWORD):
        updated = update_once()
        if updated or FILEPATH in os.listdir():
            run_script()
    blik(OFF)

if __name__ == "__main__":
    main()
