# Public snapshot procedure

1. Confirm the intended repository name, license and public content. Review all tracked files and `git diff --cached --check`.
2. Run offline tests, signal reproduction, JavaScript composition tests and syntax checks and `audit_public.py`.
3. Start the app with API execution disabled. Test tab navigation, example bridges, dialogue stages, historical missing data, independent interface/prompt language switches, all/single/custom selections, ordering, empty selection, persistence, prompt modes, download and responsive layout. Validate live dispatch separately with a bounded synthetic input only when intended.
4. Stage only reviewed files. Export with `package_release.py`; inspect the archive and receipt. Do not add local `.runs/`, private provenance or screenshots containing private material.
5. Create or push a public remote only with explicit authorization for that destination. Repository preparation and local tests are separate from publication.
6. After publishing, verify remote URL, visibility, exact commit, license recognition and CI result. Identify the published tree by its Git commit.

The snapshot uses the stable filename `sr_fields.zip`. Git commits identify code changes and SHA-256 identifies each compiled prompt. The project does not use numbered application releases.
