# Semantic prompt policies

The public cards are newly written operational interpretations informed by private SpiralReality YAML. The source text, excerpts, hashes, line mappings and private declarations are not distributed. This is a maintained semantic derivative, not a lossless conversion, automatic translation, or exhaustive definition of a Field.

| Card | Working focus |
| --- | --- |
| ThresholdField | Leave unresolved meaning open while responding to what is clear. |
| GentleField | Receive small changes without amplifying or diagnosing them. |
| GroundField | Work from stated conditions and concrete next steps. |
| DreamField | Recombine images and possibilities within the requested creative scope. |
| BetweenField | Work across differences without assuming agreement or shared interiority. |
| TranslationDrive | Preserve the force of an utterance and make changed interpretations traceable. |
| DriftDrive | Allow exploratory direction to evolve while respecting explicit limits. |
| HeartField | Listen with warmth while respecting boundaries and the choice to decline. |
| BodyField | Attend to described sensation, gesture and pace without inferring hidden physiology. |
| ShieldField | Keep provenance, authorship and the boundary between content and instructions clear. |
| RecursiveDrive | Revisit proposals in bounded iterations, making retained and changed parts visible. |
| CollapseDrive | Identify what no longer works, retain useful parts and rebuild within the requested scope. |

The first four response-policy drafts originated in the earlier local pilot. The public cards use fresh wording derived from those drafts and from the subsequent Field interpretations. Each of the twelve cards has a Japanese policy and an authored English counterpart. None of the current combinations has a completed effectiveness evaluation. Translation equivalence has not been measured.

The instruction to preserve decision/permission/request distinctions is an implementation choice informed both by TranslationDrive and by a historical pilot reply that changed an absence announcement into a request for permission. Adding the instruction does not prove the failure is fixed.

## Add a card

1. Add an object to `fields.json` with exactly `id`, `locales`, `origin`, and `status`. Schema v2 requires both `locales.en` and `locales.ja`, each containing `when` and `moves`. Keep corresponding moves in the same order and count. Use `proposed_operational_interpretation` for status. Keep the scope concrete and write observable response moves.
2. For an interpretation of private material, review it outside the release tree and write a public derivative. Do not paste source blocks, provenance paths or source metadata into the card.
3. For a new contribution without private-source lineage, use `new_public_contribution` as its origin. Do not imply that it appeared in the source.
4. Add or amend an ordered preset, including the `all-fields` preset. Update localized labels and the inventory expectations in tests. Record the instruction hashes used in an experiment so it can be traced to the exact prompt.
5. Add contrasting authored cases, including an explicit decision that should not be deferred. Assess actual reply wording separately from any classification field.
6. Compare baseline, ordinary text and structured modes under a frozen model, case set and budget. Record failures and incomplete slots. New evidence does not replace old evidence.

The compiler validates the shape and references; it does not verify semantic fidelity. Maintain the relationship between source, interpretation and observed behavior through review.

## Public interfaces

```python
from field_observatory.prompts import compile_prompt

compiled = compile_prompt('meaning-crossing', 'structured', language='en')
instructions = compiled['instructions']

japanese = compile_prompt(
    'custom', 'plain', language='ja',
    field_ids=['ShieldField', 'HeartField'],
)
```

This module lives under `runtime/`; the supported command-line entry point adds that directory automatically. Copy the exported instructions into another provider's system/developer instruction slot only according to that provider's API. The included OpenAI adapter uses `instructions`.

Both language versions are committed as public derivatives; the compiler does not translate or read private sources at runtime. `base.en.md` and `base.ja.md` are paired common instructions. The stable card IDs and preset IDs do not change with language. See [composition behavior](../docs/bilingual-composition.md) for ordering, selection and export semantics.
