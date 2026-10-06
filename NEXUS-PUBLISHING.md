# Maintainer Guide: Nexus Publishing

> Audience: release maintainers. Players do not need these publishing steps or
> an API key to install or use Memorial Ledger.

The [official Nexus upload action](https://github.com/Nexus-Mods/upload-action)
adds a version to an existing file. Create the mod page **and upload the initial
file manually** first. It does not create the initial listing or its first file.

## One-Time Setup

1. Publish the repository to GitHub, including `.github/workflows/nexus-upload.yml`.
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

No `mod_id` is needed for this workflow because it does not submit Nexus
changelog entries. Version notes and the mod page remain manually maintained.

## Dry Run

On GitHub, open Actions > Nexus Upload > Run workflow, select `main`, and leave
**dry_run checked**. It runs the Lua and release-guard tests, builds and verifies
the ZIP, and retains it as a workflow artifact. The Nexus publish job is skipped,
so no API key or file ID is needed and no Nexus API request is made.

## Automatic Version Updates

Update `VERSION`, release notes, and relevant documentation first. Finish native
in-game testing and resolve licensing before public distribution. Push the
reviewed commit to `main`.

Create and push a tag matching `VERSION`, for example:

```sh
git tag v0.2.6
git push origin v0.2.6
```

Use the actual version, not this example verbatim. The tag push starts tests
and packaging, checks that the tag matches `VERSION`, then uploads that exact
tested ZIP to Nexus and updates the Nexus mod's version. Ordinary branch pushes
only run validation; they never publish. Invalid tags and mismatched versions
fail before uploading, and tag deletion does not publish.

Do not force-move or recreate release tags. GitHub release creation remains
separate and will not upload again, avoiding two triggers for the same release.

## Manual Fallback

Run Nexus Upload on `main`, uncheck **dry_run**, and enter the exact `VERSION`
value in **confirm_version**. A mismatched confirmation fails before publishing.
Approve the environment deployment if required reviewers are configured.

The publish job downloads the exact tested ZIP, checks its SHA-256 and required
configuration, and invokes the pinned Nexus action. It keeps old file versions,
does not make the new file the primary mod-manager download, and updates
the mod page's version to match the uploaded file. Mod-manager downloads remain enabled, and the
requirements popup is requested.

Verify the resulting file on Nexus after upload. Do not blindly rerun a failed
upload: the action may have created a version before reporting a later failure,
and repeat runs may create duplicate uploads. Publication has no automatic retry.

## Boundaries

Only pushes of matching `vX.Y.Z` tags and manually confirmed dispatches from
`main` can publish. There is no branch-push, pull-request, or GitHub-release
upload trigger. GitHub release creation,
Nexus page descriptions/images, and website deployment remain separate.

The API key is exposed only to the publish job's configuration check and upload
step. The upload action is pinned to commit
`c96019556046053aa26044b44396cd38929daf23`; review upstream changes before updating
that pin. Do not enable verbose action debugging with production credentials.

The workflow has been prepared and its local guards tested, but has not run on
GitHub or uploaded to Nexus yet.
