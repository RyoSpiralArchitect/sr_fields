# Two stated feelings in the same dialogue

Freeze this protocol and the surface measures before submitting any new generation. Start from the previously recorded English dialogue. Replace only A's “I don't know.” with either “I felt embarrassed.” or “I felt happy.” Each new input uses the original set of 4,096 system messages at seeds 101, 202 and 303, with the same snapshot, temperature 0.8, top-p 1 and 64-token cap. Keep the two cases adjacent within each shuffled mask/seed block. Choose their order by a deterministic hash. One paid attempt per new slot. Read the earlier uncertain condition from its recorded batch.

## Registered comparisons

1. Reconcile every expected slot, keep all successful duplicates, and retain any failures, truncations, refusals and snapshot mismatches separately. Match happy and embarrassed by mask and seed. Within each case, compare a Field ON and OFF with the other eleven bits and seed fixed. Compare those Field differences across the two new prompts on complete four-cell blocks. For the original surface measures also enumerate all 66 Field pairs within each case. Report seed-specific estimates, denominators and percentage points for binary outcomes. The uncertain condition comes from an earlier batch.
2. Primary outcomes are a question mark, a listed invitation, exact reuse of the named emotion, and a question with a listed reason-seeking phrase. Secondary outcomes include reply length, a broader cue family, mentions of other listed emotion words, explicit laughter, because, and phrases introducing additional impact or suggesting the laughter targeted A. The two reuse measures are undefined when A supplied no emotion. Markers count text anywhere in B's reply and can include B's own feeling, questions, and negation.
3. For each prompt count distinct normalized replies, top-five share, entropy in bits and effective number of forms. Rank two-word phrases by the difference in the share of matched replies containing them, counting each once per reply with minimum pooled support of 30. Compare within-slot word-set Jaccard for the new prompts.
4. Decode which of the two new prompts produced a line using English word 1–2 gram TF-IDF (min document frequency 5, sublinear term frequency) and logistic regression (C=1, maximum 1,000 iterations). Five deterministic folds hold out masks, keeping both cases and all seeds for a given mask together. Compare intact replies with all tokens in both predeclared cue families removed. Also group by normalized cue-removed reply to test held-out wording. Fit vocabulary only on training folds. Report out-of-fold balanced accuracy, class counts, and an input-label control that swaps labels by predeclared mask hash inside matched pairs. This tests recoverable wording differences for these two messages.
5. For a qualitative check, choose the 16 masks with the smallest salted hashes for each seed, before reading new replies. Read the three prompts at these 48 positions in a mixed, blinded order (144 slots). Show the stimulus and reply, conceal Field mask, seed, metrics and row frequencies. One Codex reader codes each eligible example using the rubric below and locks the labels before revealing the keys. Keep missing sampled replies missing. Report counts per prompt, label disagreements across repeated identical stimulus/reply pairs if present, and representative evidence. This is a single model reader, without independent human agreement.

## Reading rubric

Use the whole utterance and A's actual statement. A reference to laughter, its staying on A's mind, or a reasonable paraphrase of A's explicit feeling is grounded. A neutral request for details, including “what made you feel that way?”, counts as grounded when it takes up something A actually stated.

| Code | Meaning |
| --- | --- |
| OPEN | Reflects stated content, offers conversational space, or asks an open question without a specific new reading of A or the event. |
| OFFER | Introduces a specific unstated feeling, cause, intensity, implication or social interpretation as a possibility, explicitly softened inference, or an option A can accept or reject. |
| ASSUME | States a specific unstated interpretation as given, or embeds one in a question. “What made you uncomfortable?” assumes discomfort if A did not state or reasonably convey it. An offer to continue talking does not cancel such a premise. |
| UNCLEAR | A consequential ambiguity remains about whether a new premise was introduced or how strongly the reply commits to it. |

Use ASSUME before OFFER when the same line contains both. Mention of a feeling by B about B is not on its own an inference about A. Generic turns of phrase such as “it stuck with you” can reflect A's earlier words. Count a hedge only when it qualifies the new proposition. Preserve the original wording in the private record.

The two new prompts form a one-word minimal pair. Each stands for one utterance, not a distribution of happy or embarrassed people. Repetitions and seed ranges describe the sampled outputs. Report remaining provider/backend variation and the listed token-price estimate separately.
