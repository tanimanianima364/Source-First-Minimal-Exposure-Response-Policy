# 技術判断メモ  
**調査カットオフ：2026年9月27日 00:00 UTC**

## 結論

最初に試す構成は、**Bを小さくした「独立2実行＋証拠を見ながらの統合・検証＋条件付き1回修復」**を推奨します。純粋なBの「4本生成して多数決」ではありません。2本は調査中に通信させず並列に走らせ、最後に同じ固定基盤モデルで、主張・引用・相違点を比較する統合器を置きます。意見が割れた重要論点だけ再検索し、必要な場合だけ局所修復します。

根拠は三つです。第一に、単一エージェントへ計算を足すだけのAは、一般エージェントの逐次スケーリングやGAIA上の反省実験で、停滞・悪化が実際に観測されています。:chatgpt-content-reference{index="0"} 第二に、独立候補の増加は「候補集合内に正解がある確率」をかなり上げられますが、**選択器がその正解を取り出せない**ことも実証されています。このため、Bの価値は候補数ではなく、最終統合・検証の質に依存します。:chatgpt-content-reference{index="1"} 第三に、Cの通信型マルチエージェントは条件次第で強力ですが、2026年9月のParkらの実験では、各エージェントに十分なローカル予算と密な進捗信号があることが重要で、予算を薄く配ると同じ総計算量でも単一実行を下回りました。:chatgpt-content-reference{index="2"}

したがって、**4倍は「実行数4」という意味にしない**のが重要です。パイロット時の予算台帳は、現在の1回実行の実測総費用を \(C_0\) とし、例として「独立2実行 ≤2.0 \(C_0\)、統合・検証 ≤0.75 \(C_0\)、条件付き再検索・修復の予備 ≤1.25 \(C_0\)」というハード上限にします。モデル入出力、検索API、文書取得、再ランキング、検証器、通信・統合をすべて含めます。この比率は論文から導かれた最適値ではなく、**4倍上限を破らないための試験用配賦**です。30分制約は費用とは独立した別のハード制約として測定します。

**採用を見送る条件**は、少なくとも次のいずれかです。専門家の盲検確認時間が現行より有意に短くならない、重大な誤りまたは引用不忠実性が悪化する、p95の総費用が4倍を超える、p95の壁時計時間が30分を超える、あるいは「候補のどれかは正しい」が増えても最終選択後の成果物が改善しない場合です。確度は**中程度**です。今回の文献には深いWeb調査そのものを扱う研究がありますが、「30分・総費用4倍・専門家確認時間」を同時に主要評価指標とした実験はありません。

---

## 研究比較

以下はカットオフ以前の版に固定しました。6本すべて独自実験を含み、うちParkらとCIPHERは**2026年7月1日以降に初公開**されています。

| 研究・版管理 | 対象タスク／モデル・構成 | 計算予算の単位・含まれるもの | 評価・選択 | 主要結果 | 今回への適用限界 |
|---|---|---|---|---|---|
| **Park et al., “Scaling Discovery through Test-Time Communication”**。初公開 **2026-09-17**、arXiv v1、使用版 v1 (2026-09-17)。今回の検索では査読済み掲載先未確認。:chatgpt-content-reference{index="3"} | ARC-AGI-3、ポリオミノ充填、MNIST、Terminal-Bench。主にClaude Sonnet/Opus 4.6、MNISTはGPT-5.6 Sol。独立 `best@k` と、共有追記ワークスペースを使う `team@k`。専任オーケストレータなし。 | ARCは行動予算・**出力トークン**、長期実験は時間（packing最大72h、MNIST 96h）。各エージェント側の資源も操作。検索料金等を含む総金額ではない。 | ARC等は環境上の客観的進捗・成功判定。Terminal-Benchは公式 verifier。 | ARCで通信チームは十分な予算下では強く、最終solve-rateに独立方式が追いつくには best@13 / best@33 が必要で、出力トークンはチームの約3.8×/4.9×。一方、低計算域（1 agentあたり≤400K output tokens）では独立方式が優勢。**同じ総予算にするため5 agentを各0.2×にするとteam@5はsingleを下回る**（Fig.3–4）。:chatgpt-content-reference{index="4"} Terminal-Benchでは single 52.53%、independent pass@2平均62.36%、team@2平均60.67%（Table 3）。:chatgpt-content-reference{index="5"} | 成功した通信実験は、客観的で頻繁な進捗信号があり、数時間～数十時間走らせる条件を含む。30分・4倍にそのまま移植できない。Terminalの「independent pass@2」はoracle的候補存在率で、実運用の選択済み回答正答率ではない。 |
| **Heuillet & Peddiraju, “CIPHER: A Decoupled Exploration-Selection Framework for Test-Time Scaling of Data Science Agents”**。初公開 **2026-07-15**、arXiv v1、使用版 v1。同日版。査読済み掲載先は今回未確認。:chatgpt-content-reference{index="6"} | Infi-DA-Bench 257件、InsightBench 100件。最初にN案を作り、M案を選び、並列実行後に集約。Haiku 3.5 / Sonnet 3.7。 | 入出力**トークン数**を報告。N/Mおよびリーダーモデルが主な計算操作。検索等のユーザー想定総費用ではない。 | random / max-entropy / clustering / goal-alignmentで案を選択。self aggregation または強いleader。Infiは公式評価、InsightはClaude 3.5 Haiku judge。 | M=1→3で +7.2pp (Infi) / +3.3pp (Insight)、3→5は +1.9pp / +1.4ppと限界効用が低下。:chatgpt-content-reference{index="7"} 強いleaderで +2.81点 / +4.52点、self aggregationでは生成戦略間に有意差なし。:chatgpt-content-reference{index="8"} Infiで CIPHER(1,1) 69.13→CIPHER†(10,5) 81.06、raw tokenは21K→91K（Table 4）。:chatgpt-content-reference{index="9"} | 好成績の一部が**より強い統合モデル**に依存し、基盤モデル固定という相談条件から外れる。著者自身も「完全にcompute-matchedな5×単一/独立 baseline」を評価していないと記載。:chatgpt-content-reference{index="10"} データ分析エージェントから文献調査への転移は未実証。 |
| **Wan et al., “Inference-Time Scaling of Verification: Self-Evolving Deep Research Agents via Test-Time Rubric-Guided Verification”**。arXiv初公開 **2026-01-22**、v2 2026-04-29。使用版は **Findings of ACL 2026, July 2026**。査読付き会議論文。:chatgpt-content-reference{index="11"} | GAIA-Web/Full、XBench-DeepSearch、BrowseComp。主にClaude 3.7 Sonnet、ほかGPT-4.1等。Web閲覧を伴うdeep research。 | **検証ラウンド数**。各ラウンドで軌跡を要約→疑義を分解→最大3件の追加外部証拠質問→再検索・判定。総トークン、ドル、壁時計の完全な内訳は報告されない。 | rubric-guided verifierが外部証拠を取りに行き、1–4でjudge。acceptedなら停止。 | verifier meta-evalは precision 75%、recall 71.43%、accuracy 75.56%、F1 73.17（Table 2）。:chatgpt-content-reference{index="12"} GAIA Fullは 52.22→round 4で60.12、round 10では58.93。DeepSearchも41→47 (r2)→44 (r10)と非単調（Tables 3–4）。:chatgpt-content-reference{index="13"} | 今回の業務に最も近いが、verifier自体が不完全で、正答の誤rejectもある。費用が4×以内、時間30分以内という証拠はない。追加学習を行う別実験は今回の判断根拠から除外。 |
| **Li et al., “Benchmark Test-Time Scaling of General LLM Agents”**。初公開 **2026-02-22**、arXiv v1、使用版 v1。同日版。査読済み掲載先は今回未確認。:chatgpt-content-reference{index="14"} | 検索、coding、reasoning、tool-useを含むGeneral AgentBench。parallel samplingとsequential scalingを比較。 | parallelは最大K=4。sequentialは長いコンテキスト。費用表はモデルAPIのprompt、tool出力を含むinput、中間message、outputの**トークン料金**を計上するが、外部検索API等の料金を明示的には総計していない。:chatgpt-content-reference{index="15"} | `pass@K` に加え、pointwise/pairwise self-choiceで実際に最終候補を選択。外部GPT-5 verifierも試験。 | pass@KはKとともに単調増加し、K=1→4で平均およそ50%相対改善。ただし**self-choiceはpass@Kを一貫して下回り、Kを増やすと悪化する場合もあり、外部GPT-5 verifierも概してself-judgmentを上回らなかった**（Fig.8）。:chatgpt-content-reference{index="16"} Sequential scalingは多くのモデルで停滞・飽和・悪化。:chatgpt-content-reference{index="17"} | Bに対する最も重要な反証寄りの結果。「正しい候補を生成する」ことと「採用すべき候補を選ぶ」ことは別。評価タスクも引用忠実性ではなく、元ベンチマークの正答判定が中心。 |
| **Kim et al., “Towards a Science of Scaling Agent Systems”**。初公開 **2025-12-09**、v3 **2026-04-08**、使用版v3。査読済み掲載先は今回未確認。:chatgpt-content-reference{index="18"} | 6ベンチマーク、260構成。Single、Independent、Decentralized、Centralized、Hybrid。BrowseComp-Plusは動的Webナビゲーション・情報抽出を含む。 | 方式間を平均 **4,800 reasoning tokens/trial** とtool-call accessで揃える。turn数とcoordination overheadも報告。総ドル費用や検索料金一致ではない。 | 各ベンチマークのsuccess。 | 全体平均 success: SAS .466、Independent .370、Decentralized .477、Centralized .463、Hybrid .452。平均turnは7.2 / 11.4 / 26.1 / 27.7 / 44.3（Table 5）。:chatgpt-content-reference{index="19"} BrowseComp-PlusではDecentralized .347 vs SAS .318（約+9.2%相対）だが、IndependentはSAS比約−35%。タスクで優劣が大きく変わる（Fig.2）。:chatgpt-content-reference{index="20"} | reasoning-token一致は今回の「検索等を含む4×総費用」と違う。協調はturn数・通信負荷が大きい。著者もツール多用タスクのcoordination failureや一部n=20による大きいCIを限界として挙げる。:chatgpt-content-reference{index="21"} |
| **Zhu et al., “Scaling Test-time Compute for LLM Agents”**。初公開 **2025-06-15**、arXiv v1、使用版 v1。同日版。OpenReviewに匿名ACL投稿版は確認したが、今回の検索では採録を確認できず。:chatgpt-content-reference{index="22"} | GAIA 165問、GPT-4.1、CodeAgent系。Best-of-N、beam/DVTS、reflection、複数merge方法。 | 主に**sampling width**、reflection頻度など。総トークン、検索、judgeを含むall-in金額は提示されない。 | BoN候補を voting / scoring / listwise 等で統合。Pass@Kも別に報告。 | baseline 55.76→BoN 63.03（Table 1, p.6）。一方、every-step reflectionは55.15、選択的reflectionは56.36（Table 2, p.7）。:chatgpt-content-reference{index="23"} 同じBoN候補でも voting 56.8、scoring 59.39、listwise 63.03（Table 3, p.8）で、**選択器だけで大きく差が出る**。:chatgpt-content-reference{index="24"} GPT-4.1 pass@1 55.76、pass@2 60.49、pass@4 69.14（Table 5）。:chatgpt-content-reference{index="25"} | width=4をそのまま「4×費用」と読めない。生成4本にmerge/judge等が加わり、all-in同額比較ではない。GAIAは文献比較表・引用忠実性を直接評価しない。 |

### 原文からの定量的な検算

**1. Zhuら：BoNの実現済み最終スコア。** Table 1の同一GAIA設定で baseline 55.76、BoN 63.03なので、差は **+7.27パーセントポイント**。相対改善率は \(7.27 / 55.76 = 13.04\%\) です。ここは「候補内に正解があった率」ではなく、論文が報告するmerge後のスコアです。:chatgpt-content-reference{index="26"}

**2. DeepVerifier：ラウンド増加は単調改善ではない。** GAIA Fullで52.22→round 4の60.12は **+7.90pp、相対+15.13%**。ところがround 10は58.93なので、round 4のピークから **−1.19pp** です。検証ループ自体が誤るため、「もっと長く回すA」が自動的に有利とはいえません。:chatgpt-content-reference{index="27"}

**3. ParkらのTerminal結果は、候補存在率と最終回答率を分けて読む必要があります。** single 52.53%→independent pass@2 62.36%は **+9.83pp、相対+18.71%**。team@2は60.67%でsingle比 **+8.14pp、相対+15.50%** です。しかし62.36%は「2本のどちらかが公式verifierに通る」pass@2であり、**本番でselectorが62.36%を実現したという意味ではありません**。この2数値を直接「独立方式が1.69pp優れる」として製品正答率比較に使うのは不適切です。:chatgpt-content-reference{index="28"}

**4. CIPHERのトークン比も、4倍“費用”とは同義ではありません。** Infiで(1,1)は19K input + 2K output = 21K、CIPHER†は86K + 5K = 91Kなのでraw token数では **4.33×**、inputだけなら **4.53×**。スコアは69.13→81.06、**+11.93pp、相対+17.26%**です。ところが後者は強いleaderモデルも使うため、実際の金額比は単純な91/21ではなく、今回の「固定モデル・検索費込み≤4×」を満たした証拠にはなりません。:chatgpt-content-reference{index="29"}

---

## 横断的な考察

### 1. Zhuの「BoNは有効」とLiの「候補を増やしても選べない」は矛盾するか

**実証された部分としては矛盾しません。** Zhuら自身でも、同じBoN系の候補に対してmerge方式を変えるだけで56.8から63.03まで開きます。つまり候補生成だけでなくselectorが支配的です。:chatgpt-content-reference{index="30"} Liらはこれをより明示的に分離し、oracle的なpass@Kは伸びても、実際のself-choiceが追いつかず、ときにはK増加で悪化すると示しました。:chatgpt-content-reference{index="31"}

今回への**推測**は、「論文調査では引用元を外部確認できるので、純粋な自己採点よりselectorを強くできる可能性がある」です。DeepVerifierはその方向の直接証拠ですが、accuracy 75.56%で完全ではありません。したがってBを採るなら、単なるLLM投票ではなく**主張―引用対応表、相違点抽出、重要箇所だけの再検索**をselectorに持たせる必要があります。:chatgpt-content-reference{index="32"}

### 2. Parkの通信型チームの大幅改善と、Kimの小さい/負のマルチエージェント効果は矛盾するか

これも、現在の証拠では**条件差でかなり両立します**。Parkらは、通信が成功する条件として十分な個体予算と有効な中間進捗信号を示しており、各agentを0.2×まで薄めると、総計算量を揃えてもsingleより悪化します。また低compute域では独立探索が上回ります。:chatgpt-content-reference{index="33"} Kimらは総reasoning-token予算を固定した比較で、協調方式のturn数が大幅に増え、BrowseComp-PlusではDecentralizedがわずかに上回る一方、タスクによって協調が悪化します。:chatgpt-content-reference{index="34"}

**実証された説明**は「通信の便益は課題と予算配分に依存する」です。**私の仮説**は、30分・4倍の文献調査では、ARCのような密な自動進捗スカラーがなく、通信文自体も検証対象になるため、現段階ではParkらの強いC条件よりKimらのcoordination-tax条件に近い、というものです。これは実験で覆り得ます。

### 3. DeepVerifierの反復改善と、Aが伸びない研究は矛盾するか

重要なのは「長く考える」の中身です。Zhuのevery-step reflectionは55.76→55.15と悪化し、Liのsequential scalingにも飽和・悪化があります。:chatgpt-content-reference{index="35"} 対してDeepVerifierは、答え全体を漫然と推敲するのでなく、**疑わしい主張を分解し、外部証拠質問を作り、少数の追加検索を行う**構造です。:chatgpt-content-reference{index="36"} それでもround 4以降に悪化するので、支持されるのは「限定的な検証・修復」であって「時間いっぱい自己反省を続けるA」ではありません。

### この業務に落とすと

推奨B-liteでは、二つの独立実行に**同じ最終回答を書き直させ続けない**ことがポイントです。各実行には「候補論文、版、重要数値、原文位置、支持/反証、未解決点」を構造化して残させます。統合段階では、二者一致を信頼スコアとみなすのではなく、相違した重要主張を優先して原文へ戻ります。DeepVerifier型の「最大数件の外部証拠チェック」は、この用途で追加コストを局所化する根拠があります。:chatgpt-content-reference{index="37"}

一方、**推奨に最も不利な結果はLiら**です。独立候補を増やしても、選択済み回答が改善する保証はなく、より強そうな外部GPT-5 verifierでさえ一貫した解決策になりませんでした。:chatgpt-content-reference{index="38"} さらにCIPHERのB寄りの好成績は、強いleaderを使う条件を含み、完全な同総費用独立baselineとも比較していません。:chatgpt-content-reference{index="39"} したがって、「Bの論文が多いからBを採用」ではなく、**あなた方の専門家確認時間を本当に削れるselectorを作れるか**が採否点です。

純粋Cを最初にしない理由も同じです。途中共有が、論文ID・DOI・引用位置・否定的結果など**検証可能な短い事実**に限られ、通信から新しい誤りが増えないことを自社データで示せれば、次段階の有力候補になります。現時点では、30分制約と不完全な検証器のもとで、その追加通信費を先払いする証拠が弱いです。

---

## 推奨を覆し得る小規模比較実験

これは**実験計画であり、実施済みではありません**。40件/週という実運用量を利用し、まず40件の代表的依頼で、同一課題を次の4条件にランダム化または全条件でpaired評価します。

| 条件 | 実装 | 予算条件 |
|---|---|---|
| **O：現行** | 現在の単一1回実行 | 実測 \(C_0\)、現行timeout |
| **A4** | 単一agent。追加検索・推敲・反省を継続 | all-in ≤4 \(C_0\)、30分 |
| **B4** | 独立2実行 → 証拠ベースlistwise統合 → 重要相違点の限定再検索 → 必要時のみ1回修復 | all-in ≤4 \(C_0\)、30分 |
| **C4** | 2～3 agentが共有claim/evidence ledgerに途中成果・失敗を書き、最後に統合 | 通信・統合も含めall-in ≤4 \(C_0\)、30分 |

公平性の単位は**候補数ではなく実測all-in総費用**にします。同じ基盤モデル、同じ検索プロバイダ、同じツール、同じ課題時点を使い、モデルinput/output、検索query、文書取得、reranking、validator、merge、agent間通信をすべて台帳化します。4×上限と30分上限は独立に判定し、どちらかに達した時点の最良成果物を提出します。A/B/Cが上限を使い切らなかった場合も実使用額をそのまま報告します。

専門家には**方式名、生成ログ、候補数を隠し**、書式を統一した最終成果物と引用元だけを提示します。主要評価指標は「受理可能な最終成果物にするまでの専門家の確認・修正時間（分/依頼）」とします。品質のguardrailとして、①意思決定を左右する重大な誤りが1件以上ある依頼の割合、②decision-bearingな主張―引用ペアの `完全支持 / 部分支持 / 非支持 / 誤版`、③重要研究の欠落、④最終採用判断が専門家基準と一致する割合、を記録します。

特にBについては10件程度の診断サブセットで、最終回答の評価が終わった後に生の2候補も別途判定し、**「少なくとも1候補が受理可能だった割合」**と**「selector後の最終成果物が受理可能だった割合」**を分けます。これにより、論文でしばしば混同されるpass@K的なcandidate availabilityと、実運用上のselected accuracyを直接測れます。

確率変動を見るため、40件すべてを1 seedだけで終わらせず、事前指定した10件程度を別seedでも再実行します。主解析は同一課題内のpaired差とし、課題単位bootstrapで95% CIを出します。重大誤りのような低頻度イベントについては、40件で精密な率推定ができるとは扱わず、件数とCIを併記します。少なくとも25%程度は専門家2名で独立評価し、判定不一致も記録します。

**事前採用基準の例**として、B4は現行Oに対して専門家確認時間を中央値または事前指定した平均指標で**20%以上短縮**し、そのpaired bootstrap 95% CIが少なくとも改善方向にあり、重大誤りが増えず、引用忠実性が2pp以上悪化せず、p95費用≤4×、p95壁時計≤30分を全て満たす場合に採用候補とします。20%・2ppは研究から導かれた閾値ではなく、運用上の事前規則です。

反対に、最初の20件時点である方式が現行より**意思決定を変える重大誤りを2件以上余分に発生**させる、decision-bearing citationの非支持率が10%を超える、誤版引用・存在しない出典などの系統的障害が見つかる場合は、その方式を早期中止する、と事前登録しておくのが妥当です。さらにA4またはC4が同じ4×/30分制約でB4より確認時間を例えば10%以上追加で短縮し、品質guardrailも悪化させないという結果になれば、今回のB-first推奨は覆すべきです。

---

## 短い検索記録

検索では `"test-time scaling agents parallel best-of-n verifier 2025 2026"`、`"multi-agent communication test-time 2026"`、`"deep research verification test-time scaling"`、`"agent systems scaling BrowseComp"`、各論文の正確なタイトル、およびarXiv・ACL Anthology・OpenReview上の版/掲載情報を組み合わせました。レビュー論文のみのもの、agentic retrievalとの関係が薄い純粋な数学・coding scaling、カットオフ後に初公開されたもの、主要実験条件を本文で確認できないものは中核から外しました。

**採用した6本はすべて本文PDFを取得して実験節・表・図を確認**しました。要旨だけから実験条件を補った論文はありません。ZhuらについてはarXiv本文は取得できましたが、OpenReview側の採否を今回の取得経路では確認できなかったため、査読採録を断定していません。CIPHER、Park、Li、Kimについても、今回の検索範囲では査読済み掲載先を確認できなかったため、そのまま「未確認」としています。WanらのみFindings of ACL 2026の掲載版を使用しています。:chatgpt-content-reference{index="40"}