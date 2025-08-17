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





# Testování komunikace s CC1101 na nanoESP32-C6
# Používá předpřipravenou funkci alog(text) pro debug zprávy

from machine import Pin, SPI
import time

# Definice pinů podle zadání
MOSI_PIN = 23
SCLK_PIN = 22  
MISO_PIN = 21
CSN_PIN = 18
GDO2_PIN = 20
GDO0_PIN = 19

# CC1101 registry a příkazy
CC1101_PARTNUM = 0x30     # Registr s číslem části čipu
CC1101_VERSION = 0x31     # Registr s verzí čipu
CC1101_SRES = 0x30        # Reset strobe příkaz

def init_spi():
    """Inicializace SPI rozhraní"""
    alog("Inicializuji SPI rozhrani")
    spi = SPI(1, 
              baudrate=5000000,    # 5 MHz
              polarity=0, 
              phase=0,
              sck=Pin(SCLK_PIN), 
              mosi=Pin(MOSI_PIN), 
              miso=Pin(MISO_PIN))
    
    csn = Pin(CSN_PIN, Pin.OUT)
    csn.value(1)  # CSN neaktivní (HIGH)
    alog("SPI inicializovano uspesne")
    return spi, csn

def cc1101_strobe(spi, csn, strobe_cmd):
    """Pošle strobe příkaz do CC1101"""
    csn.value(0)  # Aktivuj CSN
    response = spi.write_readinto(bytearray([strobe_cmd]), bytearray(1))
    csn.value(1)  # Deaktivuj CSN
    return response[0] if response else 0

def cc1101_read_register(spi, csn, reg_addr):
    """Přečte registr z CC1101"""
    read_addr = reg_addr | 0x80  # Nastav read bit
    csn.value(0)  # Aktivuj CSN
    
    # Pošli adresu a přečti odpověď
    status = spi.write_readinto(bytearray([read_addr]), bytearray(1))[0]
    value = spi.write_readinto(bytearray([0x00]), bytearray(1))
    
    csn.value(1)  # Deaktivuj CSN
    return value, status

def test_cc1101_communication():
    """Hlavní test komunikace s CC1101"""
    alog("Spoustim test komunikace s CC1101")
    
    # Inicializace SPI
    try:
        spi, csn = init_spi()
        alog("SPI uspesne inicializovano")
    except Exception as e:
        alog("Chyba pri inicializaci SPI")
        return False
    
    # Malá pauza pro stabilizaci
    time.sleep_ms(50)
    
    # Pokus o reset čipu
    alog("Provadim reset CC1101")
    try:
        cc1101_strobe(spi, csn, CC1101_SRES)
        time.sleep_ms(100)  # Čekání na dokončení resetu
        alog("Reset CC1101 dokoncen")
    except Exception as e:
        alog("Chyba pri resetu CC1101")
        return False
    
    # Test čtení PARTNUM registru
    alog("Ctu PARTNUM registr")
    try:
        partnum, status = cc1101_read_register(spi, csn, CC1101_PARTNUM)
        alog(f"PARTNUM: 0x{partnum:02X}, Status: 0x{status:02X}")
        
        if partnum == 0x00:
            alog("CC1101 PARTNUM je 0x00 - komunikace OK")
        else:
            alog(f"Neocekavana hodnota PARTNUM: 0x{partnum:02X}")
            return False
            
    except Exception as e:
        alog("Chyba pri cteni PARTNUM registru")
        return False
    
    # Test čtení VERSION registru  
    alog("Ctu VERSION registr")
    try:
        version, status = cc1101_read_register(spi, csn, CC1101_VERSION)
        alog(f"VERSION: 0x{version:02X}, Status: 0x{status:02X}")
        
        if version == 0x14:
            alog("CC1101 VERSION je 0x14 - spravna verze chipu")
        else:
            alog(f"Neocekavana verze chipu: 0x{version:02X}")
            return False
            
    except Exception as e:
        alog("Chyba pri cteni VERSION registru")
        return False
    
    # Finální kontrola - několik čtení po sobě
    alog("Provadim finalni test stability komunikace")
    for i in range(3):
        try:
            partnum, _ = cc1101_read_register(spi, csn, CC1101_PARTNUM)
            version, _ = cc1101_read_register(spi, csn, CC1101_VERSION)
            alog(f"Test {i+1}: PARTNUM=0x{partnum:02X}, VERSION=0x{version:02X}")
            time.sleep_ms(10)
        except Exception as e:
            alog(f"Chyba v testu {i+1}")
            return False
    
    alog("Komunikace s CC1101 uspesne overena!")
    return True

# Spuštění testu
alog("=== START CC1101 Test ===")
result = test_cc1101_communication()
if result:
    alog("=== CC1101 Test USPESNY ===")
else:
    alog("=== CC1101 Test NEUSPESNY ===")
