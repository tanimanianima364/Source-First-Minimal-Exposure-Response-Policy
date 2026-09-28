## 結論

`raw=310, gain=1.02, offset=-0.01 V` の場合、温度は **51.00 ℃** です。

計算は次の通りです。

\[
生電圧=\frac{310}{1023}\times3.3=1.000\ \mathrm{V}
\]

\[
校正電圧=1.000\times1.02-0.01=1.010\ \mathrm{V}
\]

\[
温度=(1.010-0.5)\times100=\mathbf{51.00\ ^\circ C}
\]

機器固有の `gain` と `offset` を引数で受け取る実装です。

```python
import math

def temperature_c(raw: int, gain: float, offset: float) -> float:
    # raw: 整数 0～1023
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError("raw must be an integer")
    if not 0 <= raw <= 1023:
        raise ValueError("raw must be between 0 and 1023")

    # gain: 有限かつ正
    if isinstance(gain, bool) or not isinstance(gain, (int, float)):
        raise TypeError("gain must be a number")
    if not math.isfinite(gain) or gain <= 0:
        raise ValueError("gain must be finite and greater than 0")

    # offset: 有限
    if isinstance(offset, bool) or not isinstance(offset, (int, float)):
        raise TypeError("offset must be a number")
    if not math.isfinite(offset):
        raise ValueError("offset must be finite")

    raw_voltage = raw / 1023 * 3.3
    calibrated_voltage = raw_voltage * gain + offset
    return (calibrated_voltage - 0.5) * 100


temp = temperature_c(310, gain=1.02, offset=-0.01)
print(f"{temp:.2f} °C")  # 51.00 °C
```

**Source:** 提示された「架空センサー仕様r1」の変換式と、検証済み校正値 `gain=1.02, offset=-0.01 V`。

**次の方向:** 実装を実運用に入れるなら、`raw=0/1023`、不正範囲、`NaN`、`inf`、`gain<=0` に対する単体テストを追加すると検証しやすくなります。