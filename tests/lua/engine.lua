-- Fake ToME engine shared by Lupa and Lua C-API regression tests.
-- AP and snapshot are supplied by the Python harness. No actual game is run.
fs={files={}}
function fs.mkdir(path) return true end
function fs.open(path,mode)
  if mode=="r" and not fs.files[path] then return nil end
  if mode=="w" then fs.files[path]="" end
  return {
    read=function(self,n)return fs.files[path] end,
    write=function(self,s)fs.files[path]=fs.files[path]..s end,
    close=function(self)end
  }
end
actor={archipelago_character=true,level=1,stats={12,12,12,12,12,12},raw={},definitions={},
       unused_talents=5,unused_generics=3,unused_stats=9,unused_talents_types=1,unused_prodigies=0,
       STAT_STR=1,STAT_DEX=2,STAT_CON=3,STAT_MAG=4,STAT_WIL=5,STAT_CUN=6,
       max_life=100,life=100,talents_types={},talents_types_mastery={},category_learns=0}
local talent_types={}
for _,item in ipairs(snapshot.contract.items) do
  if item.symbol and item.symbol~="" then
    actor[item.symbol]=item.symbol
    local tree=item.tree~="" and item.tree or "uber/mag"
    local resource=tree=="technique/combat-training" and "stamina" or "mana"
    actor.definitions[item.symbol]={id=item.symbol,type={tree,1},points=item.cap,name=item.name,
      uber=item.kind=="prodigy"}
    if item.kind=="talent" then actor.definitions[item.symbol][resource]=1 end
    talent_types[tree]={name=tree,generic=false}
  end
end
local resources={}
for _,short in ipairs({"mana","stamina","psi","vim","positive","negative","hate","feedback","steam","soul","equilibrium","paradox"}) do
  local tid="T_TEST_RESOURCE_"..short:upper()
  local r={short_name=short,name=short,talent=tid,regen_prop=short.."_regen",min=0,max=100}
  resources[#resources+1]=r; resources[short]=r
  actor[short]=0; actor["max_"..short]=short=="soul" and 6 or 100
  actor["min_"..short]=0; actor[r.regen_prop]=0
  actor[tid]=tid
  actor.definitions[tid]={id=tid,type={"base/other",1},points=1,hide="always"}
end
for _,tid in ipairs({"T_SHOOT","T_RELOAD"}) do
  actor[tid]=tid
  actor.definitions[tid]={id=tid,type={"base/other",1},points=1,hide="always"}
end
package.preload["engine.interface.ActorResource"]=function()return {resources_def=resources}end
package.preload["engine.interface.ActorTalents"]=function()
  return {talents_types_def=talent_types,talents_def=actor.definitions}
end
function actor:getTalentFromId(tid)return self.definitions[tid]end
function actor:getTalentLevelRaw(tid)return self.raw[tid] or 0 end
function actor:learnTalent(tid,force,nb)
  assert(force==true,"requirements must be bypassed")
  self.raw[tid]=(self.raw[tid] or 0)+nb
  self.unused_talents=self.unused_talents-nb
  local t=self.definitions[tid]
  if t and t.on_learn then t.on_learn(self,t) end
end
function actor:learnTalentType(tree,known)
  self.category_learns=self.category_learns+1
  self.talents_types[tree]=known
end
function actor:knowTalentType(tree)return self.talents_types[tree]end
function actor:incStat(id,n)self.stats[id]=self.stats[id]+n end
function actor:unlearnTalent(id)self.raw[id]=math.max(0,(self.raw[id] or 0)-1)end
game={player=actor,level={},log=function(...)end}
fs.files["/archipelago/client.json"]=JSON.encode(snapshot)
function publish_snapshot()
  fs.files["/archipelago/client.json"]=JSON.encode(snapshot)
end
function poll() for i=1,20 do AP.poll(game) end end
