local _M=loadPrevious(...)
local AP=require "mod.class.Archipelago"

local old_displayResources=_M.displayResources
assert(type(old_displayResources)=="function","Archipelago: Minimalist resource display adapter missing")
function _M:displayResources(...)
  local actor=game and game.player
  return AP.withResourceDisplay(actor,function(...) return old_displayResources(self,...) end,...)
end

return _M
