# Languages and composition

The interface starts in English. Its language selector changes controls, Field descriptions and historical case-title reading aids. Original dialogue, inputs and recorded replies remain in Japanese, with their original wording. Interface translations are presentation, not new experimental observations.

The system prompt has a separate English/Japanese selector. It changes both common instructions and the selected card policies. It does not change the interface language or translate an existing reply. Common instructions ask the model to follow the input language unless a different language is requested. Actual output remains model behavior, not a guaranteed language constraint.

## Choose a combination

- Start with all twelve on, or choose one of eight presets.
- **Only this** selects a single Field. Checkboxes add or remove individual Fields; additions go to the end.
- Arrow buttons reorder the selected Fields. The compiler preserves that order in both plain and structured formats.
- **Clear selection** removes all selected Fields. Plain and structured previews require at least one. Baseline still works because it contains only the common instructions.
- In baseline mode, selections remain available for returning to another format, but the exported active Field list is empty. Adding a Field, choosing a preset or selecting all switches back to structured mode.

The app remembers selection, order, format and prompt language separately from navigation/interface preferences. Changing languages preserves the text being edited; reloading does not preserve trial input or a reply. Local API records are a separate runtime concern.

Preview, copy and download use the exact compiled instructions. A change invalidates the old preview immediately, and stale preview responses cannot overwrite a newer selection. Run requests capture the composition used at dispatch; changing controls during a request does not relabel its result.

## Compiler interface

```python
compile_prompt(
    'custom', 'structured', language='ja',
    field_ids=['ShieldField', 'HeartField'],
)
```

```json
{
  "preset": "custom",
  "mode": "structured",
  "language": "ja",
  "fields": ["ShieldField", "HeartField"]
}
```

This is the preview payload; the server also requires the local session nonce and origin. The run payload adds `input`. An explicit ordered selection overrides a preset. The compiler retains a supplied preset name only when its ordered IDs match; otherwise the result is marked `custom`. Missing `language` means English, including for CLI calls. Use `--language ja` for Japanese instructions. Unknown languages or IDs and duplicate IDs are errors.

Prompt language and order affect the instruction hash. The export and private run record retain the exact instructions, language, ordered active Fields, format and instruction hash. A baseline export has no active Fields even if the interface retains a selection for later use.

## Interpretation limits

English/Japanese cards are maintained as paired semantic interpretations. Matching move counts and schema checks do not establish equivalent model behavior. More Fields can introduce competing tendencies or greater prompt length; all-on is a composition option, not a quality claim. Reordering changes placement without establishing a priority hierarchy. Evaluate languages, combinations and orders as distinct conditions before making effectiveness claims.
