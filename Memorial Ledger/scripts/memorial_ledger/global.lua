local core = require('openmw.core')
local world = require('openmw.world')
local types = require('openmw.types')
local policy = require('scripts.memorial_ledger.policy')

local entries, pending, nextId = {}, {}, 1
local elapsed, revision = 0, 0
local requests = {}

local function change(e, status, reason)
    if e.status ~= status or e.reason ~= reason then
        e.status, e.reason = status, reason
        revision = revision + 1
    end
end

local function isNpc(actor)
    return actor:isValid() and types.NPC.objectIsInstance(actor) and not types.Player.objectIsInstance(actor)
end

local function location(cell)
    if not cell then return 'Unknown location' end
    local name = cell.displayName
    if not name or name == '' then name = cell.name end
    if not name or name == '' then name = cell.region end
    if not name or name == '' then name = 'Wilderness' end
    return name
end

local function observe(actor)
    if not isNpc(actor) or not types.Actor.isDead(actor) or actor.count == 0 then return end
    if pending[actor.id] then return end
    local record = types.NPC.record(actor)
    local e = {
        id = nextId, objectId = actor.id, recordId = actor.recordId,
        name = record.name or actor.recordId, location = location(actor.cell),
        observedAt = core.getGameTime(), status = 'Observed', reason = 'Dead NPC recorded; body left untouched',
        note = '',
    }
    nextId = nextId + 1
    entries[#entries + 1] = e
    pending[actor.id] = {actor = actor, entry = #entries}
    revision = revision + 1
end

local function process(p)
    local actor, e = p.actor, entries[p.entry]
    if not actor:isValid() then
        -- An invalid reference can just be an unloaded cell. Keep it for later observation.
        change(e, 'Unavailable', 'Body unloaded or removed elsewhere; removal not confirmed')
        return false
    end
    if actor.count == 0 then
        change(e, 'Removed', 'Body disposed of by the game, player, or another mod')
        return true
    end
    if not types.Actor.isDead(actor) then
        change(e, 'Revived', 'Actor is alive again; a later death will create a new entry')
        return true
    end
    change(e, 'Observed', 'Dead NPC recorded; body left untouched')
    return false
end

local function scan()
    for _, actor in ipairs(world.activeActors) do
        local ok, err = pcall(observe, actor)
        if not ok then print('[Memorial Ledger] Observation skipped: ' .. tostring(err)) end
    end
    for id, p in pairs(pending) do
        local ok, done = pcall(process, p)
        if not ok then
            change(entries[p.entry], 'Unavailable', 'Observation failed; body left untouched')
            if not p.failed then print('[Memorial Ledger] Observation failed: ' .. tostring(done)) end
            p.failed = true
        elseif done then pending[id] = nil end
    end
end

local function snapshot(request)
    local filtered = policy.select(entries, request.query)
    local pageSize = math.max(1, math.min(7, math.floor(tonumber(request.pageSize) or 7)))
    local pages = math.max(1, math.ceil(#filtered / pageSize))
    local page = math.max(1, math.min(pages, math.floor(tonumber(request.page) or 1)))
    local rows = {}
    for i = (page - 1) * pageSize + 1, math.min(page * pageSize, #filtered) do
        rows[#rows + 1] = policy.copyEntry(filtered[i])
    end
    local selected
    for _, e in ipairs(filtered) do
        if e.id == request.selected then selected = policy.copyEntry(e); break end
    end
    return {rows = rows, selected = selected, total = #entries, matches = #filtered,
        page = page, pages = pages, revision = revision, token = request.token}
end

local function request(data)
    if not data or not data.player or not data.player:isValid()
        or not types.Player.objectIsInstance(data.player) then return end
    requests[#requests + 1] = data
end

local function edit(data)
    if not data or type(data.id) ~= 'number' then return end
    for _, e in ipairs(entries) do
        if e.id == data.id then
            if type(data.note) == 'string' then e.note = policy.truncate(data.note, 1000) end
            revision = revision + 1
            return
        end
    end
end

return {
    interfaceName = 'MemorialLedger',
    interface = {
        version = 1,
        open = function()
            for _, player in ipairs(world.players) do player:sendEvent('MemorialLedgerOpen', {}) end
        end,
    },
    engineHandlers = {
        onActorActive = function(actor) pcall(observe, actor) end,
        onUpdate = function(dt)
            elapsed = elapsed + dt
            if elapsed >= 5 then elapsed = 0; scan() end
            -- UI requests must also work while the Interface mode pauses simulation.
            for _, data in ipairs(requests) do
                if data.player:isValid() then data.player:sendEvent('MemorialLedgerSnapshot', snapshot(data)) end
            end
            requests = {}
        end,
        onSave = function()
            return {version = 2, entries = entries, pending = pending, nextId = nextId}
        end,
        onLoad = function(data)
            data = data or {}
            entries, pending, nextId = data.entries or {}, data.pending or {}, data.nextId or 1
            if (data.version or 1) < 2 then
                for _, e in ipairs(entries) do
                    e.keep = nil
                    if e.status == 'Cleaned' then
                        e.status, e.reason = 'Removed', 'Removal recorded by earlier mod version'
                    elseif e.status == 'Removed elsewhere' then e.status = 'Removed'
                    elseif e.status ~= 'Revived' and e.status ~= 'Unavailable' then
                        e.status, e.reason = 'Observed', 'Dead NPC recorded; body left untouched'
                    end
                end
                for _, p in pairs(pending) do p.removing, p.requestedAt = nil, nil end
            end
            elapsed, requests, revision = 0, {}, revision + 1
        end,
    },
    eventHandlers = {
        MemorialLedgerRequest = request, MemorialLedgerEdit = edit,
        MemorialLedgerOpenRequest = function()
            for _, player in ipairs(world.players) do player:sendEvent('MemorialLedgerOpen', {}) end
        end,
    },
}
