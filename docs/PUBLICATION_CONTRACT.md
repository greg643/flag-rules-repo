# Publication contract proposal — 2026-09-28

Status: PROPOSED. GSS acknowledgment is required before consumer integration.
Based on the GSS `RULES_LIBRARY_AUTHORING_2026-09-28.md` design and
`LEAGUE_RULESETS_V1.md`. This does not replace or expand that runtime contract.

## Authority

The public repository is the portable authoring/release library. Publishing there
does not select a League default, pin a fixture, grant permissions, or alter a Game.
GSS League Office remains the authority for adopting a release into GSS.
The website adopts the exact same reviewed library release through a pinned build
input; its presentation, PDF generator, comparison UI and AI provider stay local.

GSS retains its private RUL/FMT identities, derived engine projection, authorization,
CAS checks and immutable Game locks. A private import receipt must bind:

```
public UUID + revision + release_sha256 + document_sha256 + mechanics_sha256
    -> private GSS Ruleset/Format IDs + revisions + hashes + adapter version
```

Do not equate public and GSS revision counters or their aggregate hashes.
Markdown must remain byte-identical across adopted website/app revisions.
Public mechanics are sport semantics; private mappings may differ in representation
but must report every unsupported path and exception. Reject unsupported required
mechanics rather than silently substituting defaults. No engine compatibility
claim is made by this library validator.

## Release directory

`rulesets/<lowercase-uuid>/revisions/<positive-integer>/` contains exactly:

- `rules.md`: full LF UTF-8 text, one H1, stable `<!-- rule.* -->` section anchors;
  no Astro layout/frontmatter. Consumers render with raw HTML disabled and safe links.
- `mechanics.json`: schema-versioned, closed vocabulary; no executable logic,
  consumer button behavior, measured field/camera data or arbitrary expressions.
- `manifest.json`: identity, edition/effective date, provenance, parent pin and hashes.
- `validation.json`: public field-to-section evidence and explicit limitations.
  Private prompts, model output, editor identities and approvals are excluded.
- `examples.json`: reviewed situation/expected-result pairs with supporting sections.

The same UUID persists through editions. Aliases may change; identity may not.
Variants get a new UUID and exact parent pin but include fully resolved text and
mechanics. A consumer never reconstructs a variant from a mutable parent.

## Canonical bytes

Markdown must already be LF-normalized UTF-8, end with LF and have no NUL. Import
normalization happens privately; verification never silently rewrites released bytes.
`document_sha256` hashes those exact bytes. JSON hashes use UTF-8, Unicode code-point
sorted keys, no whitespace, unescaped Unicode, scalar integers (no floats), and
no trailing newline. Duplicate keys, unsafe integers and invalid Unicode fail.

Manifest `files` pins hashes for rules.md, mechanics.json, validation.json and
examples.json. `schema_sha256` pins the canonical schema bundle. `release_sha256`
hashes canonical manifest JSON with only `release_sha256` omitted. This binds
identity, content, provenance, effective date, examples and schema together. It
is deliberately NOT GSS's `ruleset_sha256`.

Checksums detect drift; they do not establish publisher identity. Consumers must
also pin a trusted repository and reviewed commit/release receipt.

## Approval and CI

Private Haiku/OpenRouter generation proposes mechanics with exact source quotes.
A separate semantic verification pass reviews omissions, contradictions and
exception precedence. Deterministic schemas, hashes and source references are
checked locally. Model agreement is not approval; unresolved issues block release.

Human review approves complete text, mechanics, examples and redistribution rights.
Public CI only performs deterministic checks: no OpenRouter secret, model call,
GSS credentials or write permissions in fork/PR jobs. Release workflow/branch
protection must compare against the trusted base and reject modifications/deletions
to existing revision directories. Current scaffold does NOT implement release
approval or a trusted publishing job and must not be presented as ready to publish.

## Migration and open decisions

1. Agree this envelope, public mechanics vocabulary and private receipt with GSS.
2. Approve GPFF's full October 3 text; the league selected a 30-second play clock and the
   pregame-announced schedule-driven running-clock option. Preserve the current website snapshot
   separately, without claiming it proves Week 1's actual or pinned rules.
3. Have GSS map the sport mechanics to its current ref-controlled projection,
   including warnings, delayed rush and mercy-specific four downs/no blitz.
4. Prove website, PDF source, website Q&A, app display and app Q&A use the same
   document hash for that selected revision. Do not require identical AI providers.
5. Explicitly adopt for eligible future fixtures; historical Game locks remain untouched.

The newer GSS ref-controlled seed is a summary, while the legacy seed has obsolete
rules. Neither should silently replace the complete website rulebook.

## Questions for the GSS owner

- Accept independent public UUIDs and hashes, mapped through private import receipts?
- Accept the proposed public mechanics schema as an import boundary, not a runtime wire change?
- Who owns the private adapter and parity/unsupported-mechanic report?
- Will website adoption use the reviewed library pin plus GSS receipt, or the existing
  public publication endpoint? Either way, require exact document equality.
- Confirm no season/fixture changes until an authorized adoption step, and no historical backfill.
