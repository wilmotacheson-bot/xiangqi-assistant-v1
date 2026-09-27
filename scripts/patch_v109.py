from pathlib import Path
import re

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

def must(old,new,label,count=1):
    global s
    if old not in s:
        raise SystemExit(f'{label} missing')
    s=s.replace(old,new,count)

must("const STATE_KEY='xiangqi_v107_trusted_state';let restoredPending=false;",
     "const STATE_KEY='xiangqi_v109_trusted_state';let restoredPending=false;",'state key')

must('if(sc<=2)matches.push(it);next.push(it);','if(sc===0)matches.push(it);next.push(it);','map reconcile exact')

anchor="function findKing(pos,red){return pos.indexOf(red?'K':'k')}function attacked(pos,sq,byRed){if(sq<0)return true;return pseudoMoves(pos,true).some(m=>isRed(m.piece)===byRed&&m.to===sq)}function kingInCheck(pos,red){const k=findKing(pos,red);return k>=0&&attacked(pos,k,!red)}"
extra=anchor+"""
function kingsFace(pos){const a=findKing(pos,true),b=findKing(pos,false);if(a<0||b<0||a%9!==b%9)return false;const x=a%9,y1=Math.min((a/9)|0,(b/9)|0),y2=Math.max((a/9)|0,(b/9)|0);for(let y=y1+1;y<y2;y++)if(pos[y*9+x])return false;return true}
function enginePositionIssue(pos,red){if(!Array.isArray(pos)||pos.length!==90)return'棋面长度异常';if(!validCounts(pos))return'棋子数量/主将位置异常';if(kingsFace(pos))return'帅将照面';const me=kingInCheck(pos,red),opp=kingInCheck(pos,!red);if(me&&opp)return'双方同时被将，局面不合法';if(opp)return'回合与将军状态冲突';const ms=legalMoves(pos,red);if(!ms.length)return me?'已被将死/无合法应将':'当前无合法着法';return''}
"""
must(anchor,extra,'position sanity')

old=re.search(r"function engineBestMove\(pos,red\)\{.*?\}\nfunction boardDiff",s,re.S)
if not old: raise SystemExit('engineBestMove block missing')
new="""let engineFailCount=0,engineRetryAt=0,engineRecoveryTimer=0;
function adaptiveThinkMs(pos,red){const ms=legalMoves(pos,red),n=ms.length;if(n<=1)return 260;const checked=kingInCheck(pos,red);let caps=0,checks=0;for(const m of ms){if(m.captured)caps++;try{if(kingInCheck(applyMove(pos,m),!red))checks++}catch(_){}}if(checked){if(n<=2)return 420;if(n<=4)return 700;if(n<=7)return 1100;return Math.min(2200,1100+n*110)}const tactical=caps*2+checks*3,pieces=pos.reduce((a,x)=>a+(x?1:0),0);if(n<=8&&tactical<=4)return 650;if(n<=14&&tactical<=8)return 1000;if(n<=22&&tactical<=12)return 1600;if(tactical>=20||n>=40)return 5000;if(tactical>=12||n>=30)return 3500;if(pieces<=12)return 1200;return 2400}
function scheduleEngineRecovery(reason){if(engineRecoveryTimer)return;engineFailCount=Math.min(5,engineFailCount+1);const delay=Math.min(8000,900*Math.pow(2,engineFailCount-1));engineRetryAt=Date.now()+delay;try{if(window.AndroidEngine&&AndroidEngine.resetEngine)AndroidEngine.resetEngine()}catch(_){}engineRecoveryTimer=setTimeout(()=>{engineRecoveryTimer=0;if(turn==='me'&&!hint&&!analysisRunning)setTimeout(analyzeCurrent,50)},delay+350)}
function engineBestMove(pos,red,moveTimeMs){return new Promise((resolve,reject)=>{if(!window.AndroidEngine||!AndroidEngine.analyze){reject(new Error('Pikafish 接口不可用'));return}if(Date.now()<engineRetryAt){reject(Object.assign(new Error('引擎恢复中'),{cooldown:true}));return}const id=++engineRequestSeq;const timer=setTimeout(()=>{const w=engineWaiters.get(id);if(!w)return;engineWaiters.delete(id);reject(new Error('Pikafish 响应超时'))},Math.max(9000,moveTimeMs+5000));engineWaiters.set(id,{resolve:(r)=>{clearTimeout(timer);engineFailCount=0;engineRetryAt=0;resolve(r)},reject:(e)=>{clearTimeout(timer);reject(e)}});try{AndroidEngine.analyze(boardToFen(pos,red),id,moveTimeMs)}catch(e){engineWaiters.delete(id);clearTimeout(timer);reject(e)}})}
function boardDiff"""
s=s[:old.start()]+new+s[old.end():]

s=s.replace('function reconcileExact(prev,next,preferredRed,maxDepth=4)','function reconcileExact(prev,next,preferredRed,maxDepth=6)',1)
s=s.replace('frontier=nx.slice(0,220).map(x=>x.it)','frontier=nx.slice(0,360).map(x=>x.it)',1)

m=re.search(r"async function analyzeCurrent\(\)\{.*?\}\nlet fullStableKey=",s,re.S)
if not m: raise SystemExit('analyzeCurrent block missing')
analyze="""async function analyzeCurrent(){
  if(analysisRunning||!currentBoard||turn!=='me')return;
  if(Date.now()<engineRetryAt){const left=Math.max(1,Math.ceil((engineRetryAt-Date.now())/1000));showStatus('Pikafish 正在恢复','约 '+left+' 秒后自动重试 · 不会反复重启');return}
  const pre=recognize(false);
  if(!pre||!pre.occ||!pre.side||pre.selected){showStatus('等待棋面稳定','确认落子后再开始计算');return}
  lastOcc=pre.occ.slice();lastSide=pre.side.slice();
  if(!currentMapMatch(currentBoard,pre.occ,pre.side)){showStatus('当前画面与内部棋面不一致','先重新同步，不会在错误局面上计算');return}
  if(fullStableCount<2&&obsStable<2){showStatus('棋面刚刚变化','再确认一帧后计算');return}
  if(kingInCheck(currentBoard,userRed))turn='me';
  const analysisBoard=currentBoard.slice(),startHash=hashBoard(analysisBoard),wasCheck=kingInCheck(analysisBoard,userRed);
  const issue=enginePositionIssue(analysisBoard,userRed);
  if(issue){hint=null;clearArrow();showStatus('当前局面未通过安全校验',issue+' · 不发送给 Pikafish');return}
  const legal=legalMoves(analysisBoard,userRed),thinkMs=adaptiveThinkMs(analysisBoard,userRed);
  if(legal.length===1){hint={m:legal[0],score:0,depth:0};drawMove(legal[0]);showStatus((wasCheck?'唯一应将：':'唯一合法着：')+zhMove(legal[0]),'无需等待引擎 · 已通过合法性校验');return}
  analysisRunning=true;clearArrow();
  showStatus(wasCheck?'正在计算应将/解杀…':'Pikafish 正在计算…','自适应思考 · 本局面上限 '+(thinkMs/1000).toFixed(2)+' 秒 · 最长5秒');
  try{
    const er=await engineBestMove(analysisBoard,userRed,thinkMs);
    if(turn!=='me'||startHash!==hashBoard(currentBoard))return;
    const post=recognize(false);
    if(!post||!post.occ||!post.side||post.selected||!currentMapMatch(analysisBoard,post.occ,post.side)){
      hint=null;clearArrow();showStatus('计算期间棋面发生变化','已丢弃旧结果 · 等待新棋面稳定');return
    }
    lastOcc=post.occ.slice();lastSide=post.side.slice();
    const mv=uciToMove(er.best,analysisBoard);
    if(!mv){showStatus('引擎结果已拦截','无法映射 bestmove：'+(er.best||'空'));return}
    const legalMove=legal.find(x=>x.from===mv.from&&x.to===mv.to);
    if(!legalMove){showStatus('已拦截不合法推荐','真实棋面上不是合法着 · 不显示箭头');return}
    const after=applyMove(analysisBoard,legalMove);
    if(kingInCheck(after,userRed)){showStatus('已拦截未解将着法','这步之后己方仍被将军');return}
    if(!hintFitsObserved(mv)){showStatus('已拦截画面不一致推荐','起点棋子与当前屏幕不一致');return}
    hint={m:legalMove,score:er.score,depth:er.depth};drawMove(legalMove);engineFailCount=0;engineRetryAt=0;
    const cp=Math.max(-9999,Math.min(9999,er.score))/100;
    showStatus((wasCheck?'应将：':'推荐：')+zhMove(legalMove),'Pikafish · 深度 '+(er.depth||'?')+' · 评估 '+cp.toFixed(2)+' · '+(userRed?'红方':'黑方')+'走')
  }catch(e){
    hint=null;clearArrow();
    if(e&&e.cooldown){showStatus('Pikafish 正在恢复','恢复完成后自动重试')}
    else{scheduleEngineRecovery(e&&e.message?e.message:String(e));showStatus('Pikafish 恢复中',e&&e.message?e.message+' · 本次只重启一次':String(e))}
  }finally{analysisRunning=false}
}
let fullStableKey="""
s=s[:m.start()]+analyze+s[m.end():]

s=s.replace('const sc=mapMismatch(START_BOARD,rec.occ,rec.side);if(sc<=2)return','const sc=mapMismatch(START_BOARD,rec.occ,rec.side);if(sc===0)return',1)

old="if(untrackedFrames>=3){const full=directRebuild();if(full&&full.b){currentBoard=full.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;const rt=markerTurn(full);if(kingInCheck(currentBoard,userRed))turn='me';else if(rt)turn=rt;else turn='unknown';saveTrustedState();if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'重建棋面后检测到将军':'已直接重建当前棋面',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'正在计算');setTimeout(analyzeCurrent,40)}else showStatus('已直接重建当前棋面','等待回合证据');return}}"
new="if(untrackedFrames>=3){const full=directRebuild();if(full&&full.b){const oldBoard=currentBoard.slice(),exact=reconcileExact(oldBoard,full.b,preferred,6);currentBoard=full.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;const rt=markerTurn(full);if(kingInCheck(currentBoard,userRed))turn='me';else if(exact)turn=exact.red===userRed?'me':'opp';else if(rt)turn=rt;else turn='unknown';saveTrustedState();if(turn==='me'){showStatus(kingInCheck(currentBoard,userRed)?'重建棋面后检测到将军':'已从当前完整棋盘重建',kingInCheck(currentBoard,userRed)?'正在计算应将/解杀':'正在计算');setTimeout(analyzeCurrent,80)}else showStatus('已从当前完整棋盘重建',turn==='opp'?'等待对方':'等待回合证据');return}}"
must(old,new,'rebuild exact')

startup="restoreTrustedState();showStatus('象棋助手 1.0.7 五秒强校验版',restoredPending?'已载入上一可信局面 · 等待当前画面校验':'每步重新核验当前棋面 · Pikafish 固定5秒 · 将军强制应对');"
startup_new="try{localStorage.removeItem('xiangqi_v107_trusted_state');localStorage.removeItem('xiangqi_v108_trusted_state')}catch(_){}restoreTrustedState();showStatus('象棋助手 1.0.9 稳定版',restoredPending?'已载入本版可信局面 · 等待画面校验':'Pikafish 常驻 · 简单局面快速响应 · 复杂局面最长5秒');"
must(startup,startup_new,'startup')

p.write_text(s)
