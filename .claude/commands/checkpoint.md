---
description: Distill the session into the project's living docs, routing each fact by how long it stays true and updating or removing anything invalidated. Bare `/checkpoint` shows the changes and applies them immediately; `/checkpoint review` waits for approval; `/checkpoint migration` folds existing docs into this format.
argument-hint: [review|migration]
disable-model-invocation: true
---

# /checkpoint

> Rename this command and the three filenames below to taste. The logic is what matters, not the names.

## Mode select — read this first

Treat `$ARGUMENTS` as a plain string and check it for a keyword. Do not rely on positional parsing.

| You typed | Mode | Behavior |
|---|---|---|
| `/checkpoint` | **Auto** (default) | Runs steps 1-4, prints the change summary, then **applies immediately**. Does not wait for approval — including for removals. |
| `/checkpoint review` | **Review** | Runs steps 1-4, prints the change summary, then **stops and waits** for `go`. |
| `/checkpoint migration` | **Migration** | One-time consolidation of existing docs. Jump to Migration mode at the bottom; skip everything else. |

Anything else after `/checkpoint` (or nothing at all) defaults to **Auto**.

## Core principle

Documentation is split by **how often a fact changes**, not by when it was written.
A locked architectural decision and "I stopped halfway through wiring the media field"
have completely different lifespans and must not live in the same growing file.

Your job: put each piece of knowledge where it belongs — updating or removing anything
that's been made wrong, rather than appending new text and leaving the old (now-incorrect)
text in place.

## Where things go

| File | Holds | Lifespan | How to write |
|---|---|---|---|
| **CLAUDE.md** | Stack, architecture principles, conventions, hard constraints, project structure | Rarely changes; auto-loaded every session | Edit the relevant section **in place**. Remove what's been invalidated. Keep it lean. |
| **DECISIONS.md** | Dated "chose X over Y because Z" entries with the reasoning | Permanent record | **Append.** A reversal is a NEW dated entry that supersedes the old one; mark the old entry `[SUPERSEDED <date>: see below]` — never delete it. The *why* must survive. |
| **HANDOFF.md** | Current task, where work stopped, immediate next steps, active blockers | Dies next session | **Fully overwrite** every run. No history. Ruthlessly short — this is what `@HANDOFF.md` loads into every session, so length here is a recurring token cost. |

**Overflow rule:** if a durable item is too detailed for CLAUDE.md (e.g. a full module
spec), put it in its own doc (`ARCHITECTURE.md` or `docs/<topic>.md`) and link to it from
CLAUDE.md. CLAUDE.md stays a lean map, not a dumping ground.

## Steps 1-4 — identical in Auto and Review mode

**1. Read before you write.**
Read CLAUDE.md, DECISIONS.md, and HANDOFF.md from disk in full first — whichever exist.
Do not rely on memory of their contents. This must work correctly whether it's run on a
full context right before `/compact` OR in a fresh, already-compacted session. The files on
disk are the source of truth, not the conversation.

**2. Distill this session.**
Pull out only what's genuinely useful for future development. For each item, decide its
lifespan and route it using the table above. When in doubt: "will this still be true and
relevant three sessions from now?"

**3. Reconcile against what's already there — this is the whole point.**
For each item, find where it belongs in the existing docs, then:
- **New info** -> add it to the correct section.
- **Updates existing info** -> edit that section in place.
- **Contradicts / invalidates an existing note** -> the old note must be **rewritten or
  removed**, not left to coexist with the new one. The docs must never contain two claims
  that disagree.
- (DECISIONS.md only: a reversal appends a superseding entry and marks the old one
  superseded, as described above.)

**4. Print the change summary.**
One summary covering all three files. **List removals and rewrites FIRST** — in Auto mode
they are applied without asking, so they are the only thing I might need to catch by eye.

```
CHECKPOINT — [auto: applied] / [review: awaiting `go`]

!! REMOVED / REWRITTEN (existing content changed)
  - CLAUDE.md [section]: <old note>          (invalidated by: <reason>)
  ~ CLAUDE.md [section]: <old> => <new>
  x DECISIONS.md: <old entry> superseded by <new entry>
  (none, if nothing existing was touched)

+ ADDED
  CLAUDE.md    [section]: <one line>
  DECISIONS.md [dated]:   <new entry>

HANDOFF.md — fully replaced (by design)
  <the complete new handoff content, so I can eyeball it>
```

## Step 5 — Apply

**Auto mode (`/checkpoint`):** apply the edits immediately, in the same turn, right after
printing the summary. Do not ask for approval, do not wait — not even for removals. Then
close with the undo line:

```
Inspect: git diff CLAUDE.md DECISIONS.md HANDOFF.md
Undo:    git checkout -- <file>
```

**Review mode (`/checkpoint review`):** stop after the summary and ask:
**"Reply `go` to apply, or tell me what to change."** Write nothing until I reply.

**Both modes:** use the actual current date for DECISIONS.md entries (check the system
date). Create any of the three files if it doesn't exist yet. Keep HANDOFF.md short.

## Do NOT capture

- Anything readable straight from the code or config files.
- Step-by-step narration of how we got somewhere.
- Dead-ends and detours that don't constrain future work.
- Generic framework/library behavior that isn't specific to this project.
- Anything already correctly documented — never duplicate.

## Migration mode — run once via `/checkpoint migration`

A one-time consolidation of a project's existing docs into the structure above. Use it when
adopting `/checkpoint` on a project that grew up under the old single-file `/handoff` (or any
ad-hoc mix of CLAUDE.md / HANDOFF.md / SESSION.md / notes). After it runs, use plain
`/checkpoint` from then on. **Migration always asks before writing — the auto-approve rule
above does not apply here.**

**1. Find the docs — and confirm scope before reading deeply.**
Locate the project's existing documentation / continuity markdown files: things like
CLAUDE.md, HANDOFF.md, SESSION.md, NOTES.md, TODO.md, and any working-notes `.md` under
`docs/` or `.claude/`. **Exclude** project-facing / public files — README.md, CHANGELOG.md,
LICENSE, contributor guides — and anything under vendor / build / dependency folders. List
every file you propose to fold in, flag anything ambiguous (e.g. a README-like doc), and ask
me to confirm the set before going further. Do not dissolve a public doc into agent notes.

**2. Read every in-scope file in full.**

**3. Route every piece into the three tiers, using the rules above.**
- Durable (stack, architecture, conventions, constraints, structure) -> CLAUDE.md.
- Decisions with reasoning -> DECISIONS.md as dated entries. If a source has no date, use a
  date you can recover from git history or the file itself; otherwise label the entry
  `(pre-migration, date unknown)`.
- Transient (current task, where work stopped, next steps, blockers) -> HANDOFF.md, trimmed
  to the present state only.
- Discard anything obvious from the code, step-by-step narration, dead-ends, and duplicates
  — per "Do NOT capture."
- De-duplicate across files: the same fact stated in three docs becomes one entry.
- If CLAUDE.md already exists, reconcile the consolidated content **into it in place**
  (removing anything now contradicted) — don't blindly overwrite it. Same for DECISIONS.md.
  HANDOFF.md is rewritten slim.

**4. Show the complete result and wait.**
Before writing anything, show me: the full proposed contents of CLAUDE.md, DECISIONS.md, and
HANDOFF.md; what is being dropped and from which source file; and which source files end up
redundant. Then ask: **"Reply `go` to write these, or tell me what to change."**
Write nothing until I reply.

**5. Write, then handle the old files — with confirmation.**
After I approve, write the three files. Then list the now-redundant source files and ask how
to handle each: delete, archive (e.g. move to `docs/archive/`), or leave in place.
**Never delete a file without my explicit okay.** From here on, run plain `/checkpoint`.
