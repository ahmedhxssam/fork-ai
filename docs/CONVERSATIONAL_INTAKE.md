# Conversational scenario intake

The main FORK input is now an ordinary problem description. It does not require the user to know the workflow schema or the retained compiler's line syntax. The installed application remains deterministic and local; no API key, provider calls or generated-code execution is involved.

## What the user does

1. Describe what is happening, or start with an incomplete, contradictory or separate-operation example.
2. Read what FORK has understood. Answer one focused question at a time, using a short phrase or a choice.
3. Resolve conflicting claims explicitly. Both source claims are shown; the last number is not silently selected.
4. Review the plain-language plan, the facts behind it, and its accepted limits.
5. Run the same verified three-future simulation, add resource outages, inspect independent evidence and approve a current result for export.

For example, a repair description can establish that two volunteers are present while leaving the queue size, job duration and time window unknown. FORK asks for those facts. Replies such as “Six bikes”, “About 45 minutes each” and “We have two hours” become six actual 45-minute tasks, capacity two, and a 120-minute horizon. In that model four repairs complete. Changing available capacity to three permits all six to complete. These are computations under the declared abstraction, not inferred real-world forecasts.

## Missing and conflicting details

Required modeling facts are available capacity, work quantity, processing time and planning window. Explicit deadlines, multiple work groups, pool assignment and ordering can add focused questions. Supported number words and short phrases are accepted; ambiguous or unsupported expressions lead to clarification rather than a guessed value.

Conflict examples include different available staff counts, different durations for the same work, and incompatible planning windows. The interface quotes the claims and offers choices or a fresh answer. An uncertainty such as “we might have three volunteers” is not confirmed availability. Required staff and unavailable staff do not become actual capacity merely because a number appears nearby.

Unknown operative clauses remain visible at a scope decision. The deterministic interview supports a simplified resource/task abstraction. It can ask the user to agree to a narrower model, rather than claiming that travel, physical safety, clinical judgment, materials, budgets, individual availability or arbitrary behavior were represented. A rejected scope remains unready. Important unknown constraints must not disappear just because another part of the sentence was parsed.

## Scope of the conversational model

The current interview creates checkpointable jobs, each using one unit from one explicitly selected resource pool. Work starts available at minute zero, groups are equally important, unspecified deadlines mean the end of the planning window, and costs/materials are outside the agreed simplified scope. Explicit group ordering means every job in the earlier group finishes before the later group begins; it is not a per-item pipeline. These assumptions are reviewed before simulation.

The underlying typed workflow engine still supports richer budgets, materials, units, priorities and events through its existing validated model contract. The conversational parser does not imply that it can infer every one of those semantics from arbitrary language. Advanced JSON and source traces remain optional inspectors. Natural-language authoring is a bounded deterministic interview, not an unrestricted language model.

## Edits and recovery

Editing the original issue clears dependent answers and model readiness. Editing an earlier answer clears later answers for reconfirmation. Old results become stale and approval/export is paused until a current model is run. The model review checkbox is distinct from approving a selected future.

The current draft and answer history use a separate versioned browser key, preserving earlier structured drafts. An unfinished interview can be restored by replaying its answers. New scenario starts an empty issue and preserves saved experiments. Failed answers stay editable; failed network operations preserve the draft. Outdated request responses and retries cannot replace newer text. Saved server revisions must be reconciled before approval after uncertain writes.

Earlier code-authored experiments retain their original source in storage/export. Their normal UI displays a readable generated summary and an earlier-format marker. They remain reviewable, but changing their plan starts a new conversation. A parser-produced model whose fingerprint differs from the originally saved authoring model is not treated as current evidence.

## Provenance and API gates

- `GET /api/studio/prompts` returns human prose examples and deterministic/provider-disabled flags.
- `POST /api/studio/intake` takes the original brief and an ordered answer history. It returns one next question or a reviewable validated model, accepted answer prefix, source-backed known facts, explicit assumptions and canonical hashes.
- Question IDs bind the brief and preceding accepted answers. Old IDs cannot apply to a different issue or field. Invalid answers do not mutate the accepted model state.
- Conversational launch includes authoring metadata. The API independently replays the complete interview and requires readiness and exact model/brief fingerprints before computation.
- Stored authoring remains separate from subsequently applied outage schedules. Approval/export replays that source again, then checks the current model/evidence/revision. Changed or malformed provenance fails closed with a useful conflict response.

The legacy `/compile`, `/templates` and direct reviewed-model API remain available for compatibility and engine-level work. They are not the default user authoring experience.

## Future AI adapter

A later OpenAI adapter can improve phrase interpretation and question selection, using the same typed inputs and clarification/provenance contract. It must preserve missing-fact handling, model review, bounded schema validation, deterministic simulation and independent evidence. It cannot create authoritative metrics, hide assumptions or approve itself. API-key setup remains explicitly deferred.

## Evidence

Behavioral coverage and independent checks are recorded in `CONVERSATION_ENGINE_REPORT.md`, `CONVERSATION_ACCEPTANCE.md`, `CONVERSATION_UI_REPORT.md`, `CONVERSATION_FINAL_REVIEW.md` and the final integration release note. Reports distinguish their exact snapshots from later changes. No universal understanding, global scheduling optimality, real-world data validation, formal accessibility conformance, publication or competition submission is established by these local tests.
