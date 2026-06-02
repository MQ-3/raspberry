import os
from dotenv import load_dotenv

load_dotenv()

# Flask
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# Database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "sulchingu")
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

# Sensor
USE_MOCK_SENSOR = os.getenv("USE_MOCK_SENSOR", "true").lower() == "true"
# 백그라운드 상시 측정 루프(spike 자동감지/api/status). 프론트가 /api/measure만
# 쓰면 불필요하며, 같은 SPI 장치를 동시 점유해 측정값을 깨뜨릴 수 있어 기본 off.
ENABLE_SENSOR_LOOP = os.getenv("ENABLE_SENSOR_LOOP", "false").lower() == "true"
SENSOR_CHANNEL = int(os.getenv("SENSOR_CHANNEL", 2))
SENSOR_SAMPLE_DELAY = float(os.getenv("SENSOR_SAMPLE_DELAY", 0.05))
SENSOR_LOOP_INTERVAL = float(os.getenv("SENSOR_LOOP_INTERVAL", 0.1))
BASELINE_DURATION = int(os.getenv("BASELINE_DURATION", 3))
BLOW_DURATION = int(os.getenv("BLOW_DURATION", 4))
STABILIZE_DURATION = int(os.getenv("STABILIZE_DURATION", 3))

# State thresholds (절대 peak 값 기준)
#   safe:    peak < SAFE_MAX_VALUE
#   caution: SAFE_MAX_VALUE <= peak < DANGER_MIN_VALUE
#   danger:  peak >= DANGER_MIN_VALUE
SAFE_MAX_VALUE = int(os.getenv("SAFE_MAX_VALUE", 1200))
DANGER_MIN_VALUE = int(os.getenv("DANGER_MIN_VALUE", 2400))
