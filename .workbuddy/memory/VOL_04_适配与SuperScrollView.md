# VOL_04 多分辨率适配 / SuperScrollView

> 本分册由 `MEMORY.md` 拆分而来，**原文一字未删**。覆盖：Canvas 基准与安全区、棋盘取景、边缘锚数值、三个自适应组件、UIResolution 菜单与验证；SuperScrollView 初始化时机与吸附硬约束。

## 适配（多分辨率）
- Canvas = Overlay，1920×1080，Match 0.5。
- ★根画布不能直接做安全区 → `SafeAreaFitter` 挂到 Bg/Normal/Tips 三个 Panel（`UIManager.EnsureSafeArea`）。
- ★棋盘取景在 `CameraController`（底 2 格 / 顶 1 格 / 侧 1 格 + 安全区 + 相机下移 0.5 格），`BackgroundScale = 2.2`。
- ★边缘锚已固化进 `UIPrefabBuilder`：塔按钮底锚 49、Speed/Start (64,77)、箭头 60 / Codex 34、Close 68、Quit 74；单步重建菜单 310/311/312。
- ★局部布局按父 RectTransform 的**实际可用尺寸**算，不动基准 CanvasScaler。三组件：
  - `UIFullScreenBackground`：Bg 按 root Canvas 世界角点偏移，遮罩不漏边；
  - `UIFitInParent`：固定 Panel 仅在父尺寸不足时等比缩小，留 24，max=1；
  - `UIResponsivePage`：MainMenu 内容列。
- 规则唯一源 `Assets/Editor/UIResolutionLayout.cs`；已有资源用菜单 330 定点更新（**别全量重建**）；验证用 `Assets/Editor/UIResolutionVerifier.cs`（需 Play + 隔离存档）。记录在 `Docs/UIResolution/20261018/`。

## SuperScrollView（★最坑）
- `InitListView` 会一次性快照 viewport → **绝不能放 OnEnable 初始化**；`SelectView.Build` 挂 `_pendingInit`，首帧 `LateUpdate` 再 `DoInitListView`。
- 吸附硬约束：视口宽 = 卡片宽 = 1150×550；`pivot.x = 0`、`anchoredPosition.x = -575`；三处必须同步 `UIPrefabBuilder SelectItemW` ↔ `SelectView ItemWidth(1150/56)` ↔ `SelectLevelItem`。
- 图鉴视口中心 460×640。
