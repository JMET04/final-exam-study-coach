# Token Cost Report

## Measurement Notes

Codex exposes token usage at the active goal level, not per file or per generated artifact. Therefore:

- Goal-level totals below are directly observed from Codex goal accounting.
- Per-artifact and per-feature numbers are transparent estimates based on goal boundaries, intermediate goal snapshots, and the amount of generated/edited content.
- Exact token cost for each individual HTML animation is not available.

## Observed Goal-Level Usage

| Work item | Observed tokens | Observed time | Evidence |
| --- | ---: | ---: | --- |
| Soil mechanics principle animation goal | 327,000 | about 10 min 13 sec | Codex goal completion counter after finishing the animation and skill-rule update |
| Final packaging/GitHub publishing goal, latest packaging snapshot | 227,634 | about 12 min 3 sec | Codex active goal counter while building the GitHub release package and upload-ready artifacts |

## Animation-Specific Estimate

The soil mechanics animation work included:

- Reviewing existing animation support in the skill.
- Reusing existing animations for effective stress, Darcy seepage, and Mohr-Coulomb strength.
- Creating a new interactive animation for three-phase soil composition and index conversion.
- Creating a soil mechanics animation entry page.
- Creating an animation guide with review checks.
- Updating the skill so concrete STEM-like principles can use animations, while humanities courses do not force animation.
- Validating the source and installed skill.

Observed counter before the final animation implementation pass was 217,046 tokens; final completion was 327,000 tokens. That makes the last implementation and validation pass about 109,954 tokens.

Estimated animation-related usage:

| Scope | Estimate | Confidence |
| --- | ---: | --- |
| Whole soil mechanics animation feature, including planning, rule updates, file creation, sync, and validation | up to 327,000 tokens | High as an upper bound |
| Final implementation pass for animation files, skill updates, and validation | about 109,954 tokens | High |
| Direct creation of the new animation page, animation index, and guide inside the final pass | about 60,000-75,000 tokens | Medium |
| Earlier creation of the three pre-existing animation HTML files | Not exactly measurable from current goal counter | Low |

## Practical Cost Takeaway

The expensive part was not just writing HTML. Most token usage came from:

1. Inspecting the existing skill and study artifacts.
2. Preserving the correct learning workflow.
3. Adding the general rule without breaking humanities-course behavior.
4. Validating source and installed skill copies.
5. Keeping durable recovery state so context compression will not lose progress.

For future animation generation, cost can be reduced by using reusable templates in `references/stem-visual-animation.md` and `scripts/generate_animation_demo.py`.
