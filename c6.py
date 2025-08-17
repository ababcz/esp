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



# Definice pinu podle zadani
MOSI_PIN = 6
SCLK_PIN = 7
MISO_PIN = 0
GDO2_PIN = 10
GDO0_PIN = 11
CSN_PIN = 12

# CC1101 registry pro testovani
IOCFG2_REG = 0x00
IOCFG1_REG = 0x01
IOCFG0_REG = 0x02
FIFOTHR_REG = 0x03
SYNC1_REG = 0x04
SYNC0_REG = 0x05
PKTLEN_REG = 0x06
PKTCTRL1_REG = 0x07
PKTCTRL0_REG = 0x08
ADDR_REG = 0x09
CHANNR_REG = 0x0A
FSCTRL1_REG = 0x0B
FSCTRL0_REG = 0x0C
FREQ2_REG = 0x0D
FREQ1_REG = 0x0E
FREQ0_REG = 0x0F
MDMCFG4_REG = 0x10
MDMCFG3_REG = 0x11
MDMCFG2_REG = 0x12
MDMCFG1_REG = 0x13
MDMCFG0_REG = 0x14
DEVIATN_REG = 0x15
MCSM2_REG = 0x16
MCSM1_REG = 0x17
MCSM0_REG = 0x18
FOCCFG_REG = 0x19
BSCFG_REG = 0x1A
AGCCTRL2_REG = 0x1B
AGCCTRL1_REG = 0x1C
AGCCTRL0_REG = 0x1D
WOREVT1_REG = 0x1E
WOREVT0_REG = 0x1F
WORCTRL_REG = 0x20
FREND1_REG = 0x21
FREND0_REG = 0x22
FSCAL3_REG = 0x23
FSCAL2_REG = 0x24
FSCAL1_REG = 0x25
FSCAL0_REG = 0x26
RCCTRL1_REG = 0x27
RCCTRL0_REG = 0x28

# Status registry (read-only)
PARTNUM_REG = 0x30
VERSION_REG = 0x31
FREQEST_REG = 0x32
LQI_REG = 0x33
RSSI_REG = 0x34
MARCSTATE_REG = 0x35
WORTIME1_REG = 0x36
WORTIME0_REG = 0x37
PKTSTATUS_REG = 0x38
VCO_VC_DAC_REG = 0x39
TXBYTES_REG = 0x3A
RXBYTES_REG = 0x3B

# Kommando
SRES = 0x30
SFSTXON = 0x31
SXOFF = 0x32
SCAL = 0x33
SRX = 0x34
STX = 0x35
SIDLE = 0x36
SAFC = 0x37
SWOR = 0x38
SPWD = 0x39
SFRX = 0x3A
SFTX = 0x3B
SWORRST = 0x3C
SNOP = 0x3D

def init_spi():
    """Inicializace SPI komunikace"""
    alog("Inicializuji SPI komunikaci...")
    global spi, csn
    
    try:
        # Inicializace SPI s parametry pro CC1101
        spi = SPI(1, baudrate=5000000, polarity=0, phase=0, 
                 sck=Pin(SCLK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))
        
        # CSN pin (Chip Select)
        csn = Pin(CSN_PIN, Pin.OUT, value=1)
        
        # GDO piny pro pozdejsi pouziti
        gdo0 = Pin(GDO0_PIN, Pin.IN)
        gdo2 = Pin(GDO2_PIN, Pin.IN)
        
        alog("SPI inicializace uspesna")
        alog(f"MOSI: GPIO{MOSI_PIN}, SCLK: GPIO{SCLK_PIN}, MISO: GPIO{MISO_PIN}")
        alog(f"CSN: GPIO{CSN_PIN}, GDO0: GPIO{GDO0_PIN}, GDO2: GPIO{GDO2_PIN}")
        return True
        
    except Exception as e:
        alog(f"Chyba pri inicializaci SPI: {e}")
        return False

def cc1101_strobe(cmd):
    """Posle strobe kommando do CC1101"""
    csn.value(0)
    time.sleep_us(10)  # Kratka pauza
    status = spi.write_readinto(bytearray([cmd]), bytearray(1))
    csn.value(1)
    alog(f"Strobe 0x{cmd:02X} sent")
    return status

def cc1101_write_reg(addr, value):
    """Zapise hodnotu do registru CC1101"""
    csn.value(0)
    time.sleep_us(10)
    spi.write(bytearray([addr, value]))
    csn.value(1)
    alog(f"Wrote to reg 0x{addr:02X}: 0x{value:02X}")

def cc1101_read_reg(addr):
    """Precte hodnotu z registru CC1101"""
    csn.value(0)
    time.sleep_us(10)
    # Pro cteni se nastavi bit 7 (0x80)
    spi.write(bytearray([addr | 0x80]))
    result = spi.read(1)
    csn.value(1)
    value = result[0]
    alog(f"Read from reg 0x{addr:02X}: 0x{value:02X}")
    return value

def cc1101_reset():
    """Reset CC1101 modulu"""
    alog("Resetuji CC1101...")
    
    # Hardware reset sekvence
    csn.value(0)
    time.sleep_us(10)
    csn.value(1)
    time.sleep_us(40)
    csn.value(0)
    time.sleep_us(10)
    
    # Software reset
    cc1101_strobe(SRES)
    time.sleep_ms(10)
    
    alog("Reset dokoncen")

def test_cc1101_communication():
    """Hlavni test komunikace s CC1101"""
    alog("=== ZAHAJUJI TEST KOMUNIKACE S CC1101 ===")
    
    # 1. Inicializace SPI
    if not init_spi():
        alog("CHYBA: SPI inicializace selhala!")
        return False
    
    # 2. Reset modulu
    cc1101_reset()
    
    # 3. Test cteni status registru
    alog("\n--- Test cteni status registru ---")
    try:
        # Cteni PARTNUM - melo by byt 0x00 pro CC1101
        partnum = cc1101_read_reg(PARTNUM_REG)
        
        # Cteni VERSION - melo by byt 0x14 pro CC1101
        version = cc1101_read_reg(VERSION_REG)
        
        if partnum == 0x00 and version == 0x14:
            alog(f"SUCCESS: CC1101 detekovan! PARTNUM=0x{partnum:02X}, VERSION=0x{version:02X}")
        else:
            alog(f"WARNING: Neocekavane hodnoty - PARTNUM=0x{partnum:02X}, VERSION=0x{version:02X}")
            alog("CC1101 pravdepodobne neni spravne pripojen nebo nefunkcni")
            
    except Exception as e:
        alog(f"CHYBA pri cteni status registru: {e}")
        return False
    
    # 4. Test zapisu a cteni konfiguracnich registru
    alog("\n--- Test zapisu/cteni konfiguracnich registru ---")
    test_registers = [
        (CHANNR_REG, 0x55),    # Test pattern 1
        (ADDR_REG, 0xAA),      # Test pattern 2
        (PKTLEN_REG, 0x42),    # Test pattern 3
    ]
    
    for reg_addr, test_value in test_registers:
        try:
            # Uloz puvodni hodnotu
            original = cc1101_read_reg(reg_addr)
            
            # Zapir testovaci hodnotu
            cc1101_write_reg(reg_addr, test_value)
            
            # Precti zpet
            readback = cc1101_read_reg(reg_addr)
            
            if readback == test_value:
                alog(f"OK: Reg 0x{reg_addr:02X} write/read test prošel")
            else:
                alog(f"FAIL: Reg 0x{reg_addr:02X} write/read test selhal (expected 0x{test_value:02X}, got 0x{readback:02X})")
            
            # Obnov puvodni hodnotu
            cc1101_write_reg(reg_addr, original)
            
        except Exception as e:
            alog(f"CHYBA pri testu registru 0x{reg_addr:02X}: {e}")
    
    # 5. Test MARCSTATE registru
    alog("\n--- Test MARCSTATE registru ---")
    try:
        marcstate = cc1101_read_reg(MARCSTATE_REG)
        alog(f"MARCSTATE: 0x{marcstate:02X}")
        
        if marcstate == 0x01:  # IDLE state
            alog("CC1101 je v IDLE stavu - to je v poradku")
        else:
            alog(f"CC1101 je v neocekavanem stavu: 0x{marcstate:02X}")
            
    except Exception as e:
        alog(f"CHYBA pri cteni MARCSTATE: {e}")
    
    # 6. Test strobe kommandu
    alog("\n--- Test strobe kommandu ---")
    try:
        # Posleme SIDLE kommando
        cc1101_strobe(SIDLE)
        time.sleep_ms(10)
        
        # Overime stav
        marcstate = cc1101_read_reg(MARCSTATE_REG)
        alog(f"MARCSTATE po SIDLE: 0x{marcstate:02X}")
        
    except Exception as e:
        alog(f"CHYBA pri testu strobe kommandu: {e}")
    
    alog("\n=== TEST KOMUNIKACE DOKONCEN ===")
    return True


test_cc1101_communication()
