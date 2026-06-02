from dataclasses import dataclass

import config


@dataclass(frozen=True)
class AlcoholState:
    level: str
    label: str
    message: str


STATE_PRIORITY = {
    "safe": 1,
    "caution": 2,
    "danger": 3,
}

STATE_COLOR = {
    "safe": "green",
    "caution": "yellow",
    "danger": "red",
}


def classify_sensor_value(
    value,
    baseline=None,
    safe_max_value=config.SAFE_MAX_VALUE,
    danger_min_value=config.DANGER_MIN_VALUE,
    caution_ratio=config.CAUTION_RATIO,
    danger_ratio=config.DANGER_RATIO,
):
    # baseline 이 주어지면 비율 기준(mq3_test.py 와 동일), 없으면 절대값 fallback
    if baseline and baseline > 0:
        ratio = value / baseline
        danger = ratio >= danger_ratio
        caution = ratio >= caution_ratio
    else:
        danger = value >= danger_min_value
        caution = value >= safe_max_value

    if danger:
        return AlcoholState(
            level="danger",
            label="과음 주의 단계",
            message="알코올 반응이 높게 감지되었습니다. 물을 마시고 잠시 휴식하세요.",
        )

    if caution:
        return AlcoholState(
            level="caution",
            label="주의 단계",
            message="알코올 반응이 감지되고 있습니다. 천천히 마시는 것을 권장합니다.",
        )

    return AlcoholState(
        level="safe",
        label="안정 단계",
        message="현재는 안정적인 상태로 보입니다.",
    )


def state_to_dict(state):
    return {
        "level": state.level,
        "label": state.label,
        "message": state.message,
    }


def get_state_color(state_level):
    return STATE_COLOR.get(state_level, "gray")


def get_state_priority(state_level):
    return STATE_PRIORITY.get(state_level, 0)
