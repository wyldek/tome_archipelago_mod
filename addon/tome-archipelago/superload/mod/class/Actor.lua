local _M=loadPrevious(...)
local AP=require "mod.class.Archipelago"
local function pack(...)return {n=select("#",...),...}end
-- Archipelago characters may mix antimagic and arcane talent families.  ToME's
-- vanilla power-source identity flags are primarily compatibility gates: antimagic
-- talents add forbid_arcane, while spells add has_arcane_knowledge.  Suppress both
-- flags for the AP character only so learning either side cannot disable the other,
-- block equipment, alter reward generation, close campaign portals, or apply the
-- antimagic-disruption penalty.  Keep shadow counters for diagnostics without
-- exposing the vanilla restriction attributes.
local old_attr=_M.attr
if type(old_attr)=="function" then
  function _M:attr(prop,v,fix)
    if AP.isCharacter(self) and (prop=="forbid_arcane" or prop=="has_arcane_knowledge") then
      if v then
        self._ap_suppressed_power_flags=self._ap_suppressed_power_flags or {}
        if fix then self._ap_suppressed_power_flags[prop]=v
        else self._ap_suppressed_power_flags[prop]=(self._ap_suppressed_power_flags[prop] or 0)+v end
      end
      return nil
    end
    return old_attr(self,prop,v,fix)
  end
end

local old_setQuestStatus=_M.setQuestStatus
if type(old_setQuestStatus)=="function" then
  function _M:setQuestStatus(quest,status,sub,...)
    local qid=type(quest)=="table" and quest.id or quest
    local out=pack(old_setQuestStatus(self,quest,status,sub,...))
    if AP.isCharacter(self) and self.archipelago_state and type(qid)=="string" then
      AP.recordQuest(self,qid,status,sub)
    end
    return unpack(out,1,out.n)
  end
end

local old_levelup=_M.levelup
if type(old_levelup)=="function" then
  function _M:levelup(...)
    local out=pack(old_levelup(self,...))
    if AP.isCharacter(self) then
      AP.zeroPointPools(self)
      AP.recordLevel(self)
    end
    return unpack(out,1,out.n)
  end
end
local old_learn=_M.learnTalent
if type(old_learn)=="function" then
  function _M:learnTalent(tid,force,nb,...)
    if AP.isCharacter(self) and self.archipelago_state and not self._ap_applying then
      local talent=self:getTalentFromId(tid)
      local tree=talent and talent.type and talent.type[1] or ""
      local paid=talent and (talent.points or 5)>1
      local racial=tree:match("^race/") or tree:match("^undead/")
      local inscription=tree:match("^inscriptions/")
      local helper=tree:match("/other$") or (talent and talent.hide=="always")
      if (paid and not racial and not inscription and not helper) or tree:match("^uber/") then
        self.archipelago_state.blocked_native_grants=self.archipelago_state.blocked_native_grants+1
        return false
      end
    end
    return old_learn(self,tid,force,nb,...)
  end
end
-- Vanilla quests/items may unlock or improve talent categories directly.  AP
-- build categories are seed-owned, so reject native category/mastery changes
-- after AP initialization.  AP grants and prodigy/evolution side-effects run
-- under _ap_applying and therefore still pass through the native methods.
local old_learn_type=_M.learnTalentType
if type(old_learn_type)=="function" then
  function _M:learnTalentType(tt,v,...)
    if AP.isCharacter(self) and self.archipelago_state and not self._ap_applying then
      self.archipelago_state.blocked_native_categories=(self.archipelago_state.blocked_native_categories or 0)+1
      return false
    end
    return old_learn_type(self,tt,v,...)
  end
end
local old_set_mastery=_M.setTalentTypeMastery
if type(old_set_mastery)=="function" then
  function _M:setTalentTypeMastery(tt,v,...)
    if AP.isCharacter(self) and self.archipelago_state and not self._ap_applying then
      self.archipelago_state.blocked_native_mastery=(self.archipelago_state.blocked_native_mastery or 0)+1
      return false
    end
    return old_set_mastery(self,tt,v,...)
  end
end

local old_unlearn=_M.unlearnTalent
if type(old_unlearn)=="function" then
  function _M:unlearnTalent(tid,...)
    if AP.isCharacter(self) and self.archipelago_state and not self._ap_applying then
      local t=self:getTalentFromId(tid)
      if t and t.type and (self.archipelago_state.selected_trees[t.type[1]] or self.archipelago_state.bonus_tree_rules[t.type[1]] or self.archipelago_state.extra_trees[t.type[1]] or t.type[1]:match("^uber/")) then
        return false -- no respec refund of server-owned ranks
      end
    end
    return old_unlearn(self,tid,...)
  end
end
-- Direct permanent core-stat changes from vanilla content remain legal for AP
-- characters.  AP owns distributable stat-point pools and its own +5 packages,
-- not every permanent stat bonus granted by quests/items.

local old_canwear=_M.canWearObject
if type(old_canwear)=="function" then
  function _M:canWearObject(object,...)
    if not AP.isCharacter(self) or type(object)~="table" then return old_canwear(self,object,...) end
    -- Only suspend requirement metadata for this synchronous eligibility call.
    -- Restore the actual object on success AND exception. Slot/weapon structure
    -- continues through the original validation; the item is not permanently edited.
    local req=object.require
    local levelreq=object.level_requirement
    object.require=nil
    object.level_requirement=nil
    local args=pack(...)
    local ok,result=pcall(function()return pack(old_canwear(self,object,unpack(args,1,args.n)))end)
    object.require=req
    object.level_requirement=levelreq
    if not ok then error(result,0) end
    return unpack(result,1,result.n)
  end
end

local function wrap_item_method(method)
  local base=_M[method]
  if type(base)~="function" then return end
  _M[method]=function(self,object,...)
    if not AP.isCharacter(self) or type(object)~="table" then return base(self,object,...) end
    local req,levelreq=object.require,object.level_requirement
    object.require=nil;object.level_requirement=nil
    local args=pack(...)
    local ok,result=pcall(function()return pack(base(self,object,unpack(args,1,args.n)))end)
    object.require=req;object.level_requirement=levelreq
    if not ok then error(result,0) end
    return unpack(result,1,result.n)
  end
end
wrap_item_method("canUseObject")
wrap_item_method("wearObject")

return _M
