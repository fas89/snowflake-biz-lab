# CLI Version vs `fluidVersion`

This is the most important version note in the repo.

## The Short Version

- `fluid version` tells you which CLI release you installed
- `fluidVersion` inside a contract tells FLUID which contract schema to validate against

They are related, but they are not the same number.

## What This Repo Pins Today

- Demo-release package: the **latest** `data-product-forge` release published on **TestPyPI**, resolved dynamically at install time. This is the source of truth the demo validates against.
- Repo contract schema: `fluidVersion: 0.7.2`

The launchpad first queries TestPyPI for the newest `data-product-forge` version, then installs that exact version with PyPI as the primary index and TestPyPI as the extra index. That keeps the FLUID package on the newest TestPyPI release without pulling prerelease transitive dependencies like `httpx` or `dbt-core`.

## Why The Numbers Are Different

The released package has moved ahead, but the safest bundled contract-schema target we could verify still resolves to `0.7.2`.

That means:

- you should install the newer CLI release for the demo track
- you should still author the repo contracts with `fluidVersion: 0.7.2`

## `demo-release` vs `dev-source`

### `demo-release`

- package source: TestPyPI
- install target: latest `data-product-forge` release from TestPyPI
- purpose: final demo and release-truth validation

### `dev-source`

- package source: sibling `../forge-cli` checkout
- purpose: fix something upstream, retest it quickly, then come back to the demo track
- expectation: use `forge-cli` remote `main`, not an older or unrelated local branch

## What To Run

```bash
task fluid:bootstrap:demo
task fluid:check:demo
task fluid:bootstrap:dev
task fluid:check:dev
```

## Common Confusion

### “I installed the latest TestPyPI release, so why are the contracts still `0.7.2`?”

Because the package version and the contract schema version are separate compatibility layers.

### “Why not jump the repo contracts to `0.8.0`?”

Because this repo should stay on the newest bundled contract schema that is actually verified in the runtime, not on a future-looking release hint.

If you want the detailed compatibility conversation before changing that default, treat it as an explicit upgrade task rather than a casual version bump.
