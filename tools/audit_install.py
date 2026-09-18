"""Read locally installed source archives and produce an adapter evidence report.

This does not execute game source, modify the game, or certify runtime behavior.
It identifies definitions/call sites that must be reviewed for the pinned build.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import zipfile

PATTERNS={
    "Game tick":r"function\s+(?:_M:)?tick\s*\(",
    "Game display":r"function\s+(?:_M:)?display\s*\(",
    "Actor levelup":r"function\s+(?:_M:)?levelup\s*\(",
    "Talent grant":r"function\s+(?:_M:)?learnTalent\s*\(",
    "Equipment eligibility":r"function\s+(?:_M:)?canWearObject\s*\(",
    "Raw stat mutation":r"function\s+(?:_M:)?incStat\s*\(",
    "Birth registry":r"birth_descriptor_def",
    "Module load hook":r"ToME:load",
    "Birth completion hook":r"ToME:birthDone",
    "Full winner flag":r"winner\s*=\s*[\"']full[\"']",
    "Filesystem reader":r"fs\.open",
    "Online events":r"allow_online_events|Allow online events|Disable all connectivity",
    "Item vault":r"[Ii]tem[s_ ]?[Vv]ault",
}

def sources(root):
    seen=set()
    for p in root.rglob("*"):
        if not p.is_file():continue
        if p.suffix.lower()==".lua":
            key=str(p.relative_to(root))
            if key not in seen:
                seen.add(key);yield key,p.read_text(encoding="utf-8",errors="replace")
        elif p.suffix.lower() in {".team",".teae"} and zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as z:
                for info in z.infolist():
                    if info.filename.endswith(".lua") and info.file_size<5_000_000:
                        yield f"{p.name}:{info.filename}",z.read(info).decode("utf-8",errors="replace")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--game-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("local/source-audit.md"))
    a=p.parse_args()
    found={k:[] for k in PATTERNS}
    count=0
    for name,source in sources(a.game_dir):
        count+=1;lines=source.splitlines()
        for title,pattern in PATTERNS.items():
            for number,line in enumerate(lines,1):
                if re.search(pattern,line) and len(found[title])<12:
                    lo=max(0,number-4);hi=min(len(lines),number+10)
                    found[title].append((name,number,"\n".join(f"{i+1}: {lines[i]}" for i in range(lo,hi))))
    out=["# Local ToME adapter source audit",f"\nScanned {count} Lua files. This is evidence collection, not an engine test.\n"]
    for title,entries in found.items():
        out.append(f"## {title}\n")
        if not entries:out.append("**Not located. Do not assume this adapter is supported.**\n")
        for name,line,excerpt in entries:
            out.extend([f"`{name}` line {line}\n","```lua",excerpt,"```\n"])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text("\n".join(out),encoding="utf-8")
    print(a.output.resolve())
    if not count:raise SystemExit("No source files found; verify --game-dir and installed .team/.teae archives")

if __name__=="__main__":main()
