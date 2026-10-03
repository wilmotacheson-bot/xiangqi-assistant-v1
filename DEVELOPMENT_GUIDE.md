# 象棋助手开发指南

## 新聊天启动方式
新聊天不要重新讨论历史方案。首先读取：
1. `PROJECT_STATE.md`
2. `DEVELOPMENT_GUIDE.md`
3. `VERSION_HISTORY.md`
4. 当前交付补丁：`scripts/patch_v118.py`、`patch_v119.py`、`patch_v121.py`、`patch_v127.py`、`patch_v128.py`
5. `.github/workflows/build-apk.yml`

仓库：
`wilmotacheson-bot/xiangqi-assistant-v1`

用户如果说“继续开发象棋助手 / 接着做 / 开始做”，直接按当前状态继续。

## 开发执行模式
读取源码
→ 修改补丁脚本
→ 更新 workflow（如需要）
→ 提交分支
→ PR / merge 到 main
→ 等 GitHub Actions
→ 查看失败日志并修
→ 构建成功
→ 下载 artifact
→ 输出可安装 APK

不要用纯文字“开始开发”代替实际工具调用。

## 工程结构
实际 Android 工程由 CI 在运行时生成：
- 基线：`source_v104/*.b64`
- 生成后路径包括：
  - `app/src/main/assets/overlay.html`
  - `app/src/main/java/com/openai/xiangqiassist/ChessAccessibilityService.java`
  - `app/src/main/java/com/openai/xiangqiassist/EngineBridge.java`
  - `app/src/main/java/com/openai/xiangqiassist/PikafishEngine.java`
  - `app/src/main/AndroidManifest.xml`
  - `app/build.gradle`

## 当前核心补丁职责
- `patch_v118.py`：固定双字形库、当前残局接管。
- `patch_v119.py`：强/快模式及快棋预算。
- `patch_v121.py`：用户确认最稳定的识别/跟踪基线。
- `patch_v127.py`：只做 S23 Ultra 棋盘几何/分辨率适配。
- `patch_v128.py`：只增强中途打开时的 S23 初始 y 锁定；加入 2~32 子合法占位约束、棋子/空位暗度分离评分，并在 currentBoard 未锁定时逐帧重试。
- `patch_v122.py` ~ `patch_v126.py`：历史保留，当前 workflow 不执行。

## 当前版本
v1.0.28-v121-s23-midgame-lock

最新成功构建：
- Actions run：`37118729800`
- artifact id：`11271798414`
- build SHA：`47974ab49cf21aacb5fd6f5bcaf37475d7e13228`

注意：workflow 和 artifact 名称仍残留旧 v1.0.19 字样，不代表实际功能版本。不要因此回退代码。

## 修改原则
- 不重复设计已有功能；
- 不删除已稳定修复；
- 新修复尽量以新 patch 叠加，便于回滚和定位；
- 不因单个设备问题全局粗暴放宽识别阈值；
- 优先设备适配、棋盘几何微调、整盘合法约束、唯一解判断；
- 不猜测不确定棋子，但也不能让一个轻微低置信度永久锁死整个局面；
- 每个可交付版本必须跑 GitHub Actions 构建、Pikafish smoke test、Gradle build、签名。

## 用户交互要求
- 用户偏好直接结果，不要反复确认；
- 用户已经多次明确要求“做完之前不要停”；
- 开发过程中不要发进度播报；
- 真正阻塞时才说明具体阻塞；
- 正常情况下最终只发完成说明和 APK。
