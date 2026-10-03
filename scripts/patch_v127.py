from pathlib import Path
import re

# v1.0.27: deliberately return to the v1.0.21 recognition/tracking stack and
# change only Galaxy S23 Ultra board geometry.  No v1.0.22-v1.0.26 recognition,
# transition, session or glyph logic is applied by the workflow for this build.
#
# The user's 895x1920 stills and 592x1280 recording have the same 19.3:9 ratio
# and the same grid scale, but the live-game UI shifts the whole board down by
# ~14-18 px at 592x1280.  A single fixed y therefore works before the clock/UI
# changes and then loses the board.  We keep v1.0.21 intact and dynamically fit
# only the vertical grid origin by measuring the board's horizontal/vertical
# line contrast.  This works even in sparse endgames because it does not depend
# on any particular piece being present.

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

old="const SKIN={x:0.07415852,y:0.28125000,w:0.84968512,h:0.43132324};"
new="""const SKIN_LEGACY={x:0.07415852,y:0.28125000,w:0.84968512,h:0.43132324};
const SKIN_S23={x:0.07486034,y:0.24947917,w:0.85139665,h:0.44531250};
let activeSkinProfile='legacy',s23YOffset=0,s23ProbeTick=0,s23ProbeStamp='';
function isS23Canvas(){const ar=C.height/Math.max(1,C.width);return ar>=2.10&&ar<=2.18}
function s23Lum(data,w,x,y){
  x=Math.max(0,Math.min(w-1,Math.round(x)));y=Math.max(0,Math.min(C.height-1,Math.round(y)));
  const i=(y*w+x)*4;return .299*data[i]+.587*data[i+1]+.114*data[i+2]
}
function s23GridScore(data,k,off){
  const x0=C.width*k.x,y0=C.height*k.y+off,ww=C.width*k.w,hh=C.height*k.h,dx=ww/8,dy=hh/9;
  const d=Math.max(2,Math.round(C.width/295));let sum=0,n=0;
  for(let r=0;r<10;r++){const y=y0+r*dy;for(let c=0;c<8;c++){const x=x0+(c+.5)*dx,mid=s23Lum(data,C.width,x,y),adj=(s23Lum(data,C.width,x,y-d)+s23Lum(data,C.width,x,y+d))/2;sum+=Math.max(-20,Math.min(60,adj-mid));n++}}
  for(let c=0;c<9;c++){const x=x0+c*dx;for(let r=0;r<9;r++){const y=y0+(r+.5)*dy,mid=s23Lum(data,C.width,x,y),adj=(s23Lum(data,C.width,x-d,y)+s23Lum(data,C.width,x+d,y))/2;sum+=Math.max(-20,Math.min(60,adj-mid));n++}}
  return sum/Math.max(1,n)
}
function fitS23YOffset(){
  const stamp=C.width+'x'+C.height;
  if(stamp!==s23ProbeStamp){s23ProbeStamp=stamp;s23YOffset=0;s23ProbeTick=0}
  s23ProbeTick++;
  if(s23ProbeTick>1&&s23ProbeTick%8!==0)return;
  let img;try{img=C.getContext('2d',{willReadFrequently:true}).getImageData(0,0,C.width,C.height).data}catch(_){return}
  const step=Math.max(2,Math.round(C.width/300)),lo=-Math.round(C.width*.010),hi=Math.round(C.width*.040);
  let bestOff=s23YOffset,best=s23GridScore(img,SKIN_S23,s23YOffset);
  for(let off=lo;off<=hi;off+=step){const q=s23GridScore(img,SKIN_S23,off);if(q>best){best=q;bestOff=off}}
  s23YOffset=bestOff
}
const SKIN=SKIN_LEGACY;"""
if old not in s:
    raise SystemExit('v121 SKIN anchor missing')
s=s.replace(old,new,1)

old="function setSkinCrop(){crop={x:C.width*SKIN.x,y:C.height*SKIN.y,w:C.width*SKIN.w,h:C.height*SKIN.h};return crop}"
new="""function setSkinCrop(){
  if(isS23Canvas()){
    activeSkinProfile='s23-ultra-v121';
    fitS23YOffset();
    crop={x:C.width*SKIN_S23.x,y:C.height*SKIN_S23.y+s23YOffset,w:C.width*SKIN_S23.w,h:C.height*SKIN_S23.h};
  }else{
    activeSkinProfile='legacy';
    crop={x:C.width*SKIN_LEGACY.x,y:C.height*SKIN_LEGACY.y,w:C.width*SKIN_LEGACY.w,h:C.height*SKIN_LEGACY.h};
  }
  return crop
}"""
if old not in s:
    raise SystemExit('v121 setSkinCrop anchor missing')
s=s.replace(old,new,1)

s=s.replace("showStatus('象棋助手 1.0.21 淡化状态栏版','当前【'+modeText()+'】模式 · 模式选择3秒自动收起');",
            "showStatus('象棋助手 1.0.27 · 1.0.21稳定识别/S23版','当前【'+modeText()+'】模式 · 仅适配S23棋盘分辨率/上下位移');",1)

p.write_text(s)

p=Path('app/build.gradle')
g=p.read_text()
g=re.sub(r"versionName '[^']+'", "versionName '1.0.27-v121-s23-geometry'", g, count=1)
p.write_text(g)

p=Path('app/src/main/AndroidManifest.xml')
m=p.read_text()
m=re.sub(r'android:label="[^"]*"', 'android:label="象棋助手 1.0.27 · 1.0.21稳定识别/S23版"', m, count=1)
p.write_text(m)
