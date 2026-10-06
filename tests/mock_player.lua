mode = nil
uiState = {created=0,width=1024,height=768}
translations = {
    PageName='Memorial Ledger', Controls='Controls', LedgerKey='Ledger Key',
    PageDescription='A personal record of those found dead during your travels. Keep their names, places of death, and your own memorial notes. Bodies and belongings remain untouched.',
    LedgerKeyDescription='Open or close the ledger during gameplay. Default key: M.',
    LedgerActions='Ledger Actions', OpenLedgerAction='Open Ledger',
    OpenLedgerActionDescription='Open the ledger after closing the Options menu.',
    Open='Open', Reset='Reset', Unbound='None',
}
I.MWUI = {templates={textHeader={},textNormal={},box={},boxSolid={},textEditLine={},textEditBox={},horizontalLine={}}}
I.Settings.registerRenderer = function() error('Custom renderers require Menu context') end
I.UI = {
    getMode=function() return mode end,
    addMode=function(value) mode=value end,
    removeMode=function(value) if mode==value then mode=nil end end,
}
package.preload['openmw.self'] = function() return {object=player} end
package.preload['openmw.async'] = function() return {callback=function(_,fn) return fn end} end
package.preload['openmw.util'] = function() return {vector2=function(x,y) return {x=x,y=y} end} end
package.preload['openmw.input'] = function() return {
    KEY={Escape=27,M=109,Delete=127,Backspace=8},
    getKeyName=function(code) return string.upper(string.char(code)) end,
    registerTrigger=function() end,registerTriggerHandler=function() end,
} end
menuState = 'Running'
package.preload['openmw.menu'] = function() return {
    STATE={Running='Running',NoGame='NoGame',Ended='Ended'},getState=function() return menuState end,
} end
package.preload['openmw.ui'] = function() return {
    TYPE={Text='Text',Container='Container',Widget='Widget',TextEdit='TextEdit',Image='Image'},
    ALIGNMENT={Center='Center'},content=function(t) return t end,
    screenSize=function() return {x=uiState.width,y=uiState.height} end,
    registerSettingsPage=function(page) uiState.settingsPage=page end,
    create=function(layout)
        uiState.created = uiState.created+1
        local e = {layout=layout,update=function() end,destroy=function(self) self.destroyed=true end}
        uiState.element = e; return e
    end,
} end
