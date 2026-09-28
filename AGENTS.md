# Rules library boundaries

- Do not edit immutable released revisions; corrections receive a new revision.
- Do not publish drafts, model output, private reviews, credentials, rosters,
  restricted constitutions, or unlicensed third-party text.
- Public IDs are UUIDs, not GSS RUL/FMT IDs. GSS keeps its mapping private.
- Do not implement a GSS adapter or website adoption before contract approval
  from both owning threads. No backend/Ref/permission/game-pin changes here.
- An LLM response is advisory; it cannot approve a release or game configuration.
- Keep full text and typed mechanics aligned; unsupported is never defaulted.
- Use Python 3.11+ with jsonschema installed.
- Before a public push, inspect every tracked file for unintended private data.
