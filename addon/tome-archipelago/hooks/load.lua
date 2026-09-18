local class = require "engine.class"
local Birther = require "engine.Birther"
print("[Archipelago] hooks/load.lua loaded")
class:bindHook("ToME:load", function(self, data)
  local AP = require "mod.class.Archipelago"
  local ok, err = pcall(function()
    Birther:loadDefinition("/data-archipelago/birth.lua")
  end)
  if not ok then print("[Archipelago] Birth adapter failed: "..tostring(err)) end
  local exported, why = pcall(AP.exportCatalog)
  if not exported then print("[Archipelago] Catalog export failed: "..tostring(why)) end
end)
print("[Archipelago] Player:onBirth adapter will initialize AP characters")

-- Escort rewards are a special case: keep only direct permanent core-stat
-- increases.  Talent ranks, category unlocks/mastery, and save bonuses are
-- removed from the reward menu for AP characters rather than granted and then
-- reverted.
class:bindHook("Quest:escort:reward", function(self, data)
  local AP=require "mod.class.Archipelago"
  if not game or not game.player or not AP.isCharacter(game.player) then return end
  local function stats_only(src)
    if type(src)~="table" then return {} end
    local out={}
    if type(src.stats)=="table" then out.stats=src.stats end
    if type(src.antimagic)=="table" then
      local anti=stats_only(src.antimagic)
      if next(anti) then out.antimagic=anti end
    end
    return out
  end
  local filtered={}
  for key,reward in pairs(data.reward_types or {}) do filtered[key]=stats_only(reward) end
  data.reward_types=filtered
  return true
end)
