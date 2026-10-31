# grill-me-codex

**Two AI models harden your plan before you write a line of code.** A family of Claude Code skills that close the two gaps in AI-assisted coding: the gap between *you and Claude* (do we agree on what to build?) and the gap between *Claude and the quality of what it produces* (is the plan actually correct — and how would you even know?).

Act 1 grills **you** to lock the plan. Act 2 hands that plan to **OpenAI Codex** — a rival, cross-provider model — which adversarially tears it apart over several rounds until both models sign off. Only then does code get written.

> Why a second model? Because the same model that plans the build and writes the build can't be trusted to *grade its own work* — it's an echo chamber. A different provider catches what Claude structurally can't see in itself.

Built on [Matt Pocock's `grill-me` / `grill-with-docs`](https://github.com/mattpocock/skills) skills (MIT) — Act 1 is his work; the iterative cross-model Codex review (Act 2) is the addition.

> ### 🚀 Want to go deeper?
> This skill is one piece of the full system. Get the **Claude Code Masterclass** and join builders going further with agentic AI inside **[Chase AI+](https://www.skool.com/chase-ai/about)**.

## The skills

| Skill | Act 1 | Act 2 | Use when |
|-------|-------|-------|----------|
| **`grill-me-codex`** | Claude interrogates you one question at a time until the decision tree is resolved | Codex adversarial review loop | Planning from scratch + want alignment AND a second-model check |
| **`grill-with-docs-codex`** | Same, but challenges your plan against your project's `CONTEXT.md` glossary + writes ADRs inline | Codex review loop | Same, in a project with established terminology / architecture decisions |
| **`codex-review`** | — (you already have a plan) | Codex review loop | You have a plan and just want the cross-model stress-test |

## How Act 2 works

1. Claude writes the locked plan to `PLAN.md` and starts a log at `PLAN-REVIEW-LOG.md`.
2. **Round 1:** Codex reviews the plan in a **read-only sandbox** and returns `VERDICT: APPROVED` or `VERDICT: REVISE`.
3. **Rounds 2..N:** Claude revises; the *same* Codex session is resumed so it remembers its prior critiques and only checks whether they're addressed.
4. Bounded by `MAX_ROUNDS` (default 5). Terminates on `APPROVED` or the cap (a flagged deadlock beats a fake "approved").
5. **You gate twice only:** kickoff, and final sign-off before any code. Codex is read-only every round and never writes a file.

Two artifacts: `PLAN.md` (the clean final plan — the *what*) and `PLAN-REVIEW-LOG.md` (the full round-by-round argument — the *why*).

## Install

Copy the skill folders into your Claude Code skills directory:

```bash
# macOS / Linux
cp -r skills/* ~/.claude/skills/

# Windows (PowerShell)
Copy-Item -Recurse skills\* $env:USERPROFILE\.claude\skills\
```

Then invoke in Claude Code: `/grill-me-codex`, `/grill-with-docs-codex`, or `/codex-review`.

## Prerequisites

- **Codex CLI ≥ 0.130** — `npm install -g @openai/codex@latest` (older versions error on the default `gpt-5.5` model).
- **Authenticated Codex** — run `codex login` once (a ChatGPT account works; Free/Plus/Pro/Max all fine).
- **Don't pin a model** — ChatGPT-account auth rejects `gpt-5.x-codex` model variants; the skills use your config default.

## Tunables

| Var | Default | Meaning |
|-----|---------|---------|
| `MAX_ROUNDS` | `5` | Hard cap on review rounds |
| `PLAN_FILE` | `PLAN.md` | Where the plan lives |
| `LOG_FILE` | `PLAN-REVIEW-LOG.md` | The argument transcript |

Pass e.g. `rounds=3` when invoking to override.

## Safety

Codex runs **read-only every round** — `-s read-only` on the first call, `-c sandbox_mode="read-only"` on every resume (the `resume` subcommand doesn't accept `-s`, and without forcing read-only it would inherit your `config.toml` sandbox default, which may be `danger-full-access`). The skills handle this for you. No code is ever written until you approve the final plan.

## Credits

- Act 1 (`grill-me`, `grill-with-docs`) © Matt Pocock — https://github.com/mattpocock/skills (MIT). See each skill's `THIRD-PARTY-NOTICES.md`.
- Act 2 (iterative Codex review) and packaging by [Chase AI](https://youtube.com/@chaseai). Go deeper in [Chase AI+](https://www.skool.com/chase-ai/about) (Claude Code Masterclass).

## License

MIT — see [LICENSE](./LICENSE).
