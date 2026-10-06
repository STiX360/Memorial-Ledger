"""Execute ledger Lua with doubles forbidding any corpse manipulation."""
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.test-tools'))
from lupa.lua51 import LuaRuntime

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.globals().mod_path = (ROOT / 'Memorial Ledger').as_posix()
        self.lua.execute("package.path = mod_path .. '/?.lua;' .. package.path")
        self.lua.execute((ROOT / 'tests/mock_openmw.lua').read_text())
        self.lua.execute("""
            types.Actor.inventory = function() error('Inventory forbidden') end
            mod = require('scripts.memorial_ledger.global'); handlers = mod.engineHandlers
        """)

    def test_no_corpse_interaction(self):
        self.lua.execute("""
            body = corpse('one'); body.remove = function() error('Deletion forbidden') end
            body.record.isPersistent = nil; body.inventory.items = {{count=1}}
            world.activeActors = {body}; handlers.onUpdate(5)
            now = 900000; player.cell = remote; handlers.onUpdate(5)
            assert(#handlers.onSave().entries == 1)
            assert(handlers.onSave().entries[1].status == 'Observed')
            assert(#body.inventory.items == 1 and body.removes == 0)
            assert(handlers.onActivate == nil)
        """)

    def test_quest_flags_do_not_affect_recording(self):
        self.lua.execute("""
            body = corpse('one'); body.record.isPersistent = true; body.record.isEssential = true
            body.record.isRespawning = true; body.record.mwscript = 'quest'
            handlers.onActorActive(body); assert(#handlers.onSave().entries == 1)
        """)

    def test_non_corpses_excluded(self):
        self.lua.execute("""
            alive = corpse('alive'); alive.dead = false
            creature = corpse('beast'); creature.kind = 'creature'
            world.activeActors = {alive,creature,player}; handlers.onUpdate(5)
            assert(#handlers.onSave().entries == 0)
        """)

    def test_unload_and_external_disposal(self):
        self.lua.execute("""
            body = corpse('one'); world.activeActors = {body}; handlers.onUpdate(5)
            body.valid = false; handlers.onUpdate(5); assert(handlers.onSave().entries[1].status == 'Unavailable')
            body.valid = true; handlers.onUpdate(5); assert(#handlers.onSave().entries == 1)
            body.count = 0; handlers.onUpdate(5); assert(handlers.onSave().entries[1].status == 'Removed')
            assert(next(handlers.onSave().pending) == nil and body.removes == 0)
        """)

    def test_duplicate_records_and_revival(self):
        self.lua.execute("""
            a = corpse('same','a'); b = corpse('same','b'); world.activeActors = {a,b}
            handlers.onUpdate(5); handlers.onUpdate(5); assert(#handlers.onSave().entries == 2)
            a.dead = false; handlers.onUpdate(5); assert(handlers.onSave().entries[1].status == 'Revived')
            a.dead = true; handlers.onUpdate(5); assert(#handlers.onSave().entries == 3)
        """)

    def test_notes_save_load_and_ignored_body_controls(self):
        self.lua.execute("""
            body = corpse('one'); handlers.onActorActive(body)
            mod.eventHandlers.MemorialLedgerEdit({id=1,note='Remembered',keep=true})
            handlers.onLoad(handlers.onSave()); local e = handlers.onSave().entries[1]
            assert(e.note == 'Remembered' and e.keep == nil and e.observedAt == 0)
        """)

    def test_old_cleanup_save_migration(self):
        self.lua.execute("""
            body = corpse('one'); handlers.onActorActive(body)
            saved = handlers.onSave(); saved.version = 1; saved.entries[1].keep = true
            saved.entries[1].status = 'Cleanup requested'; saved.pending.one.removing = true
            handlers.onLoad(saved); handlers.onUpdate(5)
            assert(handlers.onSave().entries[1].status == 'Observed' and body.removes == 0)
            assert(handlers.onSave().entries[1].keep == nil and handlers.onSave().pending.one.removing == nil)
        """)

    def test_snapshot_on_pause(self):
        self.lua.execute("""
            for i=1,15 do world.activeActors[i] = corpse('npc'..i) end; handlers.onUpdate(5)
            mod.eventHandlers.MemorialLedgerRequest({player=player,query='npc',filter='Observed',page=2,token=8})
            handlers.onUpdate(0); local data = player.events[#player.events].data
            assert(data.total == 15 and #data.rows == 7 and data.page == 2 and data.token == 8)
            data.rows[1].name = 'changed'; assert(handlers.onSave().entries[8].name == 'npc8')
        """)

    def test_utf8_note_limit(self):
        self.lua.execute("""
            body = corpse('one'); handlers.onActorActive(body)
            mod.eventHandlers.MemorialLedgerEdit({id=1,note=string.rep('a',999)..string.char(195,169)})
            assert(#handlers.onSave().entries[1].note == 999)
        """)

    def test_panel_has_only_note_controls(self):
        self.lua.execute((ROOT / 'tests/mock_player.lua').read_text())
        self.lua.execute("""
            panel = require('scripts.memorial_ledger.player'); panel.interface.open()
            local request = globalEvents[#globalEvents].data
            local e = {id=1,name='Someone',location='Balmora',observedAt=0,status='Observed',reason='Recorded',recordId='one',note=''}
            panel.eventHandlers.MemorialLedgerSnapshot({rows={e},total=1,matches=1,page=1,pages=1,token=request.token})
            assert(#uiState.element.layout.content[1].content[4].content == 2)
            uiState.element.layout.content[1].content[4].events.mouseClick()
            request = globalEvents[#globalEvents].data
            panel.eventHandlers.MemorialLedgerSnapshot({rows={e},selected=e,total=1,matches=1,page=1,pages=1,token=request.token})
            local children = uiState.element.layout.content[1].content; assert(#children == 7)
            assert(not children[4].props.text:find('Disposition',1,true))
            assert(not children[4].props.text:find('Record:',1,true))
            assert(children[4].props.text:find('Place of Death:',1,true))
            assert(children[4].props.text:find('Found on:',1,true))
            assert(children[5].props.text == 'Memorial Note')
            children[6].content[1].events.textChanged('New note'); panel.interface.open()
            assert(mode == nil and globalEvents[#globalEvents].data.note == 'New note')
        """)

    def test_settings_layout_and_open_action(self):
        self.lua.execute((ROOT / 'tests/mock_player.lua').read_text())
        self.lua.execute("""
            require('scripts.memorial_ledger.player')
            settingsPanel = require('scripts.memorial_ledger.menu')
            assert(uiState.settingsPage.name == 'Memorial Ledger')
            local children = uiState.settingsPage.element.layout.content
            assert(children[2].props.text == translations.PageDescription)
            assert(children[3].props.text == 'Controls')
            assert(children[4].content[1].props.text == 'Reset')
            assert(children[5].props.text == 'Ledger Key')
            assert(children[6].props.text == translations.LedgerKeyDescription)
            assert(children[7].content[1].props.text == 'M')
            assert(children[8].props.text == 'Ledger Actions')
            assert(children[9].props.text == 'Open Ledger')
            assert(children[10].props.text == translations.OpenLedgerActionDescription)
            assert(children[11].content[1].props.text == 'Open')
            local count = #globalEvents
            menuState = 'NoGame'; children[11].events.mouseClick()
            assert(#globalEvents == count)
            menuState = 'Running'; children[11].events.mouseClick()
            assert(globalEvents[#globalEvents].name == 'MemorialLedgerOpenRequest')
            mod.eventHandlers.MemorialLedgerOpenRequest()
            assert(player.events[#player.events].name == 'MemorialLedgerOpen')
        """)

    def test_settings_binding_recording_reset_and_cancel(self):
        self.lua.execute((ROOT / 'tests/mock_player.lua').read_text())
        self.lua.execute("""
            require('scripts.memorial_ledger.player')
            local settingsPanel = require('scripts.memorial_ledger.menu')
            local h = settingsPanel.engineHandlers
            local function clickKey() uiState.element.layout.content[7].events.mouseClick() end
            local function binding() return playerSections.OMWInputBindings.MemorialLedgerToggleBinding end
            h.onKeyPress({code=120}); assert(binding().button == 109)
            clickKey(); h.onKeyPress({code=120})
            assert(binding().button == 120 and binding().device == 'keyboard')
            assert(uiState.element.layout.content[7].content[1].props.text == 'X')
            clickKey(); h.onKeyPress({code=27}); assert(binding().button == 120)
            clickKey(); h.onKeyPress({code=127}); assert(binding() == nil)
            assert(uiState.element.layout.content[7].content[1].props.text == 'None')
            clickKey(); h.onMouseButtonPress(3); assert(binding().device == 'mouse')
            clickKey(); h.onControllerButtonPress(2); assert(binding().device == 'controller')
            uiState.element.layout.content[4].events.mouseClick()
            assert(binding().button == 109 and binding().device == 'keyboard')
            clickKey()
            uiState.element.layout.content[7].events.focusLoss(); h.onKeyPress({code=120})
            assert(binding().button == 109)
        """)

    def test_settings_compact_description_spacing(self):
        self.lua.execute((ROOT / 'tests/mock_player.lua').read_text())
        self.lua.execute("""
            local settingsPanel = require('scripts.memorial_ledger.menu')
            for _, w in ipairs({640,1280,1920,3840}) do
                uiState.width = w; settingsPanel.engineHandlers.onFrame()
                local root = uiState.element.layout; local c = root.content
                assert(root.props.size.x < w)
                assert(c[2].props.position.y + c[2].props.size.y < c[3].props.position.y)
                assert(c[6].props.position.y + c[6].props.size.y < c[8].props.position.y)
                assert(c[10].props.position.y + c[10].props.size.y < root.props.size.y)
                assert(c[6].props.size.x < c[7].props.position.x)
                assert(c[10].props.size.x < c[11].props.position.x)
            end
        """)

    def test_name_search_only(self):
        self.lua.execute("""
            local policy = require('scripts.memorial_ledger.policy')
            local entries = {
                {name='Braleni Dren',location='Ebonheart',recordId='guard',note='Joslin'},
                {name='Joslin',location='Ebonheart',recordId='dren',note='Remembered'},
            }
            assert(#policy.select(entries, '') == 2)
            assert(#policy.select(entries, '  DREN  ') == 1)
            assert(policy.select(entries, 'jos')[1].name == 'Joslin')
            assert(#policy.select(entries, 'Ebonheart') == 0)
            assert(#policy.select(entries, 'Remembered') == 0)
            assert(#policy.select(entries, '%') == 0)
        """)

    def test_default_m_and_respect_existing_binding(self):
        self.lua.execute((ROOT / 'tests/mock_player.lua').read_text())
        self.lua.execute("""
            require('scripts.memorial_ledger.player')
            assert(playerSections.OMWInputBindings.MemorialLedgerToggleBinding.button == 109)
            playerSections.OMWInputBindings.MemorialLedgerToggleBinding = nil
            package.loaded['scripts.memorial_ledger.player'] = nil
            require('scripts.memorial_ledger.player')
            assert(playerSections.OMWInputBindings.MemorialLedgerToggleBinding == nil)
            playerSections.MemorialLedgerInputDefaults = {}
            playerSections.OMWInputBindings.MemorialLedgerToggleBinding = {button=120}
            package.loaded['scripts.memorial_ledger.player'] = nil
            require('scripts.memorial_ledger.player')
            assert(playerSections.OMWInputBindings.MemorialLedgerToggleBinding.button == 120)
        """)

    def test_approved_list_layout_and_compact_resize(self):
        self.lua.execute((ROOT / 'tests/mock_player.lua').read_text())
        self.lua.execute("""
            panel = require('scripts.memorial_ledger.player'); panel.interface.open()
            local rows = {}
            for i=1,7 do rows[i]={id=i,name='Person '..i,location='Ebonheart',note=''} end
            local req = globalEvents[#globalEvents].data
            panel.eventHandlers.MemorialLedgerSnapshot({rows=rows,total=7,matches=7,page=1,pages=1,token=req.token})
            local children = uiState.element.layout.content[1].content
            assert(children[3].type == 'Container')
            assert(children[3].content[1].type == 'TextEdit')
            assert(children[4].content[3].type == 'Image')
            assert(children[#children].props.text == 'Search')
            assert(children[11].props.text == '7 memorials')
            children[3].content[1].events.textChanged('Person 2')
            req = globalEvents[#globalEvents].data
            assert(req.query == 'Person 2' and req.page == 1)
            uiState.width, uiState.height = 640,480
            panel.engineHandlers.onFrame()
            children = uiState.element.layout.content[1].content
            assert(globalEvents[#globalEvents].data.pageSize == 4)
            assert(#children == 12) -- header, search, four rows, footer and label
            for i=4,7 do
                local row = children[i]
                assert(row.props.position.y + row.props.size.y <= 362)
            end
        """)

if __name__ == '__main__':
    unittest.main(verbosity=2)
