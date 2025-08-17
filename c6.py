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





# MicroPython pro NanoESP32-C6 + CC1101 (868.95 MHz), příjem 10 paketů
# Zapojení:
#   MOSI: GPIO23, SCLK: GPIO22, MISO: GPIO21, CSN: GPIO18, GDO0: GPIO19, GDO2: GPIO20
# Debug/INFO: používej alog(text) - již poskytnuto uživatelem

import time
from machine import Pin, SPI

# CC1101 registr adresy
IOCFG2   = 0x00
IOCFG0   = 0x02
FIFOTHR  = 0x03
PKTCTRL1 = 0x07
PKTCTRL0 = 0x08
FSCTRL1  = 0x0B
FSCTRL0  = 0x0C
FREQ2    = 0x0D
FREQ1    = 0x0E
FREQ0    = 0x0F
MDMCFG4  = 0x10
MDMCFG3  = 0x11
MDMCFG2  = 0x12
MDMCFG1  = 0x13
MDMCFG0  = 0x14
DEVIATN  = 0x15
MCSM2    = 0x16
MCSM1    = 0x17
MCSM0    = 0x18
FOCCFG   = 0x19
BSCFG    = 0x1A
AGCCTRL2 = 0x1B
AGCCTRL1 = 0x1C
AGCCTRL0 = 0x1D
WOREVT1  = 0x1E
WOREVT0  = 0x1F
WORCTL   = 0x20
FREND1   = 0x21
FREND0   = 0x22
FSCAL3   = 0x23
FSCAL2   = 0x24
FSCAL1   = 0x25
FSCAL0   = 0x26
TEST2    = 0x2C
TEST1    = 0x2D
TEST0    = 0x2E
PATABLE  = 0x3E

# Strobe příkazy
SRES   = 0x30
SFSTXON= 0x31
SXOFF  = 0x32
SCAL   = 0x33
SRX    = 0x34
STX    = 0x35
SIDLE  = 0x36
SFRX   = 0x3A
SFTX   = 0x3B
SWOR   = 0x38
SNOP   = 0x3D

# FIFO a status
RXFIFO = 0x3F
TXFIFO = 0x3F
MARCBITS = {
    'CRC_OK': 0x80,  # v LQI byte je bit7 = CRC_OK
}

# Piny dle požadavku
PIN_MOSI = 23
PIN_SCLK = 22
PIN_MISO = 21
PIN_CSN  = 18
PIN_GDO0 = 19  # doporučeno nastavit na "assert when sync word, deassert end of packet" nebo "packet ready"
PIN_GDO2 = 20

# SPI
spi = SPI(0, baudrate=4000000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB,
          sck=Pin(PIN_SCLK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))
cs = Pin(PIN_CSN, Pin.OUT, value=1)

gdo0 = Pin(PIN_GDO0, Pin.IN)
gdo2 = Pin(PIN_GDO2, Pin.IN)

def cs_select():
    cs.value(0)

def cs_deselect():
    cs.value(1)

def strobe(cmd):
    cs_select()
    spi.write(bytearray([cmd]))
    cs_deselect()

def write_reg(addr, val):
    cs_select()
    spi.write(bytearray([addr, val & 0xFF]))
    cs_deselect()

def write_burst(addr, data_bytes):
    cs_select()
    spi.write(bytearray([0x40 | addr]))  # burst write
    spi.write(bytearray(data_bytes))
    cs_deselect()

def read_status(addr):
    cs_select()
    spi.write(bytearray([0xC0 | addr]))  # status register
    val = spi.read(1)[0]
    cs_deselect()
    return val

def read_reg(addr):
    cs_select()
    spi.write(bytearray([0x80 | addr]))  # single read
    val = spi.read(1)
    cs_deselect()
    return val

def read_fifo(n):
    cs_select()
    spi.write(bytearray([0x80 | RXFIFO]))  # burst read from RX FIFO
    data = spi.read(n)
    cs_deselect()
    return bytes(data)

def flush_fifos():
    strobe(SIDLE)
    strobe(SFRX)
    strobe(SFTX)

def reset_cc1101():
    cs.value(1)
    time.sleep_ms(1)
    cs.value(0)
    time.sleep_ms(1)
    cs.value(1)
    time.sleep_ms(1)
    strobe(SRES)
    time.sleep_ms(10)

def rssi_dbm(raw):
    # RSSI format: signed, offset per datasheet ~ -74 dBm for 0x00 on 868MHz (value/2) - RSSI_offset
    # CC1101 RSSI_OFFSET ≈ 74
    if raw >= 128:
        raw = raw - 256
    return raw/2 - 74

def hexstr(b):
    return ''.join('{:02X}'.format(x) for x in b)

def configure_868_95MHz():
    # Nastavení vycházející z datasheetu TI/SmartRF Studio pro 868-869MHz, 2-FSK, cca 38.4kbps, BW ~100kHz.
    # Frekvence = 26MHz * (FREQ / 2^16). Pro 868.95MHz -> FREQ ≈ round(868.95e6 * 2^16 / 26e6) = 0x21 71 2B
    write_reg(IOCFG2, 0x06)    # GDO2: sync word (assert), deassert end of packet
    write_reg(IOCFG0, 0x06)    # GDO0: stejné chování (snadný polling)
    write_reg(FIFOTHR, 0x47)   # RX FIFO threshold
    write_reg(PKTCTRL1, 0x04)  # APPEND_STATUS=1 (RSSI+LQI), CRC_AUTOFLUSH=0
    write_reg(PKTCTRL0, 0x05)  # CRC_EN=1, packet length fixed/var? -> 0x05 = variable length, whitening off
    write_reg(FSCTRL1, 0x06)   # IF freq
    write_reg(FSCTRL0, 0x00)
    write_reg(FREQ2, 0x21)     # 0x21
    write_reg(FREQ1, 0x71)     # 0x71
    write_reg(FREQ0, 0x2B)     # 0x2B -> 868.95MHz
    write_reg(MDMCFG4, 0xCA)   # BW ~101kHz (depends), DRATE_E=10
    write_reg(MDMCFG3, 0x83)   # DRATE_M -> ~38.4kbps
    write_reg(MDMCFG2, 0x13)   # 30/32 sync, Manchester off, 2-FSK, no preamble qual (adjustable)
    write_reg(MDMCFG1, 0x22)   # FEC off, num preamble 4
    write_reg(MDMCFG0, 0xF8)   # Channel spacing ~ 199.95kHz
    write_reg(DEVIATN, 0x34)   # Deviation ~ 20.6kHz
    write_reg(MCSM2, 0x07)
    write_reg(MCSM1, 0x3C)     # After RX, stay in RX; CCA mode optional
    write_reg(MCSM0, 0x18)     # Autocal when going from IDLE to RX/TX
    write_reg(FOCCFG, 0x16)
    write_reg(BSCFG, 0x6C)
    write_reg(AGCCTRL2, 0x43)
    write_reg(AGCCTRL1, 0x40)
    write_reg(AGCCTRL0, 0x91)
    write_reg(FREND1, 0x56)
    write_reg(FREND0, 0x10)
    write_reg(FSCAL3, 0xE9)
    write_reg(FSCAL2, 0x2A)
    write_reg(FSCAL1, 0x00)
    write_reg(FSCAL0, 0x1F)
    write_reg(TEST2, 0x81)
    write_reg(TEST1, 0x35)
    write_reg(TEST0, 0x09)
    # PA table (RX nepotřebuje, ale nastavíme konzistentně)
    write_burst(PATABLE, [0xC0])  # vysoký výkon pro TX (nepoužito)

def enter_rx():
    strobe(SIDLE)
    flush_fifos()
    strobe(SRX)

def wait_packet(timeout_ms=5000):
    # Čekáme na paket: GDO0 low->high na SYNC a deassert na end-of-packet (dle IOCFGx)
    t0 = time.ticks_ms()
    # čekat na assert (SYNC)
    while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
        if gdo0.value():
            break
        time.sleep_ms(1)
    else:
        return False
    # čekat na deassert (konec paketu)
    while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
        if not gdo0.value():
            return True
        time.sleep_ms(1)
    return False

def read_variable_packet():
    # variable-length packet: první byte = length
    # po něm payload, pak 2 byty statusu: RSSI a LQI/CRC
    # Zkontrolujeme počet v RXBYTES (status reg) a čteme
    # RXBYTES je součástí statusu (adresy 0x3B), ale zjednodušíme čtením FIFO s rozumným limitem
    # Přečteme nejprve 1 byte délky, pak payload a status
    # Pokud nastal RX overflow, vyčistíme FIFO
    RXBYTES = 0x3B
    rxbytes = read_status(RXBYTES) & 0x7F
    if rxbytes == 0:
        return None
    # čti 1. byte délky
    length = read_fifo(1)[0]
    if length == 0 or length > 61:
        # délka mimo rozsah (RX FIFO má 64B; 1 len + 2 status = max 61 payload)
        flush_fifos()
        enter_rx()
        return None
    # čekej, až dorazí zbytek
    t0 = time.ticks_ms()
    need = length + 2  # payload + 2 status
    while True:
        rxbytes = read_status(RXBYTES) & 0x7F
        if rxbytes >= need:
            break
        if time.ticks_diff(time.ticks_ms(), t0) > 100:  # krátký timeout na doplnění
            break
        time.sleep_ms(1)
    if rxbytes < need:
        # nedorazilo vše
        payload = read_fifo(rxbytes)
        flush_fifos()
        enter_rx()
        return None
    data = read_fifo(need)
    payload = data[:-2]
    rssi_raw = data[-2]
    lqi_raw = data[-1]
    crc_ok = True if (lqi_raw & 0x80) else False
    lqi = lqi_raw & 0x7F
    rssi = rssi_dbm(rssi_raw)
    return (bytes(payload), rssi, lqi, crc_ok, length)

def print_reg_dump():
    regs = [
        IOCFG2, IOCFG0, FIFOTHR, PKTCTRL1, PKTCTRL0, FSCTRL1, FSCTRL0,
        FREQ2, FREQ1, FREQ0, MDMCFG4, MDMCFG3, MDMCFG2, MDMCFG1, MDMCFG0,
        DEVIATN, MCSM2, MCSM1, MCSM0, FOCCFG, BSCFG, AGCCTRL2, AGCCTRL1, AGCCTRL0,
        FREND1, FREND0, FSCAL3, FSCAL2, FSCAL1, FSCAL0, TEST2, TEST1, TEST0
    ]
    for a in regs:
        v = read_reg(a)
        alog("REG 0x{:02X} = 0x{:02X}".format(a, v))

def rx_loop(count=10):
    alog("CC1101 init start")
    reset_cc1101()
    configure_868_95MHz()
    strobe(SCAL)
    time.sleep_ms(5)
    print_reg_dump()
    alog("Entering RX")
    enter_rx()

    received = 0
    idle_recover_needed = False

    while received < count:
        # čekání na paket indikovaný GDO0 sekvencí
        got = wait_packet(timeout_ms=15000)
        if not got:
            # žádný paket v intervalu – udržuj RX a pokračuj
            alog("Timeout waiting packet; stay in RX")
            # ošetři případný overflow
            RXBYTES = 0x3B
            rxbytes = read_status(RXBYTES)
            if rxbytes & 0x80:
                alog("RX overflow -> flush")
                flush_fifos()
                enter_rx()
            continue

        # přečíst paket
        pkt = read_variable_packet()
        if pkt is None:
            # možný framgent/rušení; pokračuj
            continue

        payload, rssi, lqi, crc_ok, length = pkt
        alog("PKT {} LEN {} CRC {} RSSI {:.1f}dBm LQI {}".format(
            received+1, length, "OK" if crc_ok else "BAD", rssi, lqi))
        alog("DATA " + hexstr(payload))

        received += 1

        # Udržujeme RX
        strobe(SRX)

    alog("Done receiving {} packets".format(received))

# Auto-run po importu
try:
    rx_loop(10)
except Exception as e:
    try:
        alog("ERROR: " + str(e))
    except:
        pass
    # pokus o návrat do bezpečného stavu
    try:
        flush_fifos()
        strobe(SIDLE)
    except:
        pass

