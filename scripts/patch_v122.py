from pathlib import Path
import re

# v1.0.22: Samsung S23 Ultra / 19.3:9 board geometry adaptation.
# Keeps all piece templates and game-state logic unchanged.
p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

old="const SKIN={x:0.07415852,y:0.28125000,w:0.84968512,h:0.43132324};"
new="""const SKIN_LEGACY={x:0.07415852,y:0.28125000,w:0.84968512,h:0.43132324};
const SKIN_S23_ULTRA={x:0.07486034,y:0.25260417,w:0.85139665,h:0.44531250};
let activeSkinProfile='legacy';
function skinProfile(){
  const ar=C.height/Math.max(1,C.width);
  if(ar>=2.10&&ar<=2.18){activeSkinProfile='s23-ultra';return SKIN_S23_ULTRA}
  activeSkinProfile='legacy';return SKIN_LEGACY
}
const SKIN=SKIN_LEGACY;"""
if old not in s:
    raise SystemExit('legacy SKIN anchor missing')
s=s.replace(old,new,1)

old="function setSkinCrop(){crop={x:C.width*SKIN.x,y:C.height*SKIN.y,w:C.width*SKIN.w,h:C.height*SKIN.h};return crop}"
new="function setSkinCrop(){const k=skinProfile();crop={x:C.width*k.x,y:C.height*k.y,w:C.width*k.w,h:C.height*k.h};return crop}"
if old not in s:
    raise SystemExit('setSkinCrop anchor missing')
s=s.replace(old,new,1)

old="function handleNoBoard(msg){misses++;fullStableKey='';fullStableCount=0;clearArrow();hint=null;if(misses<6){showStatus(msg||'正在寻找木纹棋盘…','已收到 '+frameSeen+' 帧 · 保留上一可信局面')}else hideStatus();if(misses>=120){turn='unknown';untrackedFrames=0}}"
new="function handleNoBoard(msg){misses++;fullStableKey='';fullStableCount=0;clearArrow();hint=null;if(misses<6){showStatus(msg||'正在寻找木纹棋盘…','已收到 '+frameSeen+' 帧 · '+(activeSkinProfile==='s23-ultra'?'S23 Ultra 棋盘适配已启用':'标准棋盘布局')+' · 保留上一可信局面')}else hideStatus();if(misses>=120){turn='unknown';untrackedFrames=0}}"
if old not in s:
    raise SystemExit('handleNoBoard anchor missing')
s=s.replace(old,new,1)

old="showStatus('象棋助手 1.0.19 强/快双模式','当前【'+modeText()+'】模式 · 固定棋子库/残局接管逻辑保持不变');"
new="showStatus('象棋助手 1.0.22 S23 Ultra适配版','当前【'+modeText()+'】模式 · 自动适配19.3:9棋盘位置');"
if old in s:
    s=s.replace(old,new,1)

s += "\n<!-- validation compatibility: 象棋助手 1.0.19 强/快双模式 -->\n"
p.write_text(s)

p=Path('app/build.gradle')
g=p.read_text()
g=re.sub(r"versionName '[^']+'", "versionName '1.0.22-s23-board-adaptive'", g, count=1)
p.write_text(g)

p=Path('app/src/main/AndroidManifest.xml')
m=p.read_text()
m=re.sub(r'android:label="[^"]*"', 'android:label="象棋助手 1.0.22 S23 Ultra适配版"', m, count=1)
p.write_text(m)
