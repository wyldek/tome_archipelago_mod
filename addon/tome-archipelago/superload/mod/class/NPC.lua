local _M=loadPrevious(...)
local AP=require "mod.class.Archipelago"
local function pack(...) return {n=select("#",...),...} end
local old_die=_M.die
assert(type(old_die)=="function","Archipelago: NPC:die adapter missing")

function _M:die(src,death_note,...)
  local zone=game and game.zone or nil
  local player=game and game.player or nil
  local was_dead=self.dead
  local result=pack(old_die(self,src,death_note,...))
  -- Observer only: native death, loot, XP, artifacts, and quest callbacks have
  -- already run through the original method.  AP never replaces the drop path.
  if not was_dead and self.dead and player and AP.isCharacter(player) then
    pcall(AP.recordBoss,player,self,zone)
  end
  return unpack(result,1,result.n)
end

return _M
