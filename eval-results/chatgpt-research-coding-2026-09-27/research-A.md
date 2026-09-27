# 技術判断メモ

## 結論

**最初に試す構成は、Bを骨格にした限定的なハイブリッド**を推奨します。具体的には、**同じ固定基盤モデルで2本の調査を互いに見せず並列実行し、最後に主張単位の出典検証・統合を行い、不一致や高重要度の未検証点だけ再検索する**構成です。探索途中では共有させず、A的な追加計算は「長く考え続ける」ためではなく、検証で発見した穴への限定的な再調査に使います。機械費用は「2本の探索＋検証＋統合＋再検索」の**実測総額**で4×以内に止めます。

理由は3点です。単純なAは、長い履歴を増やしても飽和・悪化する実験結果があり、単純なBは正解候補を増やせても選択器が追いつかない結果があります。一方Cは、十分な計算量と検証可能な中間進捗があると非常に強いものの、低予算では coordination tax があり、今回に最も近い長期Web調査の ArcticSwarm は**中央値83.3分**で、30分条件をそのまま満たしません。:chatgpt-content-reference{index="0"}

ただし、これはBの優位が実証済みという意味ではありません。**この推奨に最も不利なのは ArcticSwarm**で、ほぼ同じ総トークン量では独立実行＋多数決63.2%に対し82.6%でした。また、長時間探索研究では小予算域では単一長時間実行が先行します。したがって、後述の同一業務上の比較実験でCまたはAが専門家確認時間を明確に減らすなら、推奨は覆すべきです。:chatgpt-content-reference{index="1"}

調査基準日は**2026-09-27 00:00 UTC**です。以下6本はいずれも独自実験を含む一次研究で、うち4本が2026-07-01以降の初公開です。締切後の版は使用していません。

---

## 研究比較表

| 研究・版 | 対象タスク／モデル・構成 | 計算予算と費用の単位 | 評価・選択方法 | 主要結果と原文所在 | 今回への適用限界 |
|---|---|---|---|---|---|
| **Liu et al., _Budget-Aware Tool Use Enables Effective Agent Scaling_**。初公開 2025-11-21、使用 **v2 2026-08-17**。COLM 2026採択。:chatgpt-content-reference{index="2"} [本文 v2](https://arxiv.org/html/2511.17006v2) | BrowseComp / BrowseComp-ZH / HLE-Search、Gemini-2.5-Pro/Flash、Claude Sonnet 4。ReAct、Budget Tracker、BATS。BATSは計画→検索→自己検証→CONTINUE/PIVOT/SUCCESS→必要時に履歴圧縮・新試行。:chatgpt-content-reference{index="4"} | **予算**はsearch/browseの最大tool-call数。**実現費用**はLLM入出力トークン料金＋search/browse料金。tool callは実験上各$0.001に標準化。したがって「budget=100」と実費100相当は同義でない。:chatgpt-content-reference{index="5"} | BrowseComp等の正答率。BATSでは検証済み候補から最終LLM judgeが選択。並列baselineはmajority / Best-of-N / Pass@N。 | Gemini-2.5-Proで同一budget=100のBudget TrackerはBrowseComp **12.6→14.6%**（Table 1, p.5）。別比較ではTracker budget10が12.8%、ReAct budget100が12.6%、実費6.8¢対9.9¢（Table 2, p.5）。BATSのverification除去で18.7→15.4%（Table 4, pp.9–10）。:chatgpt-content-reference{index="6"} | 今回に最も近いWeb検索研究だが、評価は最終回答の正答率であり、**引用忠実性・比較表品質・専門家確認時間**は測っていない。tool価格も実験用標準値。30分制約も評価対象外。 |
| **Li et al., _Benchmark Test-Time Scaling of General LLM Agents_**。初公開・使用 **v1 2026-02-22**。査読状況はarXivから未確認。:chatgpt-content-reference{index="7"} [本文 v1](https://arxiv.org/html/2602.18998v1) | Search/Coding/Reason/Tool-useの7 dataset。10モデル。Aに相当する逐次延長と、Bに相当する独立K本生成を直接比較。K≤4、context≤196K。:chatgpt-content-reference{index="9"} | コスト表は主にモデルの**input/output token API料金**。tool output自体は入力tokenに含むが、外部検索API等のサービス料金を今回のような統一総費用にはしていない。:chatgpt-content-reference{index="10"} | Pass@Kをoracle上限として、point-wise/pair-wise Self-Choiceで実際の候補選択を評価。 | K=1→4でPass@Kは平均約50%相対改善する一方、Self-Choiceは一貫して下回り、Kを増やすと悪化する場合もある（§4.3, Fig.8, p.7）。逐次法はSearchで例としてQwen約112K、Gemini Flash約96K以降に飽和・悪化（Fig.7, p.6）。:chatgpt-content-reference{index="11"} | Bについて重要な「**候補生成≠候補選択**」の警告。ただし各問題の文献比較表や引用検証とは異なり、外部検索費用も完全には計上していない。外部GPT-5 verifierもこの設定では自己判定を概して上回らなかった。 |
| **Kwok et al., _LLM-as-a-Verifier: A General-Purpose Verification Framework_**。初公開 **2026-07-06**、使用 **v2 2026-07-07**。査読状況未確認。:chatgpt-content-reference{index="12"} [v2](https://arxiv.org/abs/2607.05391v2) | Terminal-Bench V2、SWE-Bench Verified、robotics、medical。候補を複数生成し、probabilistic verifier＋pivot tournamentで選択。fine-tuningなし。:chatgpt-content-reference{index="14"} | 候補数Nに加え、verifierは通常 **score granularity G=20、反復K=8、3基準**。論文はこの検証計算を実験するが、候補生成＋外部toolまで含む今回式の統一「4×総費用」は提示していない。:chatgpt-content-reference{index="15"} | verifierでpairwise評価し最高正規化scoreを提出。Pass@1、Oracle Pass@N、実際のselected accuracyを区別。 | Terminal-Bench：GPT-5.5をN=5生成、Gemini-2.5-Flashで検証。**83.1% Pass@1 / 92.1% oracle Pass@5 / 86.5% selected**（Table 3, p.9）。SWE-Benchは76.1 / 84.4 / 78.2%。:chatgpt-content-reference{index="16"} | 「検証を厚くすればよい」の根拠にはなるが、強い別verifierとlogprob取得を使う。今回の「固定基盤モデル」を同じモデルだけで実装した場合に同じ効果が出る証拠ではない。引用の真偽も未評価。 |
| **Yoon et al., _ArcticSwarm: Deferring Early Consensus in Long-Horizon Multi-Agent Research_**。初公開・使用 **v1 2026-09-01**。査読状況未確認。:chatgpt-content-reference{index="17"} [v1](https://arxiv.org/abs/2609.01870v1) | BrowseComp-Plus、主評価Qwen 3.5-27B（830問）、live-webでGPT-5。Cだが常時共有ではなく、BBS＋**gated isolation**＋専任review＋3段階commit gate。:chatgpt-content-reference{index="19"} | end-to-end tokensはorchestrator＋全subagentのinput/output/cacheを含む。tool callsとwall timeも報告。ただし検索サービスの金銭費用を含む統一ドルコストではない。:chatgpt-content-reference{index="20"} | 通信系はreview gateで候補をchallenge/verify。独立runについて多数決とoracle Best-of-Nも計測。 | Arctic **82.6%**。gated isolationなし78.8%、さらにreviewなし74.5%（Table 3, p.6）。約同量tokenのMiroFlow独立N≈36はmajority 63.2%、oracle Best-of-N 86.1%（Table 13, p.20）。ただしArcticは24.9M tokens/case、**中央値83.3分**（Table 14, p.21）。:chatgpt-content-reference{index="21"} | 今回に最も近い「長期Web研究＋不完全verifier」のC証拠。ただし83.3分は30分を大幅超過。平均約8 agents・大量tokenで、4×条件への外挿はできない。 |
| **Liu et al., _When Agents Slow Down_**。初公開・使用 **v1 2026-09-14**。査読状況未確認。:chatgpt-content-reference{index="22"} [v1](https://arxiv.org/abs/2609.15309v1) | 連続的にobjective scoreを得られる4種のopen-ended optimization。最大100M tokens/session。PolyominoでKimi Code/Kimi K2.7を用い、長い1 runと複数sessionへの分割を比較。 | allocation実験は総tokens、100M。cache-inclusiveだが各条件ともcontext windowを大幅に超えるため比較上の偏りは小さいとする。検索API等の総費用指標ではない。:chatgpt-content-reference{index="24"} | best-so-farのobjective scoreをElo化。推定inflection pointで総計算を複数sessionへ分割。 | Polyominoではinflection ≈38M tokens、100Mを3 sessionに割るとjoint-Elo **2245**、1 session **1981**、10 session **1890**、差は+264/+355（Fig.8, pp.13–14）。ただし**小予算では1 sessionが先行**。bootstrap 90% CIは1-session比+135～+412。:chatgpt-content-reference{index="25"} | 「AかBかは予算領域次第」という強い反例。ただし100M token級、連続objective feedbackあり。今回の4×がinflectionより前か後かは全く分からない。 |
| **Park et al., _Scaling Discovery through Test-Time Communication_**。初公開・使用 **v1 2026-09-17**。査読状況未確認。:chatgpt-content-reference{index="26"} [v1](https://arxiv.org/abs/2609.21032v1) | ARC-AGI-3（Sonnet 4.6）、Polyomino（Sonnet/Opus 4.6）、MNIST compression（GPT-5.6 Sol）。agentごとに別context、shared filesystem＋append-only log。:chatgpt-content-reference{index="28"} | ARCはper-agent action budgetとcumulative **output tokens**、長期実験は3–72h/96h。入力token・検索費用・通信を今回式の統一金額にはしていない。 | team@k vs best@k。途中で数値score/level successを確認できるタスクを中心に「verified progress sharing」を評価。 | ARCでteam@3 4.6% vs best@3 1.4%、team@5 8.0% vs best@5 2.2%（Table 1, p.2）。しかし≤400K output tokens/agentではbest@kが先行（Fig.3, p.6）。Terminal-Benchではteam@2 **60.67%**、independent pass@2 **62.36%**（Table 3, p.16）。:chatgpt-content-reference{index="29"} | Cの利点が**十分な計算量と判別力のある途中feedback**に強く依存。文献調査には局所的citation checkは作れるが、最終採用判断には完全verifierがないため直接移植できない。 |

---

## 横断的な考察

### 1. 「Aは伸びない」と「長く走る価値がある」は矛盾しない

General AgentBenchでは、Aに近い逐次スケーリングは**raw interaction historyをそのまま延長**し、一定以上で飽和・悪化しました。対してBudget-Aware研究のBATSは、残予算を明示し、失敗時には軌跡を要約してcontextを圧縮し、CONTINUE/PIVOTを選びます。つまり「同じ一つのcontextをただ長くする」のではありません。:chatgpt-content-reference{index="30"}

さらに _When Agents Slow Down_ では、小予算では1 sessionが最良で、大予算になってから複数sessionが逆転します。したがって研究から言えるのは「Aは常に悪い」「Bは常に良い」ではなく、**追加計算の限界収益とcontext/探索の固定化次第で転換点がある**ということです。:chatgpt-content-reference{index="31"}

**実証された範囲**はここまでです。**私の仮説**としては、今回の4×・30分は100M-token級の研究よりかなり別の領域であり、どちら側の転換点にいるかは論文から決められません。そこで「2本だけ独立化し、残りを検証へ回す」という保守的なBを最初に試す価値があります。3～4本へ直ちに増やす根拠はありません。

### 2. 「CはBより強い」と「通信は役に立たない」も条件付きで両立する

_Scaling Discovery_ は、**途中の改善を数値scoreやlevel successで信頼して判定できる**ARC/optimizationで大きなCの利得を示しました。しかし同じ論文のTerminal-Benchでは、最終graderはあっても途中feedbackが不完全で、team@2 60.67%はindependent pass@2 62.36%を上回りませんでした。著者自身も原因推定はdescriptive evidenceと限定しています。:chatgpt-content-reference{index="32"}

ArcticSwarmはさらに重要です。「verifierがない長期調査」でCを成功させるために、**全員が常に読み合うのではなく、探索中は一部を隔離し、共有前にreview gateを置く**設計です。gated isolationを外すだけで82.6→78.8%、reviewを段階的に除くと76.3%まで下がりました。:chatgpt-content-reference{index="33"}

したがって、Cを「agent数を増やしてチャットさせること」と捉えるのは誤りです。文献調査への**私の仮説**は、URL到達性、原文との含意、日付・版、数値の再計算のような**局所的に検証できる進捗**は共有してよい一方、「この論文が決定的」「結論はB」といった総合判断を早期共有するとherdingの危険がある、というものです。これは今回の業務でまだ実証されていません。

---

## 原文からの定量検算

**検算1：Budget Trackerの「1/10予算」は1/10費用ではない。** Table 2のGemini-2.5-Proでは、ReAct budget100が正答率12.6%、search 14.24回、browse 1.36回、総費用9.9¢。Budget Tracker budget10は12.8%、8.48回、1.09回、6.8¢です。:chatgpt-content-reference{index="34"}

したがって、正答率差は **+0.2 percentage points**、相対改善は \(0.2/12.6=1.59\%\)。費用削減は \((9.9-6.8)/9.9=31.3\%\)、search削減40.4%、browse削減19.9%です。**preset tool budgetは100→10でも、実際の費用は90%減ではありません**。また同一budget=100同士ならTable 1で12.6→14.6%、すなわち+2.0pp、相対+15.9%です。上限値と実消費を分ける必要があります。:chatgpt-content-reference{index="35"}

**検算2：候補中に正解がある確率と、最終選択正答率は別物。** LLM-as-a-VerifierのTerminal-Benchでは、N=5候補についてPass@1=83.1%、**Oracle Pass@5=92.1%**、verifierが実際に選んだ回答=86.5%です。:chatgpt-content-reference{index="36"}

したがって選択による改善は **+3.4pp**、Pass@1比の相対改善は **4.09%**。しかしoracleとの差はなお **5.6pp**。利用可能なoracle headroom \(92.1-83.1=9.0\)pp のうち回収できたのは \(3.4/9.0=37.8\%\) です。**92.1%を「Bの最終正答率」と読むのは誤り**です。また5候補を作る費用にverifier計算が加わるので、同じ候補数と同じ総費用でもありません。

**検算3：ArcticSwarmはBへの強い反証だが、比較条件を限定して読む必要がある。** MiroFlow独立N=36は24.66M tokens/case、oracle Best-of-N=86.1%、多数決=63.2%。ArcticSwarmは24.9M tokens/caseで82.6%です。総tokenは約1%差なのでtoken量ではかなり近く、C側は多数決に対し **+19.4pp、相対+30.7%**。一方、独立候補に「どれか正解がある」率86.1%と多数決63.2%の差は**22.9pp**あります。つまり独立生成そのものではなく**選択・統合が大きなボトルネック**です。:chatgpt-content-reference{index="37"}

ただしこれは「同じ総token」に近いだけで、同じagent数・検索費用・wall-clockではありません。ArcticSwarm自体は中央値83.3分です。したがってこの19.4ppを今回の30分・4×へそのまま移せません。:chatgpt-content-reference{index="38"}

---

## 今回の構成案

最初のpilotでは **B'** を次のようにします。

**探索:** 同じ固定モデルで2本。プロンプト・tool群・最終形式は同じにするが、途中の検索結果、候補論文、結論は互いに見せない。各branchには現在の1回実行に相当する実測費用上限を置く。

**検証・統合:** 「どちらの完成回答が良いか」を一発でjudgeさせるのではなく、各branchから `主張 / 一次資料 / 版 / 原文所在 / 数値 / 採用判断への影響 / 未解決点` を抽出し、同じ固定モデルによる独立検証と決定的チェックをかけます。URL・版・日付・表番号・算術は可能な限り機械的に確認し、モデルjudgeには原文との含意や相反証拠の評価を担当させます。

**追加探索:** 2 branchの不一致、重大な未検証主張、採用判断を反転させる可能性のある証拠だけ再検索します。総計算を漫然と「推敲」に使いません。2 branch分を最大2×、検証・統合・追加検索を合わせて残り最大2×とする**費用上限**は設定できますが、これはtoken数や所要時間が2倍になるという仮定ではありません。実測課金をbudget controllerで積算する必要があります。

Cを初手にしない最大の理由は、ArcticSwarmの好結果そのものではなく、**好結果を得た条件が今回のhard constraintsから遠い**ことです。逆にB'を見送るべき兆候は、独立候補には良い回答が頻繁に存在するのに統合後に悪化すること、専門家確認時間が減らないこと、または引用忠実性が落ちることです。

---

# 推奨を覆し得る検証計画

これは**提案する実験であり、実施済みではありません**。

| arm | 構成 | 機械費用 |
|---|---|---|
| **Control** | 現行の1回実行 | 実測 \(C_0(q)\) ≒ 1× |
| **A+** | 1 agentを継続。budget残量を明示し、context圧縮を許すが独立branchは作らない | ≤4 \(C_0(q)\) |
| **B'** | 独立2 branch → claim/evidence-level検証 →統合→争点のみ再検索 | ≤4 \(C_0(q)\) |
| **C-lite** | 3 agent程度。最初は探索を隔離し、その後verified findingsだけ共有、reviewerを1系統置く | ≤4 \(C_0(q)\) |

実験は次のように固定します。

1. **課題と反復。** 過去の実依頼から24件を、分野・難度・必要検索量で事前層別抽出します。A+/B'/C-liteは各課題2 seedを実行し、Controlも可能なら2回再現して現行系の分散を把握します。全armが**同じ課題**を解きます。24件は稀な重大事故率を精密推定するには小さいため、pilotは「明確な劣化を棄却する／有望案を選ぶ」用途とし、希少事故の安全性を証明したとは扱いません。

2. **公平な費用計上。** \(C_0(q)\) は同じ課題に対する現行policyの実測値です。実験armでは input/output/cache token料金、検索API、page/PDF取得、verifier、judge、synthesis、agent間通信、再検索を**すべて**積算し4 \(C_0(q)\)でhard stopします。早く終了したarmに無意味な計算を追加して4×へ揃えません。実費と品質のParetoも併記します。専門家確認時間は4×のmachine budgetには加えず、別の主要成果指標とします。

3. **wall-clock。** 30分は費用とは独立したhard constraintにします。2 branch/複数agentは可能な範囲で並列実行し、30分時点で未完ならfailureとして扱います。評価開始前にサービスのlatencyだけを測るdry runを行い、「何分まで探索を許し、いつ統合を強制開始するか」を凍結します。4×から時間配分を逆算しません。

4. **盲検専門家評価。** architecture名、seed、内部traceを隠し、最終成果物の書式を統一してランダム順に提示します。専門家は引用先を実際に開けます。主要指標は、(a) material claimを分母にした**citation fidelity**、(b)誤った採用判断、主要数値の誤読、一次資料と矛盾する引用、決定的反証の欠落を含む**重大誤りの有無**、(c)専門家が納品可と判断するまでの**active verification minutes**です。可能なら2名独立採点し、相違はarchitectureを伏せたままadjudicationします。

5. **Bのselector gapを直接測る。** 事前に無作為指定した半数の課題では、最終統合とは別に2本のbranchを専門家が個別評価します。これにより「少なくとも1本が納品可能だった率」と「統合後が納品可能だった率」を分離できます。前者が高く後者が低ければ、追加branchではなくselector/verifierがボトルネックです。これはPass@Nとselected accuracyを混同しないための業務版指標です。

6. **不確実性と事前判定。** taskをclusterとするpaired bootstrapで95% CIを出し、seedを独立taskとして数えません。提案する事前採用条件は、B'がControl比で専門家確認時間を**少なくとも20%短縮**し、その95% CIが少なくとも改善方向にあること、重大誤り率の点推定悪化が+2pp以内かつ95% CIが+5ppを超える害を支持しないこと、citation fidelity低下が2pp以内であること、そして全runが4×/30分hard cap内であることです。さらに「branchの少なくとも1本は合格だったのに統合後不合格」が5%以上ならB'は採用を保留し、selectorを改修します。**A+またはC-liteがB'に対して同じ品質条件を満たしつつ専門家時間をさらに10%以上短縮すれば、今回のB推奨を覆します。** 20%・10%・2pp・5ppは論文から導いた閾値ではなく、実験開始前に固定するための提案上の事業判断値です。

この設計で重視すべきは、モデル正答率そのものより**専門家の確認時間が本当に減ったか**です。Bで候補数だけ増え、専門家が2本分のソースを再確認することになれば、品質が少し上がっても今回のボトルネック解消には失敗です。

---

## 採用判断

現時点では、**B'を最初にshadow/pilotし、Aを無制限な長時間実行としては採用せず、Cは第二候補とする**のが妥当です。

B'を本運用へ進めない条件は、上記pilotで「確認時間の有意義な削減がない」「重大誤りまたは引用忠実性が悪化」「候補には正しいものがあるのに統合器が壊す」「4×または30分を守れない」のいずれかです。とくにGeneral AgentBenchとLLM-as-a-Verifierの結果から、**候補を増やしただけではボトルネックはselectionへ移る**可能性が高いので、2本を超える独立runを最初から増やす優先度は低いです。:chatgpt-content-reference{index="39"}

Cを再検討する条件は、B'の独立探索が同じ文献・検索経路を大量に重複し、かつ今回の業務で「一次資料がこの条件を満たす／満たさない」のような**途中で信頼して検証できる進捗単位**を設計できる場合です。その場合も、ArcticSwarm型の「探索の一部は隔離、検証済み証拠だけ共有」を比較対象にすべきで、常時全共有型Cを代表構成にはしない方がよいでしょう。:chatgpt-content-reference{index="40"}

## 短い検索記録

検索は主に `"test-time scaling" agents sequential parallel verifier 2026 arxiv`、`"multi-agent" communication "test-time" verifier research 2026 arxiv`、`"deep research" multi-agent verifier parallel independent 2026 arxiv`、`"agent scaling" web search budget tool calls 2026 arxiv` で行い、arXivの版固定HTML/PDF本文まで確認しました。

採用した6本は、A/B/C、候補選択、Web検索費用、通信の正負両結果を一次実験で直接扱うものを優先しました。検索で見つかった _Scaling Test-time Compute for LLM Agents_（2025）は広く関連しますが、6本上限の中では後発研究の方が今回の失敗条件を詳しく切り分けているため中核から除外しました。_Multi-Agent Verification_（2025）は複数verifierの研究として関連するものの、長期agent/Web調査への近さでLLM-as-a-Verifier等を優先しました。_ParallelWorld_（2026-08）はembodied reasoning中心で導入条件から遠いため除外しました。:chatgpt-content-reference{index="41"}

**中核6本については本文を取得できなかったものはありません。** 査読状況について、Budget-Aware論文はarXiv上でCOLM 2026採択を確認できましたが、それ以外の5本は締切時点のarXivメタデータから採択・査読完了を確認できなかったため「未確認」としています。