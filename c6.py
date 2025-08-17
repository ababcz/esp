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

# Definice pinů podle specifikovaného propojení
MOSI_PIN = 6    # nanoesp32-c6 GPIO6 -> CC1101 MOSI
SCLK_PIN = 7    # nanoesp32-c6 GPIO7 -> CC1101 SCLK  
MISO_PIN = 1    # nanoesp32-c6 GPIO1 -> CC1101 MISO
GDO2_PIN = 10   # nanoesp32-c6 GPIO10 -> CC1101 GDO2
GDO0_PIN = 11   # nanoesp32-c6 GPIO11 -> CC1101 GDO0
CSN_PIN = 12    # nanoesp32-c6 GPIO12 -> CC1101 CSN

def init_spi():
    """Inicializace SPI komunikace a CSN pinu"""
    alog("Inicializuji SPI komunikaci")
    
    # Konfigurace SPI: baudrate 5MHz, CPOL=0, CPHA=0
    spi = SPI(1, baudrate=5000000, polarity=0, phase=0, 
              sck=Pin(SCLK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))
    
    # CSN pin jako výstup, defaultně HIGH (neaktivní)
    csn = Pin(CSN_PIN, Pin.OUT, value=1)
    
    alog("SPI inicializace dokončena")
    return spi, csn

def cc1101_command(spi, csn, cmd):
    """Odeslání příkazu do CC1101"""
    csn.value(0)  # Aktivace CS
    spi.write(bytearray([cmd]))
    csn.value(1)  # Deaktivace CS
    alog(f"Odeslán příkaz: 0x{cmd:02X}")

def cc1101_write_reg(spi, csn, addr, value):
    """Zápis hodnoty do registru CC1101"""
    csn.value(0)
    spi.write(bytearray([addr, value]))
    csn.value(1)
    alog(f"Zapsán registr 0x{addr:02X} = 0x{value:02X}")

def cc1101_read_reg(spi, csn, addr):
    """Čtení hodnoty z registru CC1101"""
    csn.value(0)
    spi.write(bytearray([addr | 0x80]))  # Bit 7 = 1 pro čtení
    result = spi.read(1)
    value = result[0]
    csn.value(1)
    alog(f"Přečten registr 0x{addr:02X} = 0x{value:02X}")
    return value

def cc1101_read_status(spi, csn, addr):
    """Čtení stavového registru CC1101"""
    csn.value(0)
    spi.write(bytearray([addr | 0xC0]))  # Burst/status read
    result = spi.read(1)
    value = result[0]
    csn.value(1)
    alog(f"Přečten status registr 0x{addr:02X} = 0x{value:02X}")
    return value

def test_cc1101_communication():
    """Hlavní testovací funkce pro ověření komunikace s CC1101"""
    alog("=== ZAČÁTEK TESTU KOMUNIKACE S CC1101 ===")
    
    # Krok 1: Inicializace SPI
    try:
        spi, csn = init_spi()
        alog("Krok 1: SPI inicializace úspěšná")
    except Exception as e:
        alog(f"Chyba při inicializaci SPI: {e}")
        return False
    
    # Krok 2: Reset modulu
    alog("Krok 2: Provádím reset modulu CC1101")
    try:
        cc1101_command(spi, csn, 0x30)  # SRES - Software reset
        time.sleep_ms(100)  # Čekání na dokončení resetu
        alog("Reset modulu dokončen")
    except Exception as e:
        alog(f"Chyba při resetu modulu: {e}")
        return False
    
    # Krok 3: Čtení identifikačních registrů
    alog("Krok 3: Čtu identifikační registry")
    try:
        # Čtení PARTNUM registru (0x30)
        partnum = cc1101_read_status(spi, csn, 0x30)
        
        # Čtení VERSION registru (0x31) 
        version = cc1101_read_status(spi, csn, 0x31)
        
        alog(f"PARTNUM: 0x{partnum:02X}, VERSION: 0x{version:02X}")
        
        # Ověření správných hodnot pro CC1101
        if partnum == 0x00:  # CC1101 PARTNUM
            alog("✓ PARTNUM registr odpovídá CC1101")
            partnum_ok = True
        else:
            alog(f"⚠ PARTNUM neodpovídá očekávané hodnotě (0x00), získáno: 0x{partnum:02X}")
            partnum_ok = False
            
        if version in [0x03, 0x04, 0x14]:  # Známé verze CC1101
            alog(f"✓ VERSION registr je validní pro CC1101")
            version_ok = True
        else:
            alog(f"⚠ VERSION může být neočekávaný: 0x{version:02X}")
            version_ok = False
            
    except Exception as e:
        alog(f"Chyba při čtení identifikačních registrů: {e}")
        return False
    
    # Krok 4: Test zápisu a čtení registru
    alog("Krok 4: Test zápisu a čtení konfiguračního registru")
    try:
        test_reg = 0x0B  # FSCTRL1 registr
        original_value = cc1101_read_reg(spi, csn, test_reg)
        alog(f"Původní hodnota registru 0x{test_reg:02X}: 0x{original_value:02X}")
        
        # Zápis testovací hodnoty
        test_value = 0x55  # Alternující bity
        cc1101_write_reg(spi, csn, test_reg, test_value)
        
        # Přečtení zpět
        read_back = cc1101_read_reg(spi, csn, test_reg)
        
        if read_back == test_value:
            alog("✓ Test zápisu/čtení registru úspěšný")
            write_test_ok = True
        else:
            alog(f"✗ Test zápisu/čtení neúspěšný - očekáváno: 0x{test_value:02X}, získáno: 0x{read_back:02X}")
            write_test_ok = False
        
        # Obnovení původní hodnoty
        cc1101_write_reg(spi, csn, test_reg, original_value)
        alog("Původní hodnota registru obnovena")
        
    except Exception as e:
        alog(f"Chyba při testu zápisu/čtení: {e}")
        return False
    
    # Krok 5: Vyhodnocení celkového výsledku
    alog("Krok 5: Vyhodnocení výsledků testu")
    
    if partnum_ok and (version_ok or version != 0xFF) and write_test_ok:
        alog("🎉 KOMUNIKACE S CC1101 ÚSPĚŠNĚ OVĚŘENA!")
        alog("✓ Všechny testy prošly úspěšně")
        result = True
    elif write_test_ok:
        alog("⚠ KOMUNIKACE PRAVDĚPODOBNĚ FUNGUJE")  
        alog("✓ Základní komunikace funguje, ale identifikační registry jsou neočekávané")
        result = True
    else:
        alog("✗ KOMUNIKACE S CC1101 NEFUNGUJE SPRÁVNĚ")
        alog("Zkontrolujte zapojení a napájení modulu")
        result = False
    
    alog("=== KONEC TESTU KOMUNIKACE S CC1101 ===")
    return result

# Spuštění testu (bez __main__ bloku)
test_result = test_cc1101_communication()
