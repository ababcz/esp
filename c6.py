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
# Testovani komunikace pres SPI rozhrani - opravena verze

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
        
        # Inicializace SPI s nizsim baudrate pro stabilitu
        self.spi = SPI(1, 
                       baudrate=1000000,  # Snizeno z 5MHz na 1MHz
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
        
        # Kontrola pocatecnich stavu GPIO
        self.check_gpio_states()
    
    def check_gpio_states(self):
        """Kontrola stavu GPIO pinu"""
        alog("Kontrola stavu GPIO pinu:")
        alog(f"GDO0 stav: {self.gdo0.value()}")
        alog(f"GDO2 stav: {self.gdo2.value()}")
        alog(f"CS stav: {self.cs.value()}")
    
    def write_reg(self, addr, value):
        """Zapis do registru CC1101 s vylepsenym timingem"""
        self.cs.value(0)
        time.sleep_us(10)  # CS setup time
        self.spi.write(bytearray([addr, value]))
        time.sleep_us(10)  # Hold time
        self.cs.value(1)
        time.sleep_us(10)  # CS release time
        alog(f"Zapis: registr 0x{addr:02X} = 0x{value:02X}")
    
    def read_reg(self, addr):
        """Cteni z registru CC1101 s vylepsenym timingem"""
        self.cs.value(0)
        time.sleep_us(10)  # CS setup time
        # Nastaveni read bitu (bit 7)
        self.spi.write(bytearray([addr | 0x80]))
        time.sleep_us(10)  # Between write and read
        result = self.spi.read(1)
        time.sleep_us(10)  # Hold time
        self.cs.value(1)
        time.sleep_us(10)  # CS release time
        
        value = result[0] if result else 0xFF
        alog(f"Cteni: registr 0x{addr:02X} = 0x{value:02X}")
        return value
    
    def send_strobe(self, cmd):
        """Poslani strobe prikazu s vylepsenym timingem"""
        self.cs.value(0)
        time.sleep_us(10)  # CS setup time
        self.spi.write(bytearray([cmd]))
        time.sleep_us(10)  # Hold time
        self.cs.value(1)
        time.sleep_us(10)  # CS release time
        alog(f"Strobe prikaz: 0x{cmd:02X}")
    
    def reset_chip(self):
        """Reset CC1101 chipu s prodlouzenym cekacim casem"""
        alog("Spoustim reset CC1101")
        self.send_strobe(CC1101_SRES)
        time.sleep_ms(500)  # Prodlouzeno z 100ms na 500ms
        
        # Cekani na stabilizaci chipu
        alog("Cekam na stabilizaci chipu...")
        stabilized = False
        for i in range(20):  # Max 20 pokusu
            time.sleep_ms(50)
            marcstate = self.read_reg(CC1101_MARCSTATE)
            alog(f"Pokus {i+1}: MARCSTATE = 0x{marcstate:02X}")
            
            if marcstate == 0x01:  # IDLE state
                alog("Chip se stabilizoval v IDLE stavu")
                stabilized = True
                break
            elif marcstate == 0x0D:  # SLEEP state je taky OK
                alog("Chip je v SLEEP stavu")
                stabilized = True
                break
        
        if not stabilized:
            alog("UPOZORNENI: Chip se nestabilizoval v ocekavanem stavu")
        
        alog("Reset dokoncen")
        return stabilized
    
    def test_basic_communication(self):
        """Zakladni test komunikace"""
        alog("Test zakladni komunikace s CC1101")
        
        try:
            # Reset chipu
            reset_success = self.reset_chip()
            
            # Test cteni MARCSTATE registru
            alog("Cteni MARCSTATE registru")
            marcstate = self.read_reg(CC1101_MARCSTATE)
            
            # Akceptovatelne stavy po resetu
            valid_states = [0x01, 0x0D]  # IDLE nebo SLEEP
            if marcstate in valid_states:
                state_name = "IDLE" if marcstate == 0x01 else "SLEEP"
                alog(f"MARCSTATE OK - chip je v {state_name} stavu (0x{marcstate:02X})")
                return True
            else:
                alog(f"MARCSTATE neocekavana hodnota: 0x{marcstate:02X}")
                # Pokud reset probehl uspesne, zkusime pokracovat
                return reset_success
            
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
            test_values = [0x0C, 0x08, 0x06, 0x05]
            successful_tests = 0
            
            for test_val in test_values:
                # Zapis testovaci hodnoty
                self.write_reg(CC1101_FSCTRL1, test_val)
                time.sleep_ms(10)  # Cas pro zapis
                
                # Cteni zpet
                read_val = self.read_reg(CC1101_FSCTRL1)
                
                if read_val == test_val:
                    alog(f"Test zapisu/cteni OK pro hodnotu 0x{test_val:02X}")
                    successful_tests += 1
                else:
                    alog(f"Test zapisu/cteni CHYBA - zapsano 0x{test_val:02X}, precteno 0x{read_val:02X}")
            
            # Obnoveni puvodni hodnoty
            self.write_reg(CC1101_FSCTRL1, original_val)
            time.sleep_ms(10)
            verify_val = self.read_reg(CC1101_FSCTRL1)
            
            if verify_val == original_val:
                alog("Puvodni hodnota registru uspesne obnovena")
            else:
                alog(f"UPOZORNENI: Puvodni hodnota neobnovena - je 0x{verify_val:02X}, mela by byt 0x{original_val:02X}")
            
            # Test je uspesny pokud prosly alespon 3 ze 4 testu
            success = successful_tests >= 3
            alog(f"Uspesnych testu zapisu/cteni: {successful_tests}/4")
            return success
            
        except Exception as e:
            alog(f"Chyba pri testu zapisu/cteni: {e}")
            return False
    
    def test_chip_identification(self):
        """Test identifikace chipu s lepsi diagnostikou"""
        alog("Test identifikace CC1101 chipu")
        
        try:
            # Cteni PARTNUM a VERSION vickrat pro overeni
            alog("Prvni cteni identifikacnich registru:")
            partnum1 = self.read_reg(CC1101_PARTNUM)
            version1 = self.read_reg(CC1101_VERSION)
            
            time.sleep_ms(10)
            
            alog("Druhe cteni identifikacnich registru:")
            partnum2 = self.read_reg(CC1101_PARTNUM)
            version2 = self.read_reg(CC1101_VERSION)
            
            alog(f"PARTNUM: prvni=0x{partnum1:02X}, druhe=0x{partnum2:02X}")
            alog(f"VERSION: prvni=0x{version1:02X}, druhe=0x{version2:02X}")
            
            # Kontrola konzistence
            if partnum1 != partnum2 or version1 != version2:
                alog("UPOZORNENI: Nekonzistentni cteni identifikacnich registru")
            
            # CC1101 ma PARTNUM = 0x00, VERSION zavisi na revizi
            if partnum1 == 0x00:
                alog("Chip identifikace OK - detekovan CC1101")
                alog(f"Verze chipu: 0x{version1:02X}")
                return True
            elif partnum1 == 0xFF or partnum1 == 0x0F:
                alog("CHYBA: PARTNUM obsahuje 0xFF nebo 0x0F - mozny problem s komunikaci")
                return False
            else:
                alog(f"Neocekavany PARTNUM: 0x{partnum1:02X} (ocekavan 0x00)")
                # Nekdy CC1101 klony maji jiny PARTNUM, ale komunikace muze fungovat
                alog("Mozna se jedna o CC1101 klon nebo kompatibilni chip")
                return False
                
        except Exception as e:
            alog(f"Chyba pri identifikaci chipu: {e}")
            return False
    
    def test_status_registers(self):
        """Dodatecny test cteni statusovych registru"""
        alog("Test statusovych registru")
        
        try:
            # Cteni nekolika dulezitych registru
            status_regs = [
                (0x35, "MARCSTATE"),
                (0x36, "WORTIME1"),
                (0x37, "WORTIME0"),
                (0x38, "PKTSTATUS"),
                (0x39, "VCO_VC_DAC"),
                (0x3A, "TXBYTES"),
                (0x3B, "RXBYTES")
            ]
            
            consistent_reads = 0
            total_reads = len(status_regs)
            
            for addr, name in status_regs:
                val1 = self.read_reg(addr)
                time.sleep_ms(5)
                val2 = self.read_reg(addr)
                
                if val1 == val2:
                    consistent_reads += 1
                    alog(f"{name} (0x{addr:02X}): 0x{val1:02X} - konzistentni")
                else:
                    alog(f"{name} (0x{addr:02X}): 0x{val1:02X}/0x{val2:02X} - NEkonzistentni")
            
            success_rate = consistent_reads / total_reads
            alog(f"Konzistentni cteni: {consistent_reads}/{total_reads} ({success_rate*100:.1f}%)")
            
            return success_rate >= 0.7  # 70% uspesnost
            
        except Exception as e:
            alog(f"Chyba pri testu statusovych registru: {e}")
            return False
    
    def run_full_test(self):
        """Spusteni kompletniho testu komunikace"""
        alog("=== Start kompletniho testu CC1101 ===")
        
        test_results = []
        
        # Pocatecni kontrola GPIO
        self.check_gpio_states()
        
        # Test 1: Zakladni komunikace
        alog("\n--- Test 1: Zakladni komunikace ---")
        result1 = self.test_basic_communication()
        test_results.append(("Zakladni komunikace", result1))
        
        # Test 2: Zapis/cteni registru
        alog("\n--- Test 2: Zapis/cteni registru ---")
        result2 = self.test_write_read()
        test_results.append(("Zapis/cteni registru", result2))
        
        # Test 3: Identifikace chipu
        alog("\n--- Test 3: Identifikace chipu ---")
        result3 = self.test_chip_identification()
        test_results.append(("Identifikace chipu", result3))
        
        # Test 4: Statusove registry
        alog("\n--- Test 4: Statusove registry ---")
        result4 = self.test_status_registers()
        test_results.append(("Statusove registry", result4))
        
        # Vysledky testu
        alog("\n=== Vysledky testu ===")
        passed_tests = 0
        critical_tests_passed = 0
        
        for i, (test_name, result) in enumerate(test_results):
            status = "USPECH" if result else "CHYBA"
            alog(f"{test_name}: {status}")
            
            if result:
                passed_tests += 1
                # Prvni dva testy jsou kriticke
                if i < 2:
                    critical_tests_passed += 1
        
        total_tests = len(test_results)
        success_rate = passed_tests / total_tests
        
        alog(f"\nCelkova uspesnost: {passed_tests}/{total_tests} ({success_rate*100:.1f}%)")
        
        # Hodnoceni celkoveho vysledku
        if critical_tests_passed == 2 and passed_tests >= 3:
            overall_result = True
            alog("=== Celkovy vysledek testu: USPECH ===")
            alog("Komunikace s CC1101 funguje spravne")
        elif critical_tests_passed == 2:
            overall_result = True
            alog("=== Celkovy vysledek testu: CASTECNY USPECH ===")
            alog("Zakladni komunikace funguje, nektery pokrocilejsi testy selhaly")
        else:
            overall_result = False
            alog("=== Celkovy vysledek testu: CHYBA ===")
            alog("Komunikace s CC1101 ma vazne problemy")
        
        return overall_result

# Vytvoreni instance a spusteni testu
alog("Inicializace CC1101 testeru")
cc1101 = CC1101()

alog("Spoustim test komunikace s CC1101")
test_result = cc1101.run_full_test()

if test_result:
    alog("Test ukoncen uspesne")
else:
    alog("Test ukoncen s chybami")

