# CONTINUE HERE — 象棋助手

新聊天/新模型从这里开始。

仓库：`wilmotacheson-bot/xiangqi-assistant-v1`

当前实际版本：**v1.0.25-s23-glyph-bank**

请立即读取：
- `PROJECT_STATE.md`
- `DEVELOPMENT_GUIDE.md`
- `VERSION_HISTORY.md`

然后再看：
- `scripts/patch_v118.py`
- `scripts/patch_v119.py`
- `scripts/patch_v121.py`
- `scripts/patch_v122.py`
- `scripts/patch_v123.py`
- `scripts/patch_v124.py`
- `scripts/patch_v125.py`
- `.github/workflows/build-apk.yml`

最近一次完成：
- v1.0.25 为 Galaxy S23 Ultra 增加本机专用 14 类棋子固定字形库；
- 字形来自用户原始录屏中的标准开局帧；
- 解决目标：中盘/残局直接打开时因单颗棋字形置信度不足而无法整盘重建；
- legacy glyph bank 仍作为 fallback；
- GitHub Actions run `37100800574` 成功；
- APK artifact id `11266330998`；
- main SHA `d67c5907f49196f6ab76ed3baed66d534f6dac5c`。

下一步：
1. 让用户实机测试 v1.0.25；
2. 重点测试“中盘直接打开/残局直接打开/切屏回来/长局继续”；
3. 若仍卡住，直接分析用户原始录屏/截图并继续做，不要重新讨论架构。

重要工作方式：
- 用户说“开始做/继续开发”就直接调用工具；
- 不发过程状态；
- 不要只说“收到”然后停；
- 正常情况下做到构建完成再回复；
- 最终优先发 APK。
