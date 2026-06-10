# Releasing

Beacon versions are derived from git tags; there is no version number to edit in code.

## 1. Make sure main is ready

All intended changes merged, CI green.

## 2. Tag the commit

Tags follow Semantic Versioning: `vMAJOR.MINOR.PATCH`.

```bash
git checkout main
git pull
git tag v0.2.0
git push origin v0.2.0
```

Guidance on which number to increment:

- `PATCH`: bug fixes and dependency updates with no public API change
- `MINOR`: additive features and new non-breaking interfaces
- `MAJOR`: breaking API changes

## 3. Publish a GitHub release

1. Go to `https://github.com/nanacnote/beacon/releases/new`
2. Choose the tag you just pushed (for example `v0.2.0`)
3. Set the title to the tag name
4. Write release notes focused on consumer impact
5. Click Publish release

Publishing the release triggers the publish workflow and uploads built artifacts.

## 4. Verify release assets

Confirm the Publish workflow succeeds and the release includes:

- `beacon-<version>-py3-none-any.whl`
- `beacon-<version>.tar.gz`

## 5. Share install commands

Install from GitHub release wheel:

```bash
pip install https://github.com/nanacnote/beacon/releases/download/v0.2.0/beacon-0.2.0-py3-none-any.whl
```

Install from git tag:

```bash
pip install "beacon @ git+https://github.com/nanacnote/beacon.git@v0.2.0"
```

## Fixing a bad release

If a release is wrong:

1. Delete the GitHub release
2. Delete the tag locally and remotely
3. Fix the issue, tag again, and republish

```bash
git tag -d v0.2.0
git push origin --delete v0.2.0
```
