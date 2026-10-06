# Memorial Ledger 0.2.5

An observational OpenMW Lua mod. All interaction is in the ledger, never on
corpses. No cleanup, corpse activation hooks, inventory access, or body controls.
No record overrides or custom art assets.

## Install And Open

Targets builds with MWUI, Settings, UI, and input-binding APIs (developed against
current OpenMW 0.52 development APIs). Persistence flags are no longer required.
Native engine compatibility remains unverified; test on a disposable save.
Classic Morrowind/MWSE is not supported.

Add the extracted directory as a data path and enable the script content:

```ini
data="D:/Games/OpenMW/Mods/MemorialLedger"
content=MemorialLedger.omwscripts
```

Adjust the path to your install location. The default key is M. Change Ledger
Key under Settings > Scripts > Memorial Ledger > Controls if M conflicts
with another mod. Existing bindings and later deliberate unbinding are preserved.
Click the key button and press a new key; Escape cancels, Delete/Backspace clears
the binding, and Reset restores M. Mouse and controller buttons are also accepted.
Alternatively click Open under Ledger Actions and close Settings to return to gameplay.
Console fallback (close the console after running):

```lua
luag require('openmw.interfaces').MemorialLedger.open()
```

Close, Escape, or the bound key closes the panel. Existing menus are not dismissed.

## Behavior

Dead NPCs are passively discovered in active cells every five simulation seconds
and when actors become active. No touching or looting is required. This includes
bodies you did not kill and bodies not necessarily visible on screen. Creatures
and players are excluded.

Entries display name, location, discovery time, and your memorial note.
Time is elapsed game days/hours, not a claimed death time or calendar date.
NPC name search is case-insensitive and matches partial names. Pagination
makes the ledger browsable; no technical status labels or filters are shown. Click
a row for details and note editing. Back and Close persist notes automatically
(up to 1,000 UTF-8 bytes).

Reference availability and revival are tracked internally only, to avoid
duplicate memorials and retain entries when cells unload. Another observed
death after revival gets its own entry. Technical states and record IDs are
not presented as in-world memorial details.

The mod never inspects inventories, deletes bodies, adds interaction prompts,
or changes vanilla corpse behavior. Notes cannot affect bodies. Individual
instances remain separate even with matching record IDs. Entries, notes, and
observation times persist in saves. Inaccessible references remain tracked in
case their cells reload.

## Updating From 0.1.0

Entries and notes are retained. Cleanup settings and Keep body controls are
removed, and saved cleanup requests are not continued. Earlier confirmed cleanup
is retained as historical Removed entries. Updating cannot restore bodies removed
by an earlier version; recovery requires a pre-cleanup save.

## Verification

0.2.5 implements the approved settings layout using a Menu-context page, with
descriptions beneath labels and right-aligned controls. Controls contains Ledger
Key and Reset; Ledger Actions contains the separate Open command without a
Reset button. The redundant binding name and description are no longer repeated.
Sixteen automated tests pass, including rebinding, cancellation, clearing,
resetting, action dispatch, and compact settings description spacing.

0.2.4 implements both approved ledger screen mockups: a bordered Search field,
unframed name/place rows separated by thin rules, concise memorial count,
pagination, and the previously approved detail screen.

0.2.3 applies the approved detail layout: Place of Death, Found on, Memorial
Note, a bordered note field, and Back/Close only. Place of Death uses the
body's location at discovery; it cannot prove where a moved body originally
died. M is assigned once only when no existing binding is present.

0.2.2 removes the technical state filter, row labels, and diagnostic details
from the panel, replacing them with a full-width NPC name search.

0.2.1 fixes OpenMW 0.52 settings registration: the custom button renderer runs
in a Menu script, and input binding uses the required string identifier rather
than a table. Replace the mod files and fully restart OpenMW after upgrading.
The new binding setting avoids the malformed value persisted by older versions.

Tests execute real Lua 5.1 with doubles forbidding inventory access and deletion.
Native rendering, binding, reference serialization, and disposal detection still
need in-game verification; see ACCEPTANCE.md. No game profiles or saves are
modified by this build.
