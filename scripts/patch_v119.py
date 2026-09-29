from pathlib import Path
import re

# v1.0.19: strong/fast thinking modes. Recognition logic stays untouched.
p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

# Mode comes from the native floating selector.
anchor="const SESSION_ID=(()=>{try{return new URL(location.href).searchParams.get('session')||'0'}catch(_){return'0'}})();"
if anchor not in s:
    raise SystemExit('SESSION_ID anchor missing')
s=s.replace(anchor,anchor+"const ANALYSIS_MODE=(()=>{try{return new URL(location.href).searchParams.get('mode')==='fast'?'fast':'strong'}catch(_){return'strong'}})();",1)

# Keep v1.0.18 strong mode exactly as-is; add a 5-minute/50-move fast policy beside it.
old="""function boundedThinkMs(pos,red,legal){const n=legal.length;if(n<=1)return 0;if(kingInCheck(pos,red)){if(n<=3)return 650;if(n<=6)return 1100;return 1800}if(n<=10)return 700;if(n<=18)return 1100;if(n<=28)return 1800;if(n<=38)return 2800;return 4500}"""
if old not in s:
    raise SystemExit('boundedThinkMs anchor missing')
new=old+"""
const FAST_ENGINE_BUDGET_MS=115000;
let fastSpentMs=0,fastSearches=0;
function fastThinkMs(pos,red,legal){
  const n=legal.length;
  if(n<=1)return 0;
  let base;
  if(kingInCheck(pos,red)){
    base=n<=3?650:n<=6?950:1450;
  }else{
    const captures=legal.reduce((k,m)=>k+(pos[m.to]?1:0),0);
    if(n<=8)base=800;
    else if(n<=16)base=1200;
    else if(n<=26)base=1800;
    else if(n<=36)base=2500;
    else base=3400;
    if(captures>=4&&n>=18)base+=350;
    if(captures>=7&&n>=28)base+=250;
  }
  base=Math.min(4000,base);
  const remain=Math.max(0,FAST_ENGINE_BUDGET_MS-fastSpentMs);
  const future=Math.max(8,50-fastSearches);
  let budgetCap=Math.max(600,Math.min(4000,remain/Math.max(1,future)*1.35));
  if(remain<20000)budgetCap=Math.min(budgetCap,800);
  else if(remain<35000)budgetCap=Math.min(budgetCap,1100);
  else if(remain<55000)budgetCap=Math.min(budgetCap,1600);
  return Math.round(Math.max(550,Math.min(base,budgetCap,4000)));
}
function selectedThinkMs(pos,red,legal){return ANALYSIS_MODE==='fast'?fastThinkMs(pos,red,legal):boundedThinkMs(pos,red,legal)}
function modeText(){return ANALYSIS_MODE==='fast'?'快':'强'}"""
s=s.replace(old,new,1)

old="const legal=legalMoves(analysisBoard,userRed),checkMs=Math.max(0,Math.round(performance.now()-t0)),thinkMs=boundedThinkMs(analysisBoard,userRed,legal);"
new="const legal=legalMoves(analysisBoard,userRed),checkMs=Math.max(0,Math.round(performance.now()-t0)),thinkMs=selectedThinkMs(analysisBoard,userRed,legal);"
if old not in s:
    raise SystemExit('thinkMs selection anchor missing')
s=s.replace(old,new,1)

old="analysisRunning=true;clearArrow();\n  showStatus(wasCheck?'正在计算应将/解杀…':'Pikafish 正在计算…','局面校验 '+checkMs+'ms · 本步限时 '+(thinkMs/1000).toFixed(2)+' 秒 · 最长4.5秒');"
new="analysisRunning=true;clearArrow();const engineStartedAt=performance.now();\n  showStatus(wasCheck?'正在计算应将/解杀…':'Pikafish 正在计算…','【'+modeText()+'】局面校验 '+checkMs+'ms · 本步预算 '+(thinkMs/1000).toFixed(2)+' 秒'+(ANALYSIS_MODE==='fast'?' · 快棋最高4秒':' · 强模式最高4.5秒'));"
if old not in s:
    raise SystemExit('analysis status anchor missing')
s=s.replace(old,new,1)

old="  }finally{analysisRunning=false}\n}"
new="  }finally{if(ANALYSIS_MODE==='fast'){fastSearches++;fastSpentMs+=Math.max(0,performance.now()-engineStartedAt)}analysisRunning=false}\n}"
if old not in s:
    raise SystemExit('analysis finally anchor missing')
s=s.replace(old,new,1)

old="showStatus('象棋助手 1.0.18 固定棋子库版','启动即按当前棋盘作为新残局 · 红黑固定模板 · 全盘重新识别');"
new="showStatus('象棋助手 1.0.19 强/快双模式','当前【'+modeText()+'】模式 · 固定棋子库/残局接管逻辑保持不变');"
if old not in s:
    raise SystemExit('v118 startup title missing')
s=s.replace(old,new,1)
p.write_text(s)

# Native floating mode chooser. It appears on every Accessibility-service start,
# remembers the previous choice, and switching mode starts a fresh analysis session
# so any delayed result from the old mode is discarded.
p=Path('app/src/main/java/com/openai/xiangqiassist/ChessAccessibilityService.java')
j=p.read_text()

j=j.replace('import android.graphics.Color;\n','import android.graphics.Color;\nimport android.graphics.drawable.GradientDrawable;\n',1)
j=j.replace('import android.webkit.WebView;\n','import android.webkit.WebView;\nimport android.widget.LinearLayout;\nimport android.widget.TextView;\n',1)

old='    private WebView overlay;\n    private WindowManager.LayoutParams overlayLp;'
new='''    private WebView overlay;
    private WindowManager.LayoutParams overlayLp;
    private LinearLayout modePanel;
    private WindowManager.LayoutParams modePanelLp;
    private boolean modeChosen;'''
if old not in j:
    raise SystemExit('overlay fields anchor missing')
j=j.replace(old,new,1)

# Every Accessibility reconnect asks for a mode again, while keeping the last mode as the highlighted default.
old='''        loadedSession = Long.MIN_VALUE;
        loadedSide = "";
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);'''
new='''        loadedSession = Long.MIN_VALUE;
        loadedSide = "";
        modeChosen = false;
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);'''
if old not in j:
    raise SystemExit('onServiceConnected state anchor missing')
j=j.replace(old,new,1)

old='''    private String overlayUrl(String side, long session) {
        return "file:///android_asset/overlay.html?session=" + session + "#" + side;
    }

    private void applyConfigNow() {'''
new='''    private String analysisMode() {
        String m = getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE)
                .getString("analysis_mode", "strong");
        return "fast".equals(m) ? "fast" : "strong";
    }

    private String overlayUrl(String side, long session) {
        return "file:///android_asset/overlay.html?session=" + session +
                "&mode=" + analysisMode() + "#" + side;
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    private TextView modeChip(String text, boolean selected) {
        TextView v = new TextView(this);
        v.setText(text);
        v.setTextColor(Color.WHITE);
        v.setTextSize(14);
        v.setGravity(Gravity.CENTER);
        v.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        v.setPadding(dp(15), 0, dp(15), 0);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(selected ? Color.argb(245, 62, 126, 72) : Color.argb(235, 38, 38, 38));
        bg.setCornerRadius(dp(17));
        bg.setStroke(dp(1), Color.argb(220, 255, 255, 255));
        v.setBackground(bg);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, dp(34));
        lp.setMargins(dp(3), dp(3), dp(3), dp(3));
        v.setLayoutParams(lp);
        return v;
    }

    private void chooseMode(String mode) {
        String value = "fast".equals(mode) ? "fast" : "strong";
        long session = System.currentTimeMillis();
        getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE).edit()
                .putString("analysis_mode", value)
                .putLong(MainActivity.KEY_SESSION, session)
                .apply();
        modeChosen = true;
        if (modePanel != null) {
            try { wm.removeView(modePanel); } catch (Throwable ignored) {}
            modePanel = null;
            modePanelLp = null;
        }
        if (engineBridge != null) engineBridge.newSession();
        loadedSession = session;
        loadedSide = userRed() ? "red" : "black";
        if (overlay != null) {
            overlay.loadUrl(overlayUrl(loadedSide, session));
            overlay.setVisibility(View.VISIBLE);
        }
    }

    private void ensureModeSelector(Rect b) {
        if (modeChosen || wm == null || modePanel != null) return;
        String current = analysisMode();
        modePanel = new LinearLayout(this);
        modePanel.setOrientation(LinearLayout.HORIZONTAL);
        modePanel.setGravity(Gravity.CENTER);
        modePanel.setPadding(dp(5), dp(3), dp(5), dp(3));
        GradientDrawable shell = new GradientDrawable();
        shell.setColor(Color.argb(220, 18, 18, 18));
        shell.setCornerRadius(dp(21));
        shell.setStroke(dp(1), Color.argb(170, 255, 255, 255));
        modePanel.setBackground(shell);
        modePanel.setElevation(dp(6));

        TextView title = modeChip("模式", false);
        title.setTextSize(12);
        TextView strong = modeChip("强", "strong".equals(current));
        TextView fast = modeChip("快", "fast".equals(current));
        strong.setOnClickListener(v -> chooseMode("strong"));
        fast.setOnClickListener(v -> chooseMode("fast"));
        modePanel.addView(title);
        modePanel.addView(strong);
        modePanel.addView(fast);

        modePanelLp = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT, dp(44),
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                        WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN |
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        modePanelLp.gravity = Gravity.TOP | Gravity.LEFT;
        modePanelLp.x = Math.max(b.left + dp(8), b.right - dp(196));
        modePanelLp.y = b.top + dp(88);
        wm.addView(modePanel, modePanelLp);
    }

    private void applyConfigNow() {'''
if old not in j:
    raise SystemExit('overlayUrl/applyConfig anchor missing')
j=j.replace(old,new,1)

old='        ensureOverlay(bounds);\n        lastWindowId = target.getId();'
new='        ensureOverlay(bounds);\n        ensureModeSelector(bounds);\n        lastWindowId = target.getId();'
if old not in j:
    raise SystemExit('ensureOverlay capture anchor missing')
j=j.replace(old,new,1)

# Hide the chooser while screenshots are taken on Android 11-13 so it never contaminates recognition.
old='            if (overlay != null) overlay.setVisibility(View.INVISIBLE);\n            main.postDelayed(() -> takeScreenshot(Display.DEFAULT_DISPLAY, executor, new TakeScreenshotCallback() {'
new='            if (overlay != null) overlay.setVisibility(View.INVISIBLE);\n            if (modePanel != null) modePanel.setVisibility(View.INVISIBLE);\n            main.postDelayed(() -> takeScreenshot(Display.DEFAULT_DISPLAY, executor, new TakeScreenshotCallback() {'
if old not in j:
    raise SystemExit('screenshot hide anchor missing')
j=j.replace(old,new,1)

old='                    if (overlay != null && isAnalysisEnabled()) overlay.setVisibility(View.VISIBLE);\n                    handleScreenshot(result);'
new='                    if (overlay != null && isAnalysisEnabled()) overlay.setVisibility(View.VISIBLE);\n                    if (modePanel != null && !modeChosen && isAnalysisEnabled()) modePanel.setVisibility(View.VISIBLE);\n                    handleScreenshot(result);'
if old not in j:
    raise SystemExit('screenshot success restore anchor missing')
j=j.replace(old,new,1)

old='                    if (overlay != null && isAnalysisEnabled()) overlay.setVisibility(View.VISIBLE);\n                    handleCaptureError("屏幕截图失败: " + errorCode);'
new='                    if (overlay != null && isAnalysisEnabled()) overlay.setVisibility(View.VISIBLE);\n                    if (modePanel != null && !modeChosen && isAnalysisEnabled()) modePanel.setVisibility(View.VISIBLE);\n                    handleCaptureError("屏幕截图失败: " + errorCode);'
if old not in j:
    raise SystemExit('screenshot error restore anchor missing')
j=j.replace(old,new,1)

old='''    private void hideOverlay() {
        if (overlay != null && overlay.getVisibility() != View.INVISIBLE) overlay.setVisibility(View.INVISIBLE);
    }'''
new='''    private void hideOverlay() {
        if (overlay != null && overlay.getVisibility() != View.INVISIBLE) overlay.setVisibility(View.INVISIBLE);
        if (modePanel != null && modePanel.getVisibility() != View.INVISIBLE) modePanel.setVisibility(View.INVISIBLE);
    }'''
if old not in j:
    raise SystemExit('hideOverlay anchor missing')
j=j.replace(old,new,1)

old='''        if (overlay != null) {
            try { wm.removeView(overlay); } catch (Throwable ignored) {}
            overlay.destroy(); overlay = null;
        }
        inFlight = false;'''
new='''        if (modePanel != null) {
            try { wm.removeView(modePanel); } catch (Throwable ignored) {}
            modePanel = null; modePanelLp = null;
        }
        if (overlay != null) {
            try { wm.removeView(overlay); } catch (Throwable ignored) {}
            overlay.destroy(); overlay = null;
        }
        inFlight = false;'''
if old not in j:
    raise SystemExit('cleanup anchor missing')
j=j.replace(old,new,1)

p.write_text(j)


# Five-minute fast-mode retune for long 80-100 move games.
p=Path('app/src/main/assets/overlay.html')
s=p.read_text()
old_sel="function selectedThinkMs(pos,red,legal){return ANALYSIS_MODE==='fast'?fastThinkMs(pos,red,legal):boundedThinkMs(pos,red,legal)}"
new_sel="""function fastThinkMs100(pos,red,legal){
  const FAST_ENGINE_BUDGET_MS_100=72000,FAST_TARGET_MOVES_100=100;
  const n=legal.length;
  if(n<=1)return 0;
  let base;
  if(kingInCheck(pos,red)){
    base=n<=3?600:n<=6?900:1350;
  }else{
    const captures=legal.reduce((k,m)=>k+(pos[m.to]?1:0),0);
    if(n<=8)base=500;
    else if(n<=16)base=700;
    else if(n<=26)base=900;
    else if(n<=36)base=1250;
    else base=1650;
    if(captures>=4&&n>=18)base+=150;
    if(captures>=7&&n>=28)base+=150;
  }
  base=Math.min(2200,base);
  const remain=Math.max(0,FAST_ENGINE_BUDGET_MS_100-fastSpentMs);
  const future=Math.max(10,FAST_TARGET_MOVES_100-fastSearches);
  let budgetCap=Math.max(450,Math.min(2200,remain/Math.max(1,future)*1.18));
  if(remain<12000)budgetCap=Math.min(budgetCap,550);
  else if(remain<22000)budgetCap=Math.min(budgetCap,700);
  else if(remain<35000)budgetCap=Math.min(budgetCap,900);
  return Math.round(Math.max(450,Math.min(base,budgetCap,2200)));
}
function selectedThinkMs(pos,red,legal){return ANALYSIS_MODE==='fast'?fastThinkMs100(pos,red,legal):boundedThinkMs(pos,red,legal)}"""
if old_sel not in s:
    raise SystemExit('v119 selectedThinkMs missing')
s=s.replace(old_sel,new_sel,1)
s=s.replace("ANALYSIS_MODE==='fast'?' · 快棋最高4秒':' · 强模式最高4.5秒'",
            "ANALYSIS_MODE==='fast'?' · 5分钟/100步 · 最高2.2秒':' · 强模式最高4.5秒'",1)
p.write_text(s)
