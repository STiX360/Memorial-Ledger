# Contributor And Maintainer Guide

> Audience: contributors and release maintainers. This is repository maintenance
> documentation, not a mod installation or gameplay guide.

Licensing is pending. Resolve that before accepting contributions for public
reuse. Do not include Morrowind/OpenMW game assets, personal saves, logs, tokens,
or installed modlist configuration in this repository.

## Scope

Keep the mod observational: no corpse activation hooks, inventory reads, body
deletion, record overrides, or game-profile edits. All interaction belongs in
the ledger. Prefer built-in OpenMW UI assets.

## Verify Changes

Install `requirements-dev.txt`, run `python tests/run_tests.py` and
`python -m unittest discover -s tests -p test_release.py -v`, then run
`python tools/package_mod.py`. The tests use actual Lua 5.1 and mocked APIs;
native rendering, serialization, and input still require the
[acceptance checklist](Memorial%20Ledger/ACCEPTANCE.md).

`python tools/export_preview.py` refreshes the layout HTML under `reports`.
Capture replacement preview images from these files when layouts change.
Label API-double previews as previews, never in-game screenshots.

## Releases

1. Update `VERSION`, both README version references, the documentation page,
   and `CHANGELOG.md` together.
2. Run tests, package, and complete the in-game acceptance checklist.
3. Review `git diff` for personal paths, unrelated files, and accidental assets.
4. Commit the reviewed changes and push only after choosing the GitHub destination.
5. Create and push a `v`-prefixed tag matching `VERSION`. This automatically
   triggers a tested Nexus upload once the Nexus environment is configured.
6. Create the GitHub release and attach the ZIP from `dist`, not the
   automatically generated source archive. This does not upload to Nexus again.

The CI workflow only tests and uploads build artifacts. It does not publish
releases, deploy the documentation website, or push commits.
The separate Nexus Upload workflow automatically publishes matching version
tag pushes. Manual dispatch defaults to a dry run and requires version
confirmation to publish. See the [maintainer Nexus publishing guide](NEXUS-PUBLISHING.md).

Workflow actions follow the official documentation for
[checkout](https://github.com/actions/checkout),
[setup-python](https://github.com/actions/setup-python), and
[upload-artifact](https://github.com/actions/upload-artifact).
