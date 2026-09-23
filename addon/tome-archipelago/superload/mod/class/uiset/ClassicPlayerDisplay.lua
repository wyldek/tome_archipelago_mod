local _M=loadPrevious(...)
local AP=require "mod.class.Archipelago"

local old_display=_M.display
assert(type(old_display)=="function","Archipelago: Classic resource display adapter missing")
function _M:display(...)
  local actor=game and game.player
  return AP.withResourceDisplay(actor,function(...) return old_display(self,...) end,...)
end

return _M
