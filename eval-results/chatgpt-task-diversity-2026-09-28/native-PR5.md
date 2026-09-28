## 結論

```html
<label for="reservation-date">予約日</label>
<input
  type="date"
  id="reservation-date"
  name="reservation_date"
  min="2026-10-01"
  max="2026-10-31"
  required
>
```

**採用理由:** 対象ブラウザが `input type="date"` に対応しているため、外部ライブラリなしで日付選択UIと基本的な範囲・必須チェックを利用できます。`min` / `max` で予約可能期間を **2026-10-01〜2026-10-31（両端含む）** に制限します。

**サーバー側で必要な検証:** クライアント側属性は改変できるため、送信値についても必ず以下を検証します。

- 値が存在すること
- `YYYY-MM-DD` として厳密に解釈できる実在日であること
- `2026-10-01` 以上かつ `2026-10-31` 以下であること

HTMLの `required`、`min`、`max` だけをサーバー側検証の代替にはしません。