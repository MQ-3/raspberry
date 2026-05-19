import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)          # bus 0, CE0
spi.max_speed_hz = 1000000

def read_channel(channel: int) -> int:
    if not 0 <= channel <= 7:
        raise ValueError("Channel must be between 0 and 7")

    # MCP3208 single-ended read
    cmd1 = 0b00000110 | ((channel & 0b100) >> 2)
    cmd2 = (channel & 0b011) << 6

    result = spi.xfer2([cmd1, cmd2, 0])
    value = ((result[1] & 0x0F) << 8) | result[2]
    return value

try:
    while True:
        ch0 = read_channel(0)
        print(f"CH0: {ch0}")
        time.sleep(1)

except KeyboardInterrupt:
    spi.close()
    print("종료")
