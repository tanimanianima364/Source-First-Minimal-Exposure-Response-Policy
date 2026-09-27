はい。**Python 3.7以降、通常の `dict` の反復順序は「挿入順」として言語仕様上保証されています。**

2026年9月27日時点の最新安定版は **Python 3.14.7**（2026年8月5日公開）です。公式の Source Releases でも latest Python 3 release とされています。:chatgpt-content-reference{index="0"}

- **Python 3.14.7 / Language Reference → Data model → 3.2.7.1 Dictionaries**  
  辞書は挿入順を保持し、**既存キーへの再代入では位置は変わらず**、**削除したキーを再挿入すると末尾に入る**と明記されています。また「3.7で変更」として、CPython 3.6では挿入順が保持されたものの、当時は言語保証ではなく実装詳細だったと説明されています。:chatgpt-content-reference{index="1"}  
  [Python 3.14.7 — Dictionaries](https://docs.python.org/3.14/reference/datamodel.html?utm_source=chatgpt.com#dictionaries)

したがって、例えば `{'a': 1, 'b': 2, 'c': 3}` に対して `d['b'] = 20` としても順序は `a, b, c` のままです。一方、`del d['b']; d['b'] = 20` とすると `a, c, b` になります。:chatgpt-content-reference{index="3"}

**CPython 3.6との違い**は重要です。CPython 3.6の新しい compact-dict 実装は結果として挿入順を保持しましたが、公式の *What’s New in Python 3.6* は、この性質を「implementation detail」とし、依存すべきでないとしていました。:chatgpt-content-reference{index="4"}  
[Python 3.6 — New dict implementation](https://docs.python.org/3.6/whatsnew/3.6.html?utm_source=chatgpt.com#new-dict-implementation)  
Python 3.7で初めて、`dict` の挿入順保持が **Python language spec の正式な一部**になりました。:chatgpt-content-reference{index="6"}

なお、現在の **Python 3.15.0rc2** のドキュメントは存在しますが、これは release candidate（プレリリース／開発段階）であり安定版ではありません。今回の結論は最新安定版 **3.14.7** の本文を実際に取得して確認しています。:chatgpt-content-reference{index="7"}