# Data dictionary

The cases `uncertain`, `embarrassed`, and `happy` refer to A's third utterance. Mask zero uses the common instructions. Read bit positions from least to most significant using the [existing Field order](../../english-powerset/protocol.json). Individual seed values are 101, 202 and 303.

| File | Row and unit |
| --- | --- |
| [coverage.json](coverage.json) | Provider totals, completion status, source digests, reported tokens, fingerprints and dates for each collection. |
| [slot-features.csv](slot-features.csv) | One row per prompt, mask and seed. Binary markers are 0 or 1. An empty measurement indicates ineligibility or an undefined cue-reuse comparison. |
| [rates.csv](rates.csv) | Eligible denominator, numerator or word total, and mean by prompt. Binary means are proportions. |
| [echo-contexts.csv](echo-contexts.csv) | Exploratory local word contexts within replies that use the exact cue. The patterns detect forms such as “you felt happy” or “I'm happy”. Other wordings remain unassigned. |
| [field-effects.csv](field-effects.csv) | ON minus OFF holding seed and the other eleven Fields fixed. |
| [prompt-differences.csv](prompt-differences.csv) | To-prompt minus from-prompt at the same mask and seed. |
| [fingerprint-matched-prompts.csv](fingerprint-matched-prompts.csv) | Additional sensitivity check for the same comparison restricted to pairs with matching nonempty backend fingerprints. The set of eligible slots can differ across contrasts. |
| [field-by-prompt.csv](field-by-prompt.csv) | Change in a Field's ON-minus-OFF difference when moving between prompts; each complete block has two prompts × two Field states. |
| [field-pairs.csv](field-pairs.csv) | Both ON minus each alone plus both OFF, within a case at the same seed and other ten Fields. These exploratory interactions use the eight original measures. |
| [paired-phrases.csv](paired-phrases.csv) | Two-word phrases ranked by paired difference in reply prevalence. Each reply contributes at most once per phrase. |
| [wording-diversity.csv](wording-diversity.csv), [text-similarity.csv](text-similarity.csv) | Normalized word-sequence counts, top-five share, Shannon entropy and effective forms, plus word-set Jaccard and exact sequence agreement across matched prompts. |
| [decoding.csv](decoding.csv) | Out-of-fold results by grouping rule, intact or cue-removed text, original or mask-swapped labels, and fold. The row marked `all` pools held-out predictions across the five folds. Positive class is happy. |
| [reading.csv](reading.csv), [reading-counts.csv](reading-counts.csv), [reading-transitions.csv](reading-transitions.csv) | Locked single-reader judgments, counts with and without language markers, and transitions across the same 48 sampled mask/seed positions. [Repeat consistency and label digest](reading-check.json). |
| [reading-phrase-followup.csv](reading-phrase-followup.csv) | Exploratory corpus counts for two constructions noticed during the reading, including “what was so funny” in questions. |

For the four contrast tables, one unit is a percentage point for a binary measure and one word for reply length. `matched_blocks` is specific to the measure and comparison. The three per-seed results describe this run. They are printed separately to preserve variability across the seeds.
