from pathlib import Path
import re

# v1.0.21 UI polish:
# 1) make the top status pill much more transparent so underlying game text remains readable;
# 2) mode chooser disappears immediately after a choice, or after 3 seconds if untouched,
#    while keeping the last selected mode as the default.

p=Path('app/src/main/assets/overlay.html')
s=p.read_text()

old="background:rgba(18,18,18,.82);color:white;font-size:14px;font-weight:760;line-height:1.25;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,.22);"
new="background:rgba(18,18,18,.12);color:rgba(255,255,255,.68);font-size:14px;font-weight:760;line-height:1.25;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.08);"
if old not in s:
    raise SystemExit('status pill style anchor missing')
s=s.replace(old,new,1)

# Keep the label current for the user-visible overlay.
s=s.replace("showStatus('象棋助手 1.0.20 快棋100步版','当前【'+modeText()+'】模式 · 快模式按5分钟/100步重新定标');",
            "showStatus('象棋助手 1.0.21 淡化状态栏版','当前【'+modeText()+'】模式 · 模式选择3秒自动收起');",1)

p.write_text(s)

p=Path('app/src/main/java/com/openai/xiangqiassist/ChessAccessibilityService.java')
j=p.read_text()

old='''        wm.addView(modePanel, modePanelLp);
    }

    private void applyConfigNow() {'''
new='''        wm.addView(modePanel, modePanelLp);
        main.postDelayed(() -> {
            if (modePanel != null && !modeChosen) {
                modeChosen = true;
                try { wm.removeView(modePanel); } catch (Throwable ignored) {}
                modePanel = null;
                modePanelLp = null;
            }
        }, 3000);
    }

    private void applyConfigNow() {'''
if old not in j:
    raise SystemExit('mode selector addView anchor missing')
j=j.replace(old,new,1)

p.write_text(j)

# User-visible version name/label; keep package/versionCode stable so current CI validation still passes.
p=Path('app/build.gradle')
g=p.read_text()
g=re.sub(r"versionName '[^']+'", "versionName '1.0.21-light-status-auto-hide-mode'", g, count=1)
p.write_text(g)

p=Path('app/src/main/AndroidManifest.xml')
m=p.read_text()
m=re.sub(r'android:label="[^"]*"', 'android:label="象棋助手 1.0.21 淡化状态栏版"', m, count=1)
p.write_text(m)
