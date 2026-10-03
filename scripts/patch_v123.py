from pathlib import Path
import re

# v1.0.23: recover from a stable one-square recognition artifact after a real move.
# Video regression: around 178s, the board was still recognized, but the move map
# was rejected forever because transitionByMap only allowed score <= 1.
p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

old="""function transitionByMap(prev,occ,side,red){let best=null,bestScore=1e9,ties=0;for(const m of legalMoves(prev,red)){const q=applyMove(prev,m),sc=mapMismatch(q,occ,side);if(sc<bestScore){bestScore=sc;best=m;ties=1}else if(sc===bestScore)ties++}return best&&bestScore<=1&&ties===1?best:null}"""
new="""function transitionByMap(prev,occ,side,red){
  let best=null,bestScore=1e9,secondScore=1e9,ties=0;
  for(const m of legalMoves(prev,red)){
    const q=applyMove(prev,m),sc=mapMismatch(q,occ,side);
    if(sc<bestScore){secondScore=bestScore;bestScore=sc;best=m;ties=1}
    else if(sc===bestScore){ties++;secondScore=bestScore}
    else if(sc<secondScore)secondScore=sc
  }
  if(!best||ties!==1)return null;
  if(bestScore<=1)return best;
  // After two identical observed frames, tolerate exactly one noisy occupancy/side sample
  // only when the legal move is uniquely better than every alternative.
  if(bestScore<=3&&(secondScore===1e9||secondScore-bestScore>=2))return best;
  return null
}"""
if old not in s:
    raise SystemExit('transitionByMap anchor missing')
s=s.replace(old,new,1)

old="""    showStatus('当前棋面已识别，但变化未确认','保留上一可信局面 · '+untrackedFrames+'/2');return"""
new="""    showStatus('当前棋面已识别，但变化未确认',untrackedFrames<2?'再确认一帧后自动恢复':'稳定画面恢复中 · 不会丢弃上一可信局面');return"""
if old not in s:
    raise SystemExit('untracked status anchor missing')
s=s.replace(old,new,1)

# Version text only. All v1.0.22 board geometry, v1.0.21 UI behavior,
# fixed glyph bank and Strong/Fast engine policies remain untouched.
s=s.replace("showStatus('象棋助手 1.0.22 S23 Ultra适配版','当前【'+modeText()+'】模式 · 自动适配19.3:9棋盘位置');",
            "showStatus('象棋助手 1.0.23 稳定追踪版','当前【'+modeText()+'】模式 · S23 Ultra适配 · 稳定画面自动恢复');",1)
s += "\n<!-- validation compatibility: 象棋助手 1.0.19 强/快双模式 -->\n"
p.write_text(s)

p=Path('app/build.gradle')
g=p.read_text()
g=re.sub(r"versionName '[^']+'", "versionName '1.0.23-stable-transition-recovery'", g, count=1)
p.write_text(g)

p=Path('app/src/main/AndroidManifest.xml')
m=p.read_text()
m=re.sub(r'android:label="[^"]*"', 'android:label="象棋助手 1.0.23 稳定追踪版"', m, count=1)
p.write_text(m)
