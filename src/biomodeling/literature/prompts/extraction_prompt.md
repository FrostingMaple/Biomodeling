# Extraction Prompt

Use the prepared `chunks.jsonl` as the only source of evidence. Extract the variables and parameters relevant to the paper's research question, normalize their names and symbols, and return one JSON object matching `templates/extraction.schema.json`.

## Inputs

- Paper title and metadata:
- Prepared source inventory:
- Prepared chunks:
- Study focus, if narrowed by the user:

## Task

1. State the research question and its scope. Cite at least one chunk that supports the question.
2. Summarize the organism/system, design, model type, sample scale, and time scale. Use `Not reported` when the supplied text does not say.
3. Identify every analytical variable or parameter that contributes to the question, design, model, measurement, or interpretation. Extra variables outside the core question are allowed only when the source establishes them as variables or parameters; ordinary nouns, verbs, headings, and incidental keywords are not variables.
4. Apply this semantic test to every candidate: What quantity, state, category, treatment, endpoint, parameter, measured value, derived value, or latent construct does this designate in the paper, and which evidence block establishes that meaning?
5. Assign each accepted item a stable `variable_id`, a canonical English name, and a compact symbol.
6. Record the exact author term, aliases, role, type, definition, unit, range, relationship, confidence, notes, and evidence.
7. Add relationships only when the source states or directly supports them. `scaffold` extracts equations only from literal textual equalities; verify each equation and symbol assignment before relying on it.
8. Prefer parameter tables when they exist. DOCX table rows and ruled PDF table rows are preserved as pipe-separated cells, but unruled PDF tables may be collapsed into prose and must be verified against the page.
9. Record ambiguities, symbol collisions, missing definitions, and unresolved contradictions in `unresolved`.
10. Report extraction coverage and warnings in `extraction_metadata`.
11. After semantic review, set `extraction_metadata.review_status` to `reviewed`, provide `reviewer` and `reviewed_at`, and remove scaffold-only warnings. A file that still contains scaffold notes, low-confidence unverified candidates, or an extractor value containing `scaffold` is a draft, not a final extraction.

## Output discipline

- Return JSON only; do not wrap it in a code fence.
- Do not add variables from background knowledge.
- Do not infer a unit from domain convention.
- Do not cite a `block_id` that is not in the prepared chunks.
- Do not use the same symbol for different meanings without explicit notes.
- Do not report “all variables”; report coverage relative to the supplied source.
- Do not mark a scaffold or unreviewed candidate list as `reviewed`.
- A final deliverable must pass `validate --final` and `render --final`.
