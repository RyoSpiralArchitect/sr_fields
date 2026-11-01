# Public example projection

The files here are a field-selected export of verified local experiments. Original private receipts were verified before projection. `manifest.json` binds the public JSON files. It establishes integrity of this release's projection, not independent access to the omitted private source record.

| File | Contents | Evidence limits |
| --- | --- | --- |
| `signals.json` | Five original first-seed traces, 384 steps each | Display samples, not all 640 traces or 15,360 historical metric rows |
| `signal-protocol.json` | Numerical generator, seed, observation and threshold parameters | Public numerical reproduction; no private source provenance |
| `dialogue.json` | 12 authored cases, three stages, three conditions, 108 decisions and replies | Scripted replay, not an adaptive live conversation; model identity and sampling details unavailable |
| `api-pilot.json` | Six authored inputs, three conditions, 17 completed replies, one missing slot | Old source-bearing prompt version; exact prompt replay unavailable |
| `bridges.json` | Three curated correspondences across views | Interpretive navigation links, not shared measurement or a causal result |

Dialogue conditions were forced A/B, optional A/B/U, and fixed U at stage one followed by A/B. All conditions correctly classified the nine resolved final cases. The optional condition followed the author's unresolved references, while mandatory classification could produce provisional A/B labels alongside uncertain prose. Human usefulness has not been rated; no independent gold annotation is provided.

The API pilot used `gpt-5.4-mini-2026-03-17`, reasoning `none`, max output 600, one attempt per case/condition, omitted temperature and seed. An initial run completed three requests and stopped when its fourth attempt disconnected. A separately documented post-protocol continuation sent all 14 previously unattempted slots; the failed slot was not retried. The missing baseline for the absence-announcement case remains absent. Known returned usage was 18,877 tokens; delivery and usage for the disconnected request are unknown.

The old structured condition changed source quotations, naming, structure and length together. It cannot isolate a Field name or serialization effect, and its replies are not evidence about the public prompt policies.

Excluded from this projection: private YAML, exact source-bearing API requests, private receipt paths, provider response IDs, session IDs, local host paths, credential material, and the collaborator's ongoing practice log. Authored case wording and actual reply wording are retained. Never silently edit a historical reply to match a preferred interpretation.
