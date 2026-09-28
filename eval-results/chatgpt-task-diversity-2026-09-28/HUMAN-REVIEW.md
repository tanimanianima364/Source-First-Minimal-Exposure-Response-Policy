# 22回答の採点確認表

2026-09-28再開。対象はPR #8のマージ `21ee44a1d8db24eb3bd1e8fc225cc4a01352d18c` に保存された回答と、SQL訂正後の[暫定採点](grades.json)。PR5は `682f08a`、日本語Aは `29ad511`。別の比較で使ったA/B/Cと混同しない。

今回、AI評価者が22回答全文・[固定入力と基準](../../eval-tasks/format-and-diversity-2026-09-28/cases.json)・保存済み実行ログを再照合した。既存の訂正後判定を維持し、追加のモデル実行・テスト再実行・採点基準変更は行っていない。`verify.py`による記録整合性の確認は実施した。これは人による確認の代替でも、既存テストの独立再実行でもない。

## 確認方法

各行の両回答を開き、入力・基準と照合する。コード課題は下記の固定チェックと事後診断を区別する。「合格」は有限の確認範囲における暫定判定で、全入力での正しさを保証しない。

確認した本人が、対象ID・同意または修正内容・確認日を記録する。未確認の行は空欄のままにする。チャットで報告する場合は、例えば「2a・3a・1bの両回答と基準を自分で確認し、暫定判定に同意」のように対象を限定できる。PR承認やAIレビュー文の転記だけで、全行を人による確認済みにしない。

表の判定順は **内容／根拠／形式**。○は暫定合格、×は暫定不合格。確認欄はすべて未確認で開始する。

| ID | PR5原文・判定 | 日本語A原文・判定 | 判断の要点 | 人による確認・日付 |
|---|---|---|---|---|
| 2a | [原文](2a-PR5.md) ○／○／○ | [原文](2a-A-ja.md) ○／○／○ | CSV 10 MB・非同期・24時間・再試行1回を保持。追加提案なし。 | 未確認 |
| 3a | [原文](3a-PR5.md) ○／○／○ | [原文](3a-A-ja.md) ○／○／○ | 同じJSONのみ。4キーと値が一致し、フェンスや説明なし。 | 未確認 |
| 1b | [原文](1b-PR5.md) ○／○／○ | [原文](1b-A-ja.md) ○／○／○ | 要件Aのバックアップ、要件Bの復元テストだけを指定順で提示。 | 未確認 |
| native | [原文](native-PR5.md) ○／○／○ | [原文](native-A-ja.md) ○／○／○ | label・name・required・日付範囲。サーバーで必須・実在日・範囲を検証。実ブラウザ試験ではない。 | 未確認 |
| csv | [原文](csv-PR5.md) ×／○／○ | [原文](csv-A-ja.md) ×／○／○ | 固定チェックは通過。大きな金額を丸める事後診断が厳密合計の契約未達を示す。 | 未確認 |
| duration | [原文](duration-PR5.md) ○／○／○ | [原文](duration-A-ja.md) ○／○／○ | ASCII・全体一致・順序・例外型を検証。巨大整数はPR5が1桁ずつ、日本語Aが9桁ずつ変換。 | 未確認 |
| sql | [原文](sql-PR5.md) ×／○／○ | [原文](sql-A-ja.md) ○／○／○ | 固定チェックは通過。sqlite3.Row時、PR5はRowを返す。日本語Aはtuple化。任意のfactoryは未検証。 | 未確認 |
| rootcause | [原文](rootcause-PR5.md) ○／○／○ | [原文](rootcause-A-ja.md) ○／○／○ | 共有parse_amountで型・書式を検査してからカンマ除去。両呼び出し元を検証。テスト件数で優劣を付けない。 | 未確認 |
| explain | [原文](explain-PR5.md) ○／○／○ | [原文](explain-A-ja.md) ○／○／○ | 変更理由と指定5種類の同値性検証あり。掲載出力は例の結果として扱い、モデル自身の実行証拠とはしない。 | 未確認 |
| calibration | [原文](calibration-PR5.md) ○／○／○ | [原文](calibration-A-ja.md) ○／○／○ | 51.00℃、可変gain/offset、入力検証。実機精度は未検証。順序逸脱の参考観測。 | 未確認 |
| distributed | [原文](distributed-PR5.md) ×／○／○ | [原文](distributed-A-ja.md) ×／○／○ | 同じ挿入時刻を保証する試験がない。並行投入だけでは代替不可。設計の机上採点で、Redis実行は未実施。順序逸脱の参考観測。 | 未確認 |

## 実行証拠

下記は保存済みログへの案内で、今回の新規実行結果ではない。

| ID | 固定チェック／採点条件／付属例 | 事後診断 |
|---|---|---|
| csv | 固定: [PR5](csv-PR5-independent.log)・[日本語A](csv-A-ja-independent.log)。例: [PR5](csv-PR5-examples.log)・[日本語A](csv-A-ja-examples.log) | [同一診断](decimal-diagnostic.py): [PR5失敗](csv-PR5-decimal-diagnostic.log)・[日本語A失敗](csv-A-ja-decimal-diagnostic.log) |
| duration | 固定: [PR5](duration-PR5-independent.log)・[日本語A](duration-A-ja-independent.log)。例: [PR5](duration-PR5-examples.log)・[日本語A](duration-A-ja-examples.log) | なし |
| sql | 固定: [PR5](sql-PR5-independent.log)・[日本語A](sql-A-ja-independent.log)。例: [PR5](sql-PR5-examples.log)・[日本語A](sql-A-ja-examples.log) | [同一診断](sql-row-factory-diagnostic.py): [PR5失敗](sql-PR5-row-factory-diagnostic.log)・[日本語A通過](sql-A-ja-row-factory-diagnostic.log) |
| rootcause | 固定: [PR5](rootcause-PR5-independent.log)・[日本語A](rootcause-A-ja-independent.log)。付属pytest: [PR5](rootcause-PR5-examples.log)・[日本語A](rootcause-A-ja-examples.log) | なし |
| explain | 同値性の付属例: [PR5](explain-PR5-examples.log)・[日本語A](explain-A-ja-examples.log) | なし |
| calibration | 事前の手動採点条件を実行可能にした検証: [PR5](calibration-PR5-criteria.log)・[日本語A](calibration-A-ja-criteria.log)。例: [PR5](calibration-PR5-examples.log)・[日本語A](calibration-A-ja-examples.log) | 実行用コードは収集後作成。事前固定の実行テストではない |

## 保留事項

- 人による確認は22回答とも未完了。今回のAI再照合を根拠に`grades.json`の暫定状態を解除しない。
- SQL・CSVは両版合格ペアではないため簡潔さ比較から除外。校正・分散設計は[順序逸脱](order-deviations.json)により比較判断全体から除外したまま。
- 今回の対象は直近の11課題。以前の論文調査・出典課題等の採点確定や、ブラウザ設定・画像証跡の独立再検証は含まない。
- 本表の採点確認と、常用プロンプトの採用判断は別。正本は日本語Aのまま。
