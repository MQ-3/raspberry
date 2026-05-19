def classify(value: float) -> str:
    if value < 1750:
        return "안정 단계"
    elif value < 2000:
        return "주의 단계"
    else:
        return "과음 주의 단계"


def get_message(status: str) -> str:
    messages = {
        "안정 단계": "현재는 비교적 안정적인 상태입니다.",
        "주의 단계": "조금 올라온 상태입니다. 천천히 마시는 것을 추천합니다.",
        "과음 주의 단계": "과음 주의 단계입니다. 음주 속도를 조절하세요."
    }
    return messages.get(status, "상태를 확인할 수 없습니다.")
