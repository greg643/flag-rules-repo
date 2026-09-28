# Flag rules library

Portable flag-football rulebooks, independent of any league-management app.

**Status: contract proposal and validation tooling. No approved rules revisions yet.**
Do not use this repository's development branch as a game-time rules source.

Each release contains the full Markdown rulebook, typed mechanics, permanent
UUID identity, integer revision, provenance, section-level evidence and examples.
Consumers pin an immutable revision and release hash. A slug is discovery only.

See [the publication contract](docs/PUBLICATION_CONTRACT.md).

## Layout

```
schemas/1/                  proposed JSON schemas (generated from library.py)
rulesets/<uuid>/revisions/N/ approved releases only
catalog.json                generated discovery index; not a game pin
library.py                  offline deterministic packaging/verification
tests/                      synthetic test fixtures; no family or player data
```

Private drafting, prompts, model output, credentials and editorial approvals live
outside this repository. Only approved public material may enter `rulesets/`.
Do not copy restricted third-party rulebooks or constitutions here.

## Local checks

Requires Python 3.11+ and `jsonschema`.

```
python library.py schemas
python -m unittest discover -s tests -v
python library.py check-all
```

`python library.py check PATH` validates a candidate directory. It does not approve,
publish, import into GSS, or change any game. Schema validity is not proof that
the mechanics correctly interpret the prose. Human review remains required.

No reuse license has been selected yet. Public availability does not imply a
license for third-party source material.

## Website consumption

Consumers should fetch an approved revision at a pinned Git commit during their
build, verify its manifest and hashes, and retain that validated artifact locally.
The website, PDF generator and rules assistant should use the same document bytes.
Do not fetch a moving `main` branch at request time or silently fall back to a
different rules revision. No website integration is enabled by this repository.
