---
name: azf-html-ui-loop
description: >-
  Generate and compare multiple HTML/CSS visual alternatives without freezing
  an aesthetic direction: isolate each variant, render real desktop and mobile
  screenshots with independent Playwright, produce a comparison gallery, and
  apply only the user's selected variant. Use for landing pages, dashboards,
  frontend prototypes, visual polish, responsive UI, animations, and requests
  to generate many designs for selection.
---

# AZF HTML UI Loop

Use this Skill for visual frontend work when the user wants several possible
designs, a polished HTML/CSS page, responsive screenshots, or a visual choice
before changing the canonical version. Delegate routing, model selection,
approval, telemetry, and bounded rework to `azf-auto-dev-loop`; this Skill owns
the visual-variant and browser-evidence workflow.

## Core rule: explore before applying

Do not create or freeze a visual design contract. The user may want many
different visual directions before choosing one. Keep only the functional
constraints that must survive every candidate:

```yaml
target_page:
target_route:
functional_requirements:
must_keep:
must_not_break:
target_viewports:
reference_images:
variant_count:
```

Keep palette, typography, layout, animation, background, card style, and
composition open for exploration unless the user explicitly restricts one.

## Default routing

Use the fixed shared intensity baseline:

```yaml
sol_planner: high
luna_executor: medium
terra_executor: high
sol_executor: high
terra_evaluator: high
sol_evaluator: high
```

Route by task:

| Situation | Route |
|---|---|
| Small change using existing components | Luna Executor → Playwright → Terra Evaluator |
| One ordinary polished page | Terra Executor → Playwright → Terra Evaluator |
| Many visual alternatives | Terra Executor → isolated variants → Terra Evaluator |
| Important or ambiguous page | Sol Planner → Terra Executor → Sol Evaluator |
| Risky frontend architecture | Sol Planner → Sol Executor → Sol Evaluator |

Do not invoke Sol Planner for a clear, repetitive visual batch unless the user
explicitly requests `planner_mode=always` or the shared router marks the task
ambiguous or high-risk.

## Variant workflow

1. Read repository instructions, current Git status, existing design system,
   target route, and the user's functional requirements.
2. Confirm the baseline and protect pre-existing changes. Never overwrite the
   canonical page while generating candidates.
3. Choose `variant_count`: default 4, ordinary batch 8, and up to 20 when the
   user explicitly asks for broad exploration. For more than 8, generate in
   batches so the user can narrow the direction.
4. Create an isolated directory or temporary worktree for every variant. Do
   not run two write-capable agents against the same worktree.
5. Ask the Executor to make each candidate visibly different. Vary layout,
   hierarchy, color, typography, background, cards, motion, and interaction,
   while preserving the functional constraints.
6. Run the bundled capture script with independent Playwright. Do not use the
   Codex in-app browser for local HTML QA on this machine.
7. Capture at least 1440×900 and 390×844 for every candidate. Record console
   errors, failed resources, overflow, and basic accessibility results.
8. Run an independent read-only Evaluator against the screenshots and the
   functional checks. The Evaluator may recommend candidates but cannot choose
   the user's aesthetic preference for them.
9. Generate a gallery and contact sheets. Keep all candidate files and evidence
   under the run evidence directory, outside the canonical worktree.
10. Wait for the user to select a variant. Only then apply the selected diff to
    the canonical worktree and rerun functional and responsive checks.

To apply a selected isolated copy, use `scripts/azf-ui-apply.ps1 -ConfirmSelection`.
It refuses to overwrite files that already have pre-existing Git changes and
never stages, commits, or pushes.

## Evidence files

The batch controller should produce:

```text
<run-evidence>/ui/
  variants/v01/...
  variants/v02/...
  desktop-contact-sheet.png
  mobile-contact-sheet.png
  gallery.html
  variant-manifest.json
  ui-evaluation.json
```

The manifest is a reproducibility record, not a frozen design contract:

```yaml
variant_id:
source_baseline:
generation_prompt:
changed_files:
viewport_screenshots:
functional_checks:
generated_at:
```

## Evaluator checklist

Inspect the real rendered screenshots and report each candidate's:

- functional integrity and route availability;
- desktop/mobile responsive behavior;
- first-screen hierarchy and readability;
- visual distinctiveness and polish;
- spacing, contrast, overflow, clipping, and overlap;
- hover/focus and basic interaction behavior;
- console errors, failed resources, and accessibility findings;
- strengths, weaknesses, and suitable use case.

Do not mark a candidate PASS only because its HTML/CSS looks plausible. Do not
claim visual success without a real screenshot or an explicit blocked reason.

## Reuse existing capabilities selectively

- Use `extract-design-system` only when a reference website is supplied.
- Use `apple-design` only when Apple-style interaction or visual principles are
  requested.
- Use `gsap-*` only when the requested animation needs those capabilities.
- Use `azf-deepsight` only when native screenshot reading fails.
- Prefer independent Playwright for local rendering and screenshots.

## Human selection and external Harnesses

Native Codex execution may generate isolated candidates when the user asks for
it. Applying a selected candidate to the canonical worktree is a separate
approval boundary.

If routing selects Claude Code or another external Harness, stop after a route
proposal. Include the requested and resolved model, effort, permissions,
variant count, estimated cost, repository baseline, and maximum rework rounds.
Start the external Harness only after the user explicitly confirms the exact
proposal. Model changes, extra permissions, dependency installation, network,
Git writes, or canonical replacement require renewed confirmation.

## Final report

Report:

- run status and task profile;
- variant count and candidate directories;
- screenshots and gallery path;
- functional and responsive test commands/results;
- Evaluator comparison and unresolved issues;
- selected variant, if the user has selected one;
- requested/resolved models, effort, Harness, cache telemetry, and cost;
- whether the canonical worktree was changed;
- explicit statement that no commit or push was performed.
