# Naming an unsettled feeling

When someone says a moment still sticks with them, does the next reply name an emotion for them? This experiment compares two continuations of the same authored Japanese dialogue.

The first pair completed on November 1, 2026. [Read the replies and observations](observations.md).

| Order | Condition | Instructions |
| --- | --- | --- |
| 1 | Common | Japanese common instructions only |
| 2 | Threshold | The same common instructions plus the named ThresholdField policy in JSON |

The [protocol](protocol.json) fixes the input, order, model, language, token cap and both request hashes before the trial. Each condition gets one fresh Responses request to `gpt-6-sol` with reasoning effort `none`, `store: false` and a cap of 256 output tokens. The input asks for B's next line in one natural Japanese sentence. Only the instructions differ between requests.

Read each reply alongside A's actual words. Does B assert an emotion or motive that A has not named? Does B take up something A actually said? Does the reply work as B's next line in one sentence? A question can suggest a feeling without asserting it. Record the exact wording and distinguish those cases when interpreting the pair.

## Run locally

From the repository root, preview both request bodies without a credential or network request.

```sh
python3 -I -S experimental/naming-hold/run.py
```

With an existing `OPENAI_API_KEY` in the process environment, explicitly run the pair.

```sh
python3 -I -S experimental/naming-hold/run.py --execute
```

The runner checks request hashes before execution and at dispatch. It reserves a fresh `.runs/naming-hold/` directory, allows at most two requests, and stops after a failed or incomplete slot. A repeated invocation refuses to reuse that directory. A dispatch marker without a result means delivery may be unknown. Private records include exact inputs, requests, replies and file hashes.

One reply per condition supports a comparison of those two texts. Naming, structure and prompt length vary together. Estimating an effect would require additional cases and repetitions.
