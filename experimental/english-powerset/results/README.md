# Reading the measurement files

| File | One row per | What to read |
| --- | --- | --- |
| [slot-features.csv](slot-features.csv) | Field mask and seed, including excluded slots | `active` is the number of enabled cards. The [protocol](../protocol.json) lists bit order from least to most significant; zero is the common-instructions control. Indicators are 0 or 1; unavailable measurements are empty. |
| [field-contrasts.csv](field-contrasts.csv) | Field and measure | `delta` is ON minus OFF, matched on seed and the eleven other cards. Seed-specific differences and denominators follow. |
| [pair-interactions.csv](pair-interactions.csv) | Unordered pair of Fields and measure | `delta` is both ON minus each alone plus both OFF, matched on seed and the ten other cards. This is a departure from additivity on the reported scale, not the absolute rate when both are on. |
| [field-count.csv](field-count.csv), [seeds.csv](seeds.csv) | Number of active Fields, or seed | Means of reply features; binary measures are **proportions** (0–1). Extreme active counts have far fewer replies than the middle. |
| [context-count.csv](context-count.csv) | Field and number of *other* active Fields | Additional exploratory breakdown of paired ON-minus-OFF differences: indicators in percentage points, length in words. The 0 and 11 other-Field rows have at most three pairs each. |
| [fingerprint-matched.csv](fingerprint-matched.csv) | Field | Post hoc sensitivity restricted to pairs that also returned the same nonempty backend fingerprint. These are smaller selected subsets, not a replacement for the full contrasts. |
| [phrases.csv](phrases.csv) | Field, direction and two-word phrase | Change in the **percentage of replies** containing this phrase. `reply_support` counts distinct reply slots overall; a repeated phrase in one reply still counts once. |
| [within-mask.csv](within-mask.csv) | Mask | Normalized exact agreement counts and mean Jaccard similarity: shared distinct word tokens divided by all distinct word tokens across each seed pair. |
| [summary.json](summary.json) | Whole run | Eligibility, provider totals, reported usage, backend fingerprints, UTC timestamps, private file digests, and pooled means. |

In the two contrast files, indicator differences are in **percentage points** and length differences are in **words per reply**. The range of three seed-specific differences describes this run; it is not a confidence interval. The [measurement code](../features.py) is the exact English vocabulary and punctuation definition used throughout.
