from pathlib import Path

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

def must(old,new,label,count=1):
    global s
    if old not in s:
        raise SystemExit(f'{label} missing')
    s=s.replace(old,new,count)

must(
"const GLYPH_BANK_KEY='xiangqi_fixedskin_glyphbank_v3';\nlet glyphBank=null;",
"const GLYPH_BANK_KEY='xiangqi_fixedskin_glyphbank_v4';\nlet glyphBank=null;\nlet glyphCal={sig:'',frames:[]};",
'glyph bank v4'
)

start=s.find('function learnGlyphBankFromStart(rawOcc,rawSide,r)')
end=s.find('\nfunction strictIdentityBoardOK',start)
if start<0 or end<0:
    raise SystemExit('learnGlyphBankFromStart block missing')

new=r"""function medianVec(samples){if(!samples||!samples.length)return null;const n=samples[0].length,out=new Array(n);for(let i=0;i<n;i++){const a=samples.map(v=>v[i]).sort((x,y)=>x-y),m=a.length>>1;out[i]=a.length%2?a[m]:(a[m-1]+a[m])/2}return out}
function validateGlyphCandidate(samples,packed){const all=['K','A','B','N','R','C','P','k','a','b','n','r','c','p'];for(const p of all){const arr=samples[p]||[];if(!arr.length||!packed[p]||!packed[p].length)return false;for(const v of arr){let own=packedScore(v,packed[p][0]),second=-1;for(const q of all){if(q===p||isRed(q)!==isRed(p))continue;const sc=packedScore(v,packed[q][0]);if(sc>second)second=sc}if(own<.70||own-second<.020)return false}}return true}
function learnGlyphBankFromStart(rawOcc,rawSide,r){try{
  if(glyphBankReady())return true;
  if(!rawOcc||!rawSide||!crop)return false;
  let diff=0,bR=0,bB=0;
  for(let i=0;i<90;i++){if(!!rawOcc[i]!==!!START_OCC[i])diff++;if(i>=45){if(rawSide[i]==='R')bR++;else if(rawSide[i]==='B')bB++}}
  if(diff!==0||Math.max(bR,bB)<14||Math.abs(bR-bB)<10){glyphCal={sig:'',frames:[]};return false}
  const screenFlip=bB>bR,dx=crop.w/8,dy=crop.h/9,pieces=[];
  for(let i=0;i<90;i++){if(!rawOcc[i])continue;const j=screenFlip?89-i:i,p=START_BOARD[j];if(!p){glyphCal={sig:'',frames:[]};return false}const expect=isRed(p)?'R':'B';if(rawSide[i]!==expect){glyphCal={sig:'',frames:[]};return false}const x=i%9,y=(i/9)|0,desc=glyphDescriptor(crop.x+x*dx,crop.y+y*dy,r,isRed(p));if(desc.energy<5){glyphCal={sig:'',frames:[]};return false}pieces.push({i,p,v:desc.v})}
  if(pieces.length!==32){glyphCal={sig:'',frames:[]};return false}
  const sig=(screenFlip?'1':'0')+'|'+rawOcc.map(v=>v?'1':'0').join('')+'|'+rawSide.map(v=>v||'-').join('');
  const frame={pieces};
  if(glyphCal.sig!==sig){glyphCal={sig,frames:[frame]};return false}
  const prev=glyphCal.frames[glyphCal.frames.length-1];
  if(prev){let sum=0,n=0;for(let k=0;k<pieces.length;k++){if(prev.pieces[k].i!==pieces[k].i||prev.pieces[k].p!==pieces[k].p){glyphCal={sig,frames:[frame]};return false}sum+=sim(prev.pieces[k].v,pieces[k].v);n++}if(sum/Math.max(1,n)<.90){glyphCal={sig,frames:[frame]};return false}}
  glyphCal.frames.push(frame);
  if(glyphCal.frames.length<5)return false;
  const pooled={};for(const fr of glyphCal.frames.slice(-5))for(const q of fr.pieces)(pooled[q.p]||(pooled[q.p]=[])).push(q.v);
  const all=['K','A','B','N','R','C','P','k','a','b','n','r','c','p'],packed={};
  for(const p of all){const med=medianVec(pooled[p]);if(!med){glyphCal={sig:'',frames:[]};return false}packed[p]=[med.map(v=>Math.max(0,Math.min(255,Math.round(v*255))))]}
  if(!validateGlyphCandidate(pooled,packed)){glyphCal={sig,frames:[frame]};return false}
  glyphBank={version:4,samples:packed,trainedAt:Date.now(),screen:[screenW,screenH],stableFrames:5};
  saveGlyphBank();glyphCal={sig:'',frames:[]};return true
}catch(_){glyphCal={sig:'',frames:[]};return false}}"""
s=s[:start]+new+s[end:]

old="const occCount=occ.filter(Boolean).length;const occDiff=occ.reduce((n,v,i)=>n+(v!==START_OCC[i]),0);if(occDiff<=1&&!greenHit&&!cyanSeen)learnGlyphBankFromStart(rawOcc,rawSide,r);let commanderRed="
new2="const occCount=occ.filter(Boolean).length;const occDiff=occ.reduce((n,v,i)=>n+(v!==START_OCC[i]),0);if(!greenHit&&!cyanSeen)learnGlyphBankFromStart(rawOcc,rawSide,r);if(!glyphBankReady())return{invalid:true,needsCalibration:true,calFrames:glyphCal.frames.length,found:occCount,occCount,marker,selected:greenHit,occ,side,uiTurn};let commanderRed="
must(old,new2,'mandatory calibration gate')

old="showStatus('当前棋面仍在重建','第 '+frameSeen+' 帧 · '+(rec.identityUncertain?'有棋子字形不够确定，拒绝猜测':rec.solverFailed?'全局棋子分配暂未唯一':'等待动画/高亮结束'));return"
new3="showStatus(rec.needsCalibration?'棋子模板校准中':'当前棋面仍在重建',rec.needsCalibration?(rec.calFrames>0?'标准开局保持静止 · '+rec.calFrames+'/5 帧':'首次使用请先停留在完整标准开局，校准后以后不再重学'):'第 '+frameSeen+' 帧 · '+(rec.identityUncertain?'有棋子字形不够确定，拒绝猜测':rec.solverFailed?'全局棋子分配暂未唯一':'等待动画/高亮结束'));return"
must(old,new3,'calibration UI')

old="showStatus('象棋助手 1.0.16 精确棋子识别版',restoredPending?'已恢复本次会话可信局面':'每次重置/重开无障碍都全扫90点并重新识别所有棋子 · 标准开局自动校准本机字形');"
new4="showStatus('象棋助手 1.0.17 稳定字形库版',restoredPending?'已恢复本次会话可信局面':'首次标准开局连续5帧校准并锁定模板 · 以后重置只全盘重识别，不再覆盖模板');"
must(old,new4,'v117 startup')

p.write_text(s)
