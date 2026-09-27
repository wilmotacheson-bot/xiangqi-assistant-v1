from pathlib import Path

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

def must(old,new,label,count=1):
    global s
    if old not in s:
        raise SystemExit(f'{label} missing')
    s=s.replace(old,new,count)

must("let fullStableKey=","let checkHandledHash='';let fullStableKey=","check latch variable")

old="""      if(kingInCheck(currentBoard,userRed)){turn='me';hint=null;clearArrow();saveTrustedState();showStatus('检测到对方将军','立即计算应将/解杀');if(!analysisRunning)setTimeout(analyzeCurrent,20);return}
      saveTrustedState();"""
new="""      if(kingInCheck(currentBoard,userRed)){
        turn='me';saveTrustedState();
        const checkHash=currentHash||hashBoard(currentBoard);
        if(checkHandledHash!==checkHash){
          checkHandledHash=checkHash;
          hint=null;clearArrow();
          showStatus('检测到对方将军','立即计算应将/解杀');
          if(!analysisRunning)setTimeout(analyzeCurrent,20)
        }else if(hint){
          drawMove(hint.m)
        }
        return
      }
      checkHandledHash='';
      saveTrustedState();"""
must(old,new,"same-position check latch")

# When a newly observed move itself creates check, mark that exact board as already handled
# so the next stable frame won't overwrite the "正在计算/应将" status.
old="""      turn=isRed(one.piece)===userRed?'opp':'me';if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
      if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'对方已将军':'检测到对方落子',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'轮到你 · 正在计算');setTimeout(analyzeCurrent,35)}"""
new="""      turn=isRed(one.piece)===userRed?'opp':'me';const oneCheck=kingInCheck(currentBoard,userRed);if(oneCheck){turn='me';checkHandledHash=currentHash}else checkHandledHash='';saveTrustedState();
      if(turn==='me'){showStatus(oneCheck?'对方已将军':'检测到对方落子',oneCheck?'正在计算应将/解杀':'轮到你 · 正在计算');setTimeout(analyzeCurrent,35)}"""
must(old,new,"single transition check latch")

old="""      currentBoard=sync.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;turn=sync.red===userRed?'me':'opp';if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
      if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'追赶后发现被将军':'棋面已自动追赶',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'轮到你 · 正在计算');setTimeout(analyzeCurrent,40)}"""
new="""      currentBoard=sync.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;turn=sync.red===userRed?'me':'opp';const syncCheck=kingInCheck(currentBoard,userRed);if(syncCheck){turn='me';checkHandledHash=currentHash}else checkHandledHash='';saveTrustedState();
      if(turn==='me'){showStatus(syncCheck?'追赶后发现被将军':'棋面已自动追赶',syncCheck?'正在计算应将/解杀':'轮到你 · 正在计算');setTimeout(analyzeCurrent,40)}"""
must(old,new,"reconcile check latch")

old="""        turn=kingInCheck(currentBoard,userRed)?'me':exact?(exact.red===userRed?'me':'opp'):rt||'unknown';
        if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
        if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'重建棋面后检测到将军':'已从当前完整棋盘重建','轮到你 · 正在计算');setTimeout(analyzeCurrent,55)}"""
new="""        const rebuildCheck=kingInCheck(currentBoard,userRed);
        turn=rebuildCheck?'me':exact?(exact.red===userRed?'me':'opp'):rt||'unknown';
        if(rebuildCheck){turn='me';checkHandledHash=currentHash}else checkHandledHash='';saveTrustedState();
        if(turn==='me'){showStatus(rebuildCheck?'重建棋面后检测到将军':'已从当前完整棋盘重建',rebuildCheck?'正在计算应将/解杀':'轮到你 · 正在计算');setTimeout(analyzeCurrent,55)}"""
must(old,new,"rebuild check latch")

# Startup/reload starts with no latched check.
old="showStatus('象棋助手 1.0.14 手动接管版',restoredPending?'已恢复本次会话可信局面':'需要新开局或残局接管时，点右侧“新局 / 接管”按钮');"
new="showStatus('象棋助手 1.0.15 将军提示稳定版',restoredPending?'已恢复本次会话可信局面':'同一将军局面只触发一次 · 新局/残局仍可点“新局 / 接管”');"
must(old,new,"startup title")

p.write_text(s)
