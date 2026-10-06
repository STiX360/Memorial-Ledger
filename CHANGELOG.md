# Changelog

## 0.2.5

- Implemented the approved settings layout with descriptions and aligned controls.
- Separated Ledger Key under Controls from Open Ledger under Ledger Actions.
- Removed duplicate binding text and the unnecessary action-group Reset button.
- Added focused settings tests; 16 automated tests pass locally.

## 0.2.4

- Implemented the approved ledger list with bordered NPC search, thin separators,
  memorial counts, and pagination.
- Improved compact-window layouts.

## 0.2.3

- Adopted Place of Death, Found on, and Memorial Note on entry details.
- Removed Save Note; Back and Close persist the note.
- Assigned M once when no existing custom binding is present.

## 0.2.2

- Replaced technical state filters with NPC name search.
- Removed record IDs, disposition, and reason from visible entries.

## 0.2.1

- Moved the custom settings renderer to the Menu context.
- Fixed the input-binding setting's identifier contract.

## 0.2.0

- Made the mod ledger-only: no cleanup, corpse interaction, or inventory access.
- Retained save-specific entries and notes while stopping old cleanup requests.

## Upgrade Warning

Updating from the earlier cleanup prototype preserves entries and notes but
cannot restore bodies it already removed. Use a pre-cleanup save to recover them.
