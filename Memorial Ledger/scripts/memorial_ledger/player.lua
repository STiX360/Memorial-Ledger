local core = require('openmw.core')
local self = require('openmw.self')
local ui = require('openmw.ui')
local util = require('openmw.util')
local async = require('openmw.async')
local input = require('openmw.input')
local storage = require('openmw.storage')
local I = require('openmw.interfaces')
local policy = require('scripts.memorial_ledger.policy')

local templates = I.MWUI.templates
local window, snapshot, query, selected, draft = nil, nil, '', nil, ''
local page, token, queuedOpen = 1, 0, false
local screenWidth, screenHeight
local render

local function pageSize()
    return math.max(1, math.min(7, math.floor((math.min(560, ui.screenSize().y - 64) - 168) / 52)))
end

local function request()
    token = token + 1
    core.sendGlobalEvent('MemorialLedgerRequest', {
        player = self.object, query = query, page = page, selected = selected, token = token,
        pageSize = pageSize(),
    })
end

local function saveNote()
    if selected then core.sendGlobalEvent('MemorialLedgerEdit', {id = selected, note = draft}) end
end

local function close()
    queuedOpen = false
    if not window then return end
    saveNote()
    window:destroy()
    window = nil
    -- Only the Interface mode added by this window is removed; other menu modes survive.
    I.UI.removeMode('Interface')
end

local function open()
    if window then close(); return end
    if I.UI.getMode() ~= nil then queuedOpen = true; return end
    queuedOpen = false
    selected, snapshot = nil, nil
    I.UI.addMode('Interface', {windows = {}})
    render()
    request()
end

local function text(value, x, y, w, h, header)
    return {type = ui.TYPE.Text, template = header and templates.textHeader or templates.textNormal,
        props = {text = value, position = util.vector2(x, y), size = util.vector2(w, h),
            autoSize = false, multiline = true, wordWrap = true, textSize = header and 20 or 16}}
end

local function button(label, x, y, w, callback)
    return {type = ui.TYPE.Container, template = templates.box,
        props = {position = util.vector2(x, y)},
        events = {mouseClick = async:callback(callback)},
        content = ui.content({{type = ui.TYPE.Text, template = templates.textNormal,
            props = {text = label, size = util.vector2(w, 28), autoSize = false,
                textAlignH = ui.ALIGNMENT.Center, textAlignV = ui.ALIGNMENT.Center}}})}
end

local function edit(value, x, y, w, h, callback, multiline, readOnly)
    return {type = ui.TYPE.TextEdit,
        template = multiline and templates.textEditBox or templates.textEditLine,
        props = {text = value, position = util.vector2(x, y), size = util.vector2(w, h),
            multiline = multiline or false, wordWrap = multiline or false, readOnly = readOnly or false,
            textSize = 16},
        events = callback and {textChanged = async:callback(callback)} or nil}
end

local function abbreviated(value, width)
    local limit = math.max(12, math.floor(width / 10))
    if #value <= limit then return value end
    -- Do not leave a partial UTF-8 sequence at the ellipsis boundary.
    local cut = limit - 3
    while cut > 0 and value:byte(cut + 1) >= 128 and value:byte(cut + 1) < 192 do cut = cut - 1 end
    return value:sub(1, cut) .. '...'
end

render = function()
    local screen = ui.screenSize()
    screenWidth, screenHeight = screen.x, screen.y
    local w, h = math.min(820, screen.x - 64), math.min(560, screen.y - 64)
    local children = {text('Memorial Ledger', 16, 12, w - 170, 30, true),
        button('Close', w - 116, 10, 90, close)}
    local e = snapshot and snapshot.selected
    if selected and e then
        children[#children + 1] = text(abbreviated(e.name, w - 40), 16, 54, w - 32, 30, true)
        local details = table.concat({
            'Place of Death: ' .. e.location,
            'Found on: ' .. policy.date(e.observedAt),
        }, '\n')
        children[#children + 1] = text(details, 16, 90, w - 32, 64)
        local noteY = 166
        children[#children + 1] = text('Memorial Note', 16, noteY, w - 32, 24)
        children[#children + 1] = {
            type = ui.TYPE.Container, template = templates.box,
            props = {position = util.vector2(16, noteY + 28)},
            content = ui.content({edit(draft, 4, 4, w - 48, h - noteY - 108,
                function(value) draft = policy.truncate(value, 1000) end, true)}),
        }
        children[#children + 1] = button('Back', 16, h - 48, 82, function()
            saveNote(); selected = nil; request()
        end)
    else
        children[#children + 1] = {
            type = ui.TYPE.Container, template = templates.box,
            props = {position = util.vector2(96, 50)},
            content = ui.content({edit(query, 4, 4, w - 128, 28, function(value)
                query, page, selected = value, 1, nil; request()
            end)}),
        }
        local rowHeight = math.floor((h - 168) / pageSize())
        for index, row in ipairs(snapshot and snapshot.rows or {}) do
            if index > pageSize() then break end
            local y = 96 + (index - 1) * rowHeight
            local label = abbreviated(row.name, w - 48)
            local rowContent = {
                text(label, 0, 0, w - 48, 23, true),
                text(abbreviated(row.location, w - 48), 0, 25, w - 48, 21),
            }
            if index < math.min(#snapshot.rows, pageSize()) then
                rowContent[#rowContent + 1] = {
                    type = ui.TYPE.Image, template = templates.horizontalLine,
                    props = {position = util.vector2(0, rowHeight - 4), size = util.vector2(w - 32, 1),
                        ignorePointerEvents = true},
                }
            end
            children[#children + 1] = {
                type = ui.TYPE.Widget, props = {position = util.vector2(16, y), size = util.vector2(w - 32, rowHeight)},
                events = {mouseClick = async:callback(function()
                    selected, draft = row.id, row.note; request()
                end)},
                content = ui.content(rowContent),
            }
        end
        if not snapshot or #snapshot.rows == 0 then
            children[#children + 1] = text(snapshot and 'No matching memorials.' or 'Loading memorials...', 16, 106, w - 32, 40)
        end
        local count = snapshot and (snapshot.matches == snapshot.total
            and string.format('%d memorials', snapshot.total)
            or string.format('%d of %d memorials', snapshot.matches, snapshot.total)) or ''
        children[#children + 1] = text(count,
            16, h - 54, w - 260, 30)
        children[#children + 1] = button('<', w - 220, h - 56, 32, function() page = math.max(1, page - 1); request() end)
        children[#children + 1] = text(snapshot and string.format('%d / %d', snapshot.page, snapshot.pages) or '1 / 1',
            w - 168, h - 48, 80, 30)
        children[#children + 1] = button('>', w - 68, h - 56, 32, function() page = page + 1; request() end)
        children[#children + 1] = text('Search', 16, 58, 76, 24)
    end
    local layout = {
        type = ui.TYPE.Container, template = templates.boxSolid, layer = 'Windows',
        props = {relativePosition = util.vector2(0.5, 0.5), anchor = util.vector2(0.5, 0.5)},
        content = ui.content({{type = ui.TYPE.Widget, props = {size = util.vector2(w, h)}, content = ui.content(children)}}),
    }
    if window then window.layout = layout; window:update() else window = ui.create(layout) end
end

input.registerTrigger {key = 'MemorialLedgerToggle', l10n = 'MemorialLedger', name = 'OpenLedger', description = 'OpenLedgerDescription'}
input.registerTriggerHandler('MemorialLedgerToggle', async:callback(open))
local defaults = storage.playerSection('MemorialLedgerInputDefaults')
defaults:setLifeTime(storage.LIFE_TIME.Persistent)
if not defaults:get('applied') then
    local bindings = storage.playerSection('OMWInputBindings')
    if bindings:get('MemorialLedgerToggleBinding') == nil then
        bindings:set('MemorialLedgerToggleBinding', {
            device = 'keyboard', button = input.KEY.M, type = 'trigger', key = 'MemorialLedgerToggle',
        })
    end
    -- Apply once, so clearing or changing the binding later remains respected.
    defaults:set('applied', true)
end

return {
    interfaceName = 'MemorialLedgerUI',
    interface = {version = 1, open = open},
    engineHandlers = {
        onFrame = function()
            if window then
                if I.UI.getMode() ~= 'Interface' then close()
                else
                    local screen = ui.screenSize()
                    if screen.x ~= screenWidth or screen.y ~= screenHeight then render(); request() end
                end
            elseif queuedOpen and I.UI.getMode() == nil then open() end
        end,
        onKeyPress = function(key)
            if window and (key.code == input.KEY.Escape or key.symbol == 'escape') then close() end
        end,
        onLoad = function()
            if window then window:destroy(); window = nil; I.UI.removeMode('Interface') end
            queuedOpen, selected, snapshot, draft, query, page, token = false, nil, nil, '', '', 1, 0
        end,
    },
    eventHandlers = {
        MemorialLedgerOpen = open,
        MemorialLedgerSnapshot = function(data)
            if not window or data.token ~= token then return end
            snapshot, page = data, data.page
            if selected and not data.selected then selected = nil end
            render()
        end,
    },
}
