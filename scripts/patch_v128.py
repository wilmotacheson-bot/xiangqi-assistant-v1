from pathlib import Path
import re

# v1.0.28: keep the v1.0.21 recognition/tracking stack. Improve ONLY the S23
# geometry acquisition used when opening the assistant in the middle of a game.
#
# Why: from-start tracking is stable, but direct midgame entry sometimes stalls.
# In the user's 592x1280 recording a wrong initial y candidate can sample several
# empty grid intersections as pieces (e.g. 36 occupied squares, impossible in
# Xiangqi). v1.0.27 chose y mostly from grid-line contrast and then waited 8 frames
# before trying again. v1.0.28 adds an occupancy-separation sanity score and,
# while no board is locked yet, refits on every frame. Once currentBoard exists,
# the v1.0.27/v1.0.21 tracking behavior remains unchanged.

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

anchor="""function s23GridScore(data,k,off){
  const x0=C.width*k.x,y0=C.height*k.y+off,ww=C.width*k.w,hh=C.height*k.h,dx=ww/8,dy=hh/9;
  const d=Math.max(2,Math.round(C.width/295));let sum=0,n=0;
  for(let r=0;r<10;r++){const y=y0+r*dy;for(let c=0;c<8;c++){const x=x0+(c+.5)*dx,mid=s23Lum(data,C.width,x,y),adj=(s23Lum(data,C.width,x,y-d)+s23Lum(data,C.width,x,y+d))/2;sum+=Math.max(-20,Math.min(60,adj-mid));n++}}
  for(let c=0;c<9;c++){const x=x0+c*dx;for(let r=0;r<9;r++){const y=y0+(r+.5)*dy,mid=s23Lum(data,C.width,x,y),adj=(s23Lum(data,C.width,x-d,y)+s23Lum(data,C.width,x+d,y))/2;sum+=Math.max(-20,Math.min(60,adj-mid));n++}}
  return sum/Math.max(1,n)
}"""
if anchor not in s:
    raise SystemExit('v127 grid score anchor missing')

extra=anchor+"""
function s23OccupancyGeometryScore(k,off){
  const x0=C.width*k.x,y0=C.height*k.y+off,ww=C.width*k.w,hh=C.height*k.h,dx=ww/8,dy=hh/9,r=Math.min(dx,dy)*.43,darks=[];
  for(let y=0;y<10;y++)for(let x=0;x<9;x++)darks.push(pointStats(samplePatch(x0+x*dx,y0+y*dy,r)).dark);
  const hi=darks.filter(v=>v>=.090),lo=darks.filter(v=>v<.090);
  // A legal Xiangqi board can never contain more than 32 pieces and always has
  // at least two kings. Wrong vertical offsets often turn bare intersections
  // into fake occupied cells, so reject those geometries before glyph solving.
  if(hi.length<2||hi.length>32)return{ok:false,count:hi.length,sep:-1,bonus:-100};
  const minHi=Math.min(...hi),maxLo=lo.length?Math.max(...lo):0,sep=minHi-maxLo;
  return{ok:true,count:hi.length,sep,bonus:Math.max(0,sep)*50}
}"""
s=s.replace(anchor,extra,1)

old="""function fitS23YOffset(){
  const stamp=C.width+'x'+C.height;
  if(stamp!==s23ProbeStamp){s23ProbeStamp=stamp;s23YOffset=0;s23ProbeTick=0}
  s23ProbeTick++;
  if(s23ProbeTick>1&&s23ProbeTick%8!==0)return;
  let img;try{img=C.getContext('2d',{willReadFrequently:true}).getImageData(0,0,C.width,C.height).data}catch(_){return}
  const step=Math.max(2,Math.round(C.width/300)),lo=-Math.round(C.width*.010),hi=Math.round(C.width*.040);
  let bestOff=s23YOffset,best=s23GridScore(img,SKIN_S23,s23YOffset);
  for(let off=lo;off<=hi;off+=step){const q=s23GridScore(img,SKIN_S23,off);if(q>best){best=q;bestOff=off}}
  s23YOffset=bestOff
}"""
new="""function fitS23YOffset(){
  const stamp=C.width+'x'+C.height;
  if(stamp!==s23ProbeStamp){s23ProbeStamp=stamp;s23YOffset=0;s23ProbeTick=0}
  s23ProbeTick++;
  // Direct midgame/endgame entry has no trusted board yet, so refit every frame
  // until one is locked. After that keep the old lightweight every-8-frame check.
  if(currentBoard&&s23ProbeTick>1&&s23ProbeTick%8!==0)return;
  let img;try{img=C.getContext('2d',{willReadFrequently:true}).getImageData(0,0,C.width,C.height).data}catch(_){return}
  const step=Math.max(2,Math.round(C.width/300)),lo=-Math.round(C.width*.010),hi=Math.round(C.width*.040);
  let bestOff=s23YOffset,best=-1e9;
  for(let off=lo;off<=hi;off+=step){
    const oq=s23OccupancyGeometryScore(SKIN_S23,off);
    if(!oq.ok)continue;
    const q=s23GridScore(img,SKIN_S23,off)+oq.bonus;
    if(q>best){best=q;bestOff=off}
  }
  if(best>-1e8)s23YOffset=bestOff
}"""
if old not in s:
    raise SystemExit('v127 fit function anchor missing')
s=s.replace(old,new,1)

# User-visible version only; core recognition logic remains v1.0.21.
s=s.replace("showStatus('象棋助手 1.0.27 · 1.0.21稳定识别/S23版','当前【'+modeText()+'】模式 · 仅适配S23棋盘分辨率/上下位移');",
            "showStatus('象棋助手 1.0.28 · 1.0.21稳定识别/S23中途接管版','当前【'+modeText()+'】模式 · 中途打开会连续校准棋盘位置直到锁定');",1)

p.write_text(s)

p=Path('app/build.gradle')
g=p.read_text()
g=re.sub(r"versionName '[^']+'", "versionName '1.0.28-v121-s23-midgame-lock'", g, count=1)
p.write_text(g)

p=Path('app/src/main/AndroidManifest.xml')
m=p.read_text()
m=re.sub(r'android:label="[^"]*"', 'android:label="象棋助手 1.0.28 · 1.0.21稳定识别/S23中途接管版"', m, count=1)
p.write_text(m)
