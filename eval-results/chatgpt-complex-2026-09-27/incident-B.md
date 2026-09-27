{
  "decision": "proposed-hotfix r1は不採用。v2.4には冪等キー保証がなく、0件GET直後の再POST、送信前の成功記録、ログ件数だけによる再開判定はいずれも重複または誤判定を防げない。現時点では送信を保留し、全100件を照合してから権限者の判断を経て再開する。",
  "confirmed": [
    "ext-731 / 12,000円について、s101とs102の2件がcommittedで確定している。",
    "ext-731に対して本来1件の送信意図だったため、確定している重複分は1件・12,000円。2件の確定総額は24,000円。",
    "09:00:06の0件GETは失敗確定を意味しない。v2.4では確定レコードの検索反映に最大60秒かかり、タイムアウト後もサーバー側でコミット済みとなり得る。",
    "09:00:20以降は自動再試行を停止しており、incident-log上はそれ以降の送信はない。",
    "v2.5の48時間冪等キー保持は翌週有効化予定であり、現在稼働中のv2.4には適用されない。"
  ],
  "unknowns": [
    "バッチ100件すべての確定ID一覧と、ext-731以外の99件の実績が未取得であり、他の重複・未確定・欠落の有無は不明。",
    "バッチの実際の確定総額は不明。予定総額1,000,000円との差額も、全件照合前には確定できない。",
    "s101とs102のどちらを取消すかは未決定で、finance-ownerの承認時に決める必要がある。",
    "取消APIの仕様は資料群に含まれていないため、具体的な取消手順や完了状態はここから確定できない。"
  ],
  "immediate_actions": [
    "自動再試行停止を維持し、少なくとも当該バッチについて新たなPOSTを行わない。",
    "読み取り専用照会で、バッチ100件の入力、確定ID、external_ref、金額、状態を取得して全件突合し、実確定総額を算出する。",
    "ext-731についてs101とs102の双方を重複候補として記録し、finance-ownerへ取消判断をエスカレーションする。現場担当者は削除・返金・取消を実行しない。",
    "09:10期限の報告要件に従い、判明済みの重複、未照合範囲、送信停止状態、再開条件を運用側へ報告する。",
    "全件照合と権限者による重複処理方針の確定までは、ログ件数100やGETの一時的な0件だけを根拠にバッチを成功扱いしない。"
  ],
  "minimal_fix": [
    "v2.4ではIdempotency-Keyに依存しない。ローカル永続台帳に各送信の状態を送信前に永続化し、少なくともREADY、IN_FLIGHT、CONFIRMED、UNKNOWN/HOLDを区別する。",
    "単一ワーカーと利用可能な排他機構を使い、同一台帳項目を別プロセスが同時送信できないようにする。",
    "外部POSTの前には成功ではなくIN_FLIGHTを記録する。正常応答を確認して初めてCONFIRMEDへ遷移する。",
    "POSTがタイムアウト、通信断、または送信中のプロセス停止になった場合はUNKNOWN/HOLDへ遷移し、自動再POSTを禁止する。再起動時もIN_FLIGHTまたはUNKNOWN/HOLDを自動送信しない。",
    "UNKNOWN/HOLDはGET照会と台帳・バッチ照合で解消し、人による保留解除を経た場合だけ再送可能にする。GETは最大60秒の反映遅延を考慮し、少なくともその整合性窓内の0件を失敗確定として扱わない。",
    "この対策は重複リスクを抑えるがexactly-onceは保証しない。台帳更新と外部POSTを同一トランザクションにできず、v2.4サーバーにも重複拒否保証がないため、送信結果不明状態は運用上の保留として扱う。"
  ],
  "resume_checks": [
    "100件すべてについて入力と確定IDを突合し、各入力の確定件数、金額、状態を確認する。予定総額1,000,000円と実確定総額の差異を説明できる状態にする。",
    "ext-731の2件についてfinance-ownerの判断と承認を記録し、必要な取消等が権限を持つ手段で実施された場合は、その結果を読み取り専用照会で確認する。",
    "タイムアウト試験で、POST結果不明時に台帳がUNKNOWN/HOLDとなり、自動再POSTされないことを確認する。",
    "再起動試験で、IN_FLIGHTまたはUNKNOWN/HOLDの項目が起動後に自動再送されず、照会または人の保留解除を要求することを確認する。",
    "反映遅延試験で、GETが0件でも最大60秒の整合性窓内には再POSTしないことを確認する。",
    "排他試験で、利用可能な排他機構により同じ台帳項目を複数実行主体が同時送信できないことを確認する。",
    "ログ件数ではなく、台帳状態、確定ID、金額、全件突合結果を再開判定に使用することを確認する。"
  ],
  "sources": [
    "Document S: settlement-service v2.4 contract, POST /settlements — https://example.invalid/settlements/v2.4#post",
    "Document N: settlement-service v2.5 release notes, Idempotency — https://example.invalid/settlements/v2.5#idempotency",
    "Document L: incident-log 2026-09-27, Timeline — https://example.invalid/incidents/20260927#timeline",
    "Document O: operations-runbook r7, Recovery / Authority — https://example.invalid/ops/r7#recovery",
    "Document Q: proposed-hotfix r1, Changes — https://example.invalid/hotfix/r1",
    "Document E: runtime-envelope r3, Constraints — https://example.invalid/runtime/r3"
  ]
}