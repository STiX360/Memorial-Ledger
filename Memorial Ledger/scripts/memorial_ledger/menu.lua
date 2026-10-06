local core = require('openmw.core')
local ui = require('openmw.ui')
local util = require('openmw.util')
local async = require('openmw.async')
local input = require('openmw.input')
local menu = require('openmw.menu')
local storage = require('openmw.storage')
local I = require('openmw.interfaces')

local l10n = core.l10n('MemorialLedger')
local templates = I.MWUI.templates
local bindings = storage.playerSection('OMWInputBindings')
local bindingId = 'MemorialLedgerToggleBinding'
local element, recording, width = nil, false, nil
local render

local function text(key, x, y, w, h, heading)
    return {type = ui.TYPE.Text, template = heading and templates.textHeader or templates.textNormal,
        props = {text = l10n(key), position = util.vector2(x, y), size = util.vector2(w, h),
            autoSize = false, multiline = true, wordWrap = true, textSize = heading and 20 or 16}}
end

local function line(y, count)
    local content = {}
    for i = 1, count or 1 do
        content[#content + 1] = {type = ui.TYPE.Image, template = templates.horizontalLine,
            props = {position = util.vector2(0, y + (i - 1) * 3), size = util.vector2(width, 1),
                ignorePointerEvents = true}}
    end
    return content
end

local function bind(device, button)
    recording = false
    bindings:set(bindingId, {device = device, button = button, type = 'trigger', key = 'MemorialLedgerToggle'})
    render()
end

local function bindingLabel()
    if recording then return '...' end
    local binding = bindings:get(bindingId)
    if not binding then return l10n('Unbound') end
    if binding.device == 'keyboard' then return input.getKeyName(binding.button) end
    return binding.device .. ' ' .. tostring(binding.button)
end

local function button(label, x, y, w, callback, focusLoss)
    return {type = ui.TYPE.Container, template = templates.box,
        props = {position = util.vector2(x, y)},
        content = ui.content({{type = ui.TYPE.Text, template = templates.textNormal,
            props = {text = label, size = util.vector2(w, 28), autoSize = false,
                textAlignH = ui.ALIGNMENT.Center, textAlignV = ui.ALIGNMENT.Center}}}),
        events = {mouseClick = async:callback(callback), focusLoss = focusLoss and async:callback(focusLoss)},
    }
end

render = function()
    width = math.min(1000, math.max(300, math.floor(ui.screenSize().x * 0.52)))
    local descriptionHeight = math.max(66, math.ceil(#l10n('PageDescription') / (width / 9)) * 22)
    local rowWidth = width - 124
    local keyHeight = math.max(44, math.ceil(#l10n('LedgerKeyDescription') / (rowWidth / 9)) * 22)
    local actionHeight = math.max(44, math.ceil(#l10n('OpenLedgerActionDescription') / (rowWidth / 9)) * 22)
    local controlsY = 54 + descriptionHeight + 30
    local rowY = controlsY + 44
    local actionsY = rowY + 26 + keyHeight + 30
    local children = {text('PageName', 0, 0, width, 30, true),
        text('PageDescription', 0, 46, width, descriptionHeight),
        text('Controls', 0, controlsY, width - 100, 30, true),
        button(l10n('Reset'), width - 76, controlsY, 70, function() bind('keyboard', input.KEY.M) end),
        text('LedgerKey', 0, rowY, width - 124, 24),
        text('LedgerKeyDescription', 0, rowY + 26, rowWidth, keyHeight),
        button(bindingLabel(), width - 110, rowY + 16, 104, function()
            recording = true; render()
        end, function()
            if recording then recording = false; render() end
        end),
        text('LedgerActions', 0, actionsY, width, 30, true),
        text('OpenLedgerAction', 0, actionsY + 44, width - 124, 24),
        text('OpenLedgerActionDescription', 0, actionsY + 70, rowWidth, actionHeight),
        button(l10n('Open'), width - 110, actionsY + 60, 104, function()
            recording = false
            if menu.getState() == menu.STATE.Running then core.sendGlobalEvent('MemorialLedgerOpenRequest', {}) end
            render()
        end),
    }
    for _, spec in ipairs({{34, 3}, {controlsY + 34, 2}, {rowY + 26 + keyHeight + 12, 1},
        {actionsY + 34, 2}, {actionsY + 70 + actionHeight + 12, 1}}) do
        for _, widget in ipairs(line(spec[1], spec[2])) do children[#children + 1] = widget end
    end
    local layout = {type = ui.TYPE.Widget,
        props = {size = util.vector2(width, actionsY + 70 + actionHeight + 30)}, content = ui.content(children)}
    if element then element.layout = layout; element:update() else element = ui.create(layout) end
end

render()
ui.registerSettingsPage {name = l10n('PageName'), searchHints = 'memorial ledger key notes', element = element}
bindings:subscribe(async:callback(function(_, key)
    if key == nil or key == bindingId then render() end
end))

return {
    engineHandlers = {
        onFrame = function()
            local desired = math.min(1000, math.max(300, math.floor(ui.screenSize().x * 0.52)))
            if desired ~= width then render() end
        end,
        onKeyPress = function(key)
            if not recording then return end
            if key.code == input.KEY.Escape then recording = false; render()
            elseif key.code == input.KEY.Delete or key.code == input.KEY.Backspace then
                recording = false; bindings:set(bindingId, nil); render()
            elseif key.code then bind('keyboard', key.code) end
        end,
        onMouseButtonPress = function(buttonId)
            if recording then bind('mouse', buttonId) end
        end,
        onControllerButtonPress = function(buttonId)
            if recording then bind('controller', buttonId) end
        end,
    },
}
