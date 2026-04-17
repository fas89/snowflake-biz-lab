# FLUID Demo Runbooks

These runbooks are written for a real audience, not just for maintainers.

## Choose Your Path

- [Mac Greenfield Demo](mac-greenfield-demo.md): the primary live story from local apps through `fluid forge`, plan, apply, standards, and DMM publish
- [Mac Existing dbt Demo](mac-existing-dbt-demo.md): the secondary variation for a workspace that already has dbt assets
- [Greenfield Forge Prompt](greenfield-forge-prompt.md): copy/paste text for the AI-based greenfield `forge` step
- [Existing dbt Forge Prompt](existing-dbt-forge-prompt.md): copy/paste text for the import-plus-enrichment variation
- [Rehearsal Checklist](rehearsal-checklist.md): marks each step as off-stage prep, live on-stage, or future FLUID gap
- [Baby Steps Demo](baby-steps-demo.md): the shortest install-first warm-up
- [Backup Demo](backup-demo.md): the rescue path when the network or a live dependency is unreliable

## Demo Philosophy

The best final demo here is not a magic one-liner.

It should feel like:

1. local apps are up
2. Snowflake staging is loaded
3. a GitLab workspace is ready on your Mac
4. `data-product-forge` is installed live
5. `fluid init`, `fluid forge`, `fluid generate schedule`, and `fluid generate ci` happen in the workspace
6. `fluid validate`, `fluid plan`, `fluid apply`, `fluid generate standard`, and `fluid dmm publish` close the story
