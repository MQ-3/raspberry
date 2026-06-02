import spidev
import time


SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED_HZ = 1_000_000

MQ3_CHANNEL = 2   # MQ-3 AO를 MCP3208 CH2에 연결한 경우
SAMPLE_COUNT = 10
SAMPLE_DELAY = 0.05


spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = SPI_SPEED_HZ


def read_channel(channel: int) -> int:
    """MCP3208 단일 채널(0~7) 값을 읽어서 0~4095 정수로 반환."""
    if not 0 <= channel <= 7:
        raise ValueError("channel must be between 0 and 7")

    cmd1 = 0b00000110 | ((channel & 0b100) >> 2)
    cmd2 = (channel & 0b011) << 6

    result = spi.xfer2([cmd1, cmd2, 0])
    value = ((result[1] & 0x0F) << 8) | result[2]
    return value


def read_average(channel: int, sample_count: int = SAMPLE_COUNT) -> float:
    """여러 번 읽어서 평균값 반환."""
    values = []
    for _ in range(sample_count):
        values.append(read_channel(channel))
        time.sleep(SAMPLE_DELAY)
    return sum(values) / len(values)


def classify(value: float) -> str:
    # 값이 낮을수록 알코올 농도 높음 (AO 전압 반비례)
    if value > 3500:
        return "안정 단계"
    elif value > 2000:
        return "주의 단계"
    else:
        return "과음 주의 단계"


try:
    print("MQ-3 테스트 시작")
    print("예열이 덜 되었으면 값이 불안정할 수 있습니다.")
    print("Ctrl+C로 종료\n")

    while True:
        raw_value = read_channel(MQ3_CHANNEL)
        avg_value = read_average(MQ3_CHANNEL)
        status = classify(avg_value)

        print(
            f"RAW: {raw_value:4d} | "
            f"AVG: {avg_value:7.2f} | "
            f"STATUS: {status}"
        )
        time.sleep(1)

except KeyboardInterrupt:
    print("\n테스트 종료")

finally:
    spi.close()
