from pathlib import Path
import re

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

def must(old,new,label,count=1):
    global s
    if old not in s:
        raise SystemExit(f'{label} missing')
    s=s.replace(old,new,count)

must("const STATE_KEY='xiangqi_v112_trusted_state';let restoredPending=false;let sideProbeValue=null,sideProbeCount=0;",
     "const SESSION_ID=(()=>{try{return new URL(location.href).searchParams.get('session')||'0'}catch(_){return'0'}})();const STATE_KEY='xiangqi_v113_trusted_state_'+SESSION_ID;let restoredPending=false;let sideProbeValue=null,sideProbeCount=0;",'session state key')

s,n=re.subn(r"function detectUiTurn\(\)\{.*?\}", "function detectUiTurn(){return null}", s, count=1)
if n!=1: raise SystemExit('detectUiTurn missing')

m=re.search(r"function acceptStable\(rec\)\{.*?\n\}\nfunction handleNoBoard",s,re.S)
if not m: raise SystemExit('acceptStable block missing')
accept="""function acceptStable(rec){
  if(!rec)return;misses=0;if(rec.occ&&rec.side){lastOcc=rec.occ.slice();lastSide=rec.side.slice()}
  if(currentBoard&&!rec.nearStart){sideProbeValue=null;sideProbeCount=0}
  if(!rec.selected&&rec.bottomRed!==null&&rec.bottomRed!==undefined&&(!currentBoard||rec.nearStart)&&noteBottomSide(rec.bottomRed)){
    if(autoSideKnown&&rec.bottomRed!==userRed){const nr=!!rec.bottomRed;resetForSide(nr);showStatus('检测到新对局/红黑换边','开局区域连续3帧确认 · 已切换为'+(nr?'红方':'黑方'));return}
    if(!autoSideKnown){userRed=!!rec.bottomRed;autoSideKnown=true;flipped=!userRed}
  }
  if(rec.selected){if(hint&&turn==='me')drawMove(hint.m);showStatus('已提子 · 提示保持','箭头会保留到落子完成');fullStableKey='';fullStableCount=0;return}
  if(restoredPending&&currentBoard&&rec.occ&&rec.side){
    if(currentMapMatch(currentBoard,rec.occ,rec.side)){restoredPending=false;showStatus('已恢复本次会话可信局面','画面校验通过 · '+sideText())}
    else{currentBoard=null;currentHash='';turn='unknown';restoredPending=false;clearTrustedState();autoSideKnown=false;showStatus('旧局面与当前画面不同','已丢弃缓存 · 正在从当前棋面重建');return}
  }
  if(currentBoard&&!rec.b&&rec.occ&&rec.side){
    const obs=noteObservation(rec),ringTurn=markerTurnFromMap(rec);
    if(currentMapMatch(currentBoard,rec.occ,rec.side)){
      untrackedFrames=0;if(ringTurn)turn=ringTurn;
      if(kingInCheck(currentBoard,userRed)){turn='me';hint=null;clearArrow();saveTrustedState();showStatus('检测到对方将军','立即计算应将/解杀');if(!analysisRunning)setTimeout(analyzeCurrent,20);return}
      saveTrustedState();
      if(turn==='me'){if(hint)drawMove(hint.m);else if(!analysisRunning)setTimeout(analyzeCurrent,20)}
      else if(turn==='opp')showStatus('等待对方走棋','根据上一手落子与棋面变化确认 · '+sideText());
      else showStatus('当前棋面稳定','等待下一次合法变化确认回合');
      return
    }
    if(obs<2){if(hint&&turn==='me')drawMove(hint.m);showStatus('检测到棋面变化','正在确认落子 · 提示暂时保留');return}
    hint=null;clearArrow();
    const preferred=turn==='me'?userRed:turn==='opp'?!userRed:userRed;
    const one=transitionByMap(currentBoard,rec.occ,rec.side,preferred);
    if(one){
      currentBoard=applyMove(currentBoard,one);currentHash=hashBoard(currentBoard);untrackedFrames=0;
      turn=isRed(one.piece)===userRed?'opp':'me';if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
      if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'对方已将军':'检测到对方落子',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'轮到你 · 正在计算');setTimeout(analyzeCurrent,35)}
      else showStatus('已检测到你的落子','等待对方走棋');
      return
    }
    const sync=reconcileFromMap(currentBoard,rec.occ,rec.side,preferred);
    if(sync){
      currentBoard=sync.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;turn=sync.red===userRed?'me':'opp';if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
      if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'追赶后发现被将军':'棋面已自动追赶',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'轮到你 · 正在计算');setTimeout(analyzeCurrent,40)}
      else showStatus('棋面已自动追赶','等待对方走棋');
      return
    }
    untrackedFrames++;
    if(untrackedFrames>=2){
      const full=directRebuild();
      if(full&&full.b){
        const oldBoard=currentBoard.slice(),exact=reconcileExact(oldBoard,full.b,preferred,6);
        currentBoard=full.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;
        const rt=markerTurn(full);
        turn=kingInCheck(currentBoard,userRed)?'me':exact?(exact.red===userRed?'me':'opp'):rt||'unknown';
        if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
        if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'重建棋面后检测到将军':'已从当前完整棋盘重建','轮到你 · 正在计算');setTimeout(analyzeCurrent,55)}
        else showStatus('已从当前完整棋盘重建',turn==='opp'?'等待对方走棋':'等待下一次合法变化确认回合');
        return
      }
    }
    showStatus('当前棋面已识别，但变化未确认','保留上一可信局面 · '+untrackedFrames+'/2');return
  }
  if(!rec.b)return;
  const key=hashBoard(rec.b);if(key===fullStableKey)fullStableCount++;else{fullStableKey=key;fullStableCount=1}
  if(fullStableCount<2){if(hint&&turn==='me')drawMove(hint.m);showStatus('棋盘已识别','等待第二帧确认 · 自动识别'+sideText());return}
  lastOcc=rec.occ.slice();lastSide=rec.side.slice();
  const ringTurn=markerTurn(rec);
  if(!currentBoard){
    currentBoard=rec.b.slice();currentHash=key;untrackedFrames=0;
    if(rec.start)turn=userRed?'me':'opp';
    else if(kingInCheck(currentBoard,userRed))turn='me';
    else if(ringTurn)turn=ringTurn;
    else turn='unknown';
    if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
    if(turn==='me'){showStatus('当前棋面已锁定 · '+sideText(),rec.start?'开局红方先走 · 轮到你 · 正在计算':'中途接管成功 · 根据上一手标记确认轮到你');setTimeout(analyzeCurrent,45)}
    else if(turn==='opp')showStatus('当前棋面已锁定 · '+sideText(),rec.start?'开局红方先走 · 等待对方':'中途接管成功 · 根据上一手标记确认等待对方');
    else showStatus('当前棋面已锁定 · '+sideText(),'未能确认上一手 · 等下一次合法落子后自动接管');
    return
  }
}
function handleNoBoard"""
s=s[:m.start()]+accept+s[m.end():]

s=s.replace("turn=rec.uiTurn||(boot.red===userRed?'me':'opp');if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();showStatus('已从当前棋面恢复','自动识别'+sideText()+' · '+(turn==='me'?'轮到你':'等待对方'));",
            "turn=boot.red===userRed?'me':'opp';if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();showStatus('已从当前棋面恢复','自动识别'+sideText()+' · '+(turn==='me'?'轮到你':'等待对方'));",2)

old_start="try{localStorage.removeItem('xiangqi_v107_trusted_state');localStorage.removeItem('xiangqi_v108_trusted_state');localStorage.removeItem('xiangqi_v109_trusted_state');localStorage.removeItem('xiangqi_v110_trusted_state');localStorage.removeItem('xiangqi_v111_trusted_state')}catch(_){}restoreTrustedState();requestEngineWarmUp();showStatus('象棋助手 1.0.12 连续对局稳定版',restoredPending?'已载入可信局面 · 本局朝向锁定后不再随帧改变':'整局锁定棋盘朝向 · 中途进场使用全局棋子约束重建');"
new_start="try{localStorage.removeItem('xiangqi_v107_trusted_state');localStorage.removeItem('xiangqi_v108_trusted_state');localStorage.removeItem('xiangqi_v109_trusted_state');localStorage.removeItem('xiangqi_v110_trusted_state');localStorage.removeItem('xiangqi_v111_trusted_state');localStorage.removeItem('xiangqi_v112_trusted_state')}catch(_){}restoreTrustedState();requestEngineWarmUp();showStatus('象棋助手 1.0.13 新局会话版',restoredPending?'已恢复本次开始后的可信局面':'每次点开始都会新建会话 · 真人/人机均不用头像绿框判断回合');"
must(old_start,new_start,'startup')

p.write_text(s)
