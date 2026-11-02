# Twelve Fields, three seeds, one English dialogue

This experiment asks how enabling a named Field policy changes the wording of B's next line in a fixed dialogue about a moment of laughter. The English user message is identical in every request. Each Field retains its catalog position. The 4,095 nonempty subsets use the public structured compiler. With all Fields off, the model receives only the same English common instructions. Those instructions already ask the model to leave unsettled meaning open.

The [protocol](protocol.json) fixes GPT-4.1 mini's dated snapshot, temperature 0.8, top-p 1, seeds 101/202/303 and a 64-token output cap. One generation per mask and seed gives 12,288 slots. IDs are shuffled by a reproducible hash before submission. The [design lock](design-lock.json) binds the complete request file, protocol and frozen [English measures](features.py). The [Chat Completions seed](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) is best effort. Collection records returned models and backend fingerprints.

## Analysis fixed before generation

- Unit of analysis is one complete, nonempty, non-refusal reply from the requested snapshot, with finish reason `stop`. Account for every expected ID. Report missing, HTTP-error, truncated, refusal, malformed and model-mismatch slots separately. Retain repeated texts, since different conditions can legitimately produce the same line.
- Primary measures are the presence of a question mark, the presence of at least one of the listed emotion words, and English word count. The tokenizer counts letter sequences and keeps contractions together. Mentions include questions and quotations. Secondary measures track listed invitation phrases, uncertainty phrases, explicit references to laughing, body vocabulary, and a narrow declarative second-person attribution pattern. A zero is absence of that marker. Its meaning in the dialogue requires reading the line.
- For each Field, pair ON minus OFF at the same seed and identical settings for the other eleven Fields. Average complete pairs, show the per-seed means and pair counts. At full coverage this is 2,048 comparisons per seed, 6,144 per Field. Indicator differences are percentage points. Word differences are words per reply.
- Explore two-Field interactions with the matched four-cell difference `both − first only − second only + neither`, holding the other ten Fields and seed fixed. There are 66 pairs and up to 3,072 complete quartets per pair. Tabulate group means for 0–12 active Fields with denominators. Compare the three seeds within each mask using exact normalized-text agreement and token-set Jaccard similarity.
- Inspect differences in the share of replies containing a two-word phrase. Count each phrase once per reply, require at least 30 replies overall, and rank descriptively. Read illustrative verbatim lines from preselected all-off/all-on conditions and representative matched pairs. No additional model is used to judge the replies.
- This is an enumeration for one English input, not a random sample of dialogues. Three seeds describe generation variability. Seed ranges are not confidence intervals. The contrasts include the wording, name, length and placement added by each card. Interpret the 66 interactions and phrase rankings as exploratory. No significance or general effectiveness ranking is claimed.

## Running it

From the repository root, generate the committed design offline, then submit it only when intending to pay for the full run.

```sh
python3 -I -S experimental/english-powerset/design.py --prepare
python3 -I -S experimental/english-powerset/batch.py submit
python3 -I -S experimental/english-powerset/batch.py status
python3 -I -S experimental/english-powerset/batch.py collect
```

Use an existing process-level `OPENAI_API_KEY` for the three Batch commands. All provider files, raw responses and receipts stay under ignored `.runs/english-powerset/`. Exclusive dispatch markers prevent accidental resubmission. Status and collection issue GETs only. A failed or expired slot is not retried. Submissions with an ambiguous outcome require reconciliation with the provider.

The [Batch API](https://developers.openai.com/api/docs/guides/batch) allows a 24-hour completion window. On the planning date, the listed batch rates per million tokens were USD 0.20 input and USD 0.80 output. Completion of all slots can use at most 786,432 output tokens. Use returned usage for the final token-price estimate. [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
