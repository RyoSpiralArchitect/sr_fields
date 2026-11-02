# Three replies to one moment

[Open the public artifact](https://ryospiralarchitect.github.io/sr_fields/) · [日本語で開く](https://ryospiralarchitect.github.io/sr_fields/#lang=ja) · [Download the offline ZIP](https://ryospiralarchitect.github.io/sr_fields/sr-fields-artifact.zip)

The bilingual reader displays each of the 36,864 recorded replies at its original prompt, Field mask and seed. The comparison table uses averages across all matched pairs. The first prompt belongs to the earlier batch. [Complete study](../experimental/english-emotion-pair/observations.md)

In the public projection, `cases`, `seeds` and `fields` specify the axis order. `forms` stores each distinct verbatim English response once. `slots[mask][seed_index * 3 + case_index]` selects the corresponding form. Identical replies remain distinct experimental observations. [Projection receipt](projection-receipt.json)

Build from an ordinary public checkout:

```sh
python3 -I -S scripts/build_public_artifact.py
```

Open `build/public-artifact/index.html`. GitHub Actions verifies every text slot against its published language measurements, packages the HTML, license, notice and receipt in `sr-fields-artifact.zip`, and deploys the dedicated output directory to Pages after the checks on `main` pass. The [published receipt](https://ryospiralarchitect.github.io/sr_fields/receipt.json) identifies the source commit and content hashes.

The maintainer's [projection script](project_replies.py) reads the two original response files after verifying their recorded SHA-256 values. It selects completed reply text and maps it to the experimental coordinates. Raw requests, provider envelopes and private Field sources stay in the local archives.
