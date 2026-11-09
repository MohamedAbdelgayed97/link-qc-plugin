# link-qc plugin

Link Development QA pipeline for Claude: requirements review, manual test case
design and live validation, Azure DevOps publishing and bug sync, Playwright
automation, visual UI audits, white-box analysis, retesting and bug reports.

The skills come from [AhmedZaher1233/Link_AI_Pro](https://github.com/AhmedZaher1233/Link_AI_Pro).
A daily GitHub Action (`.github/workflows/sync.yml`) pulls them, applies the
plugin fixes (`build/build.py`), bumps the version and publishes a release.

## Install

**Claude Code (VS Code or terminal)**

```
/plugin marketplace add MohamedAbdelgayed97/link-qc-plugin
/plugin install link-qc@linkdev-qa
```

Then run `/plugin`, open **Marketplaces**, select `linkdev-qa` and enable
auto-update.

**Cowork (Claude desktop app)**

Download `link-qc.plugin` from the latest
[release](https://github.com/MohamedAbdelgayed97/link-qc-plugin/releases) and
upload it in Customize > Plugins.

## Start

Run `/link-qc:link-qc-1-generate-update-testing-structure` once per project.

## Maintain

- Our own skills live in `build/extra-skills/` (e.g. `ado-bug-report`).
- Hand-written descriptions go in `build/descriptions.yaml`.
- Never edit `skills/` by hand: the next sync overwrites it.
- If the Action fails, an upstream change broke a fix. The log says which one;
  nothing was published.
