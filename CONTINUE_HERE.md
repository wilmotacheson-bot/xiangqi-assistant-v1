# CONTINUE HERE — 象棋助手

新聊天/新模型从这里开始。

仓库：`wilmotacheson-bot/xiangqi-assistant-v1`

当前实际版本：**v1.0.26-s23-adaptive-grid**

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
- `scripts/patch_v126.py`
- `.github/workflows/build-apk.yml`

最近一次完成：
- v1.0.26 继续在 v1.0.25 上开发，没有回退/修复 v1.0.21；
- 参考 v1.0.21 的“打开即按当前棋面接管”稳定行为，针对用户新截图重新校准 S23 Ultra 棋盘采样位置；
- 定位到旧 S23 profile 的首行采样中心约下偏 6 px：标准开局依靠占位图仍能识别，但中盘/残局首次进入需要逐子字形识别，因此置信度明显下降；
- S23 基准首行中心已修正，并在首次全盘重建时增加 3×3 微调搜索（横/纵各 ±4 px 量级），用本机 glyph 置信度自动选择最佳采样网格；
- 保留 v1.0.25 S23 glyph bank、legacy fallback、v1.0.23 长局恢复、v1.0.24 切屏新 Session、Strong/Fast 与 Pikafish；
- GitHub Actions run `37103476373` 成功；
- APK artifact id `11266824640`；
- main 功能 SHA `b651ee1c509fb45193128a90c6552e6ab4acd76a`。

下一步：
1. 让用户实机测试 v1.0.26；
2. 重点直接从真实中盘/残局打开，不要只测标准开局；
3. 同时验证红方在下、黑方在下两种翻转方向；
4. 再测切屏回来与长局继续；
5. 若仍有具体局面失败，优先用对应原始截图/录屏做设备级几何/字形验证，继续叠加修复，不要重新讨论架构。

重要工作方式：
- 用户说“开始做/继续开发”就直接调用工具；
- 不发过程状态；
- 不要只说“收到”然后停；
- 正常情况下做到构建完成再回复；
- 最终优先发 APK。
