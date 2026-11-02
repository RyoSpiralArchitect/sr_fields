# Who found it funny?

**Proposed experiment.** The previous happy condition produced the phrase “what was so funny” in 357 of its 1,032 questions. Does B treat an event as funny, or attribute amusement specifically to A? A can enjoy being with people who laughed without finding the event funny themselves. [Previous counts](../english-emotion-pair/results/reading-phrase-followup.csv)

Keep A happy in every condition. Change whether **the others laughed or smiled**, and whether A leaves their amusement unstated, explicitly affirms it, or explicitly denies it. The two explicit statements share the word *funny*. The unstated control is shorter. The wording “the others” leaves A's outward reaction unspecified.

| Factor | Planned conditions |
| --- | --- |
| Observed reaction | “the others laughed” / “the others smiled” |
| A's words following “I felt happy.” | No added sentence / “I found it funny.” / “I didn't find it funny.” |
| System prompt | Common instructions only / GentleField / ThresholdField / both in catalog order |
| Replicates | Ten preselected seeds per cell, one single-sentence reply each |

This gives **240 planned replies** (2 × 3 × 4 × 10). Six stimuli are matched at each of 40 Field-set/seed positions. Use one interleaved batch if executed, keep failed or incomplete slots, and record backend fingerprints. [Machine-readable proposal](plan.json)

## Primary question and scoring

The primary comparison is the change from unstated to denied in the proportion of replies that **positively assert or presuppose that A found it funny**, matched within reaction, Field set and seed. There are at most 80 pairs. Report both absolute rates, the paired difference, and the counts switching in either direction. The affirmed condition provides a reference for grounded uptake. Separately compare laughter with smiling and describe how the selected Fields modify these contrasts.

Have two readers independently code the dialogue and reply in mixed order, with Field, seed, other ratings and aggregate outcomes hidden. Preserve each initial reading, identify human or model raters, report agreement and show disagreements. Use separate indicators so a reply can contain several moves.

| Indicator | Example or boundary |
| --- | --- |
| B assigns amusement to A | “What did **you** find funny?” treats A's amusement as given. An accurate report of A's denial scores zero on this indicator. |
| B presupposes something funny about the event | “What was so funny?” can imply an amusing event while leaving the experiencer unspecified. Score an attribution to A only when the wording supports it. |
| B asks an open question about A's amusement | “Did you find it funny too?” offers a choice. Record separately whether it reopens an answer A already supplied. |
| B attributes amusement to others only | “What do you think they found funny?” assigns a reading to others. Assess its compatibility with A's denial separately. |

Mark material uncertainty explicitly. Show bounds that count unresolved primary labels as absent and present; keep incomplete pairs visible in the coverage report. Preserve low or equal rates. The original phrase count was exploratory. Outcomes of the proposed study have not been collected.

## 日本語

Aの「うれしかった」は全条件で固定する。周囲が笑ったか微笑んだか、Aが「面白いと思った」と明言・否定・保留するかを変える。主に見たいのは、Aが否定したあとにも、Bが「**あなたは**何を面白いと思ったの？」と返すかどうか。英語の “What was so funny?” だけなら、誰が面白いと思ったかは未指定かもしれない。場面の面白さ、A本人への帰属、他者への帰属、開かれた質問を分けて読む。240件は計画件数である。
