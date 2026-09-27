from pathlib import Path
import re

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

# Replace the old single-template 12x12 winner-takes-all classifier with:
# 1) normalized high-resolution glyph descriptors,
# 2) per-device templates learned from a certain standard starting position,
# 3) strict ambiguity rejection instead of forced guessing.
start=s.find('function glyphVector(cx,cy,r,isR)')
end=s.find('\nfunction countPieces',start)
if start<0 or end<0:
    raise SystemExit('old glyph classifier block missing')

new=r"""const GLYPH_BANK_KEY='xiangqi_fixedskin_glyphbank_v3';
let glyphBank=null;
function loadGlyphBank(){try{const x=JSON.parse(localStorage.getItem(GLYPH_BANK_KEY)||'null');if(!x||x.version!==3||!x.samples)return null;return x}catch(_){return null}}
function saveGlyphBank(){try{if(glyphBank)localStorage.setItem(GLYPH_BANK_KEY,JSON.stringify(glyphBank))}catch(_){}}
glyphBank=loadGlyphBank();
function inkValue(R,G,B,isR){if((G-R>70&&B-R>70&&G>140&&B>160)||(G-R>12&&G-B>35&&G>110))return 0;const L=.299*R+.587*G+.114*B;if(isR)return Math.max(0,Math.min(1,((R-G)-32)/82))*Math.max(0,Math.min(1,(205-G)/118));return Math.max(0,Math.min(1,(142-L)/105))}
function glyphVector(cx,cy,r,isR){const size=48,c=document.createElement('canvas');c.width=c.height=size;const x=c.getContext('2d',{willReadFrequently:true});x.imageSmoothingEnabled=true;x.drawImage(C,cx-r*.62,cy-r*.62,r*1.24,r*1.24,0,0,size,size);const d=x.getImageData(0,0,size,size).data,v=[];for(let by=0;by<12;by++)for(let bx=0;bx<12;bx++){let ss=0,n=0;for(let yy=0;yy<4;yy++)for(let xx=0;xx<4;xx++){const i=((by*4+yy)*size+(bx*4+xx))*4;ss+=inkValue(d[i],d[i+1],d[i+2],isR);n++}v.push(ss/Math.max(1,n))}return v}
function glyphDescriptor(cx,cy,r,isR){const size=56,c=document.createElement('canvas');c.width=c.height=size;const x=c.getContext('2d',{willReadFrequently:true});x.imageSmoothingEnabled=true;x.drawImage(C,cx-r*.64,cy-r*.64,r*1.28,r*1.28,0,0,size,size);const d=x.getImageData(0,0,size,size).data,ink=new Float32Array(size*size);let minX=size,minY=size,maxX=-1,maxY=-1,energy=0;for(let y=0;y<size;y++)for(let z=0;z<size;z++){const i=(y*size+z)*4,v=inkValue(d[i],d[i+1],d[i+2],isR);ink[y*size+z]=v;energy+=v;if(v>.14){if(z<minX)minX=z;if(z>maxX)maxX=z;if(y<minY)minY=y;if(y>maxY)maxY=y}}if(maxX<0||energy<5)return{v:Array(400).fill(0),energy:0};const pad=2;minX=Math.max(0,minX-pad);minY=Math.max(0,minY-pad);maxX=Math.min(size-1,maxX+pad);maxY=Math.min(size-1,maxY+pad);const bw=Math.max(1,maxX-minX+1),bh=Math.max(1,maxY-minY+1),out=[];for(let ty=0;ty<20;ty++)for(let tx=0;tx<20;tx++){const sx0=minX+tx*bw/20,sx1=minX+(tx+1)*bw/20,sy0=minY+ty*bh/20,sy1=minY+(ty+1)*bh/20;let sum=0,n=0;for(let yy=Math.floor(sy0);yy<Math.ceil(sy1);yy++)for(let xx=Math.floor(sx0);xx<Math.ceil(sx1);xx++){if(xx>=minX&&xx<=maxX&&yy>=minY&&yy<=maxY){sum+=ink[yy*size+xx];n++}}out.push(sum/Math.max(1,n))}let mx=0;for(const v of out)if(v>mx)mx=v;if(mx>.01)for(let i=0;i<out.length;i++)out[i]=Math.min(1,out[i]/mx);return{v:out,energy}}
function sim(a,b){let ab=0,aa=0,bb=0;for(let i=0;i<a.length;i++){ab+=a[i]*b[i];aa+=a[i]*a[i];bb+=b[i]*b[i]}return ab/(Math.sqrt(aa*bb)+1e-9)}
function packedScore(v,p){let ab=0,aa=0,bb=0,mad=0,inter=0,sa=0,sb=0;for(let i=0;i<v.length;i++){const a=v[i],b=(p[i]||0)/255;ab+=a*b;aa+=a*a;bb+=b*b;mad+=Math.abs(a-b);const A=a>.20,B=b>.20;if(A)sa++;if(B)sb++;if(A&&B)inter++}const cos=ab/(Math.sqrt(aa*bb)+1e-9),shape=1-mad/v.length,f1=(2*inter)/(sa+sb+1e-9);return .50*cos+.28*shape+.22*f1}
function glyphBankReady(){const all=['K','A','B','N','R','C','P','k','a','b','n','r','c','p'];return !!(glyphBank&&all.every(p=>glyphBank.samples[p]&&glyphBank.samples[p].length))}
function bankScore(desc,p){if(!glyphBank||!glyphBank.samples[p]||!glyphBank.samples[p].length)return-1;let best=-1;for(const q of glyphBank.samples[p]){const sc=packedScore(desc.v,q);if(sc>best)best=sc}return best}
function classify(cx,cy,r,isR){const lo=glyphVector(cx,cy,r,isR),hi=glyphDescriptor(cx,cy,r,isR),cand=isR?['K','A','B','N','R','C','P']:['k','a','b','n','r','c','p'],ready=glyphBankReady(),scores=[];for(const p of cand){const base=sim(lo,TM[p]),bs=ready?bankScore(hi,p):-1,s=bs>=0?.84*bs+.16*base:base;scores.push({p,s,base,bank:bs})}scores.sort((a,b)=>b.s-a.s);return{p:scores[0].p,s:scores[0].s,margin:scores[0].s-scores[1].s,scores,calibrated:ready,energy:hi.energy}}
function learnGlyphBankFromStart(rawOcc,rawSide,r){try{if(!rawOcc||!rawSide||!crop)return false;if(glyphBank&&glyphBank.lastSession===SESSION_ID)return false;let diff=0,bR=0,bB=0;for(let i=0;i<90;i++){if(!!rawOcc[i]!==!!START_OCC[i])diff++;if(i>=45){if(rawSide[i]==='R')bR++;else if(rawSide[i]==='B')bB++}}if(diff>1||bR+bB<12)return false;const screenFlip=bB>bR,dx=crop.w/8,dy=crop.h/9,samples={};let captured=0;for(let i=0;i<90;i++){if(!rawOcc[i])continue;const j=screenFlip?89-i:i,p=START_BOARD[j];if(!p)continue;const expect=isRed(p)?'R':'B';if(rawSide[i]&&rawSide[i]!==expect)return false;const x=i%9,y=(i/9)|0,desc=glyphDescriptor(crop.x+x*dx,crop.y+y*dy,r,isRed(p));if(desc.energy<5)return false;(samples[p]||(samples[p]=[])).push(desc.v.map(v=>Math.max(0,Math.min(255,Math.round(v*255)))));captured++}const all=['K','A','B','N','R','C','P','k','a','b','n','r','c','p'];if(captured<30||!all.every(p=>samples[p]&&samples[p].length))return false;glyphBank={version:3,samples,lastSession:SESSION_ID,trainedAt:Date.now(),screen:[screenW,screenH]};saveGlyphBank();return true}catch(_){return false}}
function strictIdentityBoardOK(b,cands){if(!glyphBankReady())return true;for(let i=0;i<90;i++){const p=b[i];if(!p)continue;const arr=(cands[i]||[]).filter(q=>exactStaticSquareOK(q.p,i));if(!arr.length)return false;const mine=arr.find(q=>q.p===p);if(!mine||mine.s<.64)return false;const top=arr[0],second=arr[1];if(top&&top.p!==p&&top.s-mine.s>.028)return false;if(top&&top.p===p&&second&&top.s-second.s<.012&&top.s<.80)return false}return true}"""
s=s[:start]+new+s[end:]

old="const cl=classify(cx,cy,r,isR);cands[i]=cl.scores;if(cl.s<.42){unknown++;continue}next[i]=cl.p;found++;confidence+=cl.s"
new2="const cl=classify(cx,cy,r,isR);cands[i]=cl.scores;const minS=cl.calibrated?.64:.42,minM=cl.calibrated?.010:-1;if(cl.s<minS||cl.margin<minM){unknown++;continue}next[i]=cl.p;found++;confidence+=cl.s"
if old not in s:
    raise SystemExit('recognize classify threshold anchor missing')
s=s.replace(old,new2,1)

# Learn exact device glyphs only from a certain standard starting arrangement.
anchor="const occCount=occ.filter(Boolean).length;const occDiff=occ.reduce((n,v,i)=>n+(v!==START_OCC[i]),0);"
if anchor not in s:
    raise SystemExit('occCount anchor missing')
s=s.replace(anchor,anchor+"if(occDiff<=1&&!greenHit&&!cyanSeen)learnGlyphBankFromStart(rawOcc,rawSide,r);",1)

# Do not accept a globally repaired board when the calibrated glyph evidence still says
# one or more piece identities are ambiguous.
anchor2="return{b:next,occ,side,marker,found,occCount,score:confidence/Math.max(1,found),selected:greenHit,repaired:true,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn}}"
if anchor2 not in s:
    raise SystemExit('final recognition return anchor missing')
replacement="if(!strictIdentityBoardOK(next,cands))return{invalid:true,identityUncertain:true,found,unknown,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn};"+anchor2
s=s.replace(anchor2,replacement,1)

# Make the UI explicit that a reset/reconnect is a mandatory full 90-point re-identification.
old="showStatus('象棋助手 1.0.15 将军提示稳定版',restoredPending?'已恢复本次会话可信局面':'同一将军局面只触发一次 · 新局/残局仍可点“新局 / 接管”');"
new3="showStatus('象棋助手 1.0.16 精确棋子识别版',restoredPending?'已恢复本次会话可信局面':'每次重置/重开无障碍都全扫90点并重新识别所有棋子 · 标准开局自动校准本机字形');"
if old not in s:
    raise SystemExit('v115 startup title anchor missing')
s=s.replace(old,new3,1)

# Improve the failure message: ambiguity means wait/retry rather than inventing a piece.
s=s.replace("showStatus('当前棋面仍在重建','第 '+frameSeen+' 帧 · '+(rec.solverFailed?'全局棋子分配暂未唯一':'等待动画/高亮结束'));return",
            "showStatus('当前棋面仍在重建','第 '+frameSeen+' 帧 · '+(rec.identityUncertain?'有棋子字形不够确定，拒绝猜测':rec.solverFailed?'全局棋子分配暂未唯一':'等待动画/高亮结束'));return",1)

p.write_text(s)
