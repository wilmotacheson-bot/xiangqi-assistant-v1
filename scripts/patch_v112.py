from pathlib import Path
import re

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

def must(old,new,label,count=1):
    global s
    if old not in s:
        raise SystemExit(f'{label} missing')
    s=s.replace(old,new,count)

must("const STATE_KEY='xiangqi_v111_trusted_state';let restoredPending=false;let sideProbeValue=null,sideProbeCount=0;",
     "const STATE_KEY='xiangqi_v112_trusted_state';let restoredPending=false;let sideProbeValue=null,sideProbeCount=0;",'state key')

must("function noteBottomSide(v){if(v===null||v===undefined){sideProbeValue=null;sideProbeCount=0;return false}if(sideProbeValue===v)sideProbeCount++;else{sideProbeValue=v;sideProbeCount=1}return sideProbeCount>=2}",
     "function noteBottomSide(v){if(v===null||v===undefined){sideProbeValue=null;sideProbeCount=0;return false}if(sideProbeValue===v)sideProbeCount++;else{sideProbeValue=v;sideProbeCount=1}return sideProbeCount>=3}",'side debounce')

anchor="function detectBottomCommanderQuick(occ,side,r){let best=null,dx=crop.w/8,dy=crop.h/9;for(let y=7;y<=9;y++)for(let x=3;x<=5;x++){const i=y*9+x;if(!occ[i]||!side[i])continue;const isR=side[i]==='R',cx=crop.x+x*dx,cy=crop.y+y*dy,cl=classify(cx,cy,r,isR),king=isR?'K':'k',q=cl.scores.find(z=>z.p===king),sc=q?q.s:-9;if((cl.p===king&&cl.s>.30)||sc>.52){if(!best||sc>best.sc)best={red:isR,sc}}}return best?best.red:null}"
extra=anchor+"""
function detectBottomPalaceColor(occ,side){let r=0,b=0;for(let y=7;y<=9;y++)for(let x=3;x<=5;x++){const i=y*9+x;if(!occ[i])continue;if(side[i]==='R')r++;else if(side[i]==='B')b++}if(r===0&&b===0)return null;if(r>=b+1)return true;if(b>=r+1)return false;return null}
function exactStaticSquareOK(p,i){const x=i%9,y=(i/9)|0;if(p==='K')return x>=3&&x<=5&&y>=7&&y<=9;if(p==='k')return x>=3&&x<=5&&y>=0&&y<=2;if(p==='A')return [[3,9],[5,9],[4,8],[3,7],[5,7]].some(q=>q[0]===x&&q[1]===y);if(p==='a')return [[3,0],[5,0],[4,1],[3,2],[5,2]].some(q=>q[0]===x&&q[1]===y);if(p==='B')return [[2,9],[6,9],[0,7],[4,7],[8,7],[2,5],[6,5]].some(q=>q[0]===x&&q[1]===y);if(p==='b')return [[2,0],[6,0],[0,2],[4,2],[8,2],[2,4],[6,4]].some(q=>q[0]===x&&q[1]===y);if(p==='P')return y<=6&&(y<=4||x%2===0);if(p==='p')return y>=3&&(y>=5||x%2===0);return true}
function solveSideGlobal(indices,cands,red){const types=red?['K','A','B','N','R','C','P']:['k','a','b','n','r','c','p'],caps=[1,2,2,2,2,2,5],items=[];for(const i of indices){const a=(cands[i]||[]).filter(q=>types.includes(q.p)&&exactStaticSquareOK(q.p,i));if(!a.length)return null;items.push({i,a:a.slice(0,7)})}items.sort((u,v)=>u.a.length-v.a.length||((v.a[0]?.s||0)-(v.a[1]?.s||0))-((u.a[0]?.s||0)-(u.a[1]?.s||0)));let states=[{cnt:[0,0,0,0,0,0,0],score:0,a:[]}];for(const it of items){const next=new Map();for(const st of states){for(let rank=0;rank<it.a.length;rank++){const q=it.a[rank],k=types.indexOf(q.p);if(k<0||st.cnt[k]>=caps[k])continue;const cnt=st.cnt.slice();cnt[k]++;const key=cnt.join(','),score=st.score+q.s-(rank*.006),cand={cnt,score,a:st.a.concat([[it.i,q.p]])},old=next.get(key);if(!old||cand.score>old.score)next.set(key,cand)}}states=[...next.values()].sort((a,b)=>b.score-a.score).slice(0,1400);if(!states.length)return null}const ok=states.filter(st=>st.cnt[0]===1).sort((a,b)=>b.score-a.score);return ok.length?ok[0]:null}
function solveGlobalBoard(cands,occ,side){const ri=[],bi=[];for(let i=0;i<90;i++)if(occ[i]){if(side[i]==='R')ri.push(i);else if(side[i]==='B')bi.push(i);else return null}if(ri.length>16||bi.length>16)return null;const rs=solveSideGlobal(ri,cands,true),bs=solveSideGlobal(bi,cands,false);if(!rs||!bs)return null;const b=Array(90).fill(null);for(const [i,p] of rs.a)b[i]=p;for(const [i,p] of bs.a)b[i]=p;return validCounts(b)?b:null}
"""
must(anchor,extra,'global solver anchor')

old_fast="if(currentBoard&&!forceFull){const bottomRed=detectBottomCommanderQuick(rawOcc,rawSide,r),frameFlip=bottomRed===null?flipped:!bottomRed,marker=detectLastMoveMarkers(rawOcc,frameFlip);if(frameFlip){occ.reverse();side.reverse()}return{occ,side,marker,selected:greenHit,cyan:cyanSeen,found:occ.filter(Boolean).length,bottomRed,uiTurn}}"
new_fast="if(currentBoard&&!forceFull){const bottomRed=detectBottomCommanderQuick(rawOcc,rawSide,r),occDiffFast=rawOcc.reduce((n,v,i)=>n+(v!==START_OCC[i]),0),nearStart=occDiffFast<=2,frameFlip=flipped,marker=detectLastMoveMarkers(rawOcc,frameFlip);if(frameFlip){occ.reverse();side.reverse()}return{occ,side,marker,selected:greenHit,cyan:cyanSeen,found:occ.filter(Boolean).length,bottomRed,uiTurn,nearStart}}"
must(old_fast,new_fast,'locked orientation fast path')

old_full="const occCount=occ.filter(Boolean).length;const occDiff=occ.reduce((n,v,i)=>n+(v!==START_OCC[i]),0);let commanderRed=detectBottomCommanderSide(cands,side);if(commanderRed===null&&occDiff<=1&&side[85])commanderRed=side[85]==='R';if(commanderRed!==null){userRed=commanderRed;autoSideKnown=true;flipped=!userRed}"
new_full="const occCount=occ.filter(Boolean).length;const occDiff=occ.reduce((n,v,i)=>n+(v!==START_OCC[i]),0);let commanderRed=detectBottomCommanderSide(cands,side);if(commanderRed===null)commanderRed=detectBottomPalaceColor(rawOcc,rawSide);if(commanderRed===null&&occDiff<=1&&side[85])commanderRed=side[85]==='R';if(commanderRed!==null){userRed=commanderRed;autoSideKnown=true;flipped=!userRed}"
must(old_full,new_full,'palace side fallback')

old_repair="if(unknown>0){const repairedUnknown=repairUnknownFull(next,cands,occ,side);if(repairedUnknown){next=repairedUnknown;unknown=0}else if(unknown>7)return{unknown,found,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn}}if(!validCounts(next)){const repaired=repairStartup(next,cands);if(repaired)next=repaired;else return{invalid:true,found,unknown,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn}}return{b:next,occ,side,marker,found,occCount,score:confidence/Math.max(1,found),selected:greenHit,repaired:true,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn}}"
new_repair="if(unknown>0||!validCounts(next)){const solved=solveGlobalBoard(cands,occ,side);if(solved){next=solved;unknown=0}else{const repairedUnknown=repairUnknownFull(next,cands,occ,side);if(repairedUnknown){next=repairedUnknown;unknown=0}if(!validCounts(next)){const repaired=repairStartup(next,cands);if(repaired)next=repaired;else return{invalid:true,found,unknown,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn,solverFailed:true}}}}return{b:next,occ,side,marker,found,occCount,score:confidence/Math.max(1,found),selected:greenHit,repaired:true,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn}}"
must(old_repair,new_repair,'global repair flow')

old_side="""  if(!rec.selected&&rec.bottomRed!==null&&rec.bottomRed!==undefined&&noteBottomSide(rec.bottomRed)){
    if(autoSideKnown&&rec.bottomRed!==userRed){const nr=!!rec.bottomRed;resetForSide(nr);showStatus('检测到新对局/红黑换边','已自动切换为'+(nr?'红方':'黑方')+' · 正在按当前棋面重建');return}
    if(!autoSideKnown){userRed=!!rec.bottomRed;autoSideKnown=true;flipped=!userRed}
  }"""
new_side="""  if(currentBoard&&!rec.nearStart){sideProbeValue=null;sideProbeCount=0}
  if(!rec.selected&&rec.bottomRed!==null&&rec.bottomRed!==undefined&&(!currentBoard||rec.nearStart)&&noteBottomSide(rec.bottomRed)){
    if(autoSideKnown&&rec.bottomRed!==userRed){const nr=!!rec.bottomRed;resetForSide(nr);showStatus('检测到新对局/红黑换边','开局区域连续3帧确认 · 已切换为'+(nr?'红方':'黑方'));return}
    if(!autoSideKnown){userRed=!!rec.bottomRed;autoSideKnown=true;flipped=!userRed}
  }"""
must(old_side,new_side,'side reset only near start')

old_unknown="showStatus('棋子识别不够确定','第 '+frameSeen+' 帧 · 等待稳定');return"
new_unknown="showStatus('正在重建当前棋面','已识别 '+(rec.found||0)+'/'+(rec.occCount||'?')+' 子 · 正在用全局约束纠错');return"
s=s.replace(old_unknown,new_unknown,1)
old_invalid="showStatus('棋盘局面校验未通过','第 '+frameSeen+' 帧 · 等待动画/高亮结束');return"
new_invalid="showStatus('当前棋面仍在重建','第 '+frameSeen+' 帧 · '+(rec.solverFailed?'全局棋子分配暂未唯一':'等待动画/高亮结束'));return"
s=s.replace(old_invalid,new_invalid,1)

old_start="try{localStorage.removeItem('xiangqi_v107_trusted_state');localStorage.removeItem('xiangqi_v108_trusted_state');localStorage.removeItem('xiangqi_v109_trusted_state');localStorage.removeItem('xiangqi_v110_trusted_state')}catch(_){}restoreTrustedState();requestEngineWarmUp();showStatus('象棋助手 1.0.11 黑方/中途接管版',restoredPending?'已载入本版可信局面 · 将用当前画面复核':'每局重新判边 · 头像绿框判回合 · 支持中途接管');"
new_start="try{localStorage.removeItem('xiangqi_v107_trusted_state');localStorage.removeItem('xiangqi_v108_trusted_state');localStorage.removeItem('xiangqi_v109_trusted_state');localStorage.removeItem('xiangqi_v110_trusted_state');localStorage.removeItem('xiangqi_v111_trusted_state')}catch(_){}restoreTrustedState();requestEngineWarmUp();showStatus('象棋助手 1.0.12 连续对局稳定版',restoredPending?'已载入可信局面 · 本局朝向锁定后不再随帧改变':'整局锁定棋盘朝向 · 中途进场使用全局棋子约束重建');"
must(old_start,new_start,'startup')

p.write_text(s)
