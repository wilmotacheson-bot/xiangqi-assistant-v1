# xiangqi-assistant-v1

Android 象棋分析助手 v1 重构版。

- AccessibilityService 截取目标窗口（Android 14+ 优先 takeScreenshotOfWindow）
- 木纹棋盘专用全盘识别与合法局面校验
- 本地 Pikafish ARM64 + NNUE
- 只显示推荐走法，不自动点击
- GitHub Actions 自动构建 APK

构建产物在 Actions 的 `xiangqi-assistant-v1-apk` artifact 中。
