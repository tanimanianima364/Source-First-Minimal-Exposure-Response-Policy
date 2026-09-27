はい。**2026年9月27日時点の最新安定版は Python 3.14.7**で、`dict` の反復順序は**挿入順序として言語仕様で保証**されています。Python 3.7以降の保証であり、CPython 3.6では同じ挙動が実装されていましたが、まだ**実装詳細**でした。:chatgpt-content-reference{index="0"}

| 操作 | 順序 |
|---|---|
| 新しいキーを追加 | 末尾に追加 |
| 既存キーへ再代入 | **位置は変わらない** |
| キーを削除 → 同じキーを再挿入 | **末尾に移る** |

公式ドキュメントは、`dict` について「挿入順序を保持する」「既存キーの更新は順序に影響しない」「削除後に追加したキーは末尾に入る」と明記しています。言語リファレンスにも、既存キーの置換では順序が変わらず、削除後の再挿入は末尾になるとあります。:chatgpt-content-reference{index="1"}

**CPython 3.6との違い**は保証レベルです。3.6の新しい compact `dict` 実装は結果として挿入順序を保持しましたが、「implementation detail」であり依存すべきでないとされていました。Python 3.7で挿入順序保持が正式に言語仕様の一部になりました。:chatgpt-content-reference{index="2"}

確認した公式資料：
- **Python 3.14.7** — *Built-in Types → Mapping Types — dict*：[該当節](https://docs.python.org/3.14/library/stdtypes.html?utm_source=chatgpt.com#mapping-types-dict)
- **Python 3.14.7** — *Data model → 3.2.7.1 Dictionaries*：[該当節](https://docs.python.org/3.14/reference/datamodel.html?utm_source=chatgpt.com#dictionaries)
- **Python 3.6.15** — *What’s New In Python 3.6 → New dict implementation*：[該当節](https://docs.python.org/3.6/whatsnew/3.6.html?utm_source=chatgpt.com#new-dict-implementation)
- **Python 3.14.7収録の What’s New In Python 3.7** — 3.7で言語仕様化：[該当節](https://docs.python.org/3.14/whatsnew/3.7.html?utm_source=chatgpt.com#summary-release-highlights)

なお、**3.15はこの時点では pre-release**で、安定版ではありません。公式 `/dev/` ドキュメントはさらに先の **Python 3.16.0a0** を指しています。したがって上記判断には開発版ではなく **3.14.7安定版の本文**を使用しています。本文は取得できており、取得不能による制約はありません。:chatgpt-content-reference{index="7"}