---
name: grill-me-codex
description: Two-act plan hardening. ACT 1 (you ↔ Claude) — Claude interviews you relentlessly about a plan or design, one question at a time, recommending an answer for each and exploring the codebase when it can answer itself, until every branch of the decision tree is resolved. ACT 2 (Claude ↔ Codex) — Claude writes the locked plan to PLAN.md and OpenAI Codex adversarially reviews it in a read-only sandbox (VERDICT:APPROVED/REVISE), Claude revises and re-submits to the SAME Codex session until APPROVED or a MAX_ROUNDS cap, then you sign off before any code. Use when the user says "/grill-me-codex", "grill me then have codex review", "grill me and stress-test the plan", "interview me about this plan then get a second model on it", or is about to build something high-stakes (auth, schema, concurrency, migrations, payments) and wants both alignment AND a cross-model sanity check before implementation. Builds on Matt Pocock's grill-me (MIT). For the docs-aware variant use /grill-with-docs-codex; if you already have a plan and want only the Codex review use /codex-review. NOT for reviewing already-written code (use /codex:review) and NOT for trivial changes.
---

# Grill-Me-Codex — Get Grilled, Then Get Reviewed

Two acts, two different jobs:

- **Act 1 fixes the #1 failure mode: building the wrong thing.** Claude interrogates *you* until intent is locked — no guessing at ambiguity. (This act is Matt Pocock's `grill-me`, used under MIT — see `THIRD-PARTY-NOTICES.md`.)
- **Act 2 fixes the #2 failure mode: a plan that sounds right but breaks.** A *different model* (Codex) adversarially attacks the locked plan. Cross-model = no echo chamber.

You enter at two points only: answering the grill, and signing off the converged plan. Codex is read-only the whole time and never touches a file.

## Progress and status tracking

Report phase changes in chat and append the same status events to `PLAN-REVIEW-LOG.md`, without credentials or other secrets:

- `GRILL: RUNNING` → `GRILL: COMPLETE`
- `PLAN: DRAFTING` → `PLAN: READY`
- `CODEX_CLI: CHECKING` → `CODEX_CLI: READY (version)` or `CODEX_CLI: BLOCKED (reason)`
- `CODEX_REVIEW: NOT_STARTED` → `CODEX_REVIEW: RUNNING (round n/MAX_ROUNDS)` → `APPROVED`, `NEEDS_REVISION`, or `BLOCKED`

Log each round's start and terminal result. A review round is valid only when the command succeeds, round 1 emits a `thread.started` event, the verdict file is present and non-empty, and its last non-empty line is exactly `VERDICT: APPROVED` or `VERDICT: REVISE`. Keep errors visible. On a failed command, missing output, or malformed verdict, mark the review `BLOCKED`, report the observed error, and stop without silently retrying or treating the failure as a verdict. The CLI preflight checks installation/version; the first read-only call is the actual authentication and service-path check, not a separate endpoint probe.

---

## ACT 1 — GRILL (you ↔ Claude)

Start by reporting/logging `GRILL: RUNNING`. Once the interview is resolved, report/log `GRILL: COMPLETE` and `PLAN: DRAFTING` while writing the agreed plan. When it is ready, report/log `PLAN: READY`, then begin the Codex CLI preflight.

> Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.
>
> Ask the questions one at a time, waiting for my answer before continuing.
>
> If a question can be answered by exploring the codebase, explore the codebase instead.

When the decision tree is resolved and we're aligned, **write the agreed plan to `PLAN.md`** in this structure, then move to Act 2:

```markdown
# Plan: <task>
_Locked via grill — by Claude + <user>_

## Goal
<one paragraph — reflects what the grilling actually settled>

## Approach
<numbered, concrete steps>

## Key decisions & tradeoffs
<the contestable choices the grill resolved — name them so Codex has something to bite>

## Risks / open questions
<anything still genuinely open>

## Out of scope
<bounds the grill established>
```

Initialize `PLAN-REVIEW-LOG.md`:
```markdown
# Plan Review Log: <task>
Act 1 (grill) complete — plan locked with the user. MAX_ROUNDS=<n>.
```

---

Report/log `CODEX_CLI: CHECKING` before running the version check. Require a parseable `codex --version` result ≥ 0.130; if the executable is missing, the command fails, or the version cannot be parsed or is too old, report/log `CODEX_CLI: BLOCKED` and stop before starting Act 2. Report/log `CODEX_CLI: READY (version)` only after it passes.

## ACT 2 — REVIEW (Claude ↔ Codex)

Now hand the locked plan to Codex for adversarial review. Same engine, mechanics verified end-to-end (2026-06-04).

### Prerequisites (verify once, fast)
- `codex --version` must be parseable and ≥ 0.130 (older CLIs error on the default `gpt-5.5` model). A missing executable, failed command, unparseable version, or older version blocks Act 2.
- Codex authenticated (prior `codex login`; ChatGPT account is fine). There is no separate API health endpoint; the first read-only call checks the configured authentication and service path. On auth, network, or model error, surface it — don't silently retry.
- Do NOT pin `-m`. Use the config default. Pinning `gpt-5.x-codex` variants 400s on ChatGPT-account auth.

### Tunables (read from args, else default)
| Var | Default | Meaning |
|-----|---------|---------|
| `MAX_ROUNDS` | `5` | Hard cap on review rounds. The loop ALWAYS terminates here. |
| `PLAN_FILE` | `PLAN.md` | The plan Act 1 produced. |
| `LOG_FILE` | `PLAN-REVIEW-LOG.md` | Append-only argument transcript. The artifact. |

If invoked with e.g. `rounds=3`, use that for `MAX_ROUNDS`. Echo resolved values before starting.

### The review prompt (sent each round)
> You are an adversarial reviewer for an implementation plan. Be skeptical and specific — your job is to find what breaks, not to be agreeable. Read the plan at `PLAN.md` and any repo files you need (you are read-only). Identify concrete flaws: security holes, race conditions, missing edge cases, schema conflicts, wrong assumptions, observability gaps, simpler alternatives. For each, give a one-line fix. Do NOT modify any files. End your reply with EXACTLY one line: `VERDICT: APPROVED` if the plan is sound enough to implement, or `VERDICT: REVISE` if it still has material problems.

### Round 1 — fresh session (capture `thread_id`)
```bash
set -o pipefail
codex exec -s read-only --json -o /tmp/codex-verdict.txt "$(cat REVIEW_PROMPT)" \
  | grep '"type":"thread.started"'
```
Parse `thread_id` from the `{"type":"thread.started","thread_id":"..."}` line → that's `THREAD_ID`. The critique is in `/tmp/codex-verdict.txt`. Confirm success by the verdict file + a `thread.started` line; if neither appears, the run failed (auth/model) — stop and tell the user. `2>/dev/null` suppresses cosmetic MCP/auth stderr noise.

The command examples leave stderr visible; do not add `2>/dev/null` or other output suppression. Validate the command exit status, non-empty verdict file, and exact final verdict line on every round. A failed or malformed response is `BLOCKED`, not a verdict.

### Rounds 2..MAX — resume the SAME session (Codex remembers its prior critiques)
```bash
# resume REJECTS -s. Force read-only via -c sandbox_mode, or Codex inherits
# config.toml (possibly danger-full-access) and could WRITE files. This is the
# single most important safety line in the skill — verified 2026-06-04.
codex exec resume "$THREAD_ID" -c sandbox_mode="read-only" --json \
  -o /tmp/codex-verdict.txt \
  "I revised the plan. Re-review PLAN.md — check whether your prior findings are addressed and flag anything new. End with VERDICT: APPROVED or VERDICT: REVISE."
```
Both `codex exec` and `codex exec resume` support `--json` and `-o/--output-last-message`.
Keep stderr visible and check the command's exit status, non-empty verdict file, and exact final verdict line on every round. Report/log `CODEX_REVIEW: RUNNING (round n/MAX_ROUNDS)` before each call, then its validated `APPROVED`, `NEEDS_REVISION`, or `BLOCKED` result. A failed or malformed response is `BLOCKED`, not `REVISE`.

### Each round, after Codex returns
1. Read `/tmp/codex-verdict.txt`; append to `LOG_FILE`: `## Round <n> — Codex` + the full critique.
2. Verify the command succeeded, the verdict file is non-empty, and the last non-empty line is exactly an allowed verdict:
   - `VERDICT: APPROVED` → break to Resolution (converged).
   - `VERDICT: REVISE` → Claude decides **what's actually worth acting on** (Claude is final arbiter — Codex advises, doesn't command). Revise `PLAN_FILE`. Append `### Claude's response` to `LOG_FILE`: what changed, what was rejected, why. Increment round.
3. If round > `MAX_ROUNDS` → break to Resolution (deadlock).

### Resolution (you sign off — final gate)
- **APPROVED:** present the final `PLAN_FILE`, a 3-bullet summary of what the two acts improved, and the round count. Ask: *"Grilled + survived N rounds of Codex. Implement it now?"* Code only on yes. **No code is written during either act.**
- **MAX_ROUNDS hit without APPROVED (deadlock):** do NOT fake convergence. List each unresolved point + Claude's counter-position; hand it to the user to break the tie. A flagged disagreement beats a false "approved."

---

## Hard rules
- Act 1 always precedes Act 2 — don't write `PLAN.md` until the grill has actually resolved the decision tree with the user.
- Codex is read-only EVERY round — `-s read-only` first call, `-c sandbox_mode="read-only"` on every resume (resume has no `-s`). It never writes.
- The loop ALWAYS terminates at `MAX_ROUNDS`.
- Claude is final arbiter on every REVISE — incorporate good critiques, reject bad ones *with a logged reason*. Don't cave to everything (defeats the cross-model check) and don't ignore it (defeats the point).
- Code only after the user's final sign-off.
- `LOG_FILE` is the deliverable — keep the whole argument.

## What NOT to do
- Don't review already-written code — that's `/codex:review`.
- Don't pin a `-codex` model variant on ChatGPT-account auth — it 400s.
- Don't let Codex edit files. Read-only, always.
- Don't skip Act 1 — the grill is half the value.
