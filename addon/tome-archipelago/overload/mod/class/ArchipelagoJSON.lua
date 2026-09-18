-- Original, data-only JSON codec. No loadstring/dofile/eval on mailbox input.
local M = {}
local array_meta = {__json_array = true}
M.null = {}
function M.array(t) return setmetatable(t or {}, array_meta) end
local function fail(s) error("AP JSON: " .. s, 0) end
local escapes = {['"']='\\"', ['\\']='\\\\', ['\b']='\\b', ['\f']='\\f', ['\n']='\\n', ['\r']='\\r', ['\t']='\\t'}
local function quote(s)
  return '"' .. s:gsub('[%z\1-\31\\"]', function(c)
    return escapes[c] or string.format('\\u%04x', c:byte())
  end) .. '"'
end
function M.encode(value)
  local seen = {}
  local function emit(v, depth)
    if depth > 64 then fail("nesting limit") end
    if v == M.null then return "null" end
    local kind = type(v)
    if kind == "nil" then return "null"
    elseif kind == "boolean" then return tostring(v)
    elseif kind == "string" then return quote(v)
    elseif kind == "number" then
      if v ~= v or v == math.huge or v == -math.huge then fail("non-finite number") end
      return string.format("%.17g", v)
    elseif kind ~= "table" then fail("unsupported value " .. kind) end
    if seen[v] then fail("cycle") end
    seen[v] = true
    local parts = {}
    local mt = getmetatable(v)
    local isarray = mt and mt.__json_array
    if isarray then
      for i=1,#v do parts[i] = emit(v[i], depth+1) end
      seen[v] = nil
      return "[" .. table.concat(parts, ",") .. "]"
    end
    local keys={}
    for k in pairs(v) do
      if type(k) ~= "string" then fail("object key is not a string") end
      keys[#keys+1]=k
    end
    table.sort(keys)
    for _,k in ipairs(keys) do parts[#parts+1] = quote(k) .. ":" .. emit(v[k], depth+1) end
    seen[v] = nil
    return "{" .. table.concat(parts, ",") .. "}"
  end
  return emit(value,0)
end
local function utf8(n)
  if n < 0x80 then return string.char(n)
  elseif n < 0x800 then return string.char(0xc0+math.floor(n/64),0x80+n%64)
  elseif n < 0x10000 then return string.char(0xe0+math.floor(n/4096),0x80+math.floor(n/64)%64,0x80+n%64)
  elseif n <= 0x10ffff then return string.char(0xf0+math.floor(n/262144),0x80+math.floor(n/4096)%64,0x80+math.floor(n/64)%64,0x80+n%64) end
  fail("invalid Unicode")
end
function M.decode(s)
  if type(s) ~= "string" or #s > 8*1024*1024 then fail("input size/type") end
  local pos,len = 1,#s
  local function ws() while pos<=len and s:sub(pos,pos):match("%s") do pos=pos+1 end end
  local parse
  local function string_value()
    if s:sub(pos,pos) ~= '"' then fail("expected string") end
    pos=pos+1
    local out={}
    while pos<=len do
      local c=s:sub(pos,pos); pos=pos+1
      if c=='"' then return table.concat(out) end
      if c=='\\' then
        local e=s:sub(pos,pos); pos=pos+1
        local simple={['"']='"',['\\']='\\',['/']='/',b='\b',f='\f',n='\n',r='\r',t='\t'}
        if simple[e] then out[#out+1]=simple[e]
        elseif e=='u' then
          local h=s:sub(pos,pos+3)
          if #h~=4 or not h:match('^%x%x%x%x$') then fail("bad Unicode escape") end
          local cp=tonumber(h,16); pos=pos+4
          if cp>=0xd800 and cp<=0xdbff then
            if s:sub(pos,pos+1)~='\\u' then fail("missing low surrogate") end
            local low=tonumber(s:sub(pos+2,pos+5),16)
            if not low or low<0xdc00 or low>0xdfff then fail("bad low surrogate") end
            cp=0x10000+(cp-0xd800)*1024+low-0xdc00; pos=pos+6
          elseif cp>=0xdc00 and cp<=0xdfff then fail("unpaired surrogate") end
          out[#out+1]=utf8(cp)
        else fail("bad escape") end
      else
        if c:byte()<32 then fail("unescaped control character") end
        out[#out+1]=c
      end
    end
    fail("unterminated string")
  end
  parse=function(depth)
    if depth>64 then fail("nesting limit") end
    ws()
    local c=s:sub(pos,pos)
    if c=='"' then return string_value()
    elseif c=='[' then
      pos=pos+1; ws(); local a=M.array()
      if s:sub(pos,pos)==']' then pos=pos+1; return a end
      while true do
        a[#a+1]=parse(depth+1); ws(); c=s:sub(pos,pos); pos=pos+1
        if c==']' then return a elseif c~=',' then fail("expected comma/end of array") end
      end
    elseif c=='{' then
      pos=pos+1; ws(); local o={}; local used={}
      if s:sub(pos,pos)=='}' then pos=pos+1; return o end
      while true do
        ws(); local k=string_value(); ws()
        if used[k] then fail("duplicate object key") end
        used[k]=true
        if s:sub(pos,pos)~=':' then fail("expected colon") end
        pos=pos+1; o[k]=parse(depth+1); ws(); c=s:sub(pos,pos); pos=pos+1
        if c=='}' then return o elseif c~=',' then fail("expected comma/end of object") end
      end
    elseif s:sub(pos,pos+3)=='true' then pos=pos+4; return true
    elseif s:sub(pos,pos+4)=='false' then pos=pos+5; return false
    elseif s:sub(pos,pos+3)=='null' then pos=pos+4; return M.null
    else

      local begin=pos
      if s:sub(pos,pos)=='-' then pos=pos+1 end
      local digit=s:sub(pos,pos)
      if digit=='0' then
        pos=pos+1
        if s:sub(pos,pos):match('%d') then fail("leading zero") end
      elseif digit:match('[1-9]') then
        repeat pos=pos+1 until not s:sub(pos,pos):match('%d')
      else fail("expected JSON value at "..pos) end
      if s:sub(pos,pos)=='.' then
        pos=pos+1
        if not s:sub(pos,pos):match('%d') then fail("missing fractional digits") end
        repeat pos=pos+1 until not s:sub(pos,pos):match('%d')
      end
      local e=s:sub(pos,pos)
      if e=='e' or e=='E' then
        pos=pos+1
        local sign=s:sub(pos,pos)
        if sign=='+' or sign=='-' then pos=pos+1 end
        if not s:sub(pos,pos):match('%d') then fail("missing exponent digits") end
        repeat pos=pos+1 until not s:sub(pos,pos):match('%d')
      end
      local n=tonumber(s:sub(begin,pos-1))
      if not n or n~=n or n==math.huge or n==-math.huge then fail("invalid number") end
      return n
    end
  end
  local result=parse(0); ws()
  if pos<=len then fail("trailing data") end
  return result
end
return M
