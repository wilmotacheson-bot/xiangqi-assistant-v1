from pathlib import Path
import re

p = Path("app/src/main/assets/overlay.html")
s = p.read_text()

def must_replace(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f"{label} missing")
    s = s.replace(old, new, 1)

# --- Persistent trusted state for reopening the assistant mid-game ---
decl = "let currentBoard=null,currentHash='',stableHash='',stableCount=0,turn='me',hint=null,misses=0,analysisRunning=false;"
state = """let currentBoard=null,currentHash='',stableHash='',stableCount=0,turn='me',hint=null,misses=0,analysisRunning=false;
const STATE_KEY='xiangqi_v107_trusted_state';let restoredPending=false;
function saveTrustedState(){if(!currentBoard||!autoSideKnown)return;try{localStorage.setItem(STATE_KEY,JSON.stringify({b:currentBoard,u:userRed,t:turn,ts:Date.now()}))}catch(_){}}
function clearTrustedState(){try{localStorage.removeItem(STATE_KEY)}catch(_){}}
function restoreTrustedState(){try{const x=JSON.parse(localStorage.getItem(STATE_KEY)||'null');if(!x||!Array.isArray(x.b)||x.b.length!==90||Date.now()-(x.ts||0)>30*60*1000)return false;currentBoard=x.b.slice();userRed=!!x.u;autoSideKnown=true;flipped=!userRed;turn=['me','opp','unknown'].includes(x.t)?x.t:'unknown';currentHash=hashBoard(currentBoard);restoredPending=true;return true}catch(_){return false}}"""
must_replace(decl, state, "state declaration")

# --- Improve full-board rebuild when several glyphs have low confidence ---
anchor = "function repairStartup(src,cands){const b=src.slice(),cnt=countPieces(b);"
if anchor not in s:
    raise SystemExit("repairStartup anchor missing")
# Insert after repairStartup's closing return line.
repair_end = "return validCounts(b)?b:null}"
repair_extra = """return validCounts(b)?b:null}
function squareOK(p,i){const x=i%9,y=(i/9)|0;if(p==='K')return x>=3&&x<=5&&y>=7&&y<=9;if(p==='k')return x>=3&&x<=5&&y>=0&&y<=2;if(p==='A')return x>=3&&x<=5&&y>=7&&y<=9;if(p==='a')return x>=3&&x<=5&&y>=0&&y<=2;if(p==='B')return y>=5;if(p==='b')return y<=4;return true}
function repairUnknownFull(src,cands,occ,side){const b=src.slice(),cnt=countPieces(b),todo=[];for(let i=0;i<90;i++)if(occ[i]&&!b[i]&&cands[i]){const a=cands[i].filter(q=>squareOK(q.p,i));if(a.length)todo.push({i,a,certainty:a[0].s-(a[1]?.s||0)})}todo.sort((x,y)=>y.certainty-x.certainty||y.a[0].s-x.a[0].s);for(const t of todo){let pick=null;for(const q of t.a){if(q.s<.22)continue;if((cnt[q.p]||0)>=(MAXCOUNT[q.p]||0))continue;pick=q;break}if(!pick)return null;b[t.i]=pick.p;cnt[pick.p]=(cnt[pick.p]||0)+1}const r=repairStartup(b,cands)||b;if(r.filter(Boolean).length!==occ.filter(Boolean).length)return null;return validCounts(r)?r:null}"""
must_replace(repair_end, repair_extra, "repairStartup end")

old_unknown = "if(unknown>4)return{unknown,found,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null};if(!validCounts(next)){const repaired=repairStartup(next,cands);if(repaired)next=repaired;else return{invalid:true,found,unknown,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null}}"
new_unknown = "if(unknown>0){const repairedUnknown=repairUnknownFull(next,cands,occ,side);if(repairedUnknown){next=repairedUnknown;unknown=0}else if(unknown>7)return{unknown,found,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null}}if(!validCounts(next)){const repaired=repairStartup(next,cands);if(repaired)next=repaired;else return{invalid:true,found,unknown,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null}}"
must_replace(old_unknown, new_unknown, "unknown repair block")

# --- Explicit check detection; if our commander is attacked, it is necessarily our turn to respond. ---
attacked_anchor = "function findKing(pos,red){return pos.indexOf(red?'K':'k')}function attacked(pos,sq,byRed){if(sq<0)return true;return pseudoMoves(pos,true).some(m=>isRed(m.piece)===byRed&&m.to===sq)}"
attacked_new = attacked_anchor + "function kingInCheck(pos,red){const k=findKing(pos,red);return k>=0&&attacked(pos,k,!red)}"
must_replace(attacked_anchor, attacked_new, "attacked helper")

# --- Fixed 5-second Pikafish search per move ---
s, n = re.subn(r"AndroidEngine\.analyze\(boardToFen\(pos,red\),id,\d+\)", "AndroidEngine.analyze(boardToFen(pos,red),id,5000)", s, count=1)
if n != 1:
    raise SystemExit("engine movetime patch missing")

# --- Every recommendation is calculated from a freshly screen-validated current board,
#     then validated again after Pikafish returns. ---
m = re.search(r"async function analyzeCurrent\(\)\{.*?\}\nlet fullStableKey=", s, re.S)
if not m:
    raise SystemExit("analyzeCurrent block missing")
analyze = """async function analyzeCurrent(){
  if(analysisRunning||!currentBoard||turn!=='me')return;
  const pre=recognize(false);
  if(!pre||!pre.occ||!pre.side||pre.selected){showStatus('等待棋面稳定','确认落子后再开始 5 秒计算');return}
  lastOcc=pre.occ.slice();lastSide=pre.side.slice();
  if(!currentMapMatch(currentBoard,pre.occ,pre.side)){showStatus('当前画面与内部棋面不一致','先重新同步，不会在错误局面上计算');return}
  if(kingInCheck(currentBoard,userRed))turn='me';
  const analysisBoard=currentBoard.slice(),startHash=hashBoard(analysisBoard),wasCheck=kingInCheck(analysisBoard,userRed);
  analysisRunning=true;clearArrow();
  showStatus(wasCheck?'正在计算应将/解杀…':'Pikafish 正在深度计算…','当前完整局面 · 固定 5 秒搜索');
  try{
    const er=await engineBestMove(analysisBoard,userRed);
    if(turn!=='me'||startHash!==hashBoard(currentBoard))return;
    const post=recognize(false);
    if(!post||!post.occ||!post.side||post.selected||!currentMapMatch(analysisBoard,post.occ,post.side)){
      hint=null;clearArrow();showStatus('计算期间棋面发生变化','已丢弃旧结果 · 下一帧重新同步');return
    }
    lastOcc=post.occ.slice();lastSide=post.side.slice();
    const m=uciToMove(er.best,analysisBoard);
    if(!m){showStatus('引擎走法无法映射',er.best||'无 bestmove');return}
    const legal=legalMoves(analysisBoard,userRed),legalMove=legal.find(x=>x.from===m.from&&x.to===m.to);
    if(!legalMove){showStatus('已拦截不合法推荐','当前真实局面不会显示这支箭头');return}
    if(wasCheck&&kingInCheck(applyMove(analysisBoard,legalMove),userRed)){showStatus('已拦截未解将着法','重新计算应将');return}
    if(!hintFitsObserved(m)){showStatus('已拦截画面不一致推荐','起点棋子与当前屏幕不一致 · 重新同步');return}
    hint={m,score:er.score,depth:er.depth};drawMove(m);
    const cp=Math.max(-9999,Math.min(9999,er.score))/100;
    showStatus((wasCheck?'应将：':'推荐：')+zhMove(m),'Pikafish 5秒 · 深度 '+(er.depth||'?')+' · 评估 '+cp.toFixed(2)+' · '+(userRed?'红方':'黑方')+'走')
  }catch(e){
    hint=null;clearArrow();showStatus('Pikafish 正在自愈',e&&e.message?e.message+' · 稍后自动重试':String(e))
  }finally{analysisRunning=false}
}
let fullStableKey="""
s = s[:m.start()] + analyze + s[m.end():]

# --- Strengthen the v1.0.6 state machine ---
# Always keep latest screen map for final arrow validation.
s = s.replace("function acceptStable(rec){\n  if(!rec)return;misses=0;",
              "function acceptStable(rec){\n  if(!rec)return;misses=0;if(rec.occ&&rec.side){lastOcc=rec.occ.slice();lastSide=rec.side.slice()}")

# Validate a restored board against the first actual screen frame; discard stale saved state immediately.
needle = "  if(rec.selected){if(hint&&turn==='me')drawMove(hint.m);showStatus('已提子 · 提示保持','箭头会保留到落子完成');fullStableKey='';fullStableCount=0;return}\n"
restored = needle + """  if(restoredPending&&currentBoard&&rec.occ&&rec.side){if(currentMapMatch(currentBoard,rec.occ,rec.side)){restoredPending=false;showStatus('已恢复上一可信局面','画面校验通过 · '+sideText())}else{currentBoard=null;currentHash='';turn='unknown';restoredPending=false;clearTrustedState();showStatus('旧局面与当前画面不同','已丢弃缓存 · 正在重新识别');return}}
"""
must_replace(needle, restored, "restored-state insertion")

# Stable map: force immediate response if the opponent has just given check.
old_stable = """    if(currentMapMatch(currentBoard,rec.occ,rec.side)){
      untrackedFrames=0;if(ringTurn)turn=ringTurn;
      if(turn==='me'){if(hint)drawMove(hint.m);else if(!analysisRunning)setTimeout(analyzeCurrent,20)}
      else if(turn==='opp')showStatus('等待对方走棋','自动识别'+sideText());
      else showStatus('当前棋面稳定','等待下一次合法变化');
      return
    }"""
new_stable = """    if(currentMapMatch(currentBoard,rec.occ,rec.side)){
      untrackedFrames=0;if(ringTurn)turn=ringTurn;
      if(kingInCheck(currentBoard,userRed)){turn='me';hint=null;clearArrow();saveTrustedState();showStatus('检测到对方将军','立即计算应将/解杀');if(!analysisRunning)setTimeout(analyzeCurrent,20);return}
      saveTrustedState();
      if(turn==='me'){if(hint)drawMove(hint.m);else if(!analysisRunning)setTimeout(analyzeCurrent,20)}
      else if(turn==='opp')showStatus('等待对方走棋','自动识别'+sideText());
      else showStatus('当前棋面稳定','等待下一次合法变化');
      return
    }"""
must_replace(old_stable, new_stable, "stable map branch")

old_one = """      currentBoard=applyMove(currentBoard,one);currentHash=hashBoard(currentBoard);untrackedFrames=0;
      turn=isRed(one.piece)===userRed?'opp':'me';
      if(turn==='me'){showStatus('检测到对方落子','轮到你 · 正在计算');setTimeout(analyzeCurrent,35)}
      else showStatus('已检测到你的落子','等待对方走棋');"""
new_one = """      currentBoard=applyMove(currentBoard,one);currentHash=hashBoard(currentBoard);untrackedFrames=0;
      turn=isRed(one.piece)===userRed?'opp':'me';if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
      if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'对方已将军':'检测到对方落子',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'轮到你 · 正在计算');setTimeout(analyzeCurrent,35)}
      else showStatus('已检测到你的落子','等待对方走棋');"""
must_replace(old_one, new_one, "one-move branch")

old_sync = """      currentBoard=sync.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;turn=sync.red===userRed?'me':'opp';
      if(turn==='me'){showStatus('棋面已自动追赶','轮到你 · 正在计算');setTimeout(analyzeCurrent,40)}
      else showStatus('棋面已自动追赶','等待对方');"""
new_sync = """      currentBoard=sync.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;turn=sync.red===userRed?'me':'opp';if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();
      if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'追赶后发现被将军':'棋面已自动追赶',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'轮到你 · 正在计算');setTimeout(analyzeCurrent,40)}
      else showStatus('棋面已自动追赶','等待对方');"""
must_replace(old_sync, new_sync, "sync branch")

# If legal history recovery fails repeatedly, directly rebuild the current board instead of staying stuck.
old_fail = "    untrackedFrames++;showStatus('当前棋面已识别，但变化未确认','保留上一可信局面 · '+untrackedFrames+'/3');return"
new_fail = """    untrackedFrames++;
    if(untrackedFrames>=3){const full=directRebuild();if(full&&full.b){currentBoard=full.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;const rt=markerTurn(full);if(kingInCheck(currentBoard,userRed))turn='me';else if(rt)turn=rt;else turn='unknown';saveTrustedState();if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'重建棋面后检测到将军':'已直接重建当前棋面',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'正在计算');setTimeout(analyzeCurrent,40)}else showStatus('已直接重建当前棋面','等待回合证据');return}}
    showStatus('当前棋面已识别，但变化未确认','保留上一可信局面 · '+untrackedFrames+'/3');return"""
must_replace(old_fail, new_fail, "rebuild fallback")

old_lock = """    currentBoard=rec.b.slice();currentHash=key;untrackedFrames=0;
    if(rec.start)turn=userRed?'me':'opp';else if(ringTurn)turn=ringTurn;else turn='unknown';
    if(turn==='me'){showStatus('棋盘已锁定 · 自动识别'+sideText(),rec.start?'开局红方先走 · 正在计算':'轮到你走 · 正在计算');setTimeout(analyzeCurrent,45)}"""
new_lock = """    currentBoard=rec.b.slice();currentHash=key;untrackedFrames=0;
    if(rec.start)turn=userRed?'me':'opp';else if(kingInCheck(currentBoard,userRed))turn='me';else if(ringTurn)turn=ringTurn;else turn='unknown';saveTrustedState();
    if(turn==='me'){showStatus('棋盘已锁定 · 自动识别'+sideText(),kingInCheck(currentBoard,userRed)?'检测到将军 · 正在计算应将':(rec.start?'开局红方先走 · 正在计算':'轮到你走 · 正在计算'));setTimeout(analyzeCurrent,45)}"""
must_replace(old_lock, new_lock, "initial lock")

# Save bootstrapped positions too.
s = s.replace("currentBoard=boot.b.slice();currentHash=hashBoard(currentBoard);turn=boot.red===userRed?'me':'opp';",
              "currentBoard=boot.b.slice();currentHash=hashBoard(currentBoard);turn=boot.red===userRed?'me':'opp';if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();")

# Do not erase the last trusted board just because the target window is absent for a while.
s = s.replace("if(misses>=40){currentBoard=null;currentHash='';turn='unknown';untrackedFrames=0}",
              "if(misses>=120){turn='unknown';untrackedFrames=0}")

# Restore trusted state only after all helpers have been defined.
startup = "showStatus('象棋助手 1.0.6 黑方修复版','主帅颜色自动判边 · 红方开局先走 · 提子后箭头保持到落子');"
startup_new = "restoreTrustedState();showStatus('象棋助手 1.0.7 五秒强校验版',restoredPending?'已载入上一可信局面 · 等待当前画面校验':'每步重新核验当前棋面 · Pikafish 固定5秒 · 将军强制应对');"
must_replace(startup, startup_new, "startup status")

p.write_text(s)
