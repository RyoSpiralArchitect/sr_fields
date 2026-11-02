# What happens when A names the feeling?

[Findings in English](observations.md) · [日本語の結果](observations.ja.md) · [Full comparison figure](results/field-by-prompt.svg)

This experiment extends the [English powerset](../english-powerset/observations.md). The original dialogue used “I don't know.” The two new versions use “I felt embarrassed.” and “I felt happy.” Everything else in the user message and all 4,096 system messages are identical across prompts. Each combination has three seed slots. The 24,576 new requests share one Batch job, with both prompts adjacent within each mask/seed block. The 12,288 uncertain replies come from the earlier batch.

The [plan](plan.md), [protocol](protocol.json), [English markers](measures.py) and [design lock](design-lock.json) specify the questions and fixed inputs. The [reading guide](reading-guide.md) gives examples for the blinded language assessment. The [data dictionary](results/README.md) lists the measurement files.

## Reproduce the analysis

From the repository root, `python3 -I -S experimental/english-emotion-pair/verify_study.py` checks the published per-slot tables without raw replies or API access. It checks paired prompt differences, Field effects, Field-by-prompt differences, the 66 two-Field interactions in each case, and agreement with the previous study's 624 contrasts.

With the two private collected batches present locally:

```sh
python3 -I -S experimental/english-emotion-pair/collect_texts.py
python3 -I experimental/english-emotion-pair/study.py
python3 -I experimental/english-emotion-pair/decode.py
python3 -I experimental/english-emotion-pair/plot.py
python3 -I -S experimental/english-emotion-pair/reader.py
```

The statistics, decoding and figure scripts use NumPy, scikit-learn and Matplotlib; they are optional analysis dependencies. The local file `.runs/english-emotion-pair/compare-prompts.html` lets a reader hold the Field set and seed constant across three recorded replies. The full text table and the reading sample with annotations stay under the ignored run directory.

For a new independent reading, `blind.py prepare` draws the fixed sample after collection. Read each displayed stimulus and response in order, record a code and short note without seeing the Field settings, save `blind-labels.csv` in the private run directory, then run `blind.py reveal` and `reading_summary.py`. The reveal step records the original labels' digest before decoding the sample positions. A future reader should keep their own labels separate from the locked first reading.

## Reproduce the request design

```sh
python3 -I -S experimental/english-emotion-pair/run.py prepare
```

Preparation is offline and compares the regenerated historical request bytes with their original digest. To run a fresh experiment, `run.py submit` sends the single verified file and starts up to 24,576 billable generations. `run.py status` and `run.py collect` only read from the provider. The existing run directory has exclusive submission markers. Keep the exact requests and the original private receipts for reconciliation if any submission is interrupted.
