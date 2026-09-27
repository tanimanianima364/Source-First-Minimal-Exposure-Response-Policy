# 技術判断メモ  
**調査基準時点：2026年9月27日 00:00 UTC**

## 結論

**最初に試すべき構成は B を主軸にした「2本の独立調査 + 証拠ベースの検証・統合」です。** 具体的には、同じ固定基盤モデルで2実行を並列に走らせ、両者が終了するまで相互通信させず、その後に別工程で一次資料を再確認し、相違点を解消して比較表と採用判断を作ります。Aのような無条件の長時間継続は補助的な再調査に限定し、Cの途中通信は第1候補にしません。

理由は、追加計算で**正しい候補が生成される確率はかなり上がる一方、その正解を選べない「verification gap」が複数研究で再現**されているからです。一般エージェントでは K=1→4 で pass@K が平均約50%増えても自己選択が追随せず、外部GPT-5 verifierさえ悪化要因になる例があります。 :chatgpt-content-reference{index="0"} 2026年8月の大規模研究でも、正解候補が94.62%の問題に存在していても、reference-free verifierの最終正答率は86.56%でした。 :chatgpt-content-reference{index="1"}

したがって4倍枠を3～4本目の候補生成まで使い切るより、**概ね2倍までを独立探索、残り最大2倍を「出典の再読・数値検算・候補間の相違解消・統合」に残す**方が今回のボトルネックに整合します。これは論文が直接証明した最適配分ではなく、下記の証拠から導く導入仮説です。

最も強い反証は二つあります。第一に、等thinking-token条件では単一エージェントがmulti-agentをほぼ一貫して上回った研究があります。 :chatgpt-content-reference{index="2"} 第二に、2026年9月の研究では、十分な計算量と信頼できる途中評価がある場合、通信型チームが独立実行を大差で上回っています。 :chatgpt-content-reference{index="3"} したがってBの採用は実測で決めるべきであり、30分・4倍で成功する保証はありません。

---

## 中核研究の比較

以下6本を中核にしました。**6本すべて独自実験を含む一次研究**で、Hariri et al. と Park et al. は2026年7月1日以降の初公開です。本文はすべて、指定版のarXiv HTML本文まで取得して確認しました。ページ番号ではなく、版に依存しにくい**節・表・図番号**を所在として記します。

| 研究・版 | 対象タスク | モデル・実行構成 | 計算予算・含む費用 | 評価・選択 | 主要結果と原文所在 | 今回への適用限界 |
|---|---|---|---|---|---|---|
| **Li et al., *Benchmark Test-Time Scaling of General LLM Agents***。初公開 **2026-02-22**、使用 **v1, 2026-02-22**。査読状況未確認。 :chatgpt-content-reference{index="4"} | Search、coding、reasoning、tool use。BrowseComp 124、WebVoyager 65、SWE-Bench 50等（Table 1）。 :chatgpt-content-reference{index="5"} | 10モデル。Sequential＝同じ軌跡を延長、Parallel＝独立K軌跡。K≤4、context≤196K。温度0.7。 :chatgpt-content-reference{index="6"} | API token cost。入力にはprompt、tool outputs、再投入された中間messageを含め、出力tokenも課金式に含む（App. C.1）。ただし検索サービス固有料金等まで統一した「総運用費」ではない。 :chatgpt-content-reference{index="7"} | pass@K、自己pointwise/pairwise選択、GPT-5外部verifier。 | Sequentialは多くの条件で停滞・振動・劣化（§4.2）。K=1→4のpass@Kは平均約50%向上するが自己選択は追随せず、場合によって悪化。GPT-5 verifierも概して自己判定以下（§4.3, Figs.5/8）。 :chatgpt-content-reference{index="8"} | 今回に比較的近いweb/tool agentだが、学術比較表・引用忠実性・専門家確認時間は評価していない。 |
| **Zhu et al., *Scaling Test-time Compute for LLM Agents***。初公開・使用版 **v1, 2025-06-15**。査読状況未確認。 :chatgpt-content-reference{index="9"} | GAIA validation 165件。web search＋multimodal files。 :chatgpt-content-reference{index="10"} | 主実験GPT-4.1。BoN、BoN-wise、beam/tree search、reflection。sampling width=4。多様化実験では他モデルも混合。 :chatgpt-content-reference{index="11"} | 主に**sampling width**で比較。verifier/merge/searchを含む統一された金額ベース総費用は本文で提示されていない。 | voting、scoring、list-wise verifier/merge。 | GPT-4.1 baseline 55.76→BoN 63.03（Table 1）。List-wise BoN 63.03、voting 56.8、scoring 59.39（Table 3）。毎step reflectionは55.15でbaseline 55.76を下回る。 :chatgpt-content-reference{index="12"} | Bを支持するが「候補数4＝総費用4倍」ではない。mixed-modelの74.55 pass@4は基盤モデル固定条件には使えない。なおv1 HTML内に “August 24, 2026” と表示される一方、arXiv version historyは2025-06-15 v1。ここではversion historyを版日として扱った。 :chatgpt-content-reference{index="13"} |
| **Tran & Kiela, *Single-Agent LLMs Outperform Multi-Agent Systems…***。初公開 **2026-04-02**、使用 **v2, 2026-04-11**。査読状況未確認。 :chatgpt-content-reference{index="14"} | FRAMES、MuSiQue 4-hop。 | Qwen3、DeepSeek-R1-Distill-Llama、Gemini 2.5。SAS対Sequential、parallel roles、debate、ensemble等。 :chatgpt-content-reference{index="15"} | **global thinking-token budget**。planner/aggregatorは「可能な限りnear budget-neutral」。検索、通信、API金額の総コストではない。 | task accuracy。 | 100-token極小条件以外、SASが最良または最良と統計的に区別不能（§5.1）。またnominal 10kでも実消費はQwen/MuSiQue SAS 1,462、Debate 4,465等と大きく異なる（Table 4）。 :chatgpt-content-reference{index="16"} | Aに有利な重要な反証。ただし外部検索・引用検証のない静的multi-hop QAで、予算単位も今回の「推論＋検索＋通信＋検証費」と異なる。 |
| **Wunderlich et al., *Multi-Agent Reasoning Improves Compute Efficiency***。初公開・使用 **v1, 2026-05-02**。arXivコメントは **ACL 2026 SRW accepted**；査読方式の詳細は未確認。 :chatgpt-content-reference{index="17"} | MMLU-Pro 1,000問、BBH。 | 主にLlama 3.1 70B。同一LLMをproposerに使う設定。self-consistency、self-refinement、debate、MoA。 :chatgpt-content-reference{index="18"} | FLOPs＋memory transferから理論execution timeを算出。8×A100 40GB、4-bit、batch16前提（App. B）。 :chatgpt-content-reference{index="19"} | 最終choiceのlog-likelihood、debateではvote等。 | comparable computeでdebateがself-consistency比 **+1.3pp**、MoA **+2.7pp**。最大予算20×CoTでは最大+7.1pp（Abstract/§5）。 :chatgpt-content-reference{index="20"} | Cを支持するが、静的多肢選択・明確な正解・最大20×。金額、検索、通信API費、専門家時間を含む今回の4×ではない。MoAも「途中の失敗を共有するC」と同義ではない。 |
| **Hariri et al., *Test-Time Scaling in Reasoning LLMs***。初公開 **2026-08-04**、使用 **v2, 2026-08-31**。査読状況未確認。 :chatgpt-content-reference{index="21"} | MMLU-Pro、BBH、競技数学等。192,000回答の候補bankを用いたselection実験等。 | sequential、repeated candidate、prefix searchを区別。複数open-weight reasoning models。 | 論文の会計原則ではgenerationだけでなく**warm-up、破棄token、evaluator、controller、final decision**を同じbudgetへ入れる。latencyは別軸。 :chatgpt-content-reference{index="22"} | pass@k、plurality、logprob、reference-free pointwise verifier、goldを見るdiagnostic verifier。 | median Pass@k は56.49%→82.08%（k=1→80）。Qwen3-30Bではpass@80 91.67%に対しplurality 78.33%。別のQwen3.6では94.62%のpass@80に対しreference-free selection 86.56%（Figs.5/6）。verifier計算はcandidate-count軸から除外。 :chatgpt-content-reference{index="23"} | Bの最重要な注意点。数学であり文献検索ではない。k=80は今回の4×から遠いが、候補生成と選択性能を混同してはいけないという結論は直接転用できる。 |
| **Park et al., *Scaling Discovery through Test-Time Communication***。初公開・使用 **v1, 2026-09-17**。査読状況未確認。 :chatgpt-content-reference{index="24"} | ARC-AGI-3、polyomino packing、MNIST compression、Terminal-Bench 2.0。 | 同一モデル・同一toolのagents。append-only shared logで発見、反証、score等を非同期共有。 :chatgpt-content-reference{index="25"} | ARCはaction/output-token等。polyominoは3–72時間、MNISTは96時間。通信費を含むteamは最終的に独立best@kよりoutput tokenが多い。 :chatgpt-content-reference{index="26"} | 外部score/official verifier等。 | ARC full solve: team@3 4.6% vs best@3 1.4%、team@5 8.0% vs best@5 2.2%（Table 2）。一方Terminal-Benchではindependent pass@2 62.36% > communicating team@2 60.67%（Table 3）。 :chatgpt-content-reference{index="27"} | Cへの最も直接的な資料。ただし大きな成功は**数時間～96時間・明瞭な途中score**がある条件。論文自身、low-computeではcoordination taxがあり、途中feedbackが信頼できないTerminal-Benchで独立実行に負けるとしている。今回の30分・完全verifierなしには後者の方が近い。 |

### 業務固有の補助証拠

AutoResearchBench（v1, 2026-04-28）は3百万超の論文本文を検索する1,000問の学術文献探索benchmarkであり、今回の業務にタスク面で最も近い補助資料です。決定的な証拠が要旨ではなくmethod、table、appendix、citation chainにあることを明示しています。 :chatgpt-content-reference{index="28"}

ここでは「長く回せば改善」という単純な関係がありません。例えばDeep ResearchでGPT-5.4は平均6.1 turnsで7.44%なのに対し、DeepSeek-V3.2は28.8 turnsで4.21%、Kimi-K2.5は27.0 turnsで4.69%。著者らは冗長な再検索や同じ候補の反復を観察しています。 :chatgpt-content-reference{index="29"} 一方、同一agentを複数回実行するoracle pass@kは特にDeep Researchで改善していますが、Wide Researchでは同じ見落としが再現されやすく伸びが小さいとされています。 :chatgpt-content-reference{index="30"}

これは、今回 **Aを無条件に伸ばすよりBで探索経路を分散しつつ、最終予算を検証に使う**という判断を補強します。ただしAutoResearchBenchのpass@k/best@kはoracle評価であり、実運用の選択精度ではありません。

---

# 横断的な考察

## 1. Zhu と Li は本当に矛盾するか

一見すると、

- Zhu: parallel BoN は 55.76 → 63.03 と改善。list-wise selectionも有効。 :chatgpt-content-reference{index="31"}
- Li: parallel samplingで正解候補は増えるが、自己選択は追いつかず、ときに悪化。GPT-5 verifierも十分でない。 :chatgpt-content-reference{index="32"}

で逆の結論に見えます。

**実証されている差**は、ZhuがGAIA単一benchmark、GPT-4.1、width=4、専用list-wise verifierを使ったのに対し、Liはsearch/coding/reason/tool useを横断し、複数モデルでself-choiceや外部verifierまで評価した点です。またZhuは「幅4」を合わせていますが、verifierや検索を含む**同一総費用**には正規化していません。

したがって両立します。Bには「候補を複数作る能力」と「正しい候補を選ぶ能力」の二つが必要で、後者が十分ならZhu型の改善が出ても、弱ければLi型のverification gapが支配します。

**今回への私の仮説**は、回答全体を「どちらが良さそうか」とLLM judgeに選ばせるより、一次資料を再読して各主張を検証する構造化integratorに予算を使えば、このgapを縮められるというものです。これは6本の研究から直接実証されたものではないため、後述のpilotで検証対象にします。

## 2. Tran と Wunderlich は本当に矛盾するか

Tran & Kielaは「等thinking-tokenならSASが最良か同等」と報告します。 :chatgpt-content-reference{index="33"} Wunderlichらは「等computeならdebate +1.3pp、MoA +2.7pp」と報告します。 :chatgpt-content-reference{index="34"}

これも直接矛盾とは言えません。

**実証された相違**は、少なくとも次の通りです。

- 予算単位：Tranはthinking tokens。Wunderlichは特定GPU仮定から算出するFLOP/memory runtime。
- 比較対象：TranのSASは1本の長い推論。Wunderlichの主要比較相手はself-consistency。
- タスク：FRAMES/MuSiQue と MMLU-Pro/BBH。
- aggregating costの扱いも同じではない。
- Tran自身、nominal token budgetと実消費の乖離を観測している。 :chatgpt-content-reference{index="35"}

**仮説としては**、一つのcontext内で必要情報を安定して保持できるタスクでは分割・通信がoverheadになりやすく、独立探索や途中成果の合成が本質的なタスクでは並列性が価値を持ちやすい、と考えられます。しかし論文調査でどちら側になるかは、この研究群だけでは確定できません。

## 3. Park自身の正負の結果が、今回には特に重要

Parkらの通信型Cは、ARCでteam@5 8.0%対best@5 2.2%という大差を出しました。 :chatgpt-content-reference{index="36"} ただし低compute域では独立実行が先行し、teamはcoordination taxを負います。最終的なteamは独立best@kのおよそ2倍のoutput tokensも使っています。 :chatgpt-content-reference{index="37"}

さらにTerminal-Benchでは、同じ2 agentでも **independent pass@2 62.36% > communicating team@2 60.67%**。著者は、途中の公開tests等が最終正解を忠実に示さないことを理由の一つとして挙げています。 :chatgpt-content-reference{index="38"}

今回も「途中でこの論文が本当に条件を満たすか」を完全自動判定するoracleがありません。そのため、**Cを最初から全面展開する条件よりTerminal-Bench側に近い**と判断します。

---

## 原文からの定量的検算

### 検算1：Zhu et al. のBoN改善

Table 1 のGAIA validation 165件で、

- baseline = 55.76
- BoN = 63.03

なので、

**パーセントポイント差**
\[
63.03-55.76=7.27\ \mathrm{pp}
\]

**baselineを分母とする相対改善率**
\[
7.27/55.76=13.04\%
\]

です。 :chatgpt-content-reference{index="39"}

本文は「eight-point improvement」と丸めていますが、表の数値からは**+7.27pp、相対+13.04%**です。なおsampling width=4なので、これは「4候補」での比較ですが、verifier・merge・tool searchまで含む**総費用がbaselineのちょうど4倍**という意味ではありません。 :chatgpt-content-reference{index="40"}

### 検算2：Hariri et al. の「正解候補あり」と「実際に選べる」の差

Figure 6 のQwen3.6では k=80 で、

- **Pass@80 = 94.62%**：80候補のどこかに正解が存在する問題の割合
- **reference-free pointwise selection accuracy = 86.56%**：verifierが実際に1候補を選んだ後の最終正答率

したがってselection gapは

\[
94.62-86.56=8.06\ \mathrm{pp}
\]

Pass@80を分母にすれば、

\[
8.06/94.62=8.52\%
\]

の相対的なoracle-ceiling取りこぼしです。原論文も8.06ppと報告しています。 :chatgpt-content-reference{index="41"}

重要なのは、Figure 6の横軸は**生成候補数だけで、verifier計算を含まない**点です。よって「同じkだから同じ総費用」でもありません。 :chatgpt-content-reference{index="42"}

### 検算3：Park et al. のTerminal-Bench

Table 3:

- independent pass@2 = 62.36%
- communicating team@2 = 60.67%

なので、

\[
60.67-62.36=-1.69\ \mathrm{pp}
\]

independentを分母にした相対差は約 **-2.71%** です。 :chatgpt-content-reference{index="43"}

ただしここでのpass@2は「2独立候補中のどちらかが成功」というoracle的評価です。deploy時に正解を自動判定できなければ62.36%をそのまま最終回答精度とはみなせません。**同じ2 agentというだけで、選択条件も総通信費も同一ではありません。**

---

# 推奨する初期構成

### B2 + evidence verifier

1件の現行machine costを \(C_0\) とします。これはtokenだけでなく、現在課金・内部計上している推論と検索の実費です。

**第1段階：独立2実行**

- 同じ基盤モデル・同じtool access・同じ依頼文。
- 相互に途中結果を見せない。
- 各実行の実費capを最大 \(1.0C_0\)。
- 並列実行し、壁時計は例えば最長18～20分でcutする。これは費用から換算した時間ではなく、別のwall-clock guardrailとする。

各runには最終文章そのものより、最低限以下の**evidence ledger**を返させます：paper ID/版、初公開日、採否、判断根拠となる一次資料URL、表・図・節、主要数値、反証候補、不確実点。

**第2段階：最大 \(2.0C_0\) の検証・統合**

単純な多数決や「どちらの回答が良いか」judgeではなく、

- 2 runで食い違う研究・数値を抽出
- 決定に効く引用を一次資料から再取得
- cutoff/版を再確認
- ppと相対率等を再計算
- 片方だけが見つけた反証研究を検討
- 比較表を再構成
- 最後に採用判断を書く

という順にします。再検索、source reopen、integrator inferenceもすべて4倍枠に計上します。未使用予算を使い切る必要はありません。

これはBに短い統合処理を足したものですが、Aのように「同一trajectoryを漫然と延長」するのとは区別します。

### Aを最初にしない理由

一般agentでは長いcontextで停滞・劣化があり、 :chatgpt-content-reference{index="44"} GAIAでも無条件reflectionは悪化し、 :chatgpt-content-reference{index="45"} 学術検索そのものでもturn数やthinking増加と性能に単調関係がありません。 :chatgpt-content-reference{index="46"}

ただしAは捨てません。統合工程で「この1本の論文のTable 4だけ再確認」のように**未解決点が具体化した後の局所的な追加調査**に使うのが妥当です。

### Cを初手にしない理由

Cの有力な成功例は存在します。しかしParkらの成功条件は、明確な外部progress signalとかなり長い計算時間です。論文自身がlow-budget coordination taxと、途中feedbackが弱いTerminal-Benchでの敗北を示しています。 :chatgpt-content-reference{index="47"}

後からCを試すなら、自由会話型debateではなく、**「発見済み論文ID・確認済み箇所・棄却理由」だけを共有するappend-only evidence ledger**程度に限定するのが検証しやすいでしょう。

---

# 推奨を覆し得る小規模比較実験

これは**未実施の提案**です。

## 比較arm

同じ20件程度の実際の調査依頼を、少なくとも次の4条件で処理します。

- **Control**：現行1回実行、現行費用 \(C_{0,i}\)
- **A4**：単一agentを延長。総machine cost ≤ \(4C_{0,i}\)、30分
- **B4**：上記「独立2 run + evidence verifier」。総額 ≤ \(4C_{0,i}\)、30分
- **C4**：Bと同じ2 workerを使うが、途中からshared evidence ledgerを読書き可能にする。通信input/output、最終integratorも同じ4倍枠へ含める

B/Cのworker数・基盤モデル・tool accessを同じにすることで、「独立か通信か」をできるだけ分離します。

**費用は候補数やtoken数ではなく、各taskの同じmachine-cost ledgerで計上**します。モデルinput/output、search/API calls、verifier、aggregator、共有ledgerを再読するtoken、失敗して破棄した試行も含めます。Haririらが指摘するように、evaluatorや最終decisionを予算外にしてはいけません。 :chatgpt-content-reference{index="48"}

壁時計30分は別制約です。例えばB/Cではworker phaseを最大20分、残り最低10分を統合に予約すると事前固定できます。**4倍の金額から20分を導いたわけではなく、独立したscheduler設定**です。

## 課題と反復

20件は最近の実業務から、少なくとも

- 狭い条件で特定論文を探す依頼
- 複数研究の比較依頼
- 否定的証拠・「該当研究なし」を含む依頼
- 広いrecallが必要な依頼

が偏らないよう層化して抽出します。promptを調整した案件は評価setから外します。

全20件を一度ずつ4 armで実行し、さらに事前に無作為選択した5件を**別seedで全arm再実行**してrun-to-run varianceを測ります。小規模なのでCIは広くなり得ます。CIが採用条件を判定できない場合は「差なし」と決めず、**inconclusiveとして採用を見送る**のが妥当です。

## 専門家による盲検評価

system名、agent数等を隠し、表の見た目も共通templateに正規化します。可能なら**同じ専門家が同じtaskの別armを続けて見ない**よう割付を回転させ、先にソースを覚えたことによる確認時間短縮を防ぎます。一部（例えば20～25%）は二重評価して判定ずれも記録します。

主要指標は次の4つです。

1. **専門家確認時間**：成果物を開いてから承認・修正完了までのactive minutes。休止時間を除く。
2. **出典忠実性**：意思決定に使われたmaterial claimのうち、指定された一次資料・指定版が実際にそのclaimを支持する割合。
3. **重大な誤り**：論文の採否・最終判断を変え得る誤り。例：異なる版の数字、pass@kをfinal accuracyと誤認、実験条件の欠落、引用が主張を支持しない、存在しない出典。
4. **最終判断の一致**：未修正AI判断が、全証拠を確認した専門家の最終判断と一致する割合。これは専門家をoracleとみなす運用指標であり、「客観的真理」とは扱わない。

## 不確実性

各taskをpaired unitとして扱います。review timeは歪みが大きいので平均だけでなく中央値とpaired differenceを示し、task→seedの階層bootstrap等で95% CIを出します。citation fidelityはpp差、major-errorは成果物単位の絶対risk differenceを報告します。

**異なるtaskの独自scoreを平均して「A/B/Cランキング」を作るのではなく、同じtask上の差を見る**べきです。

## 事前に固定する採用・見送り条件

以下は研究結果ではなく、今回の運用向けに提案するdecision ruleです。

**Bを採用**する条件を、例えば次のすべてとします。

- machine costが全runでhard cap \(4C_0\) 内。30分を超えたrunは未完了失敗として扱う。
- 現行比で**専門家確認時間の中央値が20%以上低下**し、paired 95% CIが少なくとも「改善なし」を跨がない。
- citation fidelity差の95% CI下限が **−2ppより上**。
- major-error率の差について95% CI上限が **+5pp未満**、かつpoint estimateが現行より悪化していない。
- 上記改善が「専門家が実質的に文章を作り直している」ことで成立していない。

**Bを見送る**のは、確認時間が減らない、citation fidelity/major errorsが上記gateを破る、verifierが候補間の誤りを頻繁に選び直してしまう、または4×/30分内に統合工程を安定して完了できない場合です。

そしてこのpilotは推薦を反証可能にします。**A4またはC4がB4より専門家確認時間をさらに10%以上短縮し、同じcitation/major-error gateを満たす**なら、Bを初期構成にする根拠は覆ったと扱います。特にCが勝った場合は、Parkらの「共有可能な検証済み進捗」がこの文献調査にも存在した、という重要な実証になります。

---

## 最終判断

現状の証拠では、優先順位を「候補を増やすこと」ではなく**候補の独立性を確保した上で、残りの予算を一次資料検証へ移すこと**に置くのが妥当です。したがって最初の実装候補は **B：独立2 run + evidence-grounded verification/integration** とします。

Aは長時間化そのものに再現性のある利益がなく、Cは成功条件として信頼できる途中feedbackと十分なcomputeを強く要求します。一方Bもoracle selectionがない以上、自動的には成功しません。LiとHaririのverification gapは、この推薦に対する中心的なリスクです。 :chatgpt-content-reference{index="49"}

---

## 短い検索記録

検索は2026年9月27日 00:00 UTC以前に公開されたものに限定し、代表的には `"test-time scaling" LLM agents parallel sequential verifier`、`"single-agent" "multi-agent" equal compute budget LLM`、`"multi-agent reasoning" compute efficiency test-time scaling`、`"test-time scaling" pass@k verifier reproducibility`、`"test-time communication" agents shared workspace`、`"scientific literature discovery" AI agents benchmark full text` を用いました。

中核採用理由は、Li/ZhuがA対Bとverifier、Tran/Wunderlichが等予算でのsingle対multi、Haririがbudget/selectionの厳密な切り分け、ParkがCそのものの正負条件を実験しているためです。AutoResearchBenchはA/B/Cの直接比較ではないため中核6本から外しましたが、今回の業務への外的妥当性確認に使用しました。

中核6本およびAutoResearchBenchは**指定版の本文を取得済み**で、要旨しか取得できなかった研究から実験条件を補完した箇所はありません。検索で見つけたtraining-time multi-agent研究、2025年以前の主要研究、およびA/B/Cの比較に直接寄与しないbranch/latency最適化研究は中核から除外しました。