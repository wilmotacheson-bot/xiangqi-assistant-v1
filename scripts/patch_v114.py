from pathlib import Path
import re

# Add a small touchable accessibility-overlay button for manual new-game / midgame takeover.
p=Path('app/src/main/java/com/openai/xiangqiassist/ChessAccessibilityService.java')
s=p.read_text()

# imports
s=s.replace('import android.graphics.Color;\n', 'import android.graphics.Color;\nimport android.graphics.drawable.GradientDrawable;\n', 1)
s=s.replace('import android.view.Gravity;\n', 'import android.view.Gravity;\nimport android.view.MotionEvent;\n', 1)
s=s.replace('import android.webkit.WebView;\n', 'import android.webkit.WebView;\nimport android.widget.TextView;\nimport android.widget.Toast;\n', 1)

# fields
old='    private WebView overlay;\n    private WindowManager.LayoutParams overlayLp;'
new='    private WebView overlay;\n    private WindowManager.LayoutParams overlayLp;\n    private TextView sessionButton;\n    private WindowManager.LayoutParams sessionButtonLp;\n    private boolean sessionButtonMoved;'
if old not in s: raise SystemExit('overlay field anchor missing')
s=s.replace(old,new,1)

# Re-enabling Accessibility is itself a fresh-session boundary.
p=Path('app/src/main/java/com/openai/xiangqiassist/ChessAccessibilityService.java')
_src=p.read_text()
old='''    @Override protected void onServiceConnected() {
        super.onServiceConnected();
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);'''
new='''    @Override protected void onServiceConnected() {
        super.onServiceConnected();
        long reconnectSession = System.currentTimeMillis();
        getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE).edit()
                .putLong(MainActivity.KEY_SESSION, reconnectSession).apply();
        loadedSession = Long.MIN_VALUE;
        loadedSide = "";
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);'''
if old not in _src: raise SystemExit('onServiceConnected anchor missing')
_src=_src.replace(old,new,1)
p.write_text(_src)

# add helper methods before applyConfigNow
anchor='    private void applyConfigNow() {'
helpers=r'''    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    private void startFreshSessionFromOverlay() {
        long session = System.currentTimeMillis();
        getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE).edit()
                .putLong(MainActivity.KEY_SESSION, session).apply();

        if (engineBridge != null) engineBridge.newSession();

        String side = userRed() ? "red" : "black";
        loadedSession = session;
        loadedSide = side;

        if (overlay != null) {
            overlay.loadUrl(overlayUrl(side, session));
            overlay.setVisibility(View.VISIBLE);
        }
        if (sessionButton != null) {
            sessionButton.setText("重建中…");
            main.postDelayed(() -> {
                if (sessionButton != null) sessionButton.setText("↻ 新局 / 接管");
            }, 1200);
        }
        Toast.makeText(this, "已清空上一局状态，正在从当前棋盘重新接管", Toast.LENGTH_SHORT).show();
    }

    private void ensureSessionButton(Rect b) {
        if (wm == null) return;
        final int bw = dp(116), bh = dp(40);
        if (sessionButton == null) {
            sessionButton = new TextView(this);
            sessionButton.setText("↻ 新局 / 接管");
            sessionButton.setTextColor(Color.WHITE);
            sessionButton.setTextSize(13);
            sessionButton.setGravity(Gravity.CENTER);
            sessionButton.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
            sessionButton.setPadding(dp(8), 0, dp(8), 0);

            GradientDrawable bg = new GradientDrawable();
            bg.setColor(Color.argb(220, 28, 28, 28));
            bg.setCornerRadius(dp(20));
            bg.setStroke(dp(1), Color.argb(210, 255, 255, 255));
            sessionButton.setBackground(bg);
            sessionButton.setElevation(dp(4));

            sessionButtonLp = new WindowManager.LayoutParams(
                    bw, bh, WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN |
                            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                    PixelFormat.TRANSLUCENT);
            sessionButtonLp.gravity = Gravity.TOP | Gravity.LEFT;
            sessionButtonLp.x = Math.max(b.left + dp(8), b.right - bw - dp(10));
            sessionButtonLp.y = b.top + dp(132);

            final float[] down = new float[2];
            final int[] origin = new int[2];
            final boolean[] moved = new boolean[1];

            sessionButton.setOnTouchListener((v, e) -> {
                switch (e.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        down[0] = e.getRawX(); down[1] = e.getRawY();
                        origin[0] = sessionButtonLp.x; origin[1] = sessionButtonLp.y;
                        moved[0] = false;
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        float dx = e.getRawX() - down[0], dy = e.getRawY() - down[1];
                        if (Math.abs(dx) > dp(5) || Math.abs(dy) > dp(5)) moved[0] = true;
                        if (moved[0]) {
                            int nx = origin[0] + Math.round(dx);
                            int ny = origin[1] + Math.round(dy);
                            nx = Math.max(b.left, Math.min(b.right - bw, nx));
                            ny = Math.max(b.top, Math.min(b.bottom - bh, ny));
                            sessionButtonLp.x = nx;
                            sessionButtonLp.y = ny;
                            sessionButtonMoved = true;
                            try { wm.updateViewLayout(sessionButton, sessionButtonLp); } catch (Throwable ignored) {}
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (!moved[0]) v.performClick();
                        return true;
                    case MotionEvent.ACTION_CANCEL:
                        return true;
                }
                return false;
            });
            sessionButton.setOnClickListener(v -> startFreshSessionFromOverlay());
            wm.addView(sessionButton, sessionButtonLp);
        } else {
            if (!sessionButtonMoved) {
                sessionButtonLp.x = Math.max(b.left + dp(8), b.right - bw - dp(10));
                sessionButtonLp.y = b.top + dp(132);
                try { wm.updateViewLayout(sessionButton, sessionButtonLp); } catch (Throwable ignored) {}
            } else {
                int nx = Math.max(b.left, Math.min(b.right - bw, sessionButtonLp.x));
                int ny = Math.max(b.top, Math.min(b.bottom - bh, sessionButtonLp.y));
                if (nx != sessionButtonLp.x || ny != sessionButtonLp.y) {
                    sessionButtonLp.x = nx; sessionButtonLp.y = ny;
                    try { wm.updateViewLayout(sessionButton, sessionButtonLp); } catch (Throwable ignored) {}
                }
            }
            if (sessionButton.getVisibility() != View.VISIBLE) sessionButton.setVisibility(View.VISIBLE);
        }
    }

'''
if anchor not in s: raise SystemExit('applyConfigNow anchor missing')
s=s.replace(anchor,helpers+anchor,1)

# Ensure button whenever main overlay is ensured.
old='        ensureOverlay(bounds);\n        lastWindowId = target.getId();'
new='        ensureOverlay(bounds);\n        ensureSessionButton(bounds);\n        lastWindowId = target.getId();'
if old not in s: raise SystemExit('capture ensureOverlay anchor missing')
s=s.replace(old,new,1)

# Hide button on Android 11-13 screenshots, restore after.
old='            if (overlay != null) overlay.setVisibility(View.INVISIBLE);\n            main.postDelayed(() -> takeScreenshot(Display.DEFAULT_DISPLAY, executor, new TakeScreenshotCallback() {'
new='            if (overlay != null) overlay.setVisibility(View.INVISIBLE);\n            if (sessionButton != null) sessionButton.setVisibility(View.INVISIBLE);\n            main.postDelayed(() -> takeScreenshot(Display.DEFAULT_DISPLAY, executor, new TakeScreenshotCallback() {'
if old not in s: raise SystemExit('screenshot hide anchor missing')
s=s.replace(old,new,1)

s=s.replace('                    if (overlay != null && isAnalysisEnabled()) overlay.setVisibility(View.VISIBLE);\n                    handleScreenshot(result);',
            '                    if (overlay != null && isAnalysisEnabled()) overlay.setVisibility(View.VISIBLE);\n                    if (sessionButton != null && isAnalysisEnabled()) sessionButton.setVisibility(View.VISIBLE);\n                    handleScreenshot(result);',1)
s=s.replace('                    if (overlay != null && isAnalysisEnabled()) overlay.setVisibility(View.VISIBLE);\n                    handleCaptureError("屏幕截图失败: " + errorCode);',
            '                    if (overlay != null && isAnalysisEnabled()) overlay.setVisibility(View.VISIBLE);\n                    if (sessionButton != null && isAnalysisEnabled()) sessionButton.setVisibility(View.VISIBLE);\n                    handleCaptureError("屏幕截图失败: " + errorCode);',1)

# Hide button when overlay is hidden.
old='    private void hideOverlay() {\n        if (overlay != null && overlay.getVisibility() != View.INVISIBLE) overlay.setVisibility(View.INVISIBLE);\n    }'
new='    private void hideOverlay() {\n        if (overlay != null && overlay.getVisibility() != View.INVISIBLE) overlay.setVisibility(View.INVISIBLE);\n        if (sessionButton != null && sessionButton.getVisibility() != View.INVISIBLE) sessionButton.setVisibility(View.INVISIBLE);\n    }'
if old not in s: raise SystemExit('hideOverlay anchor missing')
s=s.replace(old,new,1)

# Remove button on cleanup.
old='        if (overlay != null) {\n            try { wm.removeView(overlay); } catch (Throwable ignored) {}\n            overlay.destroy(); overlay = null;\n        }\n        inFlight = false;'
new='        if (sessionButton != null) {\n            try { wm.removeView(sessionButton); } catch (Throwable ignored) {}\n            sessionButton = null; sessionButtonLp = null;\n        }\n        if (overlay != null) {\n            try { wm.removeView(overlay); } catch (Throwable ignored) {}\n            overlay.destroy(); overlay = null;\n        }\n        inFlight = false;'
if old not in s: raise SystemExit('cleanup anchor missing')
s=s.replace(old,new,1)

p.write_text(s)

# Expose EngineBridge.newSession to native service and also make it callable from JS if needed later.
p=Path('app/src/main/java/com/openai/xiangqiassist/EngineBridge.java')
s=p.read_text()
old='    synchronized void newSession() {\n        generation.incrementAndGet();'
new='    @JavascriptInterface\n    public synchronized void newSession() {\n        generation.incrementAndGet();'
if old not in s: raise SystemExit('newSession method anchor missing')
s=s.replace(old,new,1)
p.write_text(s)

# Bump overlay text only; actual reset is native so the fullscreen WebView remains non-touchable.
p=Path('app/src/main/assets/overlay.html')
s=p.read_text()
old="showStatus('象棋助手 1.0.13 新局会话版',restoredPending?'已恢复本次开始后的可信局面':'每次点开始都会新建会话 · 真人/人机均不用头像绿框判断回合');"
new="showStatus('象棋助手 1.0.14 手动接管版',restoredPending?'已恢复本次会话可信局面':'需要新开局或残局接管时，点右侧“新局 / 接管”按钮');"
if old not in s: raise SystemExit('overlay startup text anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
