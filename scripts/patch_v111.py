from pathlib import Path
import re
p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

def must(old,new,label,count=1):
    global s
    if old not in s:
        raise SystemExit(f'{label} missing')
    s=s.replace(old,new,count)

must("const STATE_KEY='xiangqi_v110_trusted_state';let restoredPending=false;",
     "const STATE_KEY='xiangqi_v111_trusted_state';let restoredPending=false;let sideProbeValue=null,sideProbeCount=0;",'state key')

anchor="function sideText(){return userRed?'红方':'黑方'}"
extra=anchor+"""
function greenRatioRect(rx1,ry1,rx2,ry2){try{const x1=Math.max(0,Math.floor(screenW*rx1)),y1=Math.max(0,Math.floor(screenH*ry1)),x2=Math.min(screenW,Math.ceil(screenW*rx2)),y2=Math.min(screenH,Math.ceil(screenH*ry2));if(x2-x1<4||y2-y1<4)return 0;const d=ctx.getImageData(x1,y1,x2-x1,y2-y1).data;let hit=0,n=0;for(let y=0;y<y2-y1;y+=2)for(let x=0;x<x2-x1;x+=2){const i=(y*(x2-x1)+x)*4,R=d[i],G=d[i+1],B=d[i+2];n++;if(G>160&&G-R>60&&G-B>30)hit++}return hit/Math.max(1,n)}catch(_){return 0}}
function detectUiTurn(){const top=greenRatioRect(.027,.050,.055,.100),bottom=greenRatioRect(.833,.930,.862,.985);if(bottom>.22&&bottom>top+.12)return'me';if(top>.22&&top>bottom+.12)return'opp';return null}
function noteBottomSide(v){if(v===null||v===undefined){sideProbeValue=null;sideProbeCount=0;return false}if(sideProbeValue===v)sideProbeCount++;else{sideProbeValue=v;sideProbeCount=1}return sideProbeCount>=2}
function resetForSide(red){userRed=!!red;autoSideKnown=true;flipped=!userRed;currentBoard=null;currentHash='';turn='unknown';hint=null;analysisRunning=false;restoredPending=false;clearArrow();clearTrustedState();fullStableKey='';fullStableCount=0;untrackedFrames=0;obsKey='';obsStable=0;lastOcc=null;lastSide=null}
"""
must(anchor,extra,'ui turn anchor')

anchor2="function candScore(cands,i,p){const a=cands[i];if(!a)return-9;const q=a.find(x=>x.p===p);return q?q.s:-9}function detectBottomCommanderSide(cands,side){let best=null;for(let y=7;y<=9;y++)for(let x=3;x<=5;x++){const i=y*9+x;if(!side[i]||!cands[i]||!cands[i].length)continue;const king=side[i]==='R'?'K':'k',top=cands[i][0],sc=candScore(cands,i,king);if((top.p===king&&top.s>.26)||sc>.48){if(!best||sc>best.sc)best={red:side[i]==='R',sc}}}return best?best.red:null}"
extra2=anchor2+"""
function detectBottomCommanderQuick(occ,side,r){let best=null,dx=crop.w/8,dy=crop.h/9;for(let y=7;y<=9;y++)for(let x=3;x<=5;x++){const i=y*9+x;if(!occ[i]||!side[i])continue;const isR=side[i]==='R',cx=crop.x+x*dx,cy=crop.y+y*dy,cl=classify(cx,cy,r,isR),king=isR?'K':'k',q=cl.scores.find(z=>z.p===king),sc=q?q.s:-9;if((cl.p===king&&cl.s>.30)||sc>.52){if(!best||sc>best.sc)best={red:isR,sc}}}return best?best.red:null}
"""
must(anchor2,extra2,'quick commander anchor')

old="""const rawOcc=occ.slice(),rawSide=side.slice();
if(currentBoard&&!forceFull){const marker=detectLastMoveMarkers(rawOcc,flipped);if(flipped){occ.reverse();side.reverse()}return{occ,side,marker,selected:greenHit,cyan:cyanSeen,found:occ.filter(Boolean).length}}
const occCount=occ.filter(Boolean).length;"""
new="""const rawOcc=occ.slice(),rawSide=side.slice();
const uiTurn=detectUiTurn();
if(currentBoard&&!forceFull){const bottomRed=detectBottomCommanderQuick(rawOcc,rawSide,r),frameFlip=bottomRed===null?flipped:!bottomRed,marker=detectLastMoveMarkers(rawOcc,frameFlip);if(frameFlip){occ.reverse();side.reverse()}return{occ,side,marker,selected:greenHit,cyan:cyanSeen,found:occ.filter(Boolean).length,bottomRed,uiTurn}}
const occCount=occ.filter(Boolean).length;"""
must(old,new,'recognize tracking')

s=s.replace("return{b:START_BOARD.slice(),occ,side,marker,found:32,occCount,score:1,selected:greenHit,start:true,autoRed:autoSideKnown?userRed:null}",
            "return{b:START_BOARD.slice(),occ,side,marker,found:32,occCount,score:1,selected:greenHit,start:true,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn}",1)
s=s.replace("return{unknown,found,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null}",
            "return{unknown,found,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn}",1)
s=s.replace("return{invalid:true,found,unknown,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null}",
            "return{invalid:true,found,unknown,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn}",1)
s=s.replace("return{b:next,occ,side,marker,found,occCount,score:confidence/Math.max(1,found),selected:greenHit,repaired:true,autoRed:autoSideKnown?userRed:null}",
            "return{b:next,occ,side,marker,found,occCount,score:confidence/Math.max(1,found),selected:greenHit,repaired:true,autoRed:autoSideKnown?userRed:null,bottomRed:commanderRed,uiTurn}",1)

old_engine="""function pollEngineRecovery(started){if(engineRecoveryTimer)clearTimeout(engineRecoveryTimer);engineRecoveryTimer=setTimeout(()=>{engineRecoveryTimer=0;if(engineReady()){engineFailCount=0;engineRetryAt=0;if(turn==='me'&&!hint&&!analysisRunning)setTimeout(analyzeCurrent,40);return}if(Date.now()-started<6500){pollEngineRecovery(started);return}showStatus('Pikafish 启动失败','本次恢复超过6秒 · 等待下一次棋面变化再重试')},350)}
function scheduleEngineRecovery(reason){if(engineRecoveryTimer)return;engineFailCount=Math.min(3,engineFailCount+1);engineRetryAt=Date.now()+500;try{if(window.AndroidEngine&&AndroidEngine.resetEngine)AndroidEngine.resetEngine()}catch(_){}pollEngineRecovery(Date.now())}"""
new_engine="""function requestEngineWarmUp(){try{if(window.AndroidEngine&&AndroidEngine.warmUp)AndroidEngine.warmUp()}catch(_){}}
function pollEngineRecovery(started,kick=false){if(kick)requestEngineWarmUp();if(engineRecoveryTimer)clearTimeout(engineRecoveryTimer);engineRecoveryTimer=setTimeout(()=>{engineRecoveryTimer=0;if(engineReady()){engineFailCount=0;engineRetryAt=0;if(turn==='me'&&!hint&&!analysisRunning)setTimeout(analyzeCurrent,40);return}if(Date.now()-started<10000){pollEngineRecovery(started,false);return}showStatus('Pikafish 仍在启动','棋盘与回合已锁定 · 下一次会继续尝试启动引擎')},350)}
function scheduleEngineRecovery(reason){if(engineRecoveryTimer)return;engineFailCount=Math.min(3,engineFailCount+1);engineRetryAt=Date.now()+500;try{if(window.AndroidEngine&&AndroidEngine.resetEngine)AndroidEngine.resetEngine()}catch(_){}pollEngineRecovery(Date.now(),false)}"""
must(old_engine,new_engine,'engine recovery')

s=s.replace("if(!engineReady()){showStatus('Pikafish 正在预热','局面已确认（'+checkMs+'ms）· 引擎就绪后自动计算');if(!engineRecoveryTimer)pollEngineRecovery(Date.now());return}",
            "if(!engineReady()){showStatus('Pikafish 正在预热','局面已确认（'+checkMs+'ms）· 正在主动启动引擎');if(!engineRecoveryTimer)pollEngineRecovery(Date.now(),true);return}",1)
s=s.replace("if(e&&e.warming){showStatus('Pikafish 正在预热','局面已经确认 · 引擎就绪后自动计算');if(!engineRecoveryTimer)pollEngineRecovery(Date.now())}",
            "if(e&&e.warming){showStatus('Pikafish 正在预热','局面已经确认 · 正在主动启动引擎');if(!engineRecoveryTimer)pollEngineRecovery(Date.now(),true)}",1)

m=re.search(r"function acceptStable\(rec\)\{.*?\n\}\nfunction handleNoBoard",s,re.S)
if not m:
    raise SystemExit('acceptStable block missing')
accept="""function acceptStable(rec){
  if(!rec)return;misses=0;if(rec.occ&&rec.side){lastOcc=rec.occ.slice();lastSide=rec.side.slice()}
  const uiTurn=rec.uiTurn||detectUiTurn();
  if(!rec.selected&&rec.bottomRed!==null&&rec.bottomRed!==undefined&&noteBottomSide(rec.bottomRed)){
    if(autoSideKnown&&rec.bottomRed!==userRed){const nr=!!rec.bottomRed;resetForSide(nr);showStatus('检测到新对局/红黑换边','已自动切换为'+(nr?'红方':'黑方')+' · 正在按当前棋面重建');return}
    if(!autoSideKnown){userRed=!!rec.bottomRed;autoSideKnown=true;flipped=!userRed}
  }
  if(rec.selected){if(uiTurn)turn=uiTurn;if(hint&&turn==='me')drawMove(hint.m);showStatus('已提子 · 提示保持','箭头会保留到落子完成');fullStableKey='';fullStableCount=0;return}
  if(restoredPending&&currentBoard&&rec.occ&&rec.side){if(currentMapMatch(currentBoard,rec.occ,rec.side)){restoredPending=false;if(uiTurn)turn=uiTurn;showStatus('已恢复上一可信局面','画面校验通过 · '+sideText())}else{currentBoard=null;currentHash='';turn='unknown';restoredPending=false;clearTrustedState();autoSideKnown=false;showStatus('旧局面与当前画面不同','已丢弃缓存 · 正在从当前棋面重建');return}}
  if(currentBoard&&!rec.b&&rec.occ&&rec.side){
    const obs=noteObservation(rec),ringTurn=markerTurnFromMap(rec);
    if(currentMapMatch(currentBoard,rec.occ,rec.side)){
      untrackedFrames=0;if(uiTurn)turn=uiTurn;else if(ringTurn)turn=ringTurn;
      if(kingInCheck(currentBoard,userRed)){turn='me';hint=null;clearArrow();saveTrustedState();showStatus('检测到对方将军','立即计算应将/解杀');if(!analysisRunning)setTimeout(analyzeCurrent,20);return}
      saveTrustedState();
      if(turn==='me'){if(hint)drawMove(hint.m);else if(!analysisRunning)setTimeout(analyzeCurrent,20)}
      else if(turn==='opp')showStatus('等待对方走棋','头像绿框确认 · 自动识别'+sideText());
      else showStatus('当前棋面稳定','等待回合信号');
      return
    }
    if(obs<2){if(hint&&turn==='me')drawMove(hint.m);showStatus('检测到棋面变化','正在确认落子 · 提示暂时保留');return}
    hint=null;clearArrow();
    const preferred=uiTurn==='opp'?userRed:uiTurn==='me'?!userRed:(turn==='me'?userRed:turn==='opp'?!userRed:userRed);
    const one=transitionByMap(currentBoard,rec.occ,rec.side,preferred);
    if(one){
      currentBoard=applyMove(currentBoard,one);currentHash=hashBoard(currentBoard);untrackedFrames=0;
      turn=uiTurn||(isRed(one.piece)===userRed?'opp':'me');if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
      if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'对方已将军':'检测到对方落子',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'头像绿框确认轮到你 · 正在计算');setTimeout(analyzeCurrent,35)}
      else showStatus('已检测到你的落子','头像绿框已切到对方 · 等待对方');
      return
    }
    const sync=reconcileFromMap(currentBoard,rec.occ,rec.side,preferred);
    if(sync){
      currentBoard=sync.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;turn=uiTurn||(sync.red===userRed?'me':'opp');if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
      if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'追赶后发现被将军':'棋面已自动追赶',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'头像绿框确认轮到你 · 正在计算');setTimeout(analyzeCurrent,40)}
      else showStatus('棋面已自动追赶','头像绿框确认等待对方');
      return
    }
    untrackedFrames++;
    if(untrackedFrames>=2){const full=directRebuild();if(full&&full.b){const oldBoard=currentBoard.slice(),exact=reconcileExact(oldBoard,full.b,preferred,6),fullUi=full.uiTurn||uiTurn;currentBoard=full.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;const rt=markerTurn(full);turn=fullUi||(kingInCheck(currentBoard,userRed)?'me':exact?(exact.red===userRed?'me':'opp'):rt||'unknown');if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'重建棋面后检测到将军':'已从当前完整棋盘重建','中途接管成功 · 轮到你 · 正在计算');setTimeout(analyzeCurrent,55)}else showStatus('已从当前完整棋盘重建',turn==='opp'?'中途接管成功 · 等待对方':'棋面已重建 · 等待回合信号');return}}
    showStatus('当前棋面已识别，但变化未确认','保留上一可信局面 · '+untrackedFrames+'/2');return
  }
  if(!rec.b)return;
  const key=hashBoard(rec.b);if(key===fullStableKey)fullStableCount++;else{fullStableKey=key;fullStableCount=1}
  if(fullStableCount<2){if(hint&&turn==='me')drawMove(hint.m);showStatus('棋盘已识别','等待第二帧确认 · 自动识别'+sideText());return}
  lastOcc=rec.occ.slice();lastSide=rec.side.slice();
  const ringTurn=markerTurn(rec),fullUi=rec.uiTurn||uiTurn;
  if(!currentBoard){
    currentBoard=rec.b.slice();currentHash=key;untrackedFrames=0;
    if(fullUi)turn=fullUi;else if(rec.start)turn=userRed?'me':'opp';else if(kingInCheck(currentBoard,userRed))turn='me';else if(ringTurn)turn=ringTurn;else turn='unknown';if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
    if(turn==='me'){showStatus('当前棋面已锁定 · '+sideText(),rec.start?'开局/接管成功 · 轮到你 · 正在计算':'中途接管成功 · 头像绿框确认轮到你');setTimeout(analyzeCurrent,45)}
    else if(turn==='opp')showStatus('当前棋面已锁定 · '+sideText(),rec.start?'红方先走 · 等待对方':'中途接管成功 · 头像绿框确认等待对方');
    else showStatus('当前棋面已锁定 · '+sideText(),'未看到头像绿框 · 等待下一次合法变化确认回合');
    return
  }
}
function handleNoBoard"""
s=s[:m.start()]+accept+s[m.end():]

s=s.replace("turn=boot.red===userRed?'me':'opp';if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();showStatus('已从开局合法变化恢复棋面','自动识别'+sideText());",
            "turn=rec.uiTurn||(boot.red===userRed?'me':'opp');if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();showStatus('已从当前棋面恢复','自动识别'+sideText()+' · '+(turn==='me'?'轮到你':'等待对方'));",2)

old_start="try{localStorage.removeItem('xiangqi_v107_trusted_state');localStorage.removeItem('xiangqi_v108_trusted_state');localStorage.removeItem('xiangqi_v109_trusted_state')}catch(_){}restoreTrustedState();showStatus('象棋助手 1.0.10 硬限时版',restoredPending?'已载入本版可信局面 · 等待画面校验':'先快速校验棋面 · 引擎单次限时 · 失败后台恢复不拖住本步');"
new_start="try{localStorage.removeItem('xiangqi_v107_trusted_state');localStorage.removeItem('xiangqi_v108_trusted_state');localStorage.removeItem('xiangqi_v109_trusted_state');localStorage.removeItem('xiangqi_v110_trusted_state')}catch(_){}restoreTrustedState();requestEngineWarmUp();showStatus('象棋助手 1.0.11 黑方/中途接管版',restoredPending?'已载入本版可信局面 · 将用当前画面复核':'每局重新判边 · 头像绿框判回合 · 支持中途接管');"
must(old_start,new_start,'startup')

p.write_text(s)
