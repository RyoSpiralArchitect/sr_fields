# sr_fields

The SpiralReality Field Observatory is a local workbench for exploring when to leave a designation open, how language changes through a dialogue, and how semantic response policies shape a model's reply.

[日本語](docs/README.ja.md) · [Architecture](docs/architecture.md) · [Prompt design](prompts/README.md) · [Evidence](data/README.md) · [Bilingual composition](docs/bilingual-composition.md)

The repository connects three layers:

| Layer | Location | Responsibility |
| --- | --- | --- |
| App | `app/` | Browse signal traces, dialogue stages and historical replies; compose and preview new prompts. |
| Runtime | `runtime/field_observatory/` | Compile prompts, reproduce sample signals, make explicitly enabled bounded API calls, record outcomes. |
| System prompt | `prompts/` | Twelve paired English/Japanese semantic cards and eight presets, derived from private source material without distributing that material. |

These response policies are proposed interpretations of SpiralReality Fields. They do not settle the meanings of the Fields or implement their full ontology.

## Start locally

Python 3.10+ is sufficient. There are no Python packages, JavaScript dependencies, external fonts or CDN assets to install.

```sh
python3 -I -S scripts/observatory.py serve
```

Open **http://127.0.0.1:8768**. The default server browses recorded examples and previews prompts without making model requests. Stop it with Ctrl-C. The interface starts in English and can switch to Japanese. System prompt language is a separate choice; both language versions are included.

The four views are **signal traces**, **dialogue progression**, **historical Field replies**, and **prompt composition**. The question buttons connect curated examples across the first three views; they do not imply equivalent measurements.

## Compose a prompt

```sh
python3 -I -S scripts/observatory.py prompt --preset meaning-crossing --mode structured
```

This exports the exact instructions, ordered Fields, prompt language and the SHA-256 of the instructions. English is the default; use `--language ja` for Japanese. The app can also copy the instructions or download their JSON envelope.

Modes are `baseline` (common instructions), `plain` (selected policies in ordinary text), and `structured` (the same scopes and moves with Field names and JSON structure). A comparison between plain and structured changes both naming and serialization; it does not isolate either one.

The app starts with **all twelve on**. Use **Only this** for one Field, checkboxes for any combination, and the arrow buttons to change prompt order. Eight starting presets are available: `quiet-dialogue`, `grounded-ideas`, `meaning-crossing`, `open-exploration`, `all-fields`, `care-and-pace`, `source-aware`, and `rebuild-and-revisit`. Your selection, order, format and prompt language are remembered locally.

To compose an ordered custom prompt in Japanese:

```sh
python3 -I -S scripts/observatory.py prompt --language ja --fields ShieldField HeartField --mode structured
```

Explicit `--fields` overrides the preset. Empty selections require baseline mode. Order controls placement in the prompt; no behavioral ranking is implied. See [language and composition details](docs/bilingual-composition.md) and [how to extend the pack](prompts/README.md).

## First experiment

Try a two-request comparison on GPT-6 Sol. Both conditions see the same short Japanese dialogue. One uses the common instructions and the other adds ThresholdField. The default command prints a preview locally. [Protocol and commands](experimental/naming-hold/README.md) · [First observed pair](experimental/naming-hold/observations.md).

```sh
python3 -I -S experimental/naming-hold/run.py
```

The [English dialogue experiment](experimental/english-powerset/observations.md) covers all 4,096 subsets (including all-off) at three seeds using GPT-4.1 mini. In 12,288 completed replies, adding GentleField raised the question-mark rate from 64.0% to 90.7% at matched settings. See the [paired contrasts and data](experimental/english-powerset/results/README.md); one English dialogue does not establish usefulness or transfer to other inputs.

## Optional OpenAI execution

The runtime reads an existing `OPENAI_API_KEY` from its process environment. It does not read or write credential files, return the key to the browser, or accept keys through the UI. Use your existing secure credential setup to provide it to the launching process.

```sh
python3 -I -S scripts/observatory.py serve --enable-api --max-requests 3
```

Each click sends **one** input with the selected prompt. New trials use `gpt-6-sol`, reasoning effort `none`, up to 600 output tokens and `store: false`. Each trial starts a fresh conversation without tools. [GPT-6 Sol model documentation](https://developers.openai.com/api/docs/models/gpt-6-sol). System-style instructions are passed through the Responses API's `instructions` field; see [Responses migration](https://developers.openai.com/api/docs/guides/migrate-to-responses).

The session stops on the first failed, incomplete or empty result. There is no automatic retry. The call budget applies to one process and resets on restart. Live calls incur provider usage. The socket timeout is 45 seconds per blocking operation, not a total run deadline. Ctrl-C stops the local server; it cannot guarantee cancellation of a request already received by the provider. `store: false` does not mean all provider-side retention is disabled.

For the CLI, preview first:

```sh
python3 -I -S scripts/observatory.py run --input-file examples/input.txt --preset meaning-crossing
```

Append `--execute` to send exactly one request. Local records go to ignored `.runs/` directories with restricted file permissions. They contain the exact input, prompt and reply; do not publish them wholesale. Model overrides must support Responses and reasoning effort `none`; incompatible models are recorded as failures without fallback.

## What the included evidence establishes

- Five original first-seed signal samples are reproducible from public parameters. They are examples from a larger numerical experiment, not the entire 640-trace dataset.
- Twelve authored dialogue cases retain all 108 original model decisions and replies. A forced binary label can coexist with uncertainty in the actual reply. Author references are not independent human ground truth.
- The historical API pilot retains 17 replies and one missing response from 18 attempted requests. Its Field condition included private source quotations, so its original prompts and exact prompt replay are not distributed.
- A separate [full comparison on one English dialogue](experimental/english-powerset/observations.md) measures wording changes with the public prompt policies. Human usefulness and transfer to other dialogues remain unmeasured. The historical pilot used different prompts.

See [evidence and limitations](data/README.md) and [the public/private boundary](docs/public-boundary.md).

## Check and package

```sh
python3 -I -S -m unittest discover -s tests -v
python3 -I -S scripts/observatory.py verify-signals --portable
node --test tests/composition.test.js
node scripts/check-js.js
python3 -I -S scripts/audit_public.py
python3 -I -S scripts/package_release.py
```

Node 22+ is needed only for the JavaScript tests and syntax check. Tests use mock transports and make no paid model calls. The public-tree audit and package command operate on Git-tracked files; stage new intended files before using them. Packaging writes a new archive and hash inventory to ignored `dist/` and refuses to overwrite an existing archive. The audit is a focused pattern/inventory check, not a guarantee that every possible secret can be recognized.

[Contribution guide](CONTRIBUTING.md) · [Public snapshot procedure](docs/releasing.md)

## License

Apache-2.0 covers the public code, documentation, semantic prompt derivatives and included public example records. Non-distributed private YAML and private provenance material are outside this release. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
