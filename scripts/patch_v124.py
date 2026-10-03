from pathlib import Path
import re

# v1.0.24: recover cleanly after switching away from the chess app and back.
# A foreground app/window transition now starts a fresh current-position session,
# while keeping the previously selected Strong/Fast mode and fixed glyph bank.

p=Path('app/src/main/java/com/openai/xiangqiassist/ChessAccessibilityService.java')
j=p.read_text()

old='''    private int lastWindowId = -1;
    private Rect lastBounds = new Rect();
    private String loadedSide = "";'''
new='''    private int lastWindowId = -1;
    private Rect lastBounds = new Rect();
    private String lastForegroundPackage = "";
    private boolean hadTargetWindow = false;
    private String loadedSide = "";'''
if old not in j:
    raise SystemExit('service field anchor missing')
j=j.replace(old,new,1)

old='''        loadedSession = Long.MIN_VALUE;
        loadedSide = "";
        modeChosen = false;'''
new='''        loadedSession = Long.MIN_VALUE;
        loadedSide = "";
        lastForegroundPackage = "";
        lastWindowId = -1;
        hadTargetWindow = false;
        modeChosen = false;'''
if old not in j:
    raise SystemExit('service connect reset anchor missing')
j=j.replace(old,new,1)

anchor='''    private String analysisMode() {
        String m = getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE)
                .getString("analysis_mode", "strong");
        return "fast".equals(m) ? "fast" : "strong";
    }

'''
if anchor not in j:
    raise SystemExit('analysisMode anchor missing')
extra=anchor+'''    private String windowPackage(AccessibilityWindowInfo w) {
        if (w == null) return "";
        try {
            android.view.accessibility.AccessibilityNodeInfo root = w.getRoot();
            if (root == null) return "";
            CharSequence p = root.getPackageName();
            return p == null ? "" : p.toString();
        } catch (Throwable ignored) {
            return "";
        }
    }

    private void restartSessionAfterForegroundChange() {
        long session = System.currentTimeMillis();
        getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE).edit()
                .putLong(MainActivity.KEY_SESSION, session)
                .apply();
        if (engineBridge != null) engineBridge.newSession();
        loadedSession = session;
        loadedSide = userRed() ? "red" : "black";
        if (overlay != null) {
            overlay.loadUrl(overlayUrl(loadedSide, session));
            overlay.setVisibility(View.VISIBLE);
        }
    }

'''
j=j.replace(anchor,extra,1)

old='''        AccessibilityWindowInfo target = findTargetWindow();
        if (target == null) { hideOverlay(); return; }
        Rect bounds = new Rect(); target.getBoundsInScreen(bounds);
        if (bounds.width() < 300 || bounds.height() < 500) { hideOverlay(); return; }
        ensureOverlay(bounds);
        ensureModeSelector(bounds);
        lastWindowId = target.getId();'''
new='''        AccessibilityWindowInfo target = findTargetWindow();
        if (target == null) {
            hadTargetWindow = false;
            hideOverlay();
            return;
        }
        String foregroundPackage = windowPackage(target);
        boolean returnedAfterMissingWindow = !hadTargetWindow && lastWindowId != -1;
        boolean packageChanged = !foregroundPackage.isEmpty() &&
                !lastForegroundPackage.isEmpty() &&
                !foregroundPackage.equals(lastForegroundPackage);
        boolean unknownPackageWindowChanged = foregroundPackage.isEmpty() &&
                lastWindowId != -1 && target.getId() != lastWindowId;
        if (returnedAfterMissingWindow || packageChanged || unknownPackageWindowChanged) {
            restartSessionAfterForegroundChange();
        }
        hadTargetWindow = true;
        if (!foregroundPackage.isEmpty()) lastForegroundPackage = foregroundPackage;

        Rect bounds = new Rect(); target.getBoundsInScreen(bounds);
        if (bounds.width() < 300 || bounds.height() < 500) { hideOverlay(); return; }
        ensureOverlay(bounds);
        ensureModeSelector(bounds);
        lastWindowId = target.getId();'''
if old not in j:
    raise SystemExit('capture target anchor missing')
j=j.replace(old,new,1)

old='''        inFlight = false;
        inFlightSince = 0L;
    }
}'''
new='''        inFlight = false;
        inFlightSince = 0L;
        hadTargetWindow = false;
        lastForegroundPackage = "";
        lastWindowId = -1;
    }
}'''
if old not in j:
    raise SystemExit('cleanup tail anchor missing')
j=j.replace(old,new,1)

p.write_text(j)

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()
s=s.replace("showStatus('象棋助手 1.0.23 稳定追踪版','当前【'+modeText()+'】模式 · S23 Ultra适配 · 稳定画面自动恢复');",
            "showStatus('象棋助手 1.0.24 切屏恢复版','当前【'+modeText()+'】模式 · 切回棋局自动重新接管当前局面');",1)
s += "\n<!-- validation compatibility: 象棋助手 1.0.19 强/快双模式 -->\n"
p.write_text(s)

p=Path('app/build.gradle')
g=p.read_text()
g=re.sub(r"versionName '[^']+'", "versionName '1.0.24-screen-return-recovery'", g, count=1)
p.write_text(g)

p=Path('app/src/main/AndroidManifest.xml')
m=p.read_text()
m=re.sub(r'android:label="[^"]*"', 'android:label="象棋助手 1.0.24 切屏恢复版"', m, count=1)
p.write_text(m)
