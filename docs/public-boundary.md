# Public and private boundary

The release includes the app, runtime, semantic response-policy derivatives, selected authored example records, tests and documentation. It includes no original or corrected private Field YAML, excerpts, private source declarations, local provenance map, raw provider request archive or personal practice log.

Private-to-public derivation is a maintainer review process outside this tree:

1. Read relevant passages and preserve their unresolved meanings.
2. Write a bounded public response policy in fresh wording.
3. Keep the source-to-interpretation mapping privately, outside this repository.
4. Review public cards and examples for accidental disclosure, including fixtures and generated archives.
5. Record the instruction hash and label untested assumptions.

The runtime never needs private sources. Git ignores `.env*`, `.runs/`, `.private/`, caches and distribution outputs. Ignore rules alone do not remove already-tracked files; the audit inspects the complete tracked tree.

The package exporter includes only tracked regular files and produces a new hash receipt. Repository preparation does not itself publish to a remote host. Review the exact export and its contents before any remote publication.

Licensing applies to the distributed material. Private source material remains outside this release and cannot be reconstructed or requested as a prerequisite for operating the public app.
