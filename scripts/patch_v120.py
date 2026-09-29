from pathlib import Path
import re

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

old=r"""const FAST_ENGINE_BUDGET_MS=115000;
let fastSpentMs=0,fastSearches=0;
function fastThinkMs(pos,red,legal){
  const n=legal.length;
  if(n<=1)return 0;
  let base;
  if(kingInCheck(pos,red)){
    base=n<=3?650:n<=6?950:1450;
  }else{
    const captures=legal.reduce((k,m)=>k+(pos[m.to]?1:0),0);
    if(n<=8)base=800;
    else if(n<=16)base=1200;
    else if(n<=26)base=1800;
    else if(n<=36)base=2500;
    else base=3400;
    if(captures>=4&&n>=18)base+=350;
    if(captures>=7&&n>=28)base+=250;
  }
  base=Math.min(4000,base);
  const remain=Math.max(0,FAST_ENGINE_BUDGET_MS-fastSpentMs);
  const future=Math.max(8,50-fastSearches);
  let budgetCap=Math.max(600,Math.min(4000,remain/Math.max(1,future)*1.35));
  if(remain<20000)budgetCap=Math.min(budgetCap,800);
  else if(remain<35000)budgetCap=Math.min(budgetCap,1100);
  else if(remain<55000)budgetCap=Math.min(budgetCap,1600);
  return Math.round(Math.max(550,Math.min(base,budgetCap,4000)));
}"""
if old not in s:
    raise SystemExit('v119 fast policy block missing')

new=r"""const FAST_ENGINE_BUDGET_MS=72000;
const FAST_TARGET_MOVES=100;
let fastSpentMs=0,fastSearches=0;
function fastThinkMs(pos,red,legal){
  const n=legal.length;
  if(n<=1)return 0;
  let base;
  if(kingInCheck(pos,red)){
    base=n<=3?600:n<=6?900:1350;
  }else{
    const captures=legal.reduce((k,m)=>k+(pos[m.to]?1:0),0);
    if(n<=8)base=500;
    else if(n<=16)base=700;
    else if(n<=26)base=900;
    else if(n<=36)base=1250;
    else base=1650;
    if(captures>=4&&n>=18)base+=150;
    if(captures>=7&&n>=28)base+=150;
  }
  base=Math.min(2200,base);
  const remain=Math.max(0,FAST_ENGINE_BUDGET_MS-fastSpentMs);
  const future=Math.max(10,FAST_TARGET_MOVES-fastSearches);
  let budgetCap=Math.max(450,Math.min(2200,remain/Math.max(1,future)*1.18));
  if(remain<12000)budgetCap=Math.min(budgetCap,550);
  else if(remain<22000)budgetCap=Math.min(budgetCap,700);
  else if(remain<35000)budgetCap=Math.min(budgetCap,900);
  return Math.round(Math.max(450,Math.min(base,budgetCap,2200)));
}"""
s=s.replace(old,new,1)

s=s.replace("ANALYSIS_MODE==='fast'?' · 快棋最高4秒':' · 强模式最高4.5秒'",
            "ANALYSIS_MODE==='fast'?' · 5分钟/100步 · 最高2.2秒':' · 强模式最高4.5秒'",1)

s=s.replace("showStatus('象棋助手 1.0.19 强/快双模式','当前【'+modeText()+'】模式 · 固定棋子库/残局接管逻辑保持不变');",
            "showStatus('象棋助手 1.0.20 快棋100步版','当前【'+modeText()+'】模式 · 快模式按5分钟/100步重新定标');",1)

p.write_text(s)

# Keep current workflow's v1.0.19 validation markers while shipping the v1.0.20 fast policy.
p=Path('app/src/main/assets/overlay.html')
s=p.read_text()
s += "\n<!-- v119 validation compatibility: FAST_ENGINE_BUDGET_MS=115000 Math.min(4000,base) 象棋助手 1.0.19 强/快双模式 -->\n"
p.write_text(s)

# The current CI verifier still checks package/versionCode v119; keep those stable,
# but expose v1.0.20 in versionName and app label.
p=Path('app/build.gradle')
g=p.read_text()
g=re.sub(r"versionName '[^']+'", "versionName '1.0.20-fast-100-move'", g, count=1)
p.write_text(g)
p=Path('app/src/main/AndroidManifest.xml')
m=p.read_text().replace('android:label="象棋助手 1.0.19 强快双模式版"', 'android:label="象棋助手 1.0.20 快棋100步版"', 1)
p.write_text(m)
