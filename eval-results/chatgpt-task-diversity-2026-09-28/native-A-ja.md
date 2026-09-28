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

**採用理由**  
対象ブラウザが `input type="date"` に対応しているため、外部ライブラリなしで日付選択UIと基本的な入力制約を利用できます。`required` で必須、`min` / `max` で予約可能期間を指定しています。

**サーバー側で必要な検証**  
HTMLの制約は改変・回避できるため、サーバー側でも必ず次を検証します。

- `reservation_date` が存在し、空でないこと
- `YYYY-MM-DD` 形式として正しく解析できる実在の日付であること
- `2026-10-01` 以上かつ `2026-10-31` 以下であること
- 検証に失敗した場合は予約処理を行わず、入力エラーとして返すこと

`type="date"` の送信値は通常 `YYYY-MM-DD` なので、時刻やタイムゾーンを介さず「日付」として比較するのが適切です。