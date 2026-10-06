# In-Game Acceptance Checklist

Native testing is outstanding. Use a disposable save.

1. Load the scripts and check logs. Check M opens the ledger unless an existing
   binding was preserved; change bindings in Scripts settings if needed.
2. Check open/close, Escape, the Settings button, and console fallback.
   Other menus should survive and mouse behavior should return on close.
3. Approach a corpse without touching or looting it. Check an entry appears
   within five simulation seconds, with no new corpse interaction prompt.
4. Leave items on bodies, wait days, and revisit. This mod must never change
   bodies or inventories; normal engine disposal remains unchanged.
5. Check persistent, essential, scripted, and respawning dead NPCs are recorded.
   Creatures, players, and living NPCs must be excluded.
6. Check Place of Death, Found on, and Memorial Note. There should be no Save
   Note button. Edit notes, use Back/Close, save/reload, and verify retention.
7. Unload/revisit cells. Memorial entries and notes must remain in the ledger.
8. Dispose of a body normally; its memorial must remain without technical
   state labels or diagnostic details appearing in the panel.
9. Revive an NPC, let a scan see it alive, then kill it again. Check distinct
   death episodes without duplicates during an uninterrupted death.
10. Test partial NPC name search, paging, long names, and notes at 640 x 480, 1280 x 720,
    and 1920 x 1080.
11. Upgrade a 0.1.0 save. Check notes survive, body controls are gone, and saved
    cleanup requests never resume.
12. In Scripts > Memorial Ledger, check descriptions under each label, one
    right-aligned Ledger Key button under Controls, and Open under Ledger Actions.
    Reset must appear only beside Controls. No duplicated binding labels.
13. Rebind the key, cancel with Escape, clear with Delete/Backspace, and Reset to M.
    Test mouse/controller binding and restart to confirm it persists. Open must
    wait for Options to close and must not request a ledger without a loaded game.
14. Check settings descriptions wrap without clipping at the resolutions above;
    use the native settings scrollbar when the page exceeds the available height.
