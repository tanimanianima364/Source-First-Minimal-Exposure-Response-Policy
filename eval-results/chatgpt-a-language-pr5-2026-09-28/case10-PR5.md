## 結論
**20 MBのCSVを分割せずに処理できると仕様上確認できるのは Product Q v3 です。**  
v2はCSV入力上限が10 MBのため20 MBは対象外、v3は上限25 MBなので範囲内です。どちらもジョブは非同期実行です。

## Source
- Product Q v2 manual — **Export limits**: CSV input up to **10 MB**  
  https://example.invalid/q/v2#export-limits
- Product Q v3 manual — **Export limits**: CSV input up to **25 MB**  
  https://example.invalid/q/v3#export-limits

## 採用前に確認すること
提示資料で確認できるのは**CSV入力サイズ上限と非同期実行**のみです。採用前に、**出力ファイル側のサイズ・件数制限、非同期ジョブの完了時間やタイムアウト、失敗時の再実行仕様**を別途確認するのが適切です。