from pathlib import Path
import re

p = Path("app/src/main/assets/overlay.html")
s = p.read_text()

def must_replace(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f"{label} missing")
    s = s.replace(old, new, 1)

# Auto side detection: use the commander (帅/将) in the bottom palace.
anchor = "function candScore(cands,i,p){const a=cands[i];if(!a)return-9;const q=a.find(x=>x.p===p);return q?q.s:-9}"
commander = "function detectBottomCommanderSide(cands,side){let best=null;for(let y=7;y<=9;y++)for(let x=3;x<=5;x++){const i=y*9+x;if(!side[i]||!cands[i]||!cands[i].length)continue;const king=side[i]==='R'?'K':'k',top=cands[i][0],sc=candScore(cands,i,king);if((top.p===king&&top.s>.26)||sc>.48){if(!best||sc>best.sc)best={red:side[i]==='R',sc}}}return best?best.red:null}"
must_replace(anchor, anchor + commander, "commander anchor")

old_start = "const occCount=occ.filter(Boolean).length;const occDiff=occ.reduce((n,v,i)=>n+(v!==START_OCC[i]),0);if(occDiff<=1){let bottomR=0,bottomB=0;for(let i=45;i<90;i++){if(side[i]==='R')bottomR++;else if(side[i]==='B')bottomB++}if(bottomR+bottomB>=4){userRed=bottomR>=bottomB;autoSideKnown=true;flipped=!userRed}else flipped=bottomB>bottomR;const marker=detectLastMoveMarkers(rawOcc,flipped);if(flipped){occ.reverse();side.reverse()}return{b:START_BOARD.slice(),occ,side,marker,found:32,occCount,score:1,selected:greenHit,start:true,autoRed:autoSideKnown?userRed:null}}"
new_start = "const occCount=occ.filter(Boolean).length;const occDiff=occ.reduce((n,v,i)=>n+(v!==START_OCC[i]),0);let commanderRed=detectBottomCommanderSide(cands,side);if(commanderRed===null&&occDiff<=1&&side[85])commanderRed=side[85]==='R';if(commanderRed!==null){userRed=commanderRed;autoSideKnown=true;flipped=!userRed}if(occDiff<=1){const marker=detectLastMoveMarkers(rawOcc,flipped);if(flipped){occ.reverse();side.reverse()}return{b:START_BOARD.slice(),occ,side,marker,found:32,occCount,score:1,selected:greenHit,start:true,autoRed:autoSideKnown?userRed:null}}"
must_replace(old_start, new_start, "startup side block")

old_kings = "if(found<2)return null;let kr=next.indexOf('K'),kb=next.indexOf('k');if(kr>=0&&kb>=0){const redBottom=Math.floor(kr/9)>Math.floor(kb/9);userRed=redBottom;autoSideKnown=true;flipped=!redBottom}const marker=detectLastMoveMarkers(rawOcc,flipped);if(flipped){next.reverse();cands.reverse();occ.reverse();side.reverse()}"
new_kings = "if(found<2)return null;if(!autoSideKnown){let kr=next.indexOf('K'),kb=next.indexOf('k');if(kr>=0&&kb>=0){const redBottom=Math.floor(kr/9)>Math.floor(kb/9);userRed=redBottom;autoSideKnown=true;flipped=!redBottom}}const marker=detectLastMoveMarkers(rawOcc,flipped);if(flipped){next.reverse();cands.reverse();occ.reverse();side.reverse()}"
must_replace(old_kings, new_kings, "king fallback block")

s = s.replace(
    "if(unknown>4)return{unknown,found,occCount,marker,selected:greenHit};",
    "if(unknown>4)return{unknown,found,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null};",
    1,
)
s = s.replace(
    "else return{invalid:true,found,unknown,occCount,marker,selected:greenHit}}",
    "else return{invalid:true,found,unknown,occCount,marker,selected:greenHit,occ,side,autoRed:autoSideKnown?userRed:null}}",
    1,
)

marker_anchor = "function markerTurn(rec){if(!rec||!rec.marker||!rec.b)return null;const m=rec.marker;if(rec.b[m.from])return null;const p=rec.b[m.to];if(!p)return null;const nextRed=!isRed(p);return nextRed===userRed?'me':'opp'}"
marker_map = "function markerTurnFromMap(rec){if(!rec||!rec.marker||!rec.occ||!rec.side)return null;const m=rec.marker;if(rec.occ[m.from])return null;const sideAtTo=rec.side[m.to];if(!sideAtTo)return null;const nextRed=sideAtTo!=='R';return nextRed===userRed?'me':'opp'}"
must_replace(marker_anchor, marker_anchor + marker_map, "marker turn anchor")

m = re.search(r"function acceptStable\(rec\)\{.*?\n\}\nfunction handleNoBoard\(msg\)", s, re.S)
if not m:
    raise SystemExit("acceptStable block missing")

replacement = """function bootstrapFromStartMap(rec){if(!rec||!rec.occ||!rec.side||!autoSideKnown)return null;const sc=mapMismatch(START_BOARD,rec.occ,rec.side);if(sc<=2)return{b:START_BOARD.slice(),red:true,seq:[]};return reconcileFromMap(START_BOARD,rec.occ,rec.side,true)}
function acceptStable(rec){
  if(!rec)return;misses=0;
  if(rec.selected){if(hint&&turn==='me')drawMove(hint.m);showStatus('已提子 · 提示保持','箭头会保留到落子完成');fullStableKey='';fullStableCount=0;return}
  if(currentBoard&&!rec.b&&rec.occ&&rec.side){
    const obs=noteObservation(rec),ringTurn=markerTurnFromMap(rec);
    if(currentMapMatch(currentBoard,rec.occ,rec.side)){
      untrackedFrames=0;if(ringTurn)turn=ringTurn;
      if(turn==='me'){if(hint)drawMove(hint.m);else if(!analysisRunning)setTimeout(analyzeCurrent,20)}
      else if(turn==='opp')showStatus('等待对方走棋','自动识别'+sideText());
      else showStatus('当前棋面稳定','等待下一次合法变化');
      return
    }
    if(obs<2){if(hint&&turn==='me')drawMove(hint.m);showStatus('检测到棋面变化','正在确认落子 · 提示暂时保留');return}
    hint=null;clearArrow();
    const preferred=turn==='me'?userRed:turn==='opp'?!userRed:userRed;
    const one=transitionByMap(currentBoard,rec.occ,rec.side,preferred);
    if(one){
      currentBoard=applyMove(currentBoard,one);currentHash=hashBoard(currentBoard);untrackedFrames=0;
      turn=isRed(one.piece)===userRed?'opp':'me';
      if(turn==='me'){showStatus('检测到对方落子','轮到你 · 正在计算');setTimeout(analyzeCurrent,35)}
      else showStatus('已检测到你的落子','等待对方走棋');
      return
    }
    const sync=reconcileFromMap(currentBoard,rec.occ,rec.side,preferred);
    if(sync){
      currentBoard=sync.b.slice();currentHash=hashBoard(currentBoard);untrackedFrames=0;turn=sync.red===userRed?'me':'opp';
      if(turn==='me'){showStatus('棋面已自动追赶','轮到你 · 正在计算');setTimeout(analyzeCurrent,40)}
      else showStatus('棋面已自动追赶','等待对方');
      return
    }
    untrackedFrames++;showStatus('当前棋面已识别，但变化未确认','保留上一可信局面 · '+untrackedFrames+'/3');return
  }
  if(!rec.b)return;
  const key=hashBoard(rec.b);if(key===fullStableKey)fullStableCount++;else{fullStableKey=key;fullStableCount=1}
  if(fullStableCount<2){if(hint&&turn==='me')drawMove(hint.m);showStatus('棋盘已识别','等待第二帧确认 · 自动识别'+sideText());return}
  lastOcc=rec.occ.slice();lastSide=rec.side.slice();
  const ringTurn=markerTurn(rec);
  if(!currentBoard){
    currentBoard=rec.b.slice();currentHash=key;untrackedFrames=0;
    if(rec.start)turn=userRed?'me':'opp';else if(ringTurn)turn=ringTurn;else turn='unknown';
    if(turn==='me'){showStatus('棋盘已锁定 · 自动识别'+sideText(),rec.start?'开局红方先走 · 正在计算':'轮到你走 · 正在计算');setTimeout(analyzeCurrent,45)}
    else if(turn==='opp')showStatus('棋盘已锁定 · 自动识别'+sideText(),rec.start?'开局红方先走 · 等待红方':'等待对方');
    else showStatus('棋盘已锁定 · 自动识别'+sideText(),'等待下一次合法变化确认回合');
    return
  }
}
function handleNoBoard(msg)"""
s = s[:m.start()] + replacement + s[m.end():]

frame_re = r"const rec=recognize\(true\);if\(!rec\)\{handleNoBoard\('未识别到木纹棋盘'\);return\}.*?status\.style\.display='block';acceptStable\(rec\)"
new_frame = "const rec=recognize(!currentBoard);if(!rec){handleNoBoard('未识别到木纹棋盘');return}if(!currentBoard&&rec.unknown&&!rec.b){const boot=bootstrapFromStartMap(rec);if(boot){currentBoard=boot.b.slice();currentHash=hashBoard(currentBoard);turn=boot.red===userRed?'me':'opp';showStatus('已从开局合法变化恢复棋面','自动识别'+sideText());if(turn==='me')setTimeout(analyzeCurrent,45);return}showStatus('棋子识别不够确定','第 '+frameSeen+' 帧 · 等待稳定');return}if(!currentBoard&&(rec.invalid||!rec.b)){const boot=bootstrapFromStartMap(rec);if(boot){currentBoard=boot.b.slice();currentHash=hashBoard(currentBoard);turn=boot.red===userRed?'me':'opp';showStatus('已从开局合法变化恢复棋面','自动识别'+sideText());if(turn==='me')setTimeout(analyzeCurrent,45);return}showStatus('棋盘局面校验未通过','第 '+frameSeen+' 帧 · 等待动画/高亮结束');return}status.style.display='block';acceptStable(rec)"
s, n = re.subn(frame_re, new_frame, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit("onFrame block missing")

# In v1.0.6 opening is deterministic; no white-ring decision is allowed to override red-to-move.
s = s.replace(
    "showStatus('象棋助手 v1.0.5 引擎自愈版','Pikafish 已预热 · 卡死自动重启 · 自动识别红黑方/白圈');",
    "showStatus('象棋助手 1.0.6 黑方修复版','主帅颜色自动判边 · 红方开局先走 · 提子后箭头保持到落子');",
    1,
)

p.write_text(s)
