import board, busio, digitalio
import pycubed_rfm9x

# Configure pins and SPI bus
CS= digitalio.DigitalInOut(board.D5)
RESET= digitalio.DigitalInOut(board.D6)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialize RFM radio
rfm9x = pycubed_rfm9x.RFM9x(spi,CS,RESET,433.0,code_rate=8,baudrate=1320000)
rfm9x.enable_crc=True

rfm9x.send('Hi BeepSat!')