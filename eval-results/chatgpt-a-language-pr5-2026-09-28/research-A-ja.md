# 技術判断メモ

## 結論

**最初に試すのは B を中心にした限定的ハイブリッド**を推奨します。具体的には、**同じ固定基盤モデルで2本の調査を相互非共有で並列実行 → 別コンテキストの検証・統合工程で主張と一次資料を照合 → 不一致だけを限定的に再検索・修正**する構成です。A の「時間がある限り推敲」は採らず、修正は verifier が具体的な欠陥を示した場合だけにします。C の常時共有型も初回候補にはしません。

根拠は、(i) 独立候補＋比較選択は web/tool agent でも改善例がある、(ii) 一律の自己反省は改善せず悪化する例がある一方、**分解された検証フィードバック**は deep-research task で有効、(iii) C の最も強い2026年の結果は魅力的だが、成功条件が**4倍・30分を大幅に超える実験規模**であり、そのまま導入条件へ外挿できない、という3点です。:chatgpt-content-reference{index="0"}

費用上限の初期配分は、あくまで**実費の会計枠**として「候補1 ≤1.0×、候補2 ≤1.0×、検証・統合 ≤0.8×、条件付き再検索・修正の予備 ≤1.2×」を置くのが妥当です。未使用枠は使いません。これはトークン数や実行時間への換算ではありません。モデル課金、検索・fetch/PDF取得、検証、統合、エージェント間メッセージ、retry をすべて同じ ledger に計上し、壁時計は別に30分の hard limit とします。

**採用見送りの中心条件**は、品質を保ったうえで専門家確認時間を十分に削れないことです。後述のpilotでは、中央値で **20%以上の確認時間短縮**を採用側の最低条件とし、引用忠実性の悪化 >2ポイント、重大誤りの悪化 >5ポイント、または「正しい候補は存在するのに自動統合が誤った答えを選ぶ」失敗が頻発する場合は B を見送ります。

---

## 研究比較

調査対象は **2026年9月27日 00:00 UTC以前に公開済みの版**に固定しました。以下5本はいずれも独自実験を含み、うち *LLM-as-a-Verifier* と *ArcticSwarm* は2026年7月1日以降の初公開です。

| 研究・公開履歴 | 対象タスク／モデル・構成 | 予算単位・含む費用／評価 | 主な結果 | 本件への適用限界 |
|---|---|---|---|---|
| **Zhu et al., Scaling Test-time Compute for LLM Agents**。初公開 2025-06-15、使用 **v1, 2025-06-15**。査読状況は確認できず、arXiv preprint。[一次資料（arXiv v1本文）](https://arxiv.org/html/2506.12928v1?utm_source=chatgpt.com) :chatgpt-content-reference{index="2"} | GAIA validation 165件。主に GPT-4.1＋SmolAgents CodeAgent。BoN/step-wise BoN/beam/tree、reflection、verifier/mergeを比較。parallelは width=4、beam size=2。:chatgpt-content-reference{index="3"} | 「計算予算」は主に候補幅・探索幅。**token/API検索料金を合算したtotal-cost比較ではない**。回答選択は voting/scoring/list-wise。 | GPT-4.1 baseline **55.76→BoN 63.03**。一方 every-step reflection は **55.15**、選択的reflection (<2) は56.36。原文 Table 1（PDF第6頁）、Table 2（第7頁）。:chatgpt-content-reference{index="4"} | Bには直接的な示唆。ただし4候補≠4倍実費。GAIAの短い正解型taskで、長い論文比較表や専門家確認時間は評価していない。異種モデルによるdiversityは「基盤モデル固定」の本件には使えない。 |
| **Liu et al., Budget-Aware Tool Use Enables Effective Agent Scaling**。初公開 2025-11-21、使用 **v2, 2026-08-17**。Google Research は **COLM 2026** と記載。[一次資料（arXiv v2本文）](https://arxiv.org/html/2511.17006v2?utm_source=chatgpt.com) :chatgpt-content-reference{index="6"} | BrowseComp / BrowseComp-ZH / HLE-Search。Gemini 2.5 Pro/Flash、Claude Sonnet 4。Budget TrackerとBATS：計画→検索→自己検証→continue/pivot/restart→最終judge。:chatgpt-content-reference{index="7"} | hard budget は **search/browse各toolのcall数**。別途 unified cost = input/output/cache tokenの料金＋実際のtool API料金。従って「budget」と「実費」を明確に区別。:chatgpt-content-reference{index="8"} | Gemini 2.5 Pro、budget100/toolで BATS **24.6/46.0/27.0%**、ReAct **12.6/31.5/20.5%**（BrowseComp/ZH/HLE）。Table 3、PDF第10頁。さらに cost-performance では BrowseComp-ZH >37% を約$0.23、parallel majorityは同程度に>$0.50。Fig.10。:chatgpt-content-reference{index="9"} | 本件に最も近いcost accounting。ただし著者自身が **token・latency・tool budgetの同時制約は未検証**と明記。本件の30分制約は結果から導けない。:chatgpt-content-reference{index="10"} |
| **Wan et al., Inference-Time Scaling of Verification / DeepVerifier**。初公開 2026-01-22、使用 **v2, 2026-04-29**。**Findings of ACL 2026** 掲載。[ACL Anthology版](https://aclanthology.org/2026.findings-acl.1243/?utm_source=chatgpt.com) :chatgpt-content-reference{index="12"} | GAIA-Web/Full、XBench-DeepSearch、BrowseComp。主に CK-Pro＋Claude 3.7 Sonnet、GPT-4.1でも検証。複雑な判定を≤3個のtargeted verification questionに分解し、feedback/retry。追加学習を使わないRQ1/RQ2が本件に対応。:chatgpt-content-reference{index="13"} | feedback round数が主なtest-time scaling軸。正誤判定はdataset ground truth。**全体のtoken/tool/API実費やwall-clockをBoNと同じledgerで報告していない**。 | Verifier F1: DeepVerifier **73.17** vs vanilla agent-as-judge **61.54**。GAIA-Web Claude 3.7: **51.11→63.33**（4 feedback roundsでpeak）、10 roundsでは62.22。Table 2/3、PDF第6–7頁。:chatgpt-content-reference{index="14"} | 「長く自己反省」ではなく**欠陥を分解して確認する**ことへの強い示唆。ただし実費・30分との対応は不明。さらに誤ったverifier feedbackでcorrect→incorrectも発生し、反復を増やせば単調改善しない。:chatgpt-content-reference{index="15"} |
| **Kwok et al., LLM-as-a-Verifier**。初公開 **2026-07-06**、使用 **v2, 2026-07-07**。査読状況は確認できず、arXiv preprint。[一次資料（arXiv v2本文）](https://arxiv.org/html/2607.05391v2?utm_source=chatgpt.com) :chatgpt-content-reference{index="17"} | Terminal-Bench、SWE-Bench Verified、robotics、medical。N候補を連続scoreのverifierでpairwise比較。通常 G=20, K=8, 3 criteria。TerminalではGPT-5.5の同一モデル候補5本、別モデルをverifierに使用。:chatgpt-content-reference{index="18"} | verification scalingの単位はscore granularity、反復回数、criteria数、比較pair数。Appendixの「budget」は**verification pair数だけ**であり候補生成・tool費用を含まない。Table 9、PDF第27頁。:chatgpt-content-reference{index="19"} | Terminal: Pass@1 **83.1%、oracle Pass@5 92.1%、実選択86.5%**。SWE: 76.1/84.4/78.2%。Table 3、PDF第10頁。:chatgpt-content-reference{index="20"} | Bの重要な弱点を示す。候補を増やせば「どこかに正解」は増えるが、verifierがそのheadroomを全部回収できない。さらに主対象はcoding等で、論文調査より機械的ground truthが強い。 |
| **Yoon et al., ArcticSwarm**。初公開 **2026-09-01**、使用 **v1, 2026-09-01**。査読状況は確認できず、arXiv preprint。[一次資料（arXiv v1本文）](https://arxiv.org/html/2609.01870v1?utm_source=chatgpt.com) :chatgpt-content-reference{index="22"} | BrowseComp-Plus 830問中心。Qwen 3.5-27B。共有bulletin boardを持つが、探索中は選択的にpeer-readを禁止する **gated isolation**、専任reviewer、alternative search、commit gateを使用。つまり単純な「全員で途中共有」ではない。:chatgpt-content-reference{index="23"} | primary controlled runではend-to-end tokenを全role・cache込みで計上。各architectureで実現team size/turn数は異なる。 | Full ArcticSwarm **82.6%**、free sharing相当（−gated isolation）78.8%、さらに3-level review除去74.5%。Table 3、PDF第7頁。だが full は **24.9M tokens/case、median 83.3分**。Table 14、PDF第22頁。:chatgpt-content-reference{index="24"} | Cに最も有利な証拠だが、**本件の30分を直接満たさない**。またtoken基準で single-agent の約20–36本分に相当する比較が中心で、4×域の効果は示していない。wall-clock自体もserver load等を含みarchitecture固有値ではない。:chatgpt-content-reference{index="25"} |

### この表から直接言えること

**Aをそのまま長時間化する根拠は弱い**です。ATTSでは every-step reflection が55.76→55.15と低下し、閾値を絞ったreflectionだけが56.36まで回復しています。DeepVerifierも反対に見えますが、そこで有効なのは「続きを考え続ける」ことではなく、rubricで脆弱箇所を≤3問に分解して外部証拠を再確認する方式です。しかもGAIA-Webは4 roundで63.33まで上がった後、10 roundで62.22へ戻ります。:chatgpt-content-reference{index="26"}

そのため、本件でAを使うなら **「verifierが不備を特定した箇所だけを一度修復」**という限定用途が妥当です。「残予算があるからさらに推敲」は採りません。

---

## 横断的考察

### 1. ATTS と DeepVerifier――「reflectionは害」対「reflectionは有効」は矛盾するか

見かけ上は逆ですが、**実験された処理が異なるため、実質的には両立します**。

ATTSの毎step reflectionは baseline 55.76 に対し55.15で、頻繁なthreshold <8/<5では53.33/52.12まで落ちています。一方、最も限定した<2では56.36です。:chatgpt-content-reference{index="27"} DeepVerifierでは、答え全体を漫然と再解答するのではなく、verification targetを分解して外部証拠を確認します。同論文のablationでも、decompositionを外したvanilla agent-as-judgeはF1 61.54、完全版は73.17でした。:chatgpt-content-reference{index="28"}

**実証されている説明**は、「feedbackの頻度・対象・verifier精度が重要で、反復数そのものには単調な利得がない」です。**本件への仮説**は、論文調査では「この比較表の数値は本当にTable Xにあるか」「この結論は対象populationを越えていないか」といったclaim-level verificationが、一般的な“もう一度よく考える”より有効だろう、というものです。これは本件条件では未実証です。

### 2. 独立B と ArcticSwarmのC――Cが圧倒しているならBは不要か

ArcticSwarmはBにかなり不利な結果です。同じ約24.9M end-to-end token域で、MiroFlowの独立runを約36本集めた**実現可能なmajority voteは63.2%**なのに対し、ArcticSwarmは82.6%です。:chatgpt-content-reference{index="29"}

しかし重要なのは、その36候補に**正解が1つでも含まれるoracle Best-of-Nは86.1%**だったことです。つまり「独立探索が正解を発見できない」のではなく、**完全なselectorがないため正解候補を取り出せない**ことが大きなボトルネックです。同論文自身もoracleを「長時間researchでは利用不能な上限」と明記しています。:chatgpt-content-reference{index="30"}

したがって、これは「Cが本質的にBより優れる」という一般則ではありません。**実証されているのは、高予算・弱いmajority selectorという条件では、gated coordination＋reviewが非常に有効**ということです。またfree sharingにすると82.6→78.8へ低下しており、「途中情報を多く共有すればよい」という単純なCも支持していません。:chatgpt-content-reference{index="31"}

本件でBから始めるのは、ArcticSwarmのfull systemが median 83.3分であり、4×よりはるかに大きなsingle-agent-equivalent budgetで実証されたためです。**4×・30分域でBと小型Cのどちらが優れるかは未解決**です。

### 3. BATS と素朴なB――「parallelよりadaptive sequentialが安い」という結果

BATSも推奨に不利な証拠です。BrowseComp-ZHではearly-stop BATSが約$0.23で37%以上、parallel majorityは同程度の結果に>$0.50を要しました。:chatgpt-content-reference{index="32"}

ただしBATSの「sequential」はAの単一run延長とは違い、**budgetを明示し、constraint decomposition、verification、continue/pivot、新しいattemptを組み合わせるadaptive architecture**です。:chatgpt-content-reference{index="33"} したがって、この結果は「Aを長く動かせ」ではなく、「固定本数のfull rerunだけに予算を使うのではなく、検証後に残予算を条件付き再配分せよ」という根拠として扱うべきです。これは推奨B′の1.2×予備枠に反映しています。

---

## 原文からの定量検算

| 比較 | 検算 | 解釈 |
|---|---|---|
| **ATTS: BoN vs 1 run** | 63.03 − 55.76 = **+7.27ポイント**。相対改善率 = 7.27 / 55.76 = **+13.04%**。原文が丸めて“eight-point”とする箇所より、表値からは7.27pt。Table 1, PDF第6頁。:chatgpt-content-reference{index="34"} | パーセントポイントと相対%を分離する必要がある。 |
| **DeepVerifier: verifier F1** | 完全版73.17 − vanilla agent-as-judge61.54 = **+11.63ポイント**。相対改善 = 11.63 / 61.54 = **+18.90%**。decomposition-only 25.00との比較なら+48.17pt、相対+192.68%。Table 2, PDF第6頁。:chatgpt-content-reference{index="35"} | 論文の「12–48% improvement」は表値との差を述べた表現で、これを相対改善率として読んではいけない。 |
| **LLM-as-a-Verifier: candidate availability と実選択** | Terminal: Pass@1=83.1%、oracle Pass@5=92.1%なので候補生成のheadroomは **9.0pt**。実選択は86.5%、実際の利得は **3.4pt**（相対+4.09%）。したがってoracle headroomの回収は **3.4/9.0=37.8%**。SWEではheadroom 8.3pt、実利得2.1pt、回収 **25.3%**。:chatgpt-content-reference{index="36"} | 「候補のどこかに正解がある確率」と「実際に正解を選べる率」は大きく違う。本件で専門家時間を減らすには後者が重要。 |
| **BATS: nominal budget と実費** | Gemini 2.5 Pro: ReAct budget=100 はacc12.6%, cost 9.9¢。Budget Tracker budget=10 は12.8%, 6.8¢。精度は **+0.2pt（相対+1.59%）**、実費は **−31.31%**。search call −40.45%、browse −19.85%。Table 2, PDF第6頁。:chatgpt-content-reference{index="37"} | nominal tool budgetが10倍違っても実費は10倍ではない。「4×予算→4×tokens/時間」の換算が不適切な実例。 |

同様に、LLM-as-a-VerifierのAppendix Table 9は「queried pairs」をverification budgetとしており、候補生成そのもののcostを含みません。したがって、例えば4,723 pairと6,609 pairを本件の「総費用4×」に直接対応させることはできません。:chatgpt-content-reference{index="38"}

---

## 推奨する初期構成

**B′: isolated two-pass + source-aware verifier + conditional repair** とします。

1. 同じ固定基盤モデルで、**2本の候補調査を同時実行**する。相互の途中出力は見せない。両方とも最終の比較表・判断まで作らせ、単なるsubtask分割にはしない。検索方向は意図的に少しずらし、一方は主要一次研究の再現、もう一方は反証・境界条件・版管理を強く要求して、同じ検索経路への相関を減らす。
2. 2本の後に、同じ固定モデルを別contextで **source-aware verifier/integrator** として動かす。多数決ではなく、decision-critical claimごとに「一次資料は取得済みか、版・日付は正しいか、引用は主張をentailするか、数値を表から再計算できるか、適用範囲を越えていないか」を比較する。
3. verifierが食い違いや未検証claimを列挙した場合だけ、残り予算でtargeted search/repairを行う。問題がなければ早期終了する。途中の自由な相互chatは導入しない。

これはBを基本に、DeepVerifier/BATS型の**限定的なA**を後段に置いたものです。C的な情報共有は候補生成が終わってからだけ行います。

この推奨に最も不利なのは、ArcticSwarmが高予算域でこの種のindependent+majorityを大差で上回ったこと、BATSがadaptive orchestrationでparallel majorityより良いcost-performanceを得たこと、そしてLLM-as-a-Verifierでもoracle headroomの25–38%程度しか回収できなかったことです。したがって **B′は最終設計案ではなく、4×・30分域で最初に反証を試みる案**として扱うべきです。

---

# 推奨を覆し得る小規模比較実験

これは**実施提案であり、実施済みではありません**。

### 比較条件

| Arm | 構成 | 費用上限 |
|---|---|---:|
| P0 | 現行の単一1回実行 | 通常の1× |
| A4 | 単一agentに追加探索・自己推敲を許す。独立候補なし | ≤4× |
| **B′** | 上記2 isolated runs＋source-aware verifier＋条件付きrepair | ≤4× |
| C-lite | 同じ固定モデルの小型swarm。まず2探索者を隔離し、初回evidence collection後だけ共有＋review | ≤4× |

A/B/Cの3案は**同じ4× hard ceiling、同じ30分 hard deadline、同じモデル・retrieval provider・tool access・出力schema**にします。余剰予算を「使い切らせる」ことはしません。構成の比較時には、model input/output/cache、search、browse/fetch/PDF、verifier、integration、inter-agent communication、retryを全て同じ価格表で記録します。

小規模pilotとして、過去案件から**12件**を分野・難度・必要一次資料数で層化して選び、各armを**独立2反復**、計96出力とします。Webの時間変動が大きい案件では同じsnapshot/cutoffを使うか、少なくとも全armを狭い時間帯で実施します。初期12件でCIが判断閾値をまたぐ場合だけ、事前規定どおり20件まで拡張します。

### 盲検評価と指標

専門家にはarchitecture名、run ID、内部trajectoryを見せず、体裁も可能な範囲で正規化します。最終成果物だけをランダム順で確認し、「採用可能になるまでの確認・修正時間」をUIで計測します。25%程度は第二の専門家にも独立評価させ、重大誤り判定の一致度を確認します。

**一次指標は専門家のsign-offまでの時間**です。品質側はhard gateとして、(a) decision-criticalな全claim/table cellに対する引用忠実性、(b)誤った論文・版・ページ・数値、(c)採用判断を変え得る重大誤り、(d)重要な反証研究・適用限界の欠落を記録します。「提出されたcitationの精度」だけではcitation数を減らしてgamingできるため、**必要なdecision-critical claimが引用されているか**も分母に入れます。

B′についてはさらに、中間2候補を専門家に後から判定してもらい、**「少なくとも一方に受容可能な答えがあった率」**と**「integratorの最終答えが受容可能だった率」**を別に測ります。これで、候補生成不足とselector failureを区別できます。

### 事前に固定する採用・中止条件

採用候補とする条件を、pilotを見る前に次のように固定します。

- 全実行を4×以下・30分以内で強制終了させたうえで、B′の専門家確認時間の中央値がP0より**20%以上短い**。task単位paired bootstrapで時間比の95% CIも1.0未満であること。
- citation fidelityはP0比 **−2ポイントより悪化しない**、重大誤り率は **+5ポイントより悪化しない**。小規模pilotでその非劣性をCIから判定できなければ、「採用」ではなく**inconclusive**として事前規定の追加sampleへ進む。
- B′で「候補には受容可能解が存在したのに、統合後は不受容」となるselector failureが**10%を超える**なら、B型の自動selectionを見送る。
- A4またはC-liteが同等以上の品質を保ち、B′より**さらに10%以上短い専門家確認時間**または明確に低い実費を示した場合、今回のB′推奨を覆す。特にC-liteが4×・30分内でArcticSwarm型のdiversity効果を再現できれば、Cを次の本命とする。
- 新しい体系的な重大citation failure（存在しない出典、版違いによる結論反転など）が反復して観測されたarmは、平均scoreを待たず停止対象とする。

CIは**runではなくtaskをcluster単位**としてbootstrapし、2反復を独立sampleとして水増ししません。12件では品質の非劣性CIが広くなる可能性が高いため、「有意差なし＝同等」とは扱わないことが重要です。

---

## 判断

現時点の研究からは、**「より長い1本」より「独立した複数の証拠探索＋明示的な検証」、ただし「常時共有する大規模swarm」までは行かない**、という順序が最も導入条件に整合します。

ただし研究が直接証明しているのは、それぞれGAIA/BrowseComp/coding等のbenchmark上の性能です。**週40件の実際の論文調査で、4×実費・30分以内に専門家確認時間が減ることは、どの論文も実証していません。** とくにBの成否はcandidate generationよりもselector/verifierの質に左右される可能性があり、この点を上記pilotで独立に測ることが導入判断の核心です。

## 短い検索記録

検索では `"agent test-time scaling" parallel sequential verifier 2025 2026`、`"deep research" verification inference-time scaling`、`"multi-agent" long-horizon research shared findings 2026`、`"best-of-N" verifier agents 2026`、`budget-aware tool use agent scaling` 等から候補を広げ、arXiv/ACL Anthology/著者所属機関の一次資料へ戻りました。採用基準は「A/B/Cまたはbudget/verifierの判断に直接関係する独自実験があること」「期限以前の版本文を取得できること」「実験条件・費用単位を追えること」です。

二次的なsurvey類は中核から除外しました。また *SwarmResearch: Orchestrating Coding Agents for Open-Ended Discovery*（arXiv:2607.02807）は候補に挙がりましたが、調査時に本文HTMLを安定して取得できず、かつ機械的objectiveを持つcoding/open-ended optimizationで本件との差が大きいため、**要旨から条件を補完せず除外**しました。中核5本については本文を取得し、PDFでも主要表・図の所在を確認しています。