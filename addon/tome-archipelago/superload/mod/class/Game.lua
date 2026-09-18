local _M=loadPrevious(...)
local AP=require "mod.class.Archipelago"
local function pack(...)return {n=select("#",...),...}end
-- Prefer the render loop so incoming items can be processed while ToME is
-- waiting for player input. This does not advance game turns.
local method=type(_M.display)=="function" and "display" or "tick"
local base=_M[method]
assert(type(base)=="function","Archipelago: no compatible Game display/tick adapter")
_M[method]=function(self,...)
  local out=pack(base(self,...))
  AP.poll(self)
  return unpack(out,1,out.n)
end
return _M
