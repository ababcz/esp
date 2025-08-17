import urequests

def alog(text):
    url = 'https://docs.google.com/forms/d/e/1FAIpQLSfJ4nKZl57DCv2YwE9NrBH9qhcLbECsYbe0-VBuYXBeE5VDjQ/formResponse'
    form_data = f'entry.443464588={text}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        response = urequests.post(url, data=form_data, headers=headers)
        response.close()  # Důležité pro uvolnění paměti
        return True
    except Exception as e:
        print(f'Chyba při odesílání: {e}')
        return False
alog("C6 start")





from machine import Pin, SPI
import time

# alog(text) je predpokladana globalni funkce pro logovani.
# Neni potreba ji zde definovat.

# alog('Inicializace skriptu pro CC1101.')

# Definice pinu podle zadani
# NanoESP32-C6  - CC1101
# --------------------
# GPIO23        - MOSI
# GPIO22        - SCLK
# GPIO21        - MISO
# GPIO20        - GDO2 (v tomto testu se nepouziva)
# GPIO19        - GDO0 (v tomto testu se nepouziva)
# GPIO18        - CSN
PIN_MOSI = 23
PIN_SCLK = 22
PIN_MISO = 21
PIN_CSN = 18

# Adresy stavovych registru CC1101
CC1101_REG_PARTNUM = 0x30
CC1101_REG_VERSION = 0x31

# Prikaz pro cteni z registru
CMD_READ = 0x80

# --- Konfigurace ---
alog('Konfigurace SPI sbernice a pinu.')

# Nastaveni CSN pinu jako vystupni
csn = Pin(PIN_CSN, Pin.OUT, value=1)

# Inicializace SPI sbernice (ID 1)
# Baudrate je nastaven na 5MHz, coz je bezpecna rychlost pro CC1101
spi = SPI(1, baudrate=5000000, polarity=0, phase=0, sck=Pin(PIN_SCLK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))

alog('SPI a piny uspesne inicializovany.')


# --- Komunikacni funkce ---

def csn_low():
    """Aktivuje komunikaci s CC1101 stazenim CSN na uroven L."""
    csn.value(0)

def csn_high():
    """Deaktivuje komunikaci s CC1101 zvednutim CSN na uroven H."""
    csn.value(1)

def cc1101_read_reg(reg_addr):
    """
    Precte hodnotu z jednoho registru CC1101.
    reg_addr: Adresa registru bez priznaku pro cteni/zapis.
    """
    csn_low()
    # Priprava adresy s prikazem pro cteni (MSB bit = 1)
    addr = bytearray([reg_addr | CMD_READ])
    alog(f"Ctu registr na adrese 0x{reg_addr:02X} (posilam 0x{addr[0]:02X})")
    
    # Odeslani adresy
    spi.write(addr)
    # Precteni jednoho bajtu dat
    value = spi.read(1)
    
    csn_high()
    alog(f"Z registru 0x{reg_addr:02X} prectena hodnota 0x{value:02X}")
    return value


# --- Hlavni testovaci funkce ---

def check_cc1101():
    """
    Provede overeni komunikace prectenim PARTNUM a VERSION registru.
    """
    alog("Spoustim test komunikace s modulem CC1101.")
    
    try:
        # Precteni PARTNUM registru
        partnum = cc1101_read_reg(CC1101_REG_PARTNUM)
        
        # Precteni VERSION registru
        version = cc1101_read_reg(CC1101_REG_VERSION)
        
        alog("--- Vysledky testu ---")
        alog(f"PARTNUM: 0x{partnum:02X}")
        alog(f"VERSION: 0x{version:02X}")
        
        # Kontrola, zda hodnoty nejsou 0x00 nebo 0xFF, coz by znacilo chybu
        if partnum != 0x00 and partnum != 0xFF and version != 0x00 and version != 0xFF:
            alog("Test uspesny: Komunikace s CC1101 se zda byt v poradu.")
            # Ocekavana hodnota pro VERSION byva casto 0x14
            if version == 0x14:
                alog("Detekovana ocekavana verze cipu (0x14).")
            return True
        else:
            alog("Test selhal: CC1101 neodpovida spravne.")
            alog("Zkontrolujte prosim zapojeni (MOSI, MISO, SCLK, CSN) a napajeni modulu.")
            return False
            
    except Exception as e:
        alog(f" behem testu nastala vyjimka: {e}")
        csn_high() # Zajisteni, ze CSN neni ponechano v aktivnim stavu
        return False

# --- Spusteni testu ---
check_cc1101()


