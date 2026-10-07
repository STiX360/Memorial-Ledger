local M = {}

function M.truncate(value, limit)
    if #value <= limit then return value end
    while limit > 0 and value:byte(limit + 1) >= 128 and value:byte(limit + 1) < 192 do
        limit = limit - 1
    end
    return value:sub(1, limit)
end

function M.copyEntry(entry)
    local copy = {}
    for key, value in pairs(entry) do copy[key] = value end
    -- Older saves stored exterior grid coordinates in the displayed place name.
    if type(copy.location) == 'string' then
        copy.location = copy.location:gsub(' %[%-?%d+, %-?%d+%]$', '')
    end
    return copy
end

function M.select(entries, query)
    query = tostring(query or ''):lower():match('^%s*(.-)%s*$')
    local found = {}
    for i = #entries, 1, -1 do
        local e = entries[i]
        if (e.name or ''):lower():find(query, 1, true) then found[#found + 1] = e end
    end
    return found
end

function M.date(seconds)
    local days = math.floor((seconds or 0) / 86400)
    local hour = math.floor((seconds or 0) / 3600) % 24
    return string.format('Day %d, %02d:00', days + 1, hour)
end

return M
