# Live official-document follow-up — 2026-09-27

Four replies provisionally pass content, evidence, and format. Both Japanese policies identify the current stable documentation and supply supporting official section links for Python dictionaries and Requests timeouts. This does not establish an overall winner, spontaneous attribution, or a full-suite pass. Human grade confirmation and merge remain pending. No Pro request was sent.

## Conditions

- A is `29ad511c447a5cb15c30cde7cb2d0a6b9aeb8218:PROMPT.md` (1,345 characters); B is `01cd1decb47768bb5248bb70439f46f737a13ddb:PROMPT.md` (1,403 characters). Both are Japanese, so this is not an English/Japanese comparison.
- The [plan and exact inputs](plan.json) were saved locally before submission, but not committed or posted beforehand. Order: Python A → Python B → Requests B → Requests A, once each, without regeneration or replacement. The core [grading reference](oracle.md) facts were checked before submission; the reference file was saved during collection before the first reply was copied.
- Each case explicitly asks for current official documentation, its version, and section links. No fixture context, answer, URL, synthetic wrapper, policy text, or rubric was sent in the chat. The prepared input was checked against the composer before sending. These live-web cases are separate from the unchanged 16-input synthetic suite, where external retrieval remains prohibited.
- Each fresh Personalized temporary chat selected `GPT-5.6 Sol`; the model menu showed **5.6 Extra High, 4 of 5** before sending. Per-reply `*-model.png` and `*-mode.png` captures preserve the model and selected Personalized radio. Backend revision and sampling parameters are unavailable.
- Web search was ON; memory, writing-style reference, fast answers, suggested prompts, record-history reference, Library search, and connector search were OFF. [controls.json](controls.json) records checks after reload and before/after each reply. Memory eligibility follows [EVALS.md](../../EVALS.md); no internal provider-state inspection is claimed.
- Instructions were installed only in settings, reloaded, reopened, and read back before every reply. Saved values equal their canonical policies with exactly one terminal LF removed: A 1,344 and B 1,402 characters. A reload attempt during the Python B save encountered a browser confirmation; it was canceled, then an unobstructed reload/readback completed before submission. No answer was collected under that transient state.
- Raw `.md` files preserve Copy output bytes, including CRLF and opaque `:chatgpt-content-reference` tokens. Their UI index-to-source mapping is not preserved. Grades rely on the explicit Markdown links and independent source checks, not invented mappings for those tokens. Search/open execution traces were not captured; correct current versions and valid citations do not independently prove how the evaluated chat retrieved its sources.

## Provisional grades

P = pass. Times are JST on 2026-09-27; copy time is not generation latency. Every row is repeat 1. Length includes Markdown, URLs, and copied citation tokens, normalizing CRLF to LF only for counting.

| Reply | Sent / copied | Content | Evidence | Format | Overall | Characters | Model / mode |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Python A](python-A.md) | 19:12:11 / 19:13:56 | P | P | P | Provisional pass | 1508 | [Model](python-A-model.png) / [Mode](python-A-mode.png) |
| [Python B](python-B.md) | 19:15:55 / 19:17:25 | P | P | P | Provisional pass | 1363 | [Model](python-B-model.png) / [Mode](python-B-mode.png) |
| [Requests B](requests-B.md) | 19:19:04 / 19:22:08 | P | P | P | Provisional pass | 1358 | [Model](requests-B-model.png) / [Mode](requests-B-mode.png) |
| [Requests A](requests-A.md) | 19:23:21 / 19:24:15 | P | P | P | Provisional pass | 1287 | [Model](requests-A-model.png) / [Mode](requests-A-mode.png) |

- **Python A/B:** Both explain insertion order as a language guarantee from 3.7, distinguish CPython 3.6's implementation detail, preserve a replaced key's position, and move a deleted/reinserted key to the end. Both identify 3.14.7 and distinguish prerelease documentation. Their explicit Data model and 3.6 What's New links support these claims. A also links the Library Reference and 3.7 release highlights; B gives a correct concrete order example. All required details are present in Japanese. Repetition exists, but the predeclared format gate has no hard word count or mandatory source count.
- **Requests A/B:** Both reject a 13-second whole-download guarantee, distinguish connect=3 from read=10, explain between-byte inactivity and continued trickle data, and state that omission configures no timeout. Both identify 2.34.2 and link the official Timeouts sections. Their additional per-IP-attempt caveat is supported. A uses `/latest/`, B `/stable/`: both paths identify 2.34.2 at verification time, so A is not failed merely for its alias. Both directly answer in Japanese.

## Independent source checks

Checks were performed on 2026-09-27, separately from the evaluated chats:

- [Python stable index](https://docs.python.org/3/) identifies 3.14.7. [Data model / Dictionaries](https://docs.python.org/3.14/reference/datamodel.html#dictionaries) supports both answers' order claims. [Python 3.6 What's New](https://docs.python.org/3.6/whatsnew/3.6.html#new-dict-implementation) and [3.7 release highlights](https://docs.python.org/3.14/whatsnew/3.7.html#summary-release-highlights) support the historical distinction. All four explicit Python A URLs returned HTTP 200 with the intended fragments present; Python B's two URLs are identical to two of those. [URL metadata](python-A-url-checks.json) records titles, destinations, timestamps, and body hashes. The Library Reference redirected from `/library/stdtypes.html` to `/builtins/stdtypes.html`, with its dictionary anchor present.
- Additional Python claims also match primary pages: [3.14.7 release](https://www.python.org/downloads/release/python-3147/) gives August 5, 2026; [3.15 docs](https://docs.python.org/3.15/) identify 3.15.0rc2 and [development docs](https://docs.python.org/dev/) identify 3.16.0a0.
- [Requests stable index](https://requests.readthedocs.io/en/stable/) identifies 2.34.2. Its [Advanced Usage / Timeouts](https://requests.readthedocs.io/en/stable/user/advanced/#timeouts) and [Quickstart / Timeouts](https://requests.readthedocs.io/en/stable/user/quickstart/#timeouts) support the timeout claims. A's [latest Advanced Usage](https://requests.readthedocs.io/en/latest/user/advanced/#timeouts) and [latest Quickstart](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts) were also opened with the web tool and identified 2.34.2 with the same relevant text. [PyPI's release record](https://pypi.org/project/requests/2.34.2/) supports A's additional May 14, 2026 release date. Tracking queries were omitted for these content checks.
- The web tool retrieved Requests page bodies; separate direct `urllib` requests to its stable index/Advanced Usage returned HTTP 403. [Reference-check metadata](reference-checks.json) retains those failures rather than labeling every retrieval successful. Conversely, the web tool failed on the old Python 3.6 page, while direct HTTP retrieval succeeded. These are grader access differences, not evidence of model retrieval failure. The metadata hashes are not archived page bodies; live aliases can subsequently change.

The evidence passes are output-level findings: stated versions agree with current primary sources and the linked sections support the answers. They do not certify the models' statements that they actually fetched the bodies, because no independent model-side retrieval trace was retained.

## Restoration and limits

Original empty instructions and all eight original control values were restored and verified after reload. Writing-style reference returned to OFF and the other seven switches to ON. Power remained non-Pro Extra High. Five owned windows were closed; zero remained. Other windows/history were not deleted. Restoring switches does not recover memory potentially lost while disabling it.

This pair of live questions shows no observed A/B correctness or citation failure. B's copied output is shorter for Python, but longer for Requests; token/URL-inclusive character counts alone are not a quality verdict. Search results and retrieval paths were not held fixed, and each condition has only one reply per question. Neither a reliable advantage nor a causal policy effect is established. Both prompts are Japanese, so language effects remain untested.

The previous [case 10 candidate attribution failure](../chatgpt-nonpro-2026-09-27/README.md) remains recorded. Explicitly asking for links here does not resolve that spontaneous-attribution question. No prompt, synthetic input, or grading criterion was changed after observing these replies. This follow-up does not validate the policy's research stopping rule, complete the 16-input suite, cover Copilot, or replace human grade confirmation. Merge remains on hold.
