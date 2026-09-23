-- All network communication belongs to the external Python bridge.
-- This module only reads/writes bounded JSON through the game's filesystem.
local JSON = require "mod.class.ArchipelagoJSON"
local M = {root="/archipelago", tick_count=0, last_error=nil}
local POINT_FIELDS={"unused_talents","unused_generics","unused_stats","unused_talents_types","unused_prodigies"}
local STAT_CONSTANTS={str="STAT_STR",dex="STAT_DEX",con="STAT_CON",mag="STAT_MAG",wil="STAT_WIL",cun="STAT_CUN"}
local function pack(...) return {n=select("#",...),...} end
local function message(g, s)
  print("[Archipelago] "..tostring(s))
  if g and g.log then g.log("#LIGHT_BLUE#[Archipelago]#LAST# %s",tostring(s)) end
end
local function whole(n,min,max)
  return type(n)=="number" and n==math.floor(n) and n>=min and n<=max
end
local function read(name)
  local ok,value=pcall(function()
    local f=fs.open(M.root.."/"..name,"r")
    if not f then return nil end
    local good,data=pcall(function() return f:read("*a") end)
    if not good then
      f:close(); f=fs.open(M.root.."/"..name,"r")
      data=f:read(8*1024*1024+1)
    end
    f:close()
    if not data or #data>8*1024*1024 then return nil end
    return JSON.decode(data)
  end)
  if ok then return value end
  return nil
end
local function write(name,data)
  fs.mkdir(M.root)
  local f=assert(fs.open(M.root.."/"..name,"w"),"Cannot write AP mailbox")
  f:write(JSON.encode(data).."\n")
  f:close()
end
M.read=read
M.write=write

function M.ensureMailboxMarker()
  write("mailbox-info.json",{
    schema=2,
    game="Tales of Maj'Eyal",
    addon="tome-archipelago",
    virtual_root=M.root,
  })
end

function M.isCharacter(actor)
  if game and game.player and actor~=game.player then return false end
  return actor and (actor.archipelago_character or
    (actor.descriptor and actor.descriptor.subclass=="Archipelago Adventurer"))
end

function M.config()
  local snap=read("client.json")
  if type(snap)~="table" or snap.protocol~=1 or snap.complete~=true or type(snap.contract)~="table" then return nil end
  local c=snap.contract
  if c.schema~=3 or c.game~="Tales of Maj'Eyal" or type(c.contract_hash)~="string" or #c.contract_hash~=64 then return nil end
  if type(snap.identity)~="table" or snap.identity.contract_hash~=c.contract_hash then return nil end
  if not whole(snap.identity.slot,1,2147483647) or not whole(snap.identity.team,0,2147483647) then return nil end
  if type(c.locations)~="table" or type(c.items)~="table" or type(c.trees)~="table" then return nil end
  if type(snap.receipts)~="table" or #snap.receipts>100000 then return nil end
  if snap.scouted_locations~=nil then
    if type(snap.scouted_locations)~="table" or #snap.scouted_locations>#c.locations then return nil end
    local seen={}
    for _,scout in ipairs(snap.scouted_locations) do
      if type(scout)~="table" or not whole(scout.location,1,9007199254740991)
        or not whole(scout.item,1,9007199254740991) or not whole(scout.player,1,2147483647)
        or not whole(scout.flags or 0,0,255) or type(scout.item_name)~="string"
        or #scout.item_name<1 or #scout.item_name>512 or type(scout.player_name)~="string"
        or #scout.player_name<1 or #scout.player_name>256 or seen[tostring(scout.location)] then return nil end
      seen[tostring(scout.location)]=true
    end
  end
  return snap
end

function M.identityMatches(a,b)
  return a and b and a.seed_name==b.seed_name and a.team==b.team and a.slot==b.slot and a.contract_hash==b.contract_hash
end

function M.withGrant(actor,fn,...)
  local before={}
  for _,key in ipairs(POINT_FIELDS) do before[key]=actor[key] or 0 end
  local old=actor._ap_applying
  actor._ap_applying=true
  local args=pack(...)
  local ok,result=pcall(function() return pack(fn(unpack(args,1,args.n))) end)
  actor._ap_applying=old
  for _,key in ipairs(POINT_FIELDS) do actor[key]=before[key] end
  if not ok then error(result,0) end
  return unpack(result,1,result.n)
end

function M.zeroPointPools(actor)
  if not M.isCharacter(actor) then return end
  for _,key in ipairs(POINT_FIELDS) do actor[key]=0 end
end

-- Runtime metadata export ----------------------------------------------------
function M.exportCatalog()
  local T=require "engine.interface.ActorTalents"
  local R=require "engine.interface.ActorResource"
  local Birther=require "engine.Birther"
  local trees,talents=JSON.array(),JSON.array()
  local members,seen,tree_resources={},{},{}
  local resource_defs=JSON.array()
  for _,r in ipairs(R.resources_def or {}) do
    resource_defs[#resource_defs+1]={
      short_name=r.short_name,name=r.name,
      talent=type(r.talent)=="string" and r.talent or JSON.null,
      regen_prop=r.regen_prop or JSON.null,
      min=r.min,max=r.max,
    }
  end

  local function talent_resources(t)
    local out,found=JSON.array(),{}
    for _,r in ipairs(R.resources_def or {}) do
      local k=r.short_name
      if rawget(t,k)~=nil or rawget(t,"sustain_"..k)~=nil or rawget(t,"drain_"..k)~=nil then
        if not found[k] then found[k]=true; out[#out+1]=k end
      end
    end
    table.sort(out)
    return out
  end

  for id,t in pairs(T.talents_def or {}) do
    if type(t)=="table" and type(t.type)=="table" and type(t.name)=="string" then
      local symbol=type(t.id)=="string" and t.id or (type(id)=="string" and id or nil)
      if symbol and symbol:match("^T_[A-Z0-9_]+$") and not seen[symbol] then
        local tree=t.type[1]
        local cap=type(t.points)=="number" and t.points or 1
        if type(tree)=="string" and whole(cap,1,20) then
          seen[symbol]=true
          local resources=talent_resources(t)
          local tactical=t.tactical
          local starter=t.mode=="activated" and t.hide~="always" and type(tactical)=="table" and
            (tactical.ATTACK~=nil or tactical.ATTACKAREA~=nil)
          talents[#talents+1]={
            symbol=symbol,name=t.name,cap=cap,prodigy=not not t.uber,
            mode=t.mode or "activated",hide=t.hide or JSON.null,starter=not not starter,
            resources=resources,
          }
          members[tree]=members[tree] or {}
          members[tree][#members[tree]+1]={symbol=symbol,order=t.type[2] or 0}
          tree_resources[tree]=tree_resources[tree] or {}
          for _,r in ipairs(resources) do tree_resources[tree][r]=true end
        end
      end
    end
  end

  for key,tt in pairs(T.talents_types_def or {}) do
    if type(key)=="string" and type(tt)=="table" and members[key] then
      table.sort(members[key],function(a,b) return a.order==b.order and a.symbol<b.symbol or a.order<b.order end)
      local symbols,res=JSON.array(),JSON.array()
      for _,m in ipairs(members[key]) do symbols[#symbols+1]=m.symbol end
      for r in pairs(tree_resources[key] or {}) do res[#res+1]=r end
      table.sort(res)
      trees[#trees+1]={
        key=key,name=type(tt.name)=="string" and tt.name or key,
        generic=not not tt.generic,symbols=symbols,resources=res,
        allow_random=not not tt.allow_random,
        source=type(tt.source)=="string" and tt.source or "@vanilla@",
      }
    end
  end

  local player_set={}
  local subclasses=Birther.birth_descriptor_def and Birther.birth_descriptor_def.subclass or {}
  for _,d in ipairs(subclasses) do
    if type(d)=="table" and d.name~="Adventurer" and d.name~="Wanderer" and d.name~="Archipelago Adventurer" then
      if type(d.talents_types)=="table" then
        for key in pairs(d.talents_types) do if members[key] then player_set[key]=true end end
      end
      if type(d.unlockable_talents_types)=="table" then
        for key in pairs(d.unlockable_talents_types) do if members[key] then player_set[key]=true end end
      end
    end
  end
  local player_trees=JSON.array()
  for key in pairs(player_set) do player_trees[#player_trees+1]=key end
  table.sort(player_trees)

  if #talents==0 or #trees==0 or #player_trees==0 then
    error("Runtime registry incomplete ("..#talents.." talents, "..#trees.." trees, "..#player_trees.." player trees); export deferred")
  end
  table.sort(trees,function(a,b)return a.key<b.key end)
  table.sort(talents,function(a,b)return a.symbol<b.symbol end)
  write("runtime-export.json",{
    schema=2,game_version="1.7.6",trees=trees,talents=talents,
    player_trees=player_trees,resources=resource_defs,
  })
  print("[Archipelago] Runtime metadata exported "..#talents.." talents in "..#trees.." trees; "..#player_trees.." player trees under "..M.root.."/runtime-export.json")
  return #talents,#trees,#player_trees
end

-- Contract/runtime validation ------------------------------------------------
local function runtimeTalent(actor,item)
  local tid=actor[item.symbol]
  assert(type(tid)=="string" and tid:match("^T_[A-Z0-9_]+$"),
    "Unavailable talent constant "..tostring(item.symbol).."; check installed content")
  local t=actor:getTalentFromId(tid)
  assert(t and t.type,"Unavailable talent definition "..tostring(item.symbol))
  if item.kind=="talent" then
    assert(t.type[1]==item.tree,"Talent/category mismatch for "..item.symbol)
    assert((t.points or 1)==item.cap,"Talent cap differs from exported catalog for "..item.symbol)
  end
  return t,tid
end

local function validate_runtime(actor,c)
  assert(c.schema==3 and c.game_version=="1.7.6","Catalog does not target the supported ToME version")
  assert(actor.learnTalent and actor.getTalentLevelRaw and actor.learnTalentType and actor.knowTalentType and actor.incStat,"Missing required engine adapters")
  assert(type(actor.stats)=="table","Unexpected ActorStats representation")
  local ids,defs,item_keys,locations,tree_defs={},{},{},{},{}
  for _,tree in ipairs(c.trees) do
    assert(type(tree.key)=="string" and not tree_defs[tree.key],"Duplicate/invalid selected tree")
    tree_defs[tree.key]=tree
  end
  local required={}
  for _,key in ipairs(c.build_item_keys or {}) do required[key]=true end
  for _,key in ipairs(c.prodigies or {}) do required[key]=true end
  for _,item in ipairs(c.items) do
    assert(whole(item.code,1,2147483647) and not ids[item.code],"Duplicate/invalid item ID")
    assert(type(item.key)=="string" and not item_keys[item.key],"Duplicate/invalid item key")
    ids[item.code]=true; defs[tostring(item.code)]=item; item_keys[item.key]=item
    if item.kind=="talent" or item.kind=="prodigy" then
      assert(type(item.symbol)=="string" and item.symbol:match("^T_[A-Z0-9_]+$"),"Invalid talent constant")
      -- The catalog lists all possible items, but only this build's content
      -- is mandatory at birth. Admin deliveries are validated when received.
      if required[item.key] or (item.kind=="talent" and tree_defs[item.tree]) then
        runtimeTalent(actor,item)
      end
    elseif item.kind=="stat" then
      assert(STAT_CONSTANTS[item.stat] and item.amount==5,"Invalid stat package")
    elseif item.kind~="vitality" then error("Unknown item kind") end
  end
  for _,loc in ipairs(c.locations) do
    assert(whole(loc.code,1,2147483647) and not locations[tostring(loc.code)],"Duplicate/invalid location")
    assert(loc.event=="level" or loc.event=="boss" or loc.event=="zone" or loc.event=="quest" or loc.event=="shop" or loc.event=="victory","Invalid location event")
    if loc.event=="level" then assert(whole(loc.level,2,50),"Invalid level milestone") end
    if loc.event=="shop" then
      assert(type(loc.trigger)=="table" and type(loc.trigger.zone)=="string" and type(loc.trigger.shop)=="string", "Invalid shop location")
      assert(whole(loc.trigger.parcel,1,3) and whole(loc.trigger.price,1,1000000), "Invalid shop parcel")
    end
    locations[tostring(loc.code)]=loc
  end
  assert(#c.locations==c.shuffled_count,"Location/item budget mismatch")
  return defs,item_keys,locations,tree_defs
end

local function array_set(values)
  local out={}
  for _,v in ipairs(values or {}) do if type(v)=="string" then out[v]=true end end
  return out
end

local RESOURCE_REGEN={
  stamina=1,mana=1,vim=0.5,positive=0.5,negative=0.5,hate=0.25,
  psi=0.5,feedback=0.5,steam=1,soul=0.25,equilibrium=-0.5,
}

local function enableResource(actor,s,short)
  -- Saved per-resource initialization, shared by every category using the pool.
  -- Reconciliation must never refill resources or undo temporary regen effects.
  if s.resources_initialized[short] then return end
  local R=require "engine.interface.ActorResource"
  local r=R.resources_def and R.resources_def[short]
  assert(r,"Unavailable resource "..tostring(short))
  if type(r.talent)=="string" and actor:getTalentLevelRaw(r.talent)<=0 then
    M.withGrant(actor,function() actor:learnTalent(r.talent,true,1) end)
  end
  if r.regen_prop and type(actor[r.regen_prop])=="number" then
    local floor=RESOURCE_REGEN[short]
    if floor then
      if floor>=0 then actor[r.regen_prop]=math.max(actor[r.regen_prop],floor)
      else actor[r.regen_prop]=math.min(actor[r.regen_prop],floor) end
    end
  end
  local current=actor[short]
  local mx=actor["max_"..short]
  local mn=actor["min_"..short]
  if type(current)~="number" then actor[short]=type(mn)=="number" and mn or 0 end
  if type(mx)=="number" and mx>0 and short~="equilibrium" and short~="paradox" then
    actor[short]=math.max(actor[short],math.min(mx,50))
  end
  s.resources_initialized[short]=true
end

local function migrateResourceState(actor,s)
  if s.resources_initialized then return end
  s.resources_initialized={}
  -- Old schema-3 saves already had their active pools initialized. Mark them
  -- without changing current values, maxima, regeneration, or receipt cursors.
  for key,tree in pairs(s.tree_defs or {}) do
    if s.selected_trees[key] or s.extra_trees[key] or actor:knowTalentType(key) then
      for _,short in ipairs(tree.resources or {}) do s.resources_initialized[short]=true end
    end
  end
end

-- Baseline utility talents ----------------------------------------------------
-- These are native one-rank infrastructure, not AP progression items.  ToME
-- normally grants Shoot/Reload opportunistically when an archery talent is
-- learned.  A random AP build may need to equip a ranged weapon before any
-- archery rank has arrived, so every AP character gets both utilities up front.
-- Attack is already guaranteed by mod.class.Actor itself; other hidden helpers
-- (resource pools, Empty Hand, stances, Spacetime Tuning, etc.) remain native
-- conditional plumbing and are granted when their corresponding mechanics apply.
local BASELINE_UTILITY_TALENTS={"T_SHOOT","T_RELOAD"}
local function enableBaselineUtilities(actor)
  M.withGrant(actor,function()
    for _,symbol in ipairs(BASELINE_UTILITY_TALENTS) do
      local tid=actor[symbol]
      if type(tid)=="string" and actor:getTalentLevelRaw(tid)<=0 then
        actor:learnTalent(tid,true,1)
      end
    end
  end)
  -- Hidden Shoot is normally bound as the ranged left-click action by ranged
  -- classes.  AP Adventurers are class-agnostic, so establish the same default.
  if actor.T_SHOOT and not actor.auto_shoot_talent then actor.auto_shoot_talent=actor.T_SHOOT end
end

local TREE_ITEM_INDEX=setmetatable({}, {__mode="k"})
local function itemsForTree(s,tree_key)
  local index=TREE_ITEM_INDEX[s]
  if not index then
    index={}
    for _,item in pairs(s.item_keys) do
      if item.kind=="talent" then
        index[item.tree]=index[item.tree] or {}
        table.insert(index[item.tree],item)
      end
    end
    for _,items in pairs(index) do
      table.sort(items,function(a,b) return a.symbol<b.symbol end)
    end
    TREE_ITEM_INDEX[s]=index
  end
  return index[tree_key] or {}
end

local function resolveTreeDefinition(actor,s,tree_key)
  if s.tree_defs[tree_key] then return s.tree_defs[tree_key] end
  -- Old and new contracts list out-of-build ITEMS, not all TREE metadata.
  -- Reconstruct an admin category from the installed registry and catalog;
  -- validate every member before learning the category or changing resources.
  local T=require "engine.interface.ActorTalents"
  local R=require "engine.interface.ActorResource"
  local native=T.talents_types_def and T.talents_types_def[tree_key]
  assert(type(native)=="table","Unavailable admin category "..tostring(tree_key))
  local items=itemsForTree(s,tree_key)
  assert(#items>0,"Admin category is absent from the seed catalog: "..tree_key)
  local symbols,resources,seen=JSON.array(),JSON.array(),{}
  for _,item in ipairs(items) do
    local t=runtimeTalent(actor,item)
    symbols[#symbols+1]=item.symbol
    for _,r in ipairs(R.resources_def or {}) do
      local short=r.short_name
      if rawget(t,short)~=nil or rawget(t,"sustain_"..short)~=nil or rawget(t,"drain_"..short)~=nil then
        if not seen[short] then seen[short]=true; resources[#resources+1]=short end
      end
    end
  end
  table.sort(resources)
  local tree={key=tree_key,name=native.name or tree_key,
    kind=native.generic and "generic" or "class",symbols=symbols,resources=resources}
  s.tree_defs[tree_key]=tree
  return tree
end

local function enableTree(actor,s,tree_key)
  local tree=resolveTreeDefinition(actor,s,tree_key)
  local known=actor:knowTalentType(tree_key)
  M.withGrant(actor,function()
    if not known then actor:learnTalentType(tree_key,true) end
    actor.talents_types_mastery=actor.talents_types_mastery or {}
    -- Preserve mastery changes that are themselves part of a prodigy effect.
    -- AP only supplies the category and its ranks; it does not erase native
    -- mastery bonuses such as Tricks of the Trade.
    if not known or type(actor.talents_types_mastery[tree_key])~="number" then
      actor.talents_types_mastery[tree_key]=1.0
    end
  end)
  for _,r in ipairs(tree.resources or {}) do enableResource(actor,s,r) end
end

-- LocationScout metadata -----------------------------------------------------
local function scout_map(snap,locations)
  local out={}
  for _,scout in ipairs(snap.scouted_locations or {}) do
    local key=tostring(scout.location)
    local loc=locations[key]
    if loc and loc.event=="shop" then out[key]=scout end
  end
  return out
end

-- Character initialization ---------------------------------------------------
function M.initialize(g,snap)
  local actor=g.player
  if not M.isCharacter(actor) or actor.archipelago_state then return end
  local c=snap.contract
  local defs,item_keys,locs,tree_defs=validate_runtime(actor,c)
  local base_selected=array_set(c.random_trees)
  for _,tree in ipairs(c.mandatory_trees or {}) do base_selected[tree]=true end
  for _,tree in ipairs(c.support_trees or {}) do base_selected[tree]=true end
  local bonus_tree_rules={}
  for item_key,rule in pairs(c.prodigy_bonus or {}) do
    for _,tree in ipairs(rule.trees or {}) do
      bonus_tree_rules[tree]=bonus_tree_rules[tree] or {}
      bonus_tree_rules[tree][#bonus_tree_rules[tree]+1]={item_key=item_key,unlock_mode=rule.unlock_mode or "immediate"}
    end
  end

  actor.archipelago_character=true
  actor.forbid_arcane=nil
  actor.has_arcane_knowledge=nil
  M.withGrant(actor,function()
    local function native_helper(tree)
      return tree:match("^base/") or tree:match("^race/") or tree:match("^undead/") or tree:match("^inscriptions/") or tree:match("/other$")
    end
    local remove={}
    for tid in pairs(actor.talents or {}) do
      local t=actor:getTalentFromId(tid)
      if t and t.type and not native_helper(t.type[1]) and (t.points or 5)>1 then remove[#remove+1]=tid end
    end
    for _,tid in ipairs(remove) do
      local count=actor:getTalentLevelRaw(tid)
      for n=1,count do
        local before=actor:getTalentLevelRaw(tid)
        actor:unlearnTalent(tid)
        assert(actor:getTalentLevelRaw(tid)<before,"Could not remove native birth talent before AP binding")
      end
    end
    actor.talents_types=actor.talents_types or {}
    actor.talents_types_mastery=actor.talents_types_mastery or {}
    for tree in pairs(actor.talents_types) do
      if not base_selected[tree] and not native_helper(tree) then
        actor.talents_types[tree]=nil; actor.talents_types_mastery[tree]=nil
      end
    end
  end)

  actor.archipelago_state={
    schema=3,identity=snap.identity,contract=c,items=defs,item_keys=item_keys,
    locations=locs,tree_defs=tree_defs,selected_trees=base_selected,
    bonus_tree_rules=bonus_tree_rules,prodigy_bonus=c.prodigy_bonus or {},
    prodigy_received={},extra_trees={},pending={},resources_initialized={},
    applied_count=0,received_ids={},checks={},revision=0,goal=false,
    scouts=scout_map(snap,locs),
    grants={},blocked_native_grants=0,blocked_native_categories=0,blocked_native_mastery=0,
  }
  local s=actor.archipelago_state
  enableBaselineUtilities(actor)
  for tree in pairs(base_selected) do enableTree(actor,s,tree) end
  M.withGrant(actor,function()
    for stat,const in pairs(STAT_CONSTANTS) do
      local id=assert(actor[const],"Missing stat constant "..const)
      assert(type(actor.stats[id])=="number","Missing raw stat slot")
      actor:incStat(id,10-actor.stats[id])
    end
  end)
  for _,code in ipairs(snap.checked_locations or {}) do
    if locs[tostring(code)] then s.checks[tostring(code)]=true end
  end
  M.zeroPointPools(actor)
  message(g,"Bound to "..snap.identity.seed_name..", slot "..snap.identity.slot..". "..#c.trees.." total build trees; "..#c.locations.." checks.")
end

local function applyTalentRank(actor,item)
  local _,tid=runtimeTalent(actor,item)
  local before=actor:getTalentLevelRaw(tid)
  if before<item.cap then
    M.withGrant(actor,function() actor:learnTalent(tid,true,1) end)
    assert(actor:getTalentLevelRaw(tid)==before+1,"Forced talent grant did not add exactly one raw rank")
  end
end

local function targetOwnedRank(s,item)
  local granted=s.grants[item.key] or 0
  local pending=s.pending[item.key] or 0
  return math.max(0,math.min(item.cap or 1,granted-pending))
end

-- Bring one AP-managed category back to exactly the ranks that have actually
-- been applied from the receipt stream.  This removes native free ranks from
-- evolutions and also restores AP ranks if an evolution tried to refund/swap
-- one of the seed's pre-existing categories.
local function normalizeTreeRanks(actor,s,tree)
  M.withGrant(actor,function()
    for _,item in ipairs(itemsForTree(s,tree)) do
      local tid=actor[item.symbol]
      if tid then
        local target=targetOwnedRank(s,item)
        local now=actor:getTalentLevelRaw(tid)
        while now>target do
          actor:unlearnTalent(tid)
          local after=actor:getTalentLevelRaw(tid)
          assert(after<now,"Could not remove non-AP talent rank from "..item.symbol)
          now=after
        end
        while now<target do
          actor:learnTalent(tid,true,1)
          local after=actor:getTalentLevelRaw(tid)
          assert(after>now,"Could not restore AP talent rank for "..item.symbol)
          now=after
        end
      end
    end
  end)
end

local function restoreOwnedBaseTrees(actor,s)
  for tree in pairs(s.selected_trees) do
    enableTree(actor,s,tree)
    normalizeTreeRanks(actor,s,tree)
  end
  for tree in pairs(s.extra_trees) do
    if s.tree_defs[tree] then enableTree(actor,s,tree) end
    normalizeTreeRanks(actor,s,tree)
  end
end

local function flushPendingTree(actor,s,tree)
  if not actor:knowTalentType(tree) then return end
  for item_key,count in pairs(s.pending) do
    local item=s.item_keys[item_key]
    if item and item.kind=="talent" and item.tree==tree and count>0 then
      for i=1,count do applyTalentRank(actor,item) end
      s.pending[item_key]=nil
    end
  end
end

local function prodigyRuleUnlocked(s,tree)
  local rules=s.bonus_tree_rules[tree]
  if not rules then return false end
  for _,r in ipairs(rules) do if s.prodigy_received[r.item_key] then return true end end
  return false
end

local function grantProdigy(actor,item)
  local s=actor.archipelago_state
  local rule=s.prodigy_bonus[item.key]
  local tid=assert(actor[item.symbol],"Unknown received prodigy")
  local t=assert(actor:getTalentFromId(tid),"Missing received prodigy definition")
  if actor:getTalentLevelRaw(tid)<1 then
    M.withGrant(actor,function()
      if rule and rule.suppress_native_on_learn then
        local old=t.on_learn; t.on_learn=nil
        local ok,err=pcall(function() actor:learnTalent(tid,true,1) end)
        t.on_learn=old
        if not ok then error(err,0) end
      else
        actor:learnTalent(tid,true,1)
      end
    end)
  end
  s.prodigy_received[item.key]=true

  -- Evolution prodigies are allowed to do their native non-point effects, but
  -- they may not delete/refund AP-owned ranks or hand out free ranks.
  restoreOwnedBaseTrees(actor,s)
  if rule then
    for _,tree in ipairs(rule.trees or {}) do
      if (rule.unlock_mode or "immediate")=="immediate" then enableTree(actor,s,tree) end
      if actor:knowTalentType(tree) then
        normalizeTreeRanks(actor,s,tree)
        flushPendingTree(actor,s,tree)
      end
    end
    for _,tree in ipairs(rule.cleanup_trees or {}) do
      if actor:knowTalentType(tree) then normalizeTreeRanks(actor,s,tree) end
    end
  end
end

local function grant(actor,item)
  local s=actor.archipelago_state
  if item.kind=="talent" then
    if s.selected_trees[item.tree] or s.extra_trees[item.tree] then
      applyTalentRank(actor,item)
    elseif s.bonus_tree_rules[item.tree] then
      if prodigyRuleUnlocked(s,item.tree) and actor:knowTalentType(item.tree) then
        applyTalentRank(actor,item)
      else
        s.pending[item.key]=(s.pending[item.key] or 0)+1
      end
    else
      -- Admin/out-of-build item creation is legal in AP. Make it usable rather
      -- than crashing the client, but keep it outside the generated build.
      enableTree(actor,s,item.tree)
      s.extra_trees[item.tree]=true
      applyTalentRank(actor,item)
    end
  elseif item.kind=="prodigy" then
    grantProdigy(actor,item)
  elseif item.kind=="stat" then
    local id=assert(actor[STAT_CONSTANTS[item.stat]])
    -- Vanilla direct stat rewards are allowed and stack with AP's fixed +5
    -- packages.  The generated item pool already limits normal AP ownership to
    -- ten packages per stat, so do not let a vanilla bonus consume AP value.
    M.withGrant(actor,function()actor:incStat(id,item.amount)end)
  elseif item.kind=="vitality" then
    assert(item.amount==1,"Unexpected vitality amount")
    actor.max_life=(actor.max_life or 1)+1
    actor.life=math.min(actor.max_life,(actor.life or 1)+1)
  else error("Unsupported grant kind") end
  s.grants[item.key]=(s.grants[item.key] or 0)+1
end

-- Check observation ----------------------------------------------------------
function M.recordLevel(actor)
  if not actor or not actor.archipelago_state then return end
  local s=actor.archipelago_state
  for key,loc in pairs(s.locations) do
    if loc.event=="level" and actor.level>=loc.level then s.checks[key]=true end
  end
end

function M.recordZone(actor,zone)
  local s=actor and actor.archipelago_state
  if not s or not zone then return end
  local short=zone.short_name or zone.name
  if type(short)~="string" then return end
  for key,loc in pairs(s.locations) do
    if loc.event=="zone" and type(loc.trigger)=="table" and loc.trigger.zone==short then
      s.checks[key]=true
    end
  end
end

function M.recordBoss(actor,target,zone)
  local s=actor and actor.archipelago_state
  if not s or not target then return end
  local short=zone and (zone.short_name or zone.name) or nil
  local name=target.name
  for key,loc in pairs(s.locations) do
    if loc.event=="boss" and type(loc.trigger)=="table" then
      local zone_ok=(not loc.trigger.zone) or loc.trigger.zone==short
      local name_ok=false
      for _,candidate in ipairs(loc.trigger.names or {}) do if candidate==name then name_ok=true break end end
      if zone_ok and name_ok then s.checks[key]=true end
    end
  end
end

local QUEST_STATUS_NAMES={[0]="pending",[1]="completed",[100]="done",[101]="failed"}

function M.recordQuest(actor,quest,status,sub)
  local s=actor and actor.archipelago_state
  if not s or type(quest)~="string" then return end
  local status_name=QUEST_STATUS_NAMES[status] or tostring(status)
  for key,loc in pairs(s.locations) do
    if loc.event=="quest" and type(loc.trigger)=="table" and loc.trigger.quest==quest then
      local status_ok=(not loc.trigger.status) or loc.trigger.status==status_name
      local sub_ok=true
      if loc.trigger.sub then sub_ok=(loc.trigger.sub==sub) end
      if loc.trigger.subs then
        sub_ok=false
        for _,candidate in ipairs(loc.trigger.subs) do if candidate==sub then sub_ok=true break end end
      end
      if status_ok and sub_ok then s.checks[key]=true end
    end
  end
end

function M.shopParcels(actor,zone,shop,store_id)
  local s=actor and actor.archipelago_state
  local out={}
  if not s or type(zone)~="string" then return out end
  for key,loc in pairs(s.locations) do
    local shop_match=type(shop)=="string" and loc.trigger and loc.trigger.shop==shop
    local store_match=type(store_id)=="string" and loc.trigger and loc.trigger.store==store_id
    local scout=s.scouts and s.scouts[key]
    if loc.event=="shop" and type(loc.trigger)=="table" and scout
      and loc.trigger.zone==zone and (shop_match or store_match) and not s.checks[key] then
      out[#out+1]={code=loc.code,name=loc.name,event=loc.event,trigger=loc.trigger,scout=scout}
    end
  end
  table.sort(out,function(a,b)return (a.trigger.parcel or 0)<(b.trigger.parcel or 0) end)
  return out
end

function M.recordShopPurchase(actor,code)
  local s=actor and actor.archipelago_state
  if not s or not whole(code,1,2147483647) then return false end
  local key=tostring(code)
  local loc=s.locations[key]
  if not loc or loc.event~="shop" or s.checks[key] then return false end
  s.checks[key]=true
  return true
end

function M.shopPurchaseAvailable(actor,code)
  local s=actor and actor.archipelago_state
  if not s or not whole(code,1,2147483647) then return false end
  local key=tostring(code)
  local loc=s.locations[key]
  return loc and loc.event=="shop" and not s.checks[key] and s.scouts and s.scouts[key]~=nil or false
end

-- Pool talents remain learned for native game mechanics. Show a resource once
-- a learned skill actually uses it, including racial and inscription talents.
local function usedResources(actor,definitions)
  local used={}
  for tid,rank in pairs(actor.talents or {}) do
    if type(rank)=="number" and rank>0 then
      local talent=actor:getTalentFromId(tid)
      if talent then
        for _,r in ipairs(definitions or {}) do
          local short=r.short_name
          if rawget(talent,short)~=nil or rawget(talent,"sustain_"..short)~=nil or
            rawget(talent,"drain_"..short)~=nil then used[short]=true end
        end
        if rawget(talent,"feedback")~=nil or rawget(talent,"sustain_feedback")~=nil then
          used.feedback=true
        end
        local tree=talent.type and talent.type[1]
        if type(tree)=="string" and
          (tree:match("^psionic/feedback") or tree:match("^psionic/discharge")) then used.feedback=true end
      end
    end
  end
  return used
end

function M.resourceVisible(actor,short)
  if not M.isCharacter(actor) or not actor.archipelago_state then return true end
  local R=require "engine.interface.ActorResource"
  return usedResources(actor,R.resources_def)[short] or false
end

function M.withResourceDisplay(actor,fn,...)
  if not M.isCharacter(actor) or not actor.archipelago_state then return fn(...) end
  local R=require "engine.interface.ActorResource"
  local used=usedResources(actor,R.resources_def)
  local hidden={}
  for _,r in ipairs(R.resources_def or {}) do
    if type(r.talent)=="string" and not used[r.short_name] then
      hidden[r.talent]=true
    end
  end
  if actor.T_FEEDBACK_POOL and not used.feedback then
    hidden[actor.T_FEEDBACK_POOL]=true
  end
  local original=rawget(actor,"knowTalent")
  local native=actor.knowTalent
  actor.knowTalent=function(self,tid,...)
    if hidden[tid] then return false end
    return native(self,tid,...)
  end
  local args=pack(...)
  local ok,result=pcall(function() return pack(fn(unpack(args,1,args.n))) end)
  actor.knowTalent=original
  if not ok then error(result,0) end
  return unpack(result,1,result.n)
end

function M.markVictory(actor)
  local s=actor and actor.archipelago_state
  if not s then return end
  s.goal=true
  -- Only variable advancement rewards are auto-collected on victory. Boss and
  -- story locations remain real accomplishments and are never fabricated.
  for key,loc in pairs(s.locations) do
    if loc.event=="level" or loc.event=="victory" then s.checks[key]=true end
  end
end

function M.publish(actor)
  local s=actor.archipelago_state
  local checks=JSON.array()
  for key,v in pairs(s.checks) do if v then checks[#checks+1]=tonumber(key) end end
  table.sort(checks)
  s.revision=s.revision+1
  write("game.json",{protocol=1,complete=true,identity=s.identity,applied_count=s.applied_count,
    checks=checks,goal=s.goal,revision=s.revision,error=s.error or JSON.null})
end

local function reconcileNativeBonusTrees(actor,s)
  restoreOwnedBaseTrees(actor,s)
  for tree,rules in pairs(s.bonus_tree_rules) do
    if actor:knowTalentType(tree) and prodigyRuleUnlocked(s,tree) then
      enableTree(actor,s,tree)
      normalizeTreeRanks(actor,s,tree)
      flushPendingTree(actor,s,tree)
    end
  end
  for item_key,rule in pairs(s.prodigy_bonus or {}) do
    if s.prodigy_received[item_key] then
      for _,tree in ipairs(rule.cleanup_trees or {}) do
        if actor:knowTalentType(tree) then normalizeTreeRanks(actor,s,tree) end
      end
    end
  end
end

function M.poll(g)
  if not g or not g.player or not g.level or not M.isCharacter(g.player) then return end
  local actor=g.player
  -- Free/distributable point rewards never belong to an AP character.  Scrub
  -- them every render-loop pass so quest rewards cannot be spent between syncs.
  M.zeroPointPools(actor)
  M.tick_count=M.tick_count+1
  if M.tick_count%20~=0 then return end
  local snap=M.config()
  if not snap then
    if not actor.archipelago_state and M.last_error~="missing" then
      message(g,"No valid bridge snapshot. Do not play this character until the client is connected.")
      M.last_error="missing"
    end
    return
  end
  local ok,err=pcall(function()
    M.initialize(g,snap)
    local s=assert(actor.archipelago_state)
    if not M.identityMatches(s.identity,snap.identity) then error("Save belongs to a different AP seed/team/slot/build") end
    s.scouts=scout_map(snap,s.locations)
    -- A restored save may predate checks already accepted by the AP server.
    for _,code in ipairs(snap.checked_locations or {}) do
      local key=tostring(code)
      if s.locations[key] then s.checks[key]=true end
    end
    if s.error then return end
    migrateResourceState(actor,s)
    M.recordZone(actor,g.zone)
    if actor.winner=="full" then M.markVictory(actor) end
    if actor.dead then M.publish(actor); return end
    if #snap.receipts<s.applied_count then error("Received history is behind saved cursor; wait for resync") end
    for index=1,s.applied_count do
      assert(s.received_ids[index]==snap.receipts[index].item,"Previously applied receipt prefix changed")
    end
    for index=s.applied_count+1,math.min(#snap.receipts,s.applied_count+8) do
      local receipt=snap.receipts[index]
      assert(type(receipt)=="table" and whole(receipt.item,1,2147483647),"Malformed receipt")
      local item=assert(s.items[tostring(receipt.item)],"Unknown item in receipt stream")
      local success,why=pcall(grant,actor,item)
      if not success then
        s.error="Grant "..index.." failed: "..tostring(why)
        error(s.error)
      end
      s.received_ids[index]=receipt.item
      s.applied_count=index
      message(g,"Received "..item.name)
    end
    reconcileNativeBonusTrees(actor,s)
    M.zeroPointPools(actor)
    M.recordLevel(actor)
    M.recordZone(actor,g.zone)
    if actor.winner=="full" then M.markVictory(actor) end
    M.publish(actor)
    M.last_error=nil
  end)
  if not ok and M.last_error~=tostring(err) then
    M.last_error=tostring(err); message(g,"SYNC STOPPED: "..tostring(err))
    if actor.archipelago_state then pcall(M.publish,actor) end
  end
end
return M
