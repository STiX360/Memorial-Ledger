now = 0
settings = {enabled=true,delayHours=24,excludedRecords=''}
local vectorMeta = {}
function vector3(x,y,z)
    return setmetatable({x=x,y=y,z=z}, vectorMeta)
end
vectorMeta.__sub = function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end
vectorMeta.__index = {length=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end}
home = {id='home',name='Balmora',displayName='Balmora',isExterior=false}
remote = {id='remote',name='Other interior',isExterior=false}
exterior = {id='0,0',name='',region='Bitter Coast',isExterior=true,gridX=0,gridY=0,worldSpaceId='default'}
exterior2 = {id='1,0',name='',region='Bitter Coast',isExterior=true,gridX=1,gridY=0,worldSpaceId='default'}
function corpse(recordId,id)
    local a = {id=id or recordId,recordId=recordId,cell=home,position=vector3(0,0,0),valid=true,
        kind='npc',count=1,dead=true,finished=true,removes=0,events={},
        record={name=recordId,isPersistent=false,isEssential=false,isRespawning=false}}
    function a:isValid() return self.valid end
    function a:remove() self.removes = self.removes + 1 end
    function a:sendEvent(name,data) self.events[#self.events+1] = {name=name,data=data} end
    a.inventory = {resolved=true,items={}}
    function a.inventory:isResolved() return self.resolved end
    function a.inventory:getAll() return self.items end
    return a
end
player = corpse('player'); player.kind = 'player'; player.dead = false
world = {players={player},activeActors={}}
types = {
    NPC = {objectIsInstance=function(a) return a.kind=='npc' or a.kind=='player' end,record=function(a) return a.record end},
    Player = {objectIsInstance=function(a) return a.kind=='player' end},
    Actor = {isDead=function(a) return a.dead end,isDeathFinished=function(a) return a.finished end,
        inventory=function(a) return a.inventory end},
}
globalEvents = {}
package.preload['openmw.core'] = function() return {getGameTime=function() return now end,
    l10n=function() return function(key) return translations and translations[key] or key end end,
    sendGlobalEvent=function(name,data) globalEvents[#globalEvents+1]={name=name,data=data} end} end
package.preload['openmw.world'] = function() return world end
package.preload['openmw.types'] = function() return types end
playerSections = {}
sectionSubscribers = {}
package.preload['openmw.storage'] = function() return {
    LIFE_TIME = {Persistent=0},
    playerSection = function(name)
        playerSections[name] = playerSections[name] or {}
        return {
            get = function(_,key) return playerSections[name][key] end,
            set = function(_,key,value)
                playerSections[name][key] = value
                for _, callback in ipairs(sectionSubscribers[name] or {}) do callback(name,key) end
            end,
            subscribe = function(_,callback)
                sectionSubscribers[name] = sectionSubscribers[name] or {}
                table.insert(sectionSubscribers[name],callback)
            end,
            setLifeTime = function() end,
        }
    end,
    globalSection=function() return {get=function(_,key) return settings[key] end} end,
} end
I = {Settings={registerGroup=function() end,registerPage=function() end,registerRenderer=function() end}}
package.preload['openmw.interfaces'] = function() return I end
