from pathlib import Path
import re

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

def must(old,new,label,count=1):
    global s
    if old not in s:
        raise SystemExit(f'{label} missing')
    s=s.replace(old,new,count)

must("const STATE_KEY='xiangqi_v109_trusted_state';let restoredPending=false;",
     "const STATE_KEY='xiangqi_v110_trusted_state';let restoredPending=false;",'state key')

m=re.search(r"let engineFailCount=0,engineRetryAt=0,engineRecoveryTimer=0;.*?\nfunction boardDiff",s,re.S)
if not m:
    raise SystemExit('engine timing block missing')
new_engine="""let engineFailCount=0,engineRetryAt=0,engineRecoveryTimer=0;
function engineReady(){try{return !!(window.AndroidEngine&&AndroidEngine.isReady&&AndroidEngine.isReady())}catch(_){return false}}
function boundedThinkMs(pos,red,legal){const n=legal.length;if(n<=1)return 0;if(kingInCheck(pos,red)){if(n<=3)return 650;if(n<=6)return 1100;return 1800}if(n<=10)return 700;if(n<=18)return 1100;if(n<=28)return 1800;if(n<=38)return 2800;return 4500}
function pollEngineRecovery(started){if(engineRecoveryTimer)clearTimeout(engineRecoveryTimer);engineRecoveryTimer=setTimeout(()=>{engineRecoveryTimer=0;if(engineReady()){engineFailCount=0;engineRetryAt=0;if(turn==='me'&&!hint&&!analysisRunning)setTimeout(analyzeCurrent,40);return}if(Date.now()-started<6500){pollEngineRecovery(started);return}showStatus('Pikafish 启动失败','本次恢复超过6秒 · 等待下一次棋面变化再重试')},350)}
function scheduleEngineRecovery(reason){if(engineRecoveryTimer)return;engineFailCount=Math.min(3,engineFailCount+1);engineRetryAt=Date.now()+500;try{if(window.AndroidEngine&&AndroidEngine.resetEngine)AndroidEngine.resetEngine()}catch(_){}pollEngineRecovery(Date.now())}
function engineBestMove(pos,red,moveTimeMs){return new Promise((resolve,reject)=>{if(!window.AndroidEngine||!AndroidEngine.analyze){reject(new Error('Pikafish 接口不可用'));return}if(!engineReady()){reject(Object.assign(new Error('Pikafish 正在预热'),{warming:true}));return}const id=++engineRequestSeq;const hardMs=Math.min(5600,Math.max(1700,moveTimeMs+1100));const timer=setTimeout(()=>{const w=engineWaiters.get(id);if(!w)return;engineWaiters.delete(id);reject(new Error('Pikafish 超过本步硬时限'))},hardMs);engineWaiters.set(id,{resolve:(r)=>{clearTimeout(timer);engineFailCount=0;engineRetryAt=0;resolve(r)},reject:(e)=>{clearTimeout(timer);reject(e)}});try{AndroidEngine.analyze(boardToFen(pos,red),id,moveTimeMs)}catch(e){engineWaiters.delete(id);clearTimeout(timer);reject(e)}})}
function boardDiff"""
s=s[:m.start()]+new_engine+s[m.end():]

m=re.search(r"async function analyzeCurrent\(\)\{.*?\}\nlet fullStableKey=",s,re.S)
if not m:
    raise SystemExit('analyzeCurrent block missing')
new_analyze="""async function analyzeCurrent(){
  if(analysisRunning||!currentBoard||turn!=='me')return;
  const t0=performance.now();
  const pre=recognize(false);
  if(!pre||!pre.occ||!pre.side||pre.selected){showStatus('等待棋面稳定','确认落子后再开始计算');return}
  lastOcc=pre.occ.slice();lastSide=pre.side.slice();
  if(!currentMapMatch(currentBoard,pre.occ,pre.side)){showStatus('当前画面与内部棋面不一致','先重新同步，不会在错误局面上计算');return}
  if(fullStableCount<2&&obsStable<2){showStatus('棋面刚刚变化','再确认一帧后计算');return}
  if(kingInCheck(currentBoard,userRed))turn='me';
  const analysisBoard=currentBoard.slice(),startHash=hashBoard(analysisBoard),wasCheck=kingInCheck(analysisBoard,userRed);
  const issue=enginePositionIssue(analysisBoard,userRed);
  if(issue){hint=null;clearArrow();showStatus('当前局面未通过安全校验',issue+' · 不发送给 Pikafish');return}
  const legal=legalMoves(analysisBoard,userRed),checkMs=Math.max(0,Math.round(performance.now()-t0)),thinkMs=boundedThinkMs(analysisBoard,userRed,legal);
  if(legal.length===1){hint={m:legal[0],score:0,depth:0};drawMove(legal[0]);showStatus((wasCheck?'唯一应将：':'唯一合法着：')+zhMove(legal[0]),'局面校验 '+checkMs+'ms · 无需等待引擎');return}
  if(!engineReady()){showStatus('Pikafish 正在预热','局面已确认（'+checkMs+'ms）· 引擎就绪后自动计算');if(!engineRecoveryTimer)pollEngineRecovery(Date.now());return}
  analysisRunning=true;clearArrow();
  showStatus(wasCheck?'正在计算应将/解杀…':'Pikafish 正在计算…','局面校验 '+checkMs+'ms · 本步限时 '+(thinkMs/1000).toFixed(2)+' 秒 · 最长4.5秒');
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
    if(e&&e.warming){showStatus('Pikafish 正在预热','局面已经确认 · 引擎就绪后自动计算');if(!engineRecoveryTimer)pollEngineRecovery(Date.now())}
    else{showStatus('Pikafish 本步失败',e&&e.message?e.message+' · 后台重新启动，不继续占用本步时间':String(e));scheduleEngineRecovery(e&&e.message?e.message:String(e))}
  }finally{analysisRunning=false}
}
let fullStableKey="""
s=s[:m.start()]+new_analyze+s[m.end():]

old="try{localStorage.removeItem('xiangqi_v107_trusted_state');localStorage.removeItem('xiangqi_v108_trusted_state')}catch(_){}restoreTrustedState();showStatus('象棋助手 1.0.9 稳定版',restoredPending?'已载入本版可信局面 · 等待画面校验':'Pikafish 常驻 · 简单局面快速响应 · 复杂局面最长5秒');"
new="try{localStorage.removeItem('xiangqi_v107_trusted_state');localStorage.removeItem('xiangqi_v108_trusted_state');localStorage.removeItem('xiangqi_v109_trusted_state')}catch(_){}restoreTrustedState();showStatus('象棋助手 1.0.10 硬限时版',restoredPending?'已载入本版可信局面 · 等待画面校验':'先快速校验棋面 · 引擎单次限时 · 失败后台恢复不拖住本步');"
must(old,new,'startup')

p.write_text(s)
