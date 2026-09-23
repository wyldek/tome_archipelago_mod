local _M=loadPrevious(...)
local AP=require "mod.class.Archipelago"
local Dialog=require "engine.ui.Dialog"
local Object=require "mod.class.Object"
local function pack(...) return {n=select("#",...),...} end

local function current_zone_key()
  local z=game and game.zone
  return z and (z.short_name or z.name) or nil
end

local function clearParcels(store)
  local inven=store:getInven("INVEN") or {}
  for i=#inven,1,-1 do
    if inven[i] and inven[i].archipelago_parcel then table.remove(inven,i) end
  end
end

local function parcelObject(loc,actor)
  local p=loc.trigger
  local scout=assert(loc.scout,"Archipelago shop item missing LocationScout data")
  local own=actor.archipelago_state and scout.player==actor.archipelago_state.identity.slot
  local recipient=own and "you" or scout.player_name
  local label=scout.item_name
  if not own then label=("%s (%s)"):format(label,scout.player_name) end
  local o=Object.new{
    type="misc", subtype="misc", name=label,
    display="!", color=colors.LIGHT_BLUE, encumber=0, identified=true,
    desc=("Archipelago item for %s. Purchasing it checks '%s'. Progression items are never placed in paid shop checks.\n\nPrice: %d gold."):format(recipient,loc.name,p.price),
  }
  o.archipelago_parcel=true
  o.archipelago_location=loc.code
  o.archipelago_price=p.price
  o.archipelago_parcel_index=p.parcel
  o.archipelago_item_name=scout.item_name
  o.archipelago_recipient=scout.player_name
  o.archipelago_zone=p.zone
  return o
end

local old_interact=_M.interact
assert(type(old_interact)=="function","Archipelago: Store:interact adapter missing")
function _M:interact(who,name,...)
  if AP.isCharacter(who) and who.archipelago_state then
    clearParcels(self)
    local zone=current_zone_key()
    if zone then
      local inven=self:getInven("INVEN")
      for _,loc in ipairs(AP.shopParcels(who,zone,name,self.define_as)) do
        self:addObject(inven,parcelObject(loc,who))
      end
      self:sortInven(inven)
    end
  end
  return old_interact(self,who,name,...)
end

local old_getObjectPrice=_M.getObjectPrice
if type(old_getObjectPrice)=="function" then
  function _M:getObjectPrice(o,what,...)
    if o and o.archipelago_parcel then
      if what=="buy" then return o.archipelago_price end
      return 0
    end
    return old_getObjectPrice(self,o,what,...)
  end
end

local old_doBuy=_M.doBuy
assert(type(old_doBuy)=="function","Archipelago: Store:doBuy adapter missing")
function _M:doBuy(who,o,item,nb,store_dialog,...)
  if not (AP.isCharacter(who) and who.archipelago_state and o and o.archipelago_parcel) then
    return old_doBuy(self,who,o,item,nb,store_dialog,...)
  end
  local price=o.archipelago_price
  if not AP.shopPurchaseAvailable(who,o.archipelago_location) then
    Dialog:simplePopup("Archipelago item unavailable","This item has already been checked or is no longer available.")
    return
  end
  if (who.money or 0)<price then
    Dialog:simplePopup("Not enough gold","You do not have enough gold!")
    return
  end
  Dialog:yesnoPopup("Buy Archipelago Item",
    ("Buy %s for %d gold?"):format(o:getName{do_color=true,no_count=true},price),
    function(ok) if ok then
      local inven=self:getInven("INVEN") or {}
      local parcel_index
      for i,entry in ipairs(inven) do if entry==o then parcel_index=i break end end
      if not parcel_index or current_zone_key()~=o.archipelago_zone or
        not AP.shopPurchaseAvailable(who,o.archipelago_location) then
        Dialog:simplePopup("Archipelago item unavailable","This item has already been checked or is no longer available.")
        if store_dialog then store_dialog:updateStore() end
        return
      end
      if (who.money or 0)<price then
        Dialog:simplePopup("Not enough gold","You do not have enough gold!")
        return
      end
      who:incMoney(-price)
      if not AP.recordShopPurchase(who,o.archipelago_location) then
        who:incMoney(price)
        return
      end
      table.remove(inven,parcel_index)
      game.log("#LIGHT_BLUE#[Archipelago]#LAST# Purchased %s for %d gold.",o.archipelago_item_name,price)
      pcall(AP.publish,who)
      if store_dialog then store_dialog:updateStore() end
    end end,
    "Buy","Cancel")
end

return _M
