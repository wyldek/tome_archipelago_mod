local _M=loadPrevious(...)
local AP=require "mod.class.Archipelago"
local function pack(...) return {n=select("#",...),...} end

local old_onBirth=_M.onBirth
assert(type(old_onBirth)=="function","Archipelago: Player:onBirth adapter missing")
function _M:onBirth(birther)
  local out=pack(old_onBirth(self,birther))
  if AP.isCharacter(self) then
    local snap=AP.config()
    if not snap then
      self.archipelago_init_error="No valid client.json build contract at birth"
      print("[Archipelago] Birth initialization failed: "..self.archipelago_init_error)
    else
      local ok,err=pcall(AP.initialize,game,snap)
      if not ok then
        self.archipelago_init_error=tostring(err)
        print("[Archipelago] Birth initialization failed: "..self.archipelago_init_error)
      else
        self.archipelago_init_error=nil
        AP.zeroPointPools(self)
        AP.recordLevel(self)
        pcall(AP.publish,self)
        print("[Archipelago] Birth initialization complete")
      end
    end
  end
  return unpack(out,1,out.n)
end

return _M
