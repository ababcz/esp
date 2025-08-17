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





# MicroPython kod pro nanoesp32-c6 s CC1101 modulem
# Testovani komunikace pres SPI rozhrani

from machine import Pin, SPI
import time

# Konfigurace pinu podle zapojeni
MOSI_PIN = 23
SCLK_PIN = 22
MISO_PIN = 21
GDO2_PIN = 20
GDO0_PIN = 19
CSN_PIN = 18

# CC1101 registry pro test
CC1101_SRES = 0x30      # Reset strobe
CC1101_MARCSTATE = 0x35 # Main Radio Control State
CC1101_FSCTRL1 = 0x0B   # Frequency synthesizer control
CC1101_PARTNUM = 0x30   # Part number
CC1101_VERSION = 0x31   # Version number

class CC1101:
    def __init__(self):
        alog("Inicializace CC1101 komunikace")
        
        # Inicializace SPI
        self.spi = SPI(1, 
                       baudrate=5000000, 
                       polarity=0, 
                       phase=0,
                       sck=Pin(SCLK_PIN), 
                       mosi=Pin(MOSI_PIN), 
                       miso=Pin(MISO_PIN))
        
        # Inicializace GPIO pinu
        self.cs = Pin(CSN_PIN, Pin.OUT, value=1)
        self.gdo0 = Pin(GDO0_PIN, Pin.IN)
        self.gdo2 = Pin(GDO2_PIN, Pin.IN)
        
        alog("SPI a GPIO piny inicializovany")
    
    def write_reg(self, addr, value):
        """Zapis do registru CC1101"""
        self.cs.value(0)
        self.spi.write(bytearray([addr, value]))
        self.cs.value(1)
        alog(f"Zapis: registr 0x{addr:02X} = 0x{value:02X}")
    
    def read_reg(self, addr):
        """Cteni z registru CC1101"""
        self.cs.value(0)
        # Nastaveni read bitu (bit 7)
        self.spi.write(bytearray([addr | 0x80]))
        result = self.spi.read(1)
        self.cs.value(1)
        
        value = result[0] if result else 0
        alog(f"Cteni: registr 0x{addr:02X} = 0x{value:02X}")
        return value
    
    def send_strobe(self, cmd):
        """Poslani strobe prikazu"""
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)
        alog(f"Strobe prikaz: 0x{cmd:02X}")
    
    def reset_chip(self):
        """Reset CC1101 chipu"""
        alog("Spoustim reset CC1101")
        self.send_strobe(CC1101_SRES)
        time.sleep_ms(100)
        alog("Reset dokoncen")
    
    def test_basic_communication(self):
        """Zakladni test komunikace"""
        alog("Test zakladni komunikace s CC1101")
        
        try:
            # Reset chipu
            self.reset_chip()
            
            # Test cteni MARCSTATE registru
            alog("Cteni MARCSTATE registru")
            marcstate = self.read_reg(CC1101_MARCSTATE)
            
            if marcstate == 0x01:  # IDLE state
                alog("MARCSTATE OK - chip je v IDLE stavu")
            else:
                alog(f"MARCSTATE neocekavana hodnota: 0x{marcstate:02X}")
            
            return True
            
        except Exception as e:
            alog(f"Chyba pri zakladnim testu: {e}")
            return False
    
    def test_write_read(self):
        """Test zapisu a cteni registru"""
        alog("Test zapisu a cteni registru")
        
        try:
            # Puvodni hodnota FSCTRL1
            original_val = self.read_reg(CC1101_FSCTRL1)
            alog(f"Puvodni hodnota FSCTRL1: 0x{original_val:02X}")
            
            # Testovaci hodnoty
            test_values = [0x0C, 0x08, 0x06]
            
            for test_val in test_values:
                # Zapis testovaci hodnoty
                self.write_reg(CC1101_FSCTRL1, test_val)
                time.sleep_ms(10)
                
                # Cteni zpet
                read_val = self.read_reg(CC1101_FSCTRL1)
                
                if read_val == test_val:
                    alog(f"Test zapisu/cteni OK pro hodnotu 0x{test_val:02X}")
                else:
                    alog(f"Test zapisu/cteni CHYBA - zapsano 0x{test_val:02X}, precteno 0x{read_val:02X}")
                    return False
            
            # Obnoveni puvodni hodnoty
            self.write_reg(CC1101_FSCTRL1, original_val)
            alog("Puvodni hodnota registru obnovena")
            
            return True
            
        except Exception as e:
            alog(f"Chyba pri testu zapisu/cteni: {e}")
            return False
    
    def test_chip_identification(self):
        """Test identifikace chipu"""
        alog("Test identifikace CC1101 chipu")
        
        try:
            # Cteni PARTNUM a VERSION
            partnum = self.read_reg(CC1101_PARTNUM)
            version = self.read_reg(CC1101_VERSION)
            
            alog(f"PARTNUM: 0x{partnum:02X}")
            alog(f"VERSION: 0x{version:02X}")
            
            # CC1101 ma PARTNUM = 0x00
            if partnum == 0x00:
                alog("Chip identifikace OK - detekovan CC1101")
                return True
            else:
                alog(f"Neocekavany PARTNUM: 0x{partnum:02X}")
                return False
                
        except Exception as e:
            alog(f"Chyba pri identifikaci chipu: {e}")
            return False
    
    def run_full_test(self):
        """Spusteni kompletniho testu komunikace"""
        alog("=== Start kompletniho testu CC1101 ===")
        
        test_results = []
        
        # Test 1: Zakladni komunikace
        result1 = self.test_basic_communication()
        test_results.append(("Zakladni komunikace", result1))
        
        # Test 2: Zapis/cteni registru
        result2 = self.test_write_read()
        test_results.append(("Zapis/cteni registru", result2))
        
        # Test 3: Identifikace chipu
        result3 = self.test_chip_identification()
        test_results.append(("Identifikace chipu", result3))
        
        # Vysledky testu
        alog("=== Vysledky testu ===")
        all_passed = True
        
        for test_name, result in test_results:
            status = "USPECH" if result else "CHYBA"
            alog(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        final_status = "USPECH" if all_passed else "CHYBA"
        alog(f"=== Celkovy vysledek testu: {final_status} ===")
        
        return all_passed

# Vytvoreni instance a spusteni testu
alog("Inicializace CC1101 testeru")
cc1101 = CC1101()

alog("Spoustim test komunikace s CC1101")
test_result = cc1101.run_full_test()

if test_result:
    alog("Komunikace s CC1101 funguje spravne")
else:
    alog("Komunikace s CC1101 ma problemy")

