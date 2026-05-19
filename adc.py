import spidev


SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED_HZ = 1_000_000


class MCP3208:
    def __init__(self, bus: int = SPI_BUS, device: int = SPI_DEVICE, speed_hz: int = SPI_SPEED_HZ):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = speed_hz

    def read_channel(self, channel: int) -> int:
        if not 0 <= channel <= 7:
            raise ValueError("channel must be between 0 and 7")

        cmd1 = 0b00000110 | ((channel & 0b100) >> 2)
        cmd2 = (channel & 0b011) << 6

        result = self.spi.xfer2([cmd1, cmd2, 0])
        value = ((result[1] & 0x0F) << 8) | result[2]
        return value

    def close(self) -> None:
        self.spi.close()
