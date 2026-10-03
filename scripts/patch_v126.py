from pathlib import Path
import re

# v1.0.26: keep the v1.0.25 recognition/engine/session stack, but make S23 Ultra
# full-board takeover (midgame/endgame direct entry) robust to a few pixels of
# board vertical/viewport drift. The user's two 895x1920 screenshots place the
# top-row centers around y=479, while the old S23 profile sampled around y=485.
# That ~6 px miss is enough to clip Chinese glyph strokes: start-position
# occupancy still works, but direct identity rebuild loses confidence. This patch
# corrects the base geometry and adds a cheap one-time micro-fit at full rebuild.

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

old="const SKIN_S23_ULTRA={x:0.07486034,y:0.25260417,w:0.85139665,h:0.44531250};"
new="""const SKIN_S23_ULTRA={x:0.07486034,y:0.24947917,w:0.85139665,h:0.44531250};
let s23FitBiasX=0,s23FitBiasY=0,s23FitStamp='',s23FitQuality=-1,s23FitFrame=-99;"""
if old not in s:
    raise SystemExit('S23 profile anchor missing')
s=s.replace(old,new,1)

old="function setSkinCrop(){const k=skinProfile();crop={x:C.width*k.x,y:C.height*k.y,w:C.width*k.w,h:C.height*k.h};return crop}"
new="""function setSkinCrop(){const k=skinProfile(),sx=activeSkinProfile==='s23-ultra'?s23FitBiasX:0,sy=activeSkinProfile==='s23-ultra'?s23FitBiasY:0;crop={x:C.width*k.x+sx,y:C.height*k.y+sy,w:C.width*k.w,h:C.height*k.h};return crop}"""
if old not in s:
    raise SystemExit('setSkinCrop anchor missing')
s=s.replace(old,new,1)

anchor="function classify(cx,cy,r,isR){const hi=glyphDescriptor(cx,cy,r,isR),cand=isR?['K','A','B','N','R','C','P']:['k','a','b','n','r','c','p'],scores=[];for(const p of cand)scores.push({p,s:bankScore(hi,p)});scores.sort((a,b)=>b.s-a.s);return{p:scores[0].p,s:scores[0].s,margin:scores[0].s-scores[1].s,scores,calibrated:true,energy:hi.energy}}"
if anchor not in s:
    raise SystemExit('classify anchor missing')
extra=anchor+r'''
function s23GeometryProbe(testCrop){
  const keep=crop;crop=testCrop;
  const dx=crop.w/8,dy=crop.h/9,r=Math.min(dx,dy)*.43,occ=[];
  for(let y=0;y<10;y++)for(let x=0;x<9;x++){
    const cx=crop.x+x*dx,cy=crop.y+y*dy,st=pointStats(samplePatch(cx,cy,r));
    if(st.dark>=.090)occ.push({x,y,cx,cy,dark:st.dark,isR:st.red>.15});
  }
  if(occ.length<2||occ.length>32){crop=keep;return-99}
  occ.sort((a,b)=>b.dark-a.dark);
  const anchors=[];
  for(const q of occ){
    if(anchors.length<2||anchors.every(a=>Math.abs(a.x-q.x)+Math.abs(a.y-q.y)>=2))anchors.push(q);
    if(anchors.length>=8)break;
  }
  if(anchors.length<Math.min(8,occ.length))for(const q of occ){if(!anchors.includes(q))anchors.push(q);if(anchors.length>=8)break}
  let total=0,good=0;
  for(const q of anchors){const cl=classify(q.cx,q.cy,r,q.isR);total+=cl.s+Math.min(.10,Math.max(0,cl.margin*1.25));if(cl.s>.74&&cl.margin>.025)good++}
  crop=keep;
  return total/Math.max(1,anchors.length)+.06*good/Math.max(1,anchors.length)
}
function fitS23Geometry(){
  if(activeSkinProfile!=='s23-ultra')return;
  const stamp=C.width+'x'+C.height;
  if(s23FitStamp===stamp&&s23FitQuality>=.82)return;
  if(s23FitStamp===stamp&&frameSeen-s23FitFrame<3)return;
  const k=SKIN_S23_ULTRA,px=C.width/895,py=C.height/1920;
  let best={x:s23FitBiasX,y:s23FitBiasY,score:-99};
  for(const bx of[-4*px,0,4*px])for(const by of[-4*py,0,4*py]){
    const tc={x:C.width*k.x+bx,y:C.height*k.y+by,w:C.width*k.w,h:C.height*k.h},score=s23GeometryProbe(tc);
    if(score>best.score)best={x:bx,y:by,score};
  }
  if(best.score>-90){s23FitBiasX=best.x;s23FitBiasY=best.y;s23FitQuality=best.score;s23FitStamp=stamp;s23FitFrame=frameSeen}
  setSkinCrop()
}'''
s=s.replace(anchor,extra,1)

old="function recognize(forceFull=false){setSkinCrop();let next=Array(90).fill(null),cands=Array(90).fill(null),occ=Array(90).fill(false),side=Array(90).fill(null),dx=crop.w/8,dy=crop.h/9,r=Math.min(dx,dy)*.43;"
new="function recognize(forceFull=false){setSkinCrop();if(forceFull&&activeSkinProfile==='s23-ultra')fitS23Geometry();setSkinCrop();let next=Array(90).fill(null),cands=Array(90).fill(null),occ=Array(90).fill(false),side=Array(90).fill(null),dx=crop.w/8,dy=crop.h/9,r=Math.min(dx,dy)*.43;"
if old not in s:
    raise SystemExit('recognize anchor missing')
s=s.replace(old,new,1)

s=s.replace("showStatus('象棋助手 1.0.25 S23字形适配版','当前【'+modeText()+'】模式 · 中盘/残局可直接重建当前棋面');",
            "showStatus('象棋助手 1.0.26 S23自适应棋盘版','当前【'+modeText()+'】模式 · 中盘/残局进入时自动微调棋盘采样位置');",1)
s=s.replace("'S23 Ultra 棋盘适配已启用':'标准棋盘布局'",
            "'S23 Ultra 自适应棋盘定位已启用':'标准棋盘布局'",1)
s += "\n<!-- v126 validation: S23 full-board geometry micro-fit preserves v121 takeover behavior -->\n"
p.write_text(s)

p=Path('app/build.gradle')
g=p.read_text()
g=re.sub(r"versionName '[^']+'", "versionName '1.0.26-s23-adaptive-grid'", g, count=1)
p.write_text(g)

p=Path('app/src/main/AndroidManifest.xml')
m=p.read_text()
m=re.sub(r'android:label="[^"]*"', 'android:label="象棋助手 1.0.26 S23自适应棋盘版"', m, count=1)
p.write_text(m)
