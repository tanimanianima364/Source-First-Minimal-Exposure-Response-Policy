# AI論文調査アシスタント：A/B/C構成の技術判断メモ

**調査基準日：2026年9月27日 00:00 UTC。** 以下はこの時点までに公開された版だけを対象とする。

## 1. 結論

**最初に試す構成は B を主軸にした限定的ハイブリッド**が妥当である。具体的には、**2本の独立した調査実行を並列で走らせ、その後に別工程で一次資料を再確認する検証器と、制約付き統合器を置く**。途中で自由形式の発見を相互共有するCは初期構成には入れず、A型の長い自己推敲も、検証で指摘された箇所だけを直す短い修復パスに限定する。

理由は三点ある。

1. 独立探索には検索範囲を広げる利点がある一方、**複数候補があっても選択器が弱ければ改善しない、あるいは悪化する**。Consilienceでは64候補を使う設定でも、単純な自己確信による選択でHMMTの76.5%が68.0%へ低下した。MAVも、検証器のコストまで同じ総計算量に入れると低予算域では不利になる。したがって「候補を増やすこと」より「候補中の事実を再検証して選べること」に予算を残す必要がある。
2. 実際のDeep Research系では、**最終統合段階そのものが大きな誤り源**になっている。Hirsch et al.ではAI-Qの確認された最終報告エラーの84.7%がorchestratorに帰属し、合成済み研究ノートを単一文書のraw snippetに置き換えるだけでcitation recallが64.5→69.7%、precisionが87.6→94.1%に上昇した。したがってBの最後を「好きに作文する統合器」にしてはいけない。
3. C型の協調は条件依存性が大きい。固定reasoning-token budgetで比較したKim et al.では、分解しやすいFinanceでは中央集権型が+80.8%だった一方、逐次依存のPlanCraftでは全MASが悪化し、独立型は−70.0%。Web調査に近いBrowseComp-Plusでも独立型はSAS比−35%で、構造化された協調の改善は小さかった。

**初期の4倍予算配分案**は、現在の1回実行で実測される「モデル推論＋検索/API」の総費用を1.0単位として、候補1に1.0、候補2に1.0、claim/source検証に1.2、統合・限定修復に0.8、計4.0以下とする。これはトークン数や時間への換算ではなく**課金・検索費用を含む実測コスト上限**である。2候補は並列実行する。壁時計については費用から推定せず、暫定的に「並列候補生成17分以内、検証＋統合10分以内、3分の余裕」の別ゲートを置き、実測p95が30分を超えるなら不採用とする。

最も不利な証拠は、Kim et al.のBrowseComp-Plusで独立型が大きく悪化したことと、Hirsch et al.で最終orchestratorが主要エラー源だったことである。つまり、**Bも中央統合も、それだけでは安全策にならない**。今回の提案が成立するかは「独立探索で得られた追加証拠を、検証段階で人間の確認時間を増やさず正しく刈り取れるか」に依存する。

---

## 2. 中核研究の比較

| 研究・版 | 対象タスク | モデル／実行構成 | 計算予算の単位・含まれるもの | 評価・選択 | 主要結果と原文位置 | 今回への適用限界 |
|---|---|---|---|---|---|---|
| **Kim et al., “Capable language models can outgrow the benefits of collaboration”**。初公開は旧題 *Towards a Science of Scaling Agent Systems*, arXiv v1 **2025-12-09**。使用：**Nature Machine Intelligence VoR, 2026-07-24**, pp.1157–1172。査読済み。 [Nature版](https://www.nature.com/articles/s42256-026-01268-y?utm_source=chatgpt.com) [arXiv版履歴](https://arxiv.org/abs/2512.08296) | BrowseComp-Plus、Finance-Agent、PlanCraft、WorkBench、SWE-bench Verified、Terminal-Bench。260構成。 | SAS、Independent、Centralized、Decentralized、Hybrid × OpenAI/Google/Anthropic系。 | **総reasoning tokensを一致**（平均4,800/trial）、同じtool-call access。通信turn/messageも計測。検索の実ドル費用・30分latencyとは同じ尺度ではない。 | ベンチ固有success/accuracy。central orchestrator等による統合。 | Finance中央集権0.631 vs SAS0.349＝+80.8%。PlanCraft独立0.170 vs 0.568＝−70.0%。BrowseComp-Plus独立はSAS比−35%、decentralizedは+9.2%。§4.1–4.2, Fig.2/Table 5。 | 最も近いWeb research benchmarkを含むが、最終成果物の「論文比較表＋採用判断」や専門家の確認時間は評価していない。token-budget一致も、検索課金・通信課金・wall timeを含む統一費用4×とは異なる。 |
| **Yang et al., “Revisiting Multi-Agent Debate as Test-Time Scaling”**。初公開 **2025-05-29**、使用 **v2 2025-06-20**。コメントは“Preprint, under review”。 [arXiv v2](https://arxiv.org/abs/2505.22960) | GSM8K、MATH500、AIME、safety/jailbreak。 | Qwen2.5 1.5B–32B、Llama/Gemma、GPT-4o-mini/4o。SC、16-round self-refinement、MAD 2×8/4×4/8×2。 | **最大generation数16を一致**。token数、通信量、wall time、検索費用を一致させた実験ではない。 | 数学は正答率、safetyはattack/refusal系。MADは対話中に回答自体を改訂。 | Qwen2.5-3B/AIME: SC 8.9%、MAD4×4 11.1%。一方MATH500は72.1% vs 71.3%。強いモデルではSCがしばしば優位。§4.1 Table 1/Fig.3。 | 正解が明確な数学が中心。論文調査のcitation fidelityとは異なる。また「16生成同士」を同一総費用と読んではいけない。 |
| **Lifshitz et al., “Multi-Agent Verification”**。初公開・使用 **arXiv v1 2025-02-27**。査読状況は期限時点で確認できず。 [arXiv](https://arxiv.org/abs/2502.20379) | MATH、MMLU-Pro、GPQA Diamond、HumanEval。 | 8 generator LLM。20種のaspect verifier候補からドメイン別subsetを選ぶBoN-MAV。 | Table 1は**n=16候補が同じ**だが、MAVは各候補に複数verifier callを追加するので同一総費用ではない。Fig.6ではgenerator＋verifierの**query数合計**を別に予算として比較。 | verifierのbinary approvalを集約しtop-1選択。 | Gemini-1.5-Flash/MATHでMAV 66.0% vs self-consistency 59.0%。ただし総query-budget比較では低予算域でMAVが当初劣る。Table 1, Fig.6。 | verifier subset自体をvalidation dataでengineeringしている。完全検証器のない文献調査で同じ精度の判定信号が得られる保証はない。query 1回を均一費用単位とする点も今回と異なる。 |
| **Go et al., “LiRA”**。初公開arXiv v1 **2025-10-01**。使用：**AAAI-26 VoR, 2026-03-14**, pp.40456–40464。査読済み。arXiv v4は2026-03-20。 [AAAI版](https://ojs.aaai.org/index.php/AAAI/article/view/41489) [版履歴](https://arxiv.org/abs/2510.05138) | 科学文献レビュー生成。SciReviewGen 125件＋ScienceDirect専門家レビュー125件。 | gpt-4o-miniを共通基盤にoutline、subsection writer、editor、reviewer等。並列writer/researcher、構造化shared message pool、最大3回review loop。 | ROUGE等、Prometheus 2、SME、Citation Quality F1。 | CQF1: SciReviewGen LiRA 0.76 vs AutoSurvey 0.63、ScienceDirect 0.73 vs 0.55。Table 3, p.40460。 | **主実験ではgold reference listが事前提供**。実retrievalにするとaer 0.170→0.152、coverage 3.892→3.839が有意に低下（Table 5, p.40461）。総推論・検索費用を揃えた比較でもない。 |
| **Kong et al., “Consilience for Verifier-Free Test-Time Scaling”**。初公開・使用 **arXiv v1 2026-08-10**。査読状況は未確認。 [arXiv](https://arxiv.org/abs/2608.09898) | LiveCodeBench、HMMT25、GPQA、SWE-bench、追加Natural Questions。 | GPT-OSS 20B/120B、Qwen3等。Best-of-n候補から内部log-prob trajectoryで選択。 | 主実験はn=64。同一候補poolからselector比較。Natural Questions追加実験は**8 generation passes**を揃え、同一hardwareでwall-timeも記録。検索費用はなし。 | 外部verifierなしのtop-1 selection。 | HMMT/GPT-OSS-20BでPass@1 76.5%、Self-Certainty選択68.0%。Natural QuestionsはPass@1 25.9%/14分、Consilience 30.1%/36分、Self-Verify 30.4%/59分、Self-Refine 26.0%/101分。Table 2、Appendix E Table 10。 | Consilience自体にはtop-k logprobsやreasoning boundaryが必要で、今回の固定基盤モデルで利用可能とは限らない。重要なのは「候補増加≠良い選択」という反証。論文検索ではない。 |
| **Hirsch et al., “Who is the Agent to Blame?”**。初公開・使用 **arXiv v1 2026-08-25**。**EMNLP 2026 Main accepted**。 [arXiv](https://arxiv.org/abs/2608.24306) | 実Web検索を行うDeep Research。DeepResearch Bench英語20件の診断、50件の介入。 | Nvidia AI-Q、MS-Agent、TrajectoryKit。AI-QはGPT-5.2 orchestrator/planner＋Nemotron Nano researcher等。 | LLM judgeによる局所entailment/citation tracing。人手検証でexact match 76%、κ=0.62。介入はcitation guidanceまたは合成note→raw snippet。 | AI-Q最終エラーの84.7%がorchestrator由来。raw snippetsでcitation recall 64.5→69.7%、precision 87.6→94.1%、RACE 52.6→52.4。§6 Table 2、§7 Table 3、PDF pp.8–9。 | 今回に最も近いが、システム間モデルが異なり因果的なagent-role比較ではない。**表内セルのcitationは評価対象外**であり、今回の最終成果物が比較表中心である点は重要なギャップ。費用・wall-time比較もない。 |

### 定量値の検算

**(a) Kim et al.：同一reasoning-token budget下の効果。**

Finance中央集権型は  
\[
0.631-0.349=0.282
\]
なので **+28.2 percentage points**。相対改善率は  
\[
0.282/0.349=80.8\%
\]
であり、論文の+80.8%と一致する。

逆にPlanCraft独立型は  
\[
0.170-0.568=-0.398
\]
すなわち **−39.8 points**、相対変化は  
\[
-0.398/0.568=-70.1\%
\]
である。したがって「MASは+80.8%改善」という一般化は不適切で、同じ研究内だけでもタスク構造によって符号が逆転する。

**(b) Yang et al.：同じ最大generation数でも結果は一方向ではない。**

Qwen2.5-3B/AIMEでは 8.9→11.1%、したがって **+2.2 points、相対+24.7%**。同じモデルのMATH500では72.1→71.3%、すなわち **−0.8 points、相対−1.1%**。なお両者が揃えているのは最大16 generationsであって、16世代＝同一token費用ではない。

**(c) Hirsch et al.：今回に近いcitation fidelity。**

raw snippet介入はrecall 64.5→69.7%なので **+5.2 points、相対+8.1%**、precisionは87.6→94.1%なので **+6.5 points、相対+7.4%**。RACEは52.6→52.4でほぼ不変だった。これは「より複雑な協調」よりも「統合器へ渡す証拠表現を一次資料に近づける」方が有効な場合がある直接的な証拠である。

**(d) 「正解候補が存在する」と「最終回答が正しい」は別。**

Yang et al. Fig.3(c)は「初回に4 agents中ちょうど1つだけが正しい」問題群を条件付けているため、その群では**初期候補集合に正解が存在する率は定義上100%**である。それでも4-round debate後のfinal accuracyは64%。つまり36 points分は、正解が候補にあったにもかかわらず最終過程で保持できていない。これは静的なselectorではなくdebateによる改訂なのでBそのものではないが、**oracle candidate coverageと実際のtop-1/final accuracyを分けて測る必要性**を明確に示す。

---

## 3. 横断的な考察

### 3.1 KimとYangは「multi-agentが効く／効かない」で矛盾しているか

**実証された範囲では矛盾しない。**

Yangでは、同じ最大16 generationという条件でMADはAIMEのような難しい数学・小さいモデルで相対的に有利だが、MATH500や強いclosed modelではself-consistencyがしばしば同等以上だった。

Kimではreasoning-token budgetまで合わせても、Financeのように独立な調査枝へ自然に分解できる課題ではMASが改善し、逐次状態を一貫して保持すべきPlanCraftでは大幅に悪化した。Web browsingのBrowseComp-Plusも協調構造への感度が大きい。

したがって説明できる差は、少なくとも**課題の分解可能性、逐次状態依存性、モデル能力、予算尺度**の違いである。

今回の論文調査について、**探索部分はFinance型の並列性を持つ一方、最後の比較・採用判断は逐次的一貫性を必要とする**、というのが私の作業仮説である。これは上記研究から直接実証された事実ではない。その仮説ゆえ、探索だけをBで複製し、最終判断をC型の自由な相互対話にしない構成を試す価値がある。

### 3.2 MAVとConsilienceは「検証を増やすほど良い／selectorは害になる」で矛盾するか

これも**予算とselectorの質を区別すれば両立する**。

MAVのTable 1は同じ16候補から複数verifierを使うと改善する例を示すが、16候補が同じだけで**検証callの総費用は同じではない**。著者自身、generator＋verifier query数を同じ予算にしたFig.6では低予算域のMAVが不利になり、十分な予算になってから逆転すると報告している。

Consilienceは逆に、64候補を用意しても単純なconfidence selectorがPass@1を下回るケースを示す。Natural Questionsでは8 generation passesを全方式に与えても、逐次Self-Refineは101分、並列選択Consilienceは36分、Self-Verifyは59分だった。**同じgeneration数も同じ総費用・同じwall-clockを意味しない。**

今回の含意は、4倍の余剰を全部「候補数」に使わないことである。Bの評価時には少なくとも

- `coverage@2 = P(2候補のどちらかが専門家基準で許容可能)`
- `selected/final accuracy = P(実際に統合後の成果物が許容可能)`
- `selector efficiency = P(finalが許容可能 | 少なくとも1候補が許容可能)`

を別々に記録すべきである。coverageだけ上がってselected accuracyが上がらないなら、3本目・4本目を増やすよりselector/verificationを直すべきである。

### 3.3 LiRAとHirschはCを支持しているようで、実際には何が違うか

LiRAは文献レビューに直接近く、専門role、parallel writer、reviewer feedback、structured shared poolsを組み合わせてcitation qualityを改善した。これはC寄りの成功例である。

しかし適用範囲はかなり限定される。主実験では正解側のreference listが既に与えられていた。実retrievalへ移したとき、一部のcoverage/entity指標は有意に低下した。また4倍の統一費用制約下でA/B/Cを比較した研究ではない。

一方Hirschは実Web DRで、合成された中間noteが必ずしも良い通信媒体ではないことを示す。単一文書raw snippetsの方がAI-Qではcitation指標を改善した。

したがって、「agent間で情報共有する」こと自体を成功要因と解釈するべきではない。**実証されたのは、LiRAでは構造化・citation-grounded workflow全体が有効だったこと、Hirschでは特定システムでraw evidence handoffがsynthetic notesより有効だったこと**である。

私の仮説は、今回Cを将来試すなら、自由形式の「他agentがこう考えた」という文章を共有するより、**DOI/URL、版、原文snippet、table/figure位置、検索失敗、矛盾flagだけを共有するstructured evidence ledger**にした方が安全、というものである。

---

## 4. 推奨する初期構成

### B2-VI：2 independent researchers → verifier → constrained integrator

1. **Researcher R1 / R2**  
   同じ依頼、同じ基盤モデル、同じ検索手段を使うが、互いの検索結果・中間推論は見せない。それぞれが一次資料候補、版情報、claim–source対応、数値を提出する。

2. **Evidence verifier**  
   2案の文章を単純採点するのではなく、候補をunionし、重要claimごとに一次資料を再openする。最低限、文献同一性、公開日・版、claim entailment、数値・分母・単位、table/figure位置、相反結果をチェックする。**検証器自身の「もっともらしい知識」は根拠にしない。**

3. **Constrained integrator**  
   verifierが承認したevidence ledgerから比較表と採用判断を構成する。証拠ledgerに存在しない新しい実証主張を追加しない。

4. **限定repair**  
   verifierの明示的flagだけを対象に1回修復する。Aのような「時間の許す限り自己推敲」は行わない。

予算は前述の **1.0 + 1.0 + 1.2 + 0.8 ≤ 4.0** を開始値とする。検索API、source reopening、通信、verification、integrationをすべて同じ会計に入れる。未使用枠を「もっと考える」に自動投入しない。

**Cへ拡張する条件**は、B2-VIの失敗がselectorではなくcoverage不足と判明した場合に限る。たとえば`coverage@2`自体がcontrolと変わらず、2本の独立探索が同じ重要論文を繰り返し落とす場合に、R1/R2が途中で「未探索query、URL/DOI、raw snippet、failure flag」のみ共有するC-liteを次候補とする。

---

## 5. 推奨を覆し得る小規模比較実験

実験はまだ実施していない。以下を事前登録してから行う。

### 比較群

同一の過去案件**24件**を、現在の専門家確認時間・領域・検索難度が偏らないよう層化する。

| 群 | 構成 |
|---|---|
| Control | 現行の1回実行。現状どおり、実測約1×。 |
| A4 | 単一agentを延長し、調査＋自己批評＋修正。上限4×。 |
| **B2-VI** | 上記2独立候補＋evidence verifier＋制約付きintegrator。上限4×。 |
| C4 | 同じ基盤モデルの複数agentが途中からstructured shared workspaceを共有する構成。上限4×。 |

A/B/Cについては**同じ4.0×実測費用上限、同じ30分hard limit、同じ検索provider・tool access**を与える。安い群に無意味なcallを追加して費用を強制一致させることはせず、実費を記録する。候補群間で実費差が大きい場合は、主比較に加えて3.0×など共通の低いcost ceilingで感度分析する。

24件すべてを1回ずつ実行し、うち**8件を各方式3 seed**で再実行してstochastic varianceを測る。結果を見て良いseedだけ選択しない。

### 盲検評価

最終成果物からsystem名、agent数、費用、ログを隠し、順序をランダム化する。案件ごとに原則2名の専門家が独立評価し、重大判定の不一致だけ第三者が裁定する。

**主指標は専門家の実確認時間**とする。単なる「読んだ時間」ではなく、成果物を最終的にapprove/reject・修正完了できるまでを測る。

同時に以下を測定する。

- **citation faithfulness**：重要claimのうち、提示sourceが実際にclaimを支える割合。表の数値セルも対象にする。
- **citation completeness**：引用が必要な重要claimのうち適切なsourceが付いている割合。
- **重大誤り率**：採用判断を変え得る誤った事実、誤った版、誤読した実験条件、存在しない文献、誤った定量比較。
- **採用判断の一致**：盲検専門家の最終判断との一致。
- **coverage@2 と final accuracy**：Bでは、候補の少なくとも一つを専門家が「許容可能」と判断できた率と、実際の最終統合物の許容率を別計測する。
- 実測総費用、検索回数、source reopen数、壁時計時間。

Hirschの研究がrunning-text citationsしか評価していないため、**今回のpilotでは比較表セルを必ず別評価**する。

### 不確実性

主要比較は案件を単位にしたpaired analysisとし、**task-level cluster bootstrap 95% CI**を報告する。claim数を独立標本とみなして疑似的にnを水増ししない。確認時間は分布が歪む可能性が高いため中央値とpaired differenceも示す。8件×3 seedのsubsetでrun-to-run分散を別途報告する。

24件では小さい差を確定する検出力は不足し得る。このpilotの目的は細かな順位付けではなく、**4×への拡張を止めるべき大きな失敗、または専門家時間を明確に削るsignalを検出すること**とする。

### 事前に固定する採用・中止条件

**B2-VIを次段階へ採用する条件：**

- Control比で**専門家確認時間の中央値を20%以上削減**し、paired bootstrap 95% CIで改善方向が維持される。
- 重大誤り率のrisk differenceについて、95% CI上限がControl比 **+2 percentage points未満**。
- citation faithfulnessはControl比**−3 points以内のnon-inferiority**を満たし、架空引用・参照不能文献を増やさない。
- 実測総費用が各案件4.0×以内、**wall-clock p95 ≤30分**。
- `coverage@2`が高くてもfinal accuracyが10 points以上低い状態が続かない。そうなればBの候補数ではなくselector/integratorを失敗要因と判定する。

**途中中止条件：**

- 最初の8～12案件で、採用判断を逆転させる重大誤りや架空引用がControlより明らかに増える。
- 30分超過が反復して発生し、単純な並列化・タイムアウト調整では解消しない。
- 4×近く使っても確認時間がControlからほぼ減らない。
- Bで`coverage@2`は高いのに統合後に正答を失う場合は、3本目の候補を増やす実験を中止し、verification/integrationを改修する。
- CがBより通信・再検索費用を増やす一方、citation fidelityまたはcoverageを改善しなければCは見送る。
- Aが追加反復にもかかわらず重大誤り・citation指標・確認時間のいずれも改善しなければ、長時間self-refinementは見送る。

この判定なら、**Bは「研究で一般的に優れているから採用」ではなく、この実運用で専門家のボトルネックを実際に減らす場合だけ採用**できる。

---

## 6. 検索記録

主な検索軸は、`multi-agent fixed compute centralized independent agent systems`、`multi-agent debate test-time scaling self consistency`、`multi-agent verification verifier test-time compute`、`literature review multi-agent citation quality`、`deep research citation errors orchestrator`、`verifier-free test-time scaling selection 2026`。arXiv、AAAI Proceedings、Natureの一次資料を優先し、実験条件・表・付録まで本文確認した。

**採用理由**：Kimは同一compute下のA/B/Cに近いarchitecture比較、Yangは長い自己改善と討論、MAVとConsilienceは候補生成とselector cost、LiRAは論文レビューへの直接性、Hirschは実Web Deep Researchのcitation propagationを扱うため選定した。6本すべて独自実験を含み、Consilience（2026-08-10）とHirsch（2026-08-25）が「2026-07-01以降初公開」の条件を満たす。

当初は2026年8月公開の逐次／並列推論研究も候補にしたが、最終的には今回の「Web論文調査・引用検証」に直接対応するHirsch et al.を優先した。古い「more agents」系研究や一般的self-refinement研究は、固定予算条件または今回のcitation-heavy workloadへの直接性が弱いため中核から外した。

**本文未取得の中核論文はない。** Nature VoRは直接open時に認証redirectが発生した箇所があったが、公開されたNature本文と期限内arXiv v3全文の双方で実験条件を照合した。LiRAはAAAI公開PDF、他はarXiv HTML/PDF本文を取得しており、要旨だけから実験詳細を補った研究はない。