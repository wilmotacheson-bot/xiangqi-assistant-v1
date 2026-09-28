from pathlib import Path
import re

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

start=s.find("const GLYPH_BANK_KEY='xiangqi_fixedskin_glyphbank_v4';")
end=s.find("\nfunction strictIdentityBoardOK",start)
if start<0 or end<0:
    raise SystemExit('v117 glyph block missing')

fixed=r"""const FIXED_GLYPH_ORDER=['K','A','B','N','R','C','P','k','a','b','n','r','c','p'];
const FIXED_GLYPH_B64='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';
function fixedGlyphSamples(){const raw=atob(FIXED_GLYPH_B64),samples={};let off=0;for(const p of FIXED_GLYPH_ORDER){const a=new Array(400);for(let i=0;i<400;i++)a[i]=raw.charCodeAt(off++);samples[p]=[a]}return samples}
const glyphBank={version:5,samples:fixedGlyphSamples(),source:'user-red-black-opening-screens'};
function glyphBankReady(){return true}
function inkValue(R,G,B,isR){if((G-R>70&&B-R>70&&G>140&&B>160)||(G-R>12&&G-B>35&&G>110))return 0;const L=.299*R+.587*G+.114*B;if(isR)return Math.max(0,Math.min(1,((R-G)-32)/82))*Math.max(0,Math.min(1,(205-G)/118));return Math.max(0,Math.min(1,(142-L)/105))}
function glyphDescriptor(cx,cy,r,isR){const size=56,c=document.createElement('canvas');c.width=c.height=size;const x=c.getContext('2d',{willReadFrequently:true});x.imageSmoothingEnabled=true;x.drawImage(C,cx-r*.64,cy-r*.64,r*1.28,r*1.28,0,0,size,size);const d=x.getImageData(0,0,size,size).data,ink=new Float32Array(size*size);let minX=size,minY=size,maxX=-1,maxY=-1,energy=0;for(let y=0;y<size;y++)for(let z=0;z<size;z++){const i=(y*size+z)*4,v=inkValue(d[i],d[i+1],d[i+2],isR);ink[y*size+z]=v;energy+=v;if(v>.14){if(z<minX)minX=z;if(z>maxX)maxX=z;if(y<minY)minY=y;if(y>maxY)maxY=y}}if(maxX<0||energy<5)return{v:Array(400).fill(0),energy:0};const pad=2;minX=Math.max(0,minX-pad);minY=Math.max(0,minY-pad);maxX=Math.min(size-1,maxX+pad);maxY=Math.min(size-1,maxY+pad);const bw=Math.max(1,maxX-minX+1),bh=Math.max(1,maxY-minY+1),out=[];for(let ty=0;ty<20;ty++)for(let tx=0;tx<20;tx++){const sx0=minX+tx*bw/20,sx1=minX+(tx+1)*bw/20,sy0=minY+ty*bh/20,sy1=minY+(ty+1)*bh/20;let sum=0,n=0;for(let yy=Math.floor(sy0);yy<Math.ceil(sy1);yy++)for(let xx=Math.floor(sx0);xx<Math.ceil(sx1);xx++){if(xx>=minX&&xx<=maxX&&yy>=minY&&yy<=maxY){sum+=ink[yy*size+xx];n++}}out.push(sum/Math.max(1,n))}let mx=0;for(const v of out)if(v>mx)mx=v;if(mx>.01)for(let i=0;i<out.length;i++)out[i]=Math.min(1,out[i]/mx);return{v:out,energy}}
function packedScoreShift(v,p,dx,dy){let ab=0,aa=0,bb=0,mad=0,inter=0,sa=0,sb=0;for(let y=0;y<20;y++)for(let x=0;x<20;x++){const i=y*20+x,a=v[i],sx=x-dx,sy=y-dy,b=(sx>=0&&sx<20&&sy>=0&&sy<20?p[sy*20+sx]:0)/255;ab+=a*b;aa+=a*a;bb+=b*b;mad+=Math.abs(a-b);const A=a>.20,B=b>.20;if(A)sa++;if(B)sb++;if(A&&B)inter++}const cos=ab/(Math.sqrt(aa*bb)+1e-9),shape=1-mad/400,f1=(2*inter)/(sa+sb+1e-9);return .50*cos+.28*shape+.22*f1}
function bankScore(desc,p){const a=glyphBank.samples[p]&&glyphBank.samples[p][0];if(!a)return-1;let best=-1;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++)best=Math.max(best,packedScoreShift(desc.v,a,dx,dy));return best}
function classify(cx,cy,r,isR){const hi=glyphDescriptor(cx,cy,r,isR),cand=isR?['K','A','B','N','R','C','P']:['k','a','b','n','r','c','p'],scores=[];for(const p of cand)scores.push({p,s:bankScore(hi,p)});scores.sort((a,b)=>b.s-a.s);return{p:scores[0].p,s:scores[0].s,margin:scores[0].s-scores[1].s,scores,calibrated:true,energy:hi.energy}}
function learnGlyphBankFromStart(){return true}"""
s=s[:start]+fixed+s[end:]

s=s.replace("const minS=cl.calibrated?.64:.42,minM=cl.calibrated?.010:-1;",
            "const minS=.68,minM=.018;",1)

old="if(!greenHit&&!cyanSeen)learnGlyphBankFromStart(rawOcc,rawSide,r);if(!glyphBankReady())return{invalid:true,needsCalibration:true,calFrames:glyphCal.frames.length,found:occCount,occCount,marker,selected:greenHit,occ,side,uiTurn};"
if old not in s:
    raise SystemExit('v117 calibration gate missing')
s=s.replace(old,"",1)

s=s.replace("showStatus(rec.needsCalibration?'棋子模板校准中':'当前棋面仍在重建',rec.needsCalibration?(rec.calFrames>0?'标准开局保持静止 · '+rec.calFrames+'/5 帧':'首次使用请先停留在完整标准开局，校准后以后不再重学'):'第 '+frameSeen+' 帧 · '+(rec.identityUncertain?'有棋子字形不够确定，拒绝猜测':rec.solverFailed?'全局棋子分配暂未唯一':'等待动画/高亮结束'));return",
            "showStatus('当前棋面仍在重建','第 '+frameSeen+' 帧 · '+(rec.identityUncertain?'固定字形库对某颗棋不够确定，拒绝猜测':rec.solverFailed?'全局棋子分配暂未唯一':'等待动画/高亮结束'));return",1)

s=s.replace("else turn='unknown';\n    if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();",
            "else turn='me';\n    if(kingInCheck(currentBoard,userRed))turn='me';saveTrustedState();",1)
s=s.replace("else showStatus('当前棋面已锁定 · '+sideText(),'未能确认上一手 · 等下一次合法落子后自动接管');",
            "else showStatus('当前棋面已锁定 · '+sideText(),'按本次启动作为残局接管');",1)

old_start="showStatus('象棋助手 1.0.17 稳定字形库版',restoredPending?'已恢复本次会话可信局面':'首次标准开局连续5帧校准并锁定模板 · 以后重置只全盘重识别，不再覆盖模板');"
if old_start not in s:
    raise SystemExit('v117 startup text missing')
s=s.replace(old_start,"showStatus('象棋助手 1.0.18 固定棋子库版','启动即按当前棋盘作为新残局 · 红黑固定模板 · 全盘重新识别');",1)

# Never restore an old board on overlay load: every service/overlay start is a fresh current-position takeover.
s=s.replace("restoreTrustedState();requestEngineWarmUp();showStatus('象棋助手 1.0.18 固定棋子库版'",
            "clearTrustedState();restoredPending=false;currentBoard=null;currentHash='';turn='unknown';requestEngineWarmUp();showStatus('象棋助手 1.0.18 固定棋子库版'",1)

p.write_text(s)

# Remove the manual floating reset/takeover button. Accessibility reconnect itself is the reset.
p=Path('app/src/main/java/com/openai/xiangqiassist/ChessAccessibilityService.java')
j=p.read_text()
for line in [
    'import android.graphics.drawable.GradientDrawable;\n',
    'import android.view.MotionEvent;\n',
    'import android.widget.TextView;\n',
    'import android.widget.Toast;\n']:
    j=j.replace(line,'')
j=j.replace('    private TextView sessionButton;\n    private WindowManager.LayoutParams sessionButtonLp;\n    private boolean sessionButtonMoved;\n','')

a=j.find('    private int dp(int v) {')
b=j.find('    private void applyConfigNow() {',a)
if a<0 or b<0:
    raise SystemExit('manual button helper block missing')
j=j[:a]+j[b:]

j=j.replace('        ensureSessionButton(bounds);\n','')
j=j.replace('            if (sessionButton != null) sessionButton.setVisibility(View.INVISIBLE);\n','')
j=j.replace('                    if (sessionButton != null && isAnalysisEnabled()) sessionButton.setVisibility(View.VISIBLE);\n','')
j=j.replace('        if (sessionButton != null && sessionButton.getVisibility() != View.INVISIBLE) sessionButton.setVisibility(View.INVISIBLE);\n','')
manual_cleanup='''        if (sessionButton != null) {
            try { wm.removeView(sessionButton); } catch (Throwable ignored) {}
            sessionButton = null; sessionButtonLp = null;
        }
'''
j=j.replace(manual_cleanup,'')

# Re-enabling Accessibility means: start analysis and create a brand-new current-position session.
j=j.replace('.edit()\n                .putLong(MainActivity.KEY_SESSION, reconnectSession).apply();',
            '.edit()\n                .putBoolean(MainActivity.KEY_ENABLED, true)\n                .putLong(MainActivity.KEY_SESSION, reconnectSession).apply();',1)

p.write_text(j)
