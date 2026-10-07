# Maintainer Guide: GitHub And Nexus Publishing

> Audience: release maintainers. Players do not need these publishing steps or
> an API key to install or use Memorial Ledger.

The [official Nexus upload action](https://github.com/Nexus-Mods/upload-action)
adds a version to an existing file. Create the mod page **and upload the initial
file manually** first. It does not create the initial listing or its first file.

## One-Time Setup

1. Publish the repository to GitHub, including `.github/workflows/nexus-upload.yml`.
   Enable GitHub Actions. GitHub publishing uses the built-in `GITHUB_TOKEN`
   with `contents: write` granted only to the release job; no extra GitHub secret
   is needed. Repository or organization policies must allow that permission.
2. Create the Nexus mod page for Morrowind and upload the import-ready ZIP once.
   Document the OpenMW requirements and current beta status on the page.
3. Find the **file ID** using Advanced on the public Files tab, or the file's
   edit menu under Manage Files. Use the ID expected by the v3 upload action,
   not a guessed number from a download URL. The mod-page ID is not the file ID.
4. In GitHub Settings > Environments, create `nexus`. Allow the `main` branch
   and `v*` tags. For unattended updates, do not require a reviewer approval;
   configured required reviewers will pause automatic updates until approved.
   Restrict creation/deletion of release tags to trusted maintainers using
   repository rulesets where supported.
5. Add environment secret **NEXUSMODS_API_KEY** and environment variable
   **NEXUSMODS_FILE_ID**. Do not put the key in source, workflow inputs, issues,
   chat messages, or screenshots.

The workflow submits the matching version's `CHANGELOG.md` entry to Nexus as
release notes. Its `mod_id` is the API **Unique Mod ID** `429496790087`, confirmed
in this mod's Advanced dialog, not the public page number `60487`. It is pinned
in the workflow and is not a secret; no additional environment variable is needed.
The mod page's description and screenshots remain manually maintained.

## Dry Run

On GitHub, open Actions > Publish Releases > Run workflow, select `main`, and leave
**dry_run checked**. It runs the Lua and release-guard tests, builds and verifies
the ZIP, validates its version's changelog entry, and retains the ZIP as a workflow
artifact. Both publishing jobs are skipped,
so no API key or file ID is needed and no publication request is made.

## Automatic Version Updates

Update `VERSION`, release notes, and relevant documentation first. Finish native
in-game testing and resolve licensing before public distribution. Push the
reviewed commit to `main`.

Add exactly one `## X.Y.Z` heading in `CHANGELOG.md` matching `VERSION`, followed
by non-empty player-facing release notes. Only that section is published to both
destinations, not older releases or the separate Upgrade Warning section.
Missing, empty, or duplicate matching entries fail before either publish job.

Create and push a tag matching `VERSION`, for example:

```sh
git tag v0.2.6
git push origin v0.2.6
```

Use the actual version, not this example verbatim. The tag push starts tests
and packaging, checks that the tag matches `VERSION`, then publishes a GitHub
Release and uploads that exact tested ZIP to Nexus, updating the Nexus mod's
version. The two publishing jobs depend only on the successful build, not on
each other: missing Nexus credentials or a Nexus failure does not block GitHub.
Ordinary branch pushes
only run validation; they never publish. Invalid tags and mismatched versions
fail before uploading, and tag deletion does not publish.

Do not force-move or recreate release tags. Creating or editing a GitHub Release
does not trigger another Nexus upload.

## GitHub Download Mirror

The release job checks the downloaded ZIP's SHA-256 before invoking GitHub CLI.
It attaches `MemorialLedger-<version>.zip`, includes the matching changelog entry and
basic installation guidance, and requires the tag to already exist.
Versions `0.x.y` are prereleases and are not marked Latest; major versions `1`
and above are regular releases. To release a beta after 1.0, extend this policy
and the version/tag guards explicitly rather than relying on a beta tag suffix.

Use https://github.com/STiX360/Memorial-Ledger/releases as the Nexus mirror link.
The `/releases/latest` endpoint is not the beta mirror. Players should select
the mod ZIP under Assets, not GitHub's generated source archives.

GitHub-only reruns verify an existing ZIP before treating it as complete. They
can add a missing ZIP or finish a draft, but never replace a differing asset.
Existing releases with a different prerelease status require manual review.
Reruns do not overwrite the notes of an existing GitHub Release.
If GitHub publishing fails, rerun only that job; rerunning the entire workflow
can upload another Nexus file version.

## Manual Fallback

Run Publish Releases on `main`, uncheck **dry_run**, and enter the exact `VERSION`
value in **confirm_version**. A mismatched confirmation fails before publishing.
Approve the environment deployment if required reviewers are configured.
This manual fallback uploads only to Nexus; it does not create a GitHub Release.

The publish job downloads the exact tested ZIP, checks its SHA-256 and required
configuration, and invokes the pinned Nexus action with the release's changelog
entry and API Unique Mod ID. It keeps old file versions,
does not make the new file the primary mod-manager download, and updates
the mod page's version to match the uploaded file. Mod-manager downloads remain enabled, and the
requirements popup is requested.

Verify the resulting file on Nexus after upload. Do not blindly rerun a failed
upload: the action may have created a version before reporting a later failure,
and repeat runs may create duplicate uploads. Publication has no automatic retry.
The action uploads the file before submitting its changelog. If the notes step
fails, check whether the ZIP was already published and repair the notes manually
rather than uploading that version again.

## Boundaries

Only pushes of matching `vX.Y.Z` tags and manually confirmed dispatches from
`main` can publish. There is no branch-push, pull-request, or GitHub-release
upload trigger. GitHub releases publish only from version-tag pushes.
Nexus page descriptions/images and website deployment remain separate.

The API key is exposed only to the publish job's configuration check and upload
step. The upload action is pinned to commit
`c96019556046053aa26044b44396cd38929daf23`; review upstream changes before updating
that pin. Do not enable verbose action debugging with production credentials.

The workflow and its publishing guards are locally tested. Live GitHub release
publishing and Nexus uploading still require verification on the hosted runner.
