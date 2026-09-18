local Birther = require "engine.Birther"
local AP = require "mod.class.Archipelago"
local function copy(value,seen)
  if type(value)~="table" then return value end
  seen=seen or {}
  if seen[value] then return seen[value] end
  local out={}; seen[value]=out
  for k,v in pairs(value) do out[copy(k,seen)]=copy(v,seen) end
  return setmetatable(out,getmetatable(value))
end
local function find_adventurer(value,seen,depth)
  if type(value)~="table" or depth>8 then return nil end
  seen=seen or {}
  if seen[value] then return nil end
  seen[value]=true
  if value.name=="Adventurer" and (value.type=="subclass" or type(value.talents_types)=="table") then return value end
  for _,v in pairs(value) do
    local found=find_adventurer(v,seen,depth+1)
    if found then return found end
  end
end
local base=find_adventurer(Birther.birth_descriptor_def or Birther,{},0)
assert(base,"Native Adventurer descriptor was not found; run the source audit before using this version")
local descriptor=copy(base)
descriptor.type="subclass"
descriptor.name="Archipelago Adventurer"
descriptor.desc={"A character assembled by an Archipelago seed.",
 "Class and generic categories are selected by the YAML settings.",
 "Talent ranks, specific stats, and specific prodigies arrive through the bridge.",
 "Fresh offline test saves only. Connect the bridge before starting."}
descriptor.locked=function() return AP.config()~=nil end
descriptor.locked_desc="Connect the ToME Archipelago bridge to a generated slot first."
descriptor.talents_types=function(birth)
  local snap=AP.config()
  local out={}
  if snap and snap.contract then
    for _,key in ipairs(snap.contract.random_trees or {}) do
      if type(key)=="string" then out[key]={true,0} end
    end
    for _,key in ipairs(snap.contract.mandatory_trees or {}) do
      if type(key)=="string" then out[key]={true,0} end
    end
    for _,key in ipairs(snap.contract.support_trees or {}) do
      if type(key)=="string" then out[key]={true,0} end
    end
  end
  return out
end
descriptor.talents={}
-- Native Adventurer starts with discretionary class/generic/category points.
-- AP characters must not inherit those currencies.
descriptor.copy_add={}
descriptor.copy=descriptor.copy or {}
descriptor.copy.archipelago_character=true
descriptor.copy.no_birth_levelup=true
descriptor.copy.unused_talents=0
descriptor.copy.unused_generics=0
descriptor.copy.unused_stats=0
descriptor.copy.unused_talents_types=0
descriptor.copy.unused_prodigies=0
-- Preserve native Adventurer's gear/resource/inscription resolvers, but not
-- its all-categories selection or account unlock requirement.
newBirthDescriptor{
  type="class",name="Archipelago",desc={"Archipelago multiworld characters."},
  descriptor_choices={subclass={["Archipelago Adventurer"]="allow",["__ALL__"]="disallow"}},
}
newBirthDescriptor(descriptor)

-- Maj'Eyal explicitly disallows unknown top-level class families via
-- descriptor_choices.class.__ALL__ = "disallow".  Whitelist our class
-- family so the character creator can actually display it.
local maj_eyal = Birther:getBirthDescriptor("world", "Maj'Eyal")
assert(maj_eyal, "Maj'Eyal world descriptor was not found")
maj_eyal.descriptor_choices = maj_eyal.descriptor_choices or {}
maj_eyal.descriptor_choices.class = maj_eyal.descriptor_choices.class or {}
maj_eyal.descriptor_choices.class["Archipelago"] = "allow"
print("[Archipelago] Enabled Archipelago class for Maj'Eyal character creation")
