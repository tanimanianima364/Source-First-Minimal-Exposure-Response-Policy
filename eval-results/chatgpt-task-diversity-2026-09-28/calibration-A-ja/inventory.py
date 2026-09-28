import math


def raw_to_temperature(raw: int, gain: float, offset: float) -> float:
    """
    ADC raw値と機器固有の校正値から温度[℃]を計算する。

    raw:    0〜1023 の整数
    gain:   有限かつ正の数
    offset: 有限の数 [V]
    """
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError("raw must be an integer")
    if not 0 <= raw <= 1023:
        raise ValueError("raw must be between 0 and 1023")

    if isinstance(gain, bool) or not isinstance(gain, (int, float)):
        raise TypeError("gain must be a number")
    gain = float(gain)
    if not math.isfinite(gain) or gain <= 0:
        raise ValueError("gain must be finite and greater than 0")

    if isinstance(offset, bool) or not isinstance(offset, (int, float)):
        raise TypeError("offset must be a number")
    offset = float(offset)
    if not math.isfinite(offset):
        raise ValueError("offset must be finite")

    raw_voltage = raw / 1023 * 3.3
    calibrated_voltage = raw_voltage * gain + offset
    temperature_c = (calibrated_voltage - 0.5) * 100

    return temperature_c


temperature = raw_to_temperature(310, gain=1.02, offset=-0.01)
print(f"{temperature:.2f} °C")  # 51.00 °C
