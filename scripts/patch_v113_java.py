from pathlib import Path

# MainActivity: every press of "开始实时分析" creates a brand-new session id.
p=Path('app/src/main/java/com/openai/xiangqiassist/MainActivity.java')
s=p.read_text()
old='public static final String KEY_RED = "user_red";'
new='public static final String KEY_RED = "user_red";\n    public static final String KEY_SESSION = "analysis_session";'
if old not in s: raise SystemExit('MainActivity KEY_RED anchor missing')
s=s.replace(old,new,1)

old="""        start.setOnClickListener(v -> {
            prefs.edit().putBoolean(KEY_ENABLED, true).apply();
            sendBroadcast(new Intent(ChessAccessibilityService.ACTION_CONFIG_CHANGED).setPackage(getPackageName()));
            refresh();
        });"""
new="""        start.setOnClickListener(v -> {
            long session = System.currentTimeMillis();
            prefs.edit().putBoolean(KEY_ENABLED, true).putLong(KEY_SESSION, session).apply();
            sendBroadcast(new Intent(ChessAccessibilityService.ACTION_CONFIG_CHANGED).setPackage(getPackageName()));
            refresh();
        });"""
if old not in s: raise SystemExit('MainActivity start block missing')
s=s.replace(old,new,1)
s=s.replace('TextView title = text("象棋助手 v1 · 重构版", 25, true);',
            'TextView title = text("象棋助手 1.0.13 · 新局会话版", 25, true);',1)
p.write_text(s)

# Accessibility service: include the session id in the overlay URL.
p=Path('app/src/main/java/com/openai/xiangqiassist/ChessAccessibilityService.java')
s=p.read_text()
old='    private String loadedSide = "";\n    private boolean registered;'
new='    private String loadedSide = "";\n    private long loadedSession = Long.MIN_VALUE;\n    private boolean registered;'
if old not in s: raise SystemExit('service field anchor missing')
s=s.replace(old,new,1)

old="""    private boolean userRed() {
        return getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE).getBoolean(MainActivity.KEY_RED, true);
    }

    private void applyConfigNow() {"""
new="""    private boolean userRed() {
        return getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE).getBoolean(MainActivity.KEY_RED, true);
    }

    private long sessionId() {
        return getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE).getLong(MainActivity.KEY_SESSION, 0L);
    }

    private String overlayUrl(String side, long session) {
        return "file:///android_asset/overlay.html?session=" + session + "#" + side;
    }

    private void applyConfigNow() {"""
if old not in s: raise SystemExit('service helper anchor missing')
s=s.replace(old,new,1)

old="""        String side = userRed() ? "red" : "black";
        if (overlay != null && !side.equals(loadedSide)) {
            overlay.loadUrl("file:///android_asset/overlay.html#" + side);
            loadedSide = side;
        }"""
new="""        String side = userRed() ? "red" : "black";
        long session = sessionId();
        if (overlay != null && (!side.equals(loadedSide) || session != loadedSession)) {
            if (engineBridge != null && session != loadedSession) engineBridge.newSession();
            overlay.loadUrl(overlayUrl(side, session));
            loadedSide = side;
            loadedSession = session;
        }"""
if old not in s: raise SystemExit('service applyConfig block missing')
s=s.replace(old,new,1)

old="""        String side = userRed() ? "red" : "black";
        if (overlay == null) {"""
new="""        String side = userRed() ? "red" : "black";
        long session = sessionId();
        if (overlay == null) {"""
if old not in s: raise SystemExit('service ensureOverlay start missing')
s=s.replace(old,new,1)

old="""            overlay.loadUrl("file:///android_asset/overlay.html#" + side);
            loadedSide = side;
            lastBounds.set(b);"""
new="""            overlay.loadUrl(overlayUrl(side, session));
            loadedSide = side;
            loadedSession = session;
            lastBounds.set(b);"""
if old not in s: raise SystemExit('service initial overlay load missing')
s=s.replace(old,new,1)

old="""            if (!side.equals(loadedSide)) {
                overlay.loadUrl("file:///android_asset/overlay.html#" + side);
                loadedSide = side;
            }"""
new="""            if (!side.equals(loadedSide) || session != loadedSession) {
                if (engineBridge != null && session != loadedSession) engineBridge.newSession();
                overlay.loadUrl(overlayUrl(side, session));
                loadedSide = side;
                loadedSession = session;
            }"""
if old not in s: raise SystemExit('service reload block missing')
s=s.replace(old,new,1)
p.write_text(s)

# EngineBridge: invalidate delayed results from previous sessions without restarting Pikafish.
p=Path('app/src/main/java/com/openai/xiangqiassist/EngineBridge.java')
s=p.read_text()

s,n=re.subn(r'(\s*)private final AtomicInteger latestRequest = new AtomicInteger\(-1\);',
           lambda m:m.group(1)+'private final AtomicInteger latestRequest = new AtomicInteger(-1);'+m.group(1)+'private final AtomicInteger generation = new AtomicInteger(0);',
           s,count=1)
if n!=1: raise SystemExit('EngineBridge latestRequest anchor missing')

pat=r'''    private void deliver\(int requestId, PikafishEngine\.Result r\) \{
        if \(latestRequest\.get\(\) != requestId\) return;
        String js = "window\.onEngineResult\(" \+ requestId \+ "," \+
                JSONObject\.quote\(r\.bestMove\) \+ "," \+ r\.scoreCp \+ "," \+ r\.depth \+ "," \+
                JSONObject\.quote\(r\.error == null \? "" : r\.error\) \+ "\)";
        webView\.post\(\(\) -> \{
            if \(latestRequest\.get\(\) == requestId\) webView\.evaluateJavascript\(js, null\);
        \}\);
    \}'''
rep='''    private void deliver(int gen, int requestId, PikafishEngine.Result r) {
        if (generation.get() != gen || latestRequest.get() != requestId) return;
        String js = "window.onEngineResult(" + requestId + "," +
                JSONObject.quote(r.bestMove) + "," + r.scoreCp + "," + r.depth + "," +
                JSONObject.quote(r.error == null ? "" : r.error) + ")";
        webView.post(() -> {
            if (generation.get() == gen && latestRequest.get() == requestId) webView.evaluateJavascript(js, null);
        });
    }'''
s,n=re.subn(pat,rep,s,count=1)
if n!=1: raise SystemExit('EngineBridge deliver block missing')

pat=r'''    public synchronized void analyze\(String fen, int requestId, int moveTimeMs\) \{
        latestRequest\.set\(requestId\);
        if \(!engine\.isReady\(\)\) \{
            deliver\(requestId, PikafishEngine\.Result\.err\("Pikafish 尚未就绪"\)\);
            return;
        \}
        worker\.getQueue\(\)\.clear\(\);
        worker\.submit\(\(\) -> deliver\(requestId, engine\.analyze\(fen, moveTimeMs\)\)\);
    \}'''
rep='''    public synchronized void analyze(String fen, int requestId, int moveTimeMs) {
        int gen = generation.get();
        latestRequest.set(requestId);
        if (!engine.isReady()) {
            deliver(gen, requestId, PikafishEngine.Result.err("Pikafish 尚未就绪"));
            return;
        }
        worker.getQueue().clear();
        worker.submit(() -> deliver(gen, requestId, engine.analyze(fen, moveTimeMs)));
    }

    synchronized void newSession() {
        generation.incrementAndGet();
        latestRequest.set(-1);
        worker.getQueue().clear();
    }'''
s,n=re.subn(pat,rep,s,count=1)
if n!=1: raise SystemExit('EngineBridge analyze block missing')

p.write_text(s)
