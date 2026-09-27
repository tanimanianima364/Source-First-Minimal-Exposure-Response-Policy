# 技術判断メモ

## 結論

**最初に試すのは B を主軸にした「独立2実行 → 差分に対する重点検証 → 1回だけ統合・必要時修正」**を推奨します。Aのように単一エージェントを単純に長く回すことは初手にせず、Cも本格導入しません。2本の独立実行では途中状態を共有せず探索多様性を残し、その後に「採用判断を左右する主張」「2本で食い違った数値・引用・論文版」「一次資料による裏づけ」に検証予算を集中させます。

理由は三つです。第一に、独立サンプリングには実証的な改善例がありますが、**候補中に正解が存在することと、それを最終回答として選べることは別問題**です。第二に、単純な長時間自己反省は悪化例があり、改善例は「再度全部を考える」のではなく**脆弱点を分解した検証**に寄っています。第三に、Cの最も強い研究結果は無視できませんが、十分な個別探索予算・客観的中間評価、または高度な隔離/レビュー機構を必要とし、本件の4倍・30分に直接移植できる実証はありません。:chatgpt-content-reference{index="0"}

予算はトークン数から逆算せず、各依頼の現行実行実費を \(C_0\) として、**独立2実行 ≤2\(C_0\)、重点検証・追加取得 ≤1\(C_0\)、統合/条件付き1回修正 ≤1\(C_0\)** というハード上限にします。これは消化目標ではなく上限です。検索・fetch、judge/verifier、統合、再試行もすべて含めます。Hariri et al. が指摘する通り、候補数が同じでも verifier・controller・decision の費用が違えば同一予算ではありません。:chatgpt-content-reference{index="1"}

---

## 研究比較表

下記6本はいずれも本文を取得して確認しました。うち Hariri、Park、Yoon/ArcticSwarm の3本は2026-07-01以降の初公開です。

| 研究・使用版・査読状況 | 対象タスク | モデル / 実行構成 | 計算予算の単位・含有範囲 | 評価・選択 | 主要結果と原文位置 | 本件への適用限界 |
|---|---|---|---|---|---|---|
| **Zhu et al., Scaling Test-time Compute for LLM Agents**。初公開 **2025-06-15 17:59 UTC**、使用 **v1=同日**。査読状況は期限時点で未確認。[arXiv v1](https://arxiv.org/abs/2506.12928v1) :chatgpt-content-reference{index="3"} | GAIA validation 165件。Web検索・マルチモーダルファイルを含む。:chatgpt-content-reference{index="4"} | 主実験 GPT-4.1/CodeAgent。BoN、BoN-wise、Beam、DVTS。parallel width=4。自己反省も比較。 | 主に**サンプリング幅**。4候補生成に加え verifier/merge があるが、end-to-endのトークン・検索・judge費用は報告されていない。したがって「width=4 = 4倍費用」ではない。 | voting/scoring/list-wise。 | Baseline 55.76 → **BoN 63.03**。連続reflectionは55.15。BoNでは voting 56.8、scoring 59.39、list-wise 63.03。PDF p.6 Table 1、p.7 Table 3–4。:chatgpt-content-reference{index="5"} GPT-4.1-only Pass@4 は69.14、PDF p.8 Table 5。:chatgpt-content-reference{index="6"} | 本件に近いtool-useだが、論文比較表・引用忠実性・専門家確認時間は測っていない。4倍実費制約も検証されていない。 |
| **Wan et al., Inference-Time Scaling of Verification / DeepVerifier**。初公開 **2026-01-22**、使用 **v2 2026-04-29**。**Findings of ACL 2026 掲載**。[ACL Anthology](https://aclanthology.org/2026.findings-acl.1243/) :chatgpt-content-reference{index="8"} | GAIA-Web/Full、XBench-DeepSearch、BrowseComp。かなり本件に近いweb research。 | 主結果は Claude-3.7-Sonnet の CK-Pro + decomposition/verifier/judge。追加学習なしのテスト時反復。別実験のQwen SFTは本件には適用しない。 | feedback round。検証を**最大3個の狙ったfollow-up question**に分解し、acceptで早期停止。ただし総検索費・総トークン・壁時計は数値化されていない。PDF p.7 §7.2 “Inference Cost”。:chatgpt-content-reference{index="9"} | verifierがaccept/reject＋修正指示。最大10 round。 | GAIA-Full **52.22 → 60.12（round 4）**、その後58.93まで低下。Web 51.11 → 63.33。DeepSearch 41→47 peak→44 final。PDF p.8 Tables 3–5。:chatgpt-content-reference{index="10"} | 「検証は効く」が「長く回せば効く」ではない。verifier誤りで correct→incorrect 回帰があり、早期ピーク。本件の引用付き長文成果物や人間レビュー時間は未測定。 |
| **Wunderlich et al., Multi-Agent Reasoning Improves Compute Efficiency**。初公開/使用 **v1 2026-05-02**。**ACL 2026 Student Research Workshop 掲載**。[ACL Anthology](https://aclanthology.org/2026.acl-srw.1/) :chatgpt-content-reference{index="12"} | MMLU-Pro 1,000問＋BBH。 | Llama 3.1 70B中心。self-consistency、self-refinement、debate、MoA。 | FLOPsとweight-memory transferから推定する**理論的 time/task**。最大約20×CoT。検索、引用取得、API料金は含まない。PDF p.4 Fig.2。:chatgpt-content-reference{index="13"} | 多肢選択のaccuracy。最終option選択。 | CoT 64.3、SC 68.7、debate 70.0、MoA 71.4。comparable computeでSC比 debate +1.3pp、MoA +2.7pp。**self-refinementはCoTを一貫して下回る**。PDF p.5 §4.1/Table 1。:chatgpt-content-reference{index="14"} | Cの構造的メリットを示すが、主な差は4倍を超える領域も含む。検索も引用検証もなく、費用単位が本件と異なる。 |
| **Hariri et al., Test-Time Scaling in Reasoning LLMs**。初公開 **2026-08-04**、使用 **v2 2026-08-31**。査読状況未確認。[arXiv v2](https://arxiv.org/abs/2608.04001v2) :chatgpt-content-reference{index="16"} | MMLU-Pro/BBH、競技数学、SuperGPQA。固定candidate bankによる大規模実証。 | Qwen3.6、gpt-oss等。最大80候補。reference-free pointwise verifier等。 | 重要なのは会計法。\(C_{total}=C_{gen}+C_{signal}+C_{control}+C_{decision}\)。warm-up・discard・judge・aggregationも含めるべきとする。:chatgpt-content-reference{index="17"} 一方Fig.6の横軸は候補数で、**verifier computeを除外**。 | Pass@k（正解候補の存在）と、plurality/pointwise BoN（実際の提出回答）を明示的に分離。 | Qwen3.6、k=80: **Pass@80 94.62%に対し、reference-free BoN 86.56%**、plurality 89.25%。PDF p.18 Fig.6、p.52 Table 10。:chatgpt-content-reference{index="18"} | Agent/web searchの研究ではない。しかし「候補を増やすだけでは最終回答が改善しない」「評価費を含める」というB設計上の重要な直接証拠。 |
| **Park et al., Scaling Discovery through Test-Time Communication**。初公開/使用 **v1 2026-09-17 19:38 UTC**。査読状況未確認。[arXiv v1](https://arxiv.org/abs/2609.21032v1) :chatgpt-content-reference{index="20"} | ARC-AGI-3、polyomino packing、MNIST compression。後2つは3–96時間級。 | 同一モデルの3/5 agent等。共有workspace、append-only log、approach/score records。 | ARCではaction budget/output tokens。長期課題では**3–72h、96h**。本件の総API/検索費ではない。:chatgpt-content-reference{index="21"} | 環境から得られる客観的score/verifierをagents自身が利用して採用判断。 | ARC team@5 8.0% vs best@5 2.2%。十分なcomputeではteamを同solve rateまで独立実行で追うのに4.9× output tokens。一方、**≤400K output tokens/agentでは独立側が先行**し、5 agentsで1 agent分の総budgetを分けるとteamが単独agentに負ける。PDF p.7 Figs.3–4。:chatgpt-content-reference{index="22"} | Cに有利な強い証拠。ただし著者自身が**客観的なagent-accessible verifierを中心条件**とし、feedbackが疎/主観的な場合は未解決としている。:chatgpt-content-reference{index="23"} |
| **Yoon et al., ArcticSwarm**。初公開/使用 **v1 2026-09-01 21:08 UTC**。査読状況未確認。[arXiv v1](https://arxiv.org/abs/2609.01870v1) :chatgpt-content-reference{index="25"} | BrowseComp-Plus 830問＋live-web。6本中、本件の「完全 verifier がない長期調査」に最も近い。 | Qwen 3.5-27B。subagentを隔離しつつbulletin boardを使い、commit/board-audit/self-checkの3段階レビュー。 | **end-to-end tokens**（input/output/cache、全subagents）と実測wall-clock。ArcticSwarm 24.9M tokens/case、median **83.3 min**。PDF p.22 Table 14。:chatgpt-content-reference{index="26"} | 独立poolはrealizable majorityとoracle best-of-Nを分離。 | Arctic 82.6%。free/unrestricted communicationにすると78.8（−3.8pp）。独立MiroFlow N≈36を24.66M tokensに合わせてもmajority **63.2%**。oracleなら86.1%だが「perfect verifierが必要」で実現不能。PDF p.6 Table 3、p.21 Table 13。:chatgpt-content-reference{index="27"} | **本推奨に最も不利な結果**。構造化Cは独立Bを大差で上回る。ただしfull systemはMiroFlow単独0.685M tokensの約36倍、median 83.3分で、本件4倍/30分から大幅に外れる。 |

---

## 横断的な考察

### 1. 「Aは効かない」と「反復検証は効く」は矛盾しない

Zhuでは、毎step/広範なself-reflectionを加えると baseline 55.76から55.15に下がり、頻繁なreflectionも悪化しました。Wunderlichでもself-refinementは追加computeを使いながらCoT未満でした。:chatgpt-content-reference{index="28"}

一方、DeepVerifierでは明確な改善があります。ただし手法は同じではありません。前の解を丸ごと再考させるのではなく、「source X は claim Y を本当に述べるか」「最新reportの数値はいくつか」といった**局所的な検証問題へ分解**し、最大3件のfollow-upに絞っています。さらに改善は早いroundでピークを迎え、verifier誤判定による正解→不正解も観測されています。:chatgpt-content-reference{index="29"}

**実証された説明:** 検証の粒度・verifier・stop ruleが異なる。  
**本件についての仮説:** 専門家確認時間がボトルネックなら、追加computeを「もう一度長く考える」より、「最終判断に効く主張と引用の局所検証」に使う方が期待値が高い。これは本件で実測する必要があります。

### 2. 「通信すると強い」と「通信を制限すると強い」も矛盾しない

Parkではcommunicationが大幅改善しましたが、agentsは客観的なlevel completion/packing score/compression sizeを見て「どちらの発見が本当に改善か」を判定できました。しかも低compute領域ではcoordination taxで独立実行の方が先行します。:chatgpt-content-reference{index="30"}

ArcticSwarmでは逆に、**自由通信を許すと82.6→78.8**へ落ち、探索中は隔離し、commit時だけ構造化レビューする方が良好でした。著者らは独立20 runでも取得文書の平均pairwise Jaccardが0.178で、実効的には約4.6 run相当と分析しています。:chatgpt-content-reference{index="31"}

したがってCを「複数agentをチャットさせる」と捉えるのは不適切です。両研究から共通して読めるのは、**独立探索を壊さず、検証済みの進捗だけを境界で共有する設計**です。本件で将来Cを試すなら、このC-liteが候補です。

### 3. 定量値の検算

**検算1 — ZhuのBoN。** 比較対象は同じGPT-4.1 GAIA experimentのbaseline 55.76%とBoN 63.03%。絶対差は

\[
63.03-55.76=\mathbf{+7.27\ pp}
\]

相対改善率は、分母をbaseline 55.76とすると

\[
7.27/55.76=\mathbf{13.04\%}
\]

です。「約8ポイント」という本文記述より、表からの正確な差は7.27ppです。:chatgpt-content-reference{index="32"}

**検算2 — DeepVerifier。** GAIA-Full/Claude-3.7で0 round 52.22%、peak 60.12%。したがって **+7.90pp**、相対改善は \(7.90/52.22=\mathbf{15.13\%}\)。10 round終了時は58.93%なので、peak後に1.19pp戻しています。「反復回数を増やせば単調改善」ではありません。:chatgpt-content-reference{index="33"}

**検算3 — 正解候補存在率と実選択率。** HaririのQwen3.6/k=80ではPass@80=94.62%、reference-free selector=86.56%。同一candidate bankにおける差は **8.06pp**。候補中に正解が存在した問題を分母にすると、選択で失った割合は \(8.06/94.62=\mathbf{8.52\%}\)。ここでPass@80を「システム正答率」と扱ってはいけません。さらにFig.6の80候補という横軸にはverifier compute自体が含まれません。:chatgpt-content-reference{index="34"}

同じ理由で、ZhuのGPT-4.1 Pass@4=69.14をBoNの最終63.03と同じ意味の数字として扱わず、Parkの「5 agents」と「同じ総費用」も同一視していません。研究間のscoreの平均による順位付けも行っていません。

### 4. 本件でBに寄せる理由と最大の反証

Bの利点は「候補数を増やすこと」そのものではありません。本件では、独立2実行で検索経路と解釈の失敗をずらし、**候補差分を検証対象の発見器として利用する**ことに価値があります。その後のselectorは単なる多数決ではなく、原論文に戻って重要主張を再検証すべきです。DeepVerifierのdecompositionと、ArcticSwarmのcommit-boundary reviewはこの部分を支持します。:chatgpt-content-reference{index="35"}

一方、推薦に最も不利なのはArcticSwarmです。同じ約24.9M-token budgetで、独立MiroFlow約36本＋majorityは63.2%、structured swarmは82.6%でした。これは**「Bを大量に増やしてvoteすれば十分」という考えを明確に否定する結果**です。:chatgpt-content-reference{index="36"} ただし実証されたfull Cは単独runの約36倍、median 83.3分です。本件で許される4倍・30分以内に縮小しても優位が残るかは研究からは分かりません。

したがって、今回の推薦は「Bが一般にCより優れる」ではなく、**与えられた制約内で最初に検証すべき仮説がB＋重点検証である**、という限定的なものです。

---

## 推奨構成

実装上は次の4段階にします。

1. **Independent R1/R2** — 同じ固定基盤モデル・同じ検索toolを用いるが、途中メモ、検索結果、仮説を互いに見せない。各々が比較表・採用判断まで一度完成させる。
2. **Disagreement audit** — 二つの成果物をclaim/citation単位に分解し、数値、論文版、母集団、比較条件、採用判断に効く主張の不一致を抽出する。一致した主張でも採用判断の根幹なら抽出対象にする。
3. **Targeted verification** — 原論文本文へ戻り、上記だけを再検索・再読する。完全な再調査はしない。「引用が本当にその主張を含むか」「分母・単位・版が一致するか」を優先する。
4. **One-shot merge** — 一つの比較表と判断に統合。検証で重大flagが残った場合だけ1回修正し、それ以上の自己反省loopはしない。

30分制約については、R1/R2を並列化します。ただし**並列化は費用を減らさず壁時計だけを変える**ため、30分と4\(C_0\)は別々に計測・強制します。

**採用を見送るべき条件**は、(a) 重点検証を入れても専門家確認時間が実質的に下がらない、(b) B固有の重大誤り・誤引用が増える、(c) disagreement detectorが重要な食い違いを取り逃す、(d) 4\(C_0\)または30分capで頻繁に未完了になる、(e) 同じcapでC-liteまたはAが品質を落とさず明確に確認時間を短縮する、のいずれかです。

---

# 推奨を覆すための小規模比較実験

### 比較arm

| Arm | 構成 | 制約 |
|---|---|---|
| **Baseline** | 現行の1回実行 | 実費 \(C_0(q)\) を記録 |
| **A-4x** | 単一agent。同じtaskを継続調査・推敲。候補agentなし | ≤4\(C_0(q)\)、≤30分 |
| **B-4x** | 独立2実行 → disagreement/claim verification → merge → flag時のみ1回修正 | ≤4\(C_0(q)\)、≤30分 |
| **C-lite-4x** | 2 worker。初期探索は隔離し、commit境界だけshared boardへ根拠付き発見を公開。最後にreview/merge | ≤4\(C_0(q)\)、≤30分 |

C-liteを単純な自由チャットにしないのは、ArcticSwarmのfree-communication ablationとParkのverified-progress条件を反映するためです。:chatgpt-content-reference{index="37"}

### 課題と費用会計

**20件**の実運用相当依頼を、実行前に固定します。検索量が少ないもの、複数論文の条件比較が必要なもの、結果が衝突する/版管理が難しいものを事前層別し、その後は結果を見て除外しません。

各課題 \(q\) について現行runの実費を \(C_0(q)\) とし、enhanced armは次をすべて同一ledgerへ計上します。

\[
C = \text{model inference}+\text{search/fetch}+\text{verifier/judge}
+\text{merge/compaction}+\text{communication}+\text{retry}
\]

専門家の時間は4倍費用枠には入れず、**別の事業KPI**として計ります。候補数、output tokens、agent数だけではbudget matchingとみなしません。これはHariri et al.のend-to-end accountingと一致します。:chatgpt-content-reference{index="38"}

### 専門家による盲検評価

成果物からarm名・内部trajectory・候補回答を除き、体裁を可能な範囲で正規化します。専門家には最終比較表と採用判断だけを渡します。

評価項目は混ぜて単一scoreにせず、少なくとも以下を個別報告します。

- **専門家確認時間**：成果物を開いてから「承認」または必要修正を完了するまでのactive minutes。主KPI。
- **重大誤り**：直せば採用判断または重要比較表セルが変わる誤り。版取り違え、分母違い、数値の誤読も含む。
- **出典忠実性**：採用判断を支える全claimについて、引用元が存在するか、一次資料か、claimを実際に支持するか、版/日付が正しいか。
- **軽微な誤り・欠落**：判断を変えないが専門家が修正した項目数。
- **最終判断の妥当性**：独立した専門家adjudicationとの一致。自動judgeを正解器とは扱わない。
- **実費とwall-clock**：上記ledgerの総額、開始からfinal artifactまで。timeoutも失敗として残す。

盲検性を守るには、可能なら4名程度の専門家へLatin-squareで割り付け、**同じ専門家が同一課題の4 armを連続して見ない**ようにします。無作為25%は第二専門家が重複評価し、重大誤り・citation fidelityのrater差も報告します。

### 反復と不確実性

20件を各arm一度実行し、事前に選んだ6件（難易度層ごと2件）は**別seedでもう一度全armを実行**します。これによりtask差とrun-to-run差を分離します。

専門家時間はtask単位のcluster bootstrapで95% CIを、重大誤りや引用失敗率は二項比率の区間とarm差のCIを報告します。「平均accuracyが高かった」だけで結論を出さず、20件で区間が広く採否境界を跨ぐ場合は**不確定＝本番採用を保留**とします。

### 事前に固定する採用・中止条件

Bを本番候補に進める条件は、**専門家確認時間の点推定で20%以上削減し、95% CIが0%削減を上回ること**、かつ重大誤り率についてbaselineとの差の95% CI上限が **+5pp以内**、判断根拠claimのcitation fidelity低下が **2pp以内**、cap内完了率が **95%以上**であること、とします。この20%/5pp/2ppは研究結果ではなく、今回の事業上の事前基準です。

途中中止は、最初の10課題で**Bにだけ存在する採用判断を変える重大誤りが2件**出る、または誤った/存在しない一次資料引用が検証段をすり抜けて採用判断に使われる事例が反復する場合です。逆にAまたはC-liteが同じ品質条件を満たしつつBより明確に短い確認時間を示せば、今回のB優先推薦を覆します。

---

## 不確実性

最大の不足は、**「出典付きの論文比較表＋採用判断」を、固定モデル、総実費4倍以内、30分以内で生成し、その後の人間専門家確認時間まで測った研究が今回の6本にはないこと**です。GAIA/BrowseCompは検索能力に近く、ArcticSwarmは長期web researchに近いものの、最終成果物・評価器・時間制約が異なります。

したがって論文から支持できるのは、(1)無条件な長時間self-refinementは安全な改善策ではない、(2)並列候補は有用だがselectionがボトルネックになり得る、(3)局所的・根拠指向のverificationは有望、(4)構造化communicationには強い可能性があるがcomputeとfeedback条件に依存する、という範囲です。**30分・4倍でBが成功する保証まではありません。**

## 次の方向

実験前にまず、現行runについてモデル推論・検索/fetch・再試行を含む \(C_0\) の計測と、専門家のactive review time計測を1週間分だけ取得して基準線を固定するのが最優先です。その後、上記20課題・4 arm・採否条件を結果を見る前に凍結すれば、「品質向上」ではなく実際のボトルネックである**専門家確認時間を減らせたか**で判断できます。

## 検索記録

検索は arXiv/ACL Anthologyを中心に、`test-time scaling LLM agents best-of-n verifier`、`deep research verification test-time scaling`、`multi-agent reasoning compute efficiency`、`test-time communication multi-agent 2026`、`long-horizon multi-agent research verifier 2026`、各候補論文タイトル＋`conference/venue`を使用しました。採用基準は、A/B/Cの少なくとも一つを実験的に切り分け、実行構成・選択方法・compute条件を本文で確認できることです。surveyや二次的な解説、訓練主体で本件のtest-time構成を切り分けない研究は中核から外しました。6本ともPDF/HTML本文を取得でき、本文未取得の中核研究はありません。Zhu、Hariri、Park、ArcticSwarmについては期限時点で査読採録を一次資料から確認できなかったため「未確認」とし、WanとWunderlichはACL Anthologyの掲載情報まで確認しました。 :chatgpt-content-reference{index="39"}