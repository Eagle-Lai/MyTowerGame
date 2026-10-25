# 选关地图预览

适用工程：FreedomTower_1 / Unity 2022.3.62f3c1。

## 使用

- `Tools > 塔防 > 关卡地图预览 > 生成全部关卡预览`：编辑模式下自动使用 main 场景进入 Play Mode，等待配置与资源就绪，按有效关卡顺序生成图片，结束后退出。使用独立测试存储，不改真实进度。
- 已在 Play Mode 时同一菜单直接生成，结束后保持运行。
- `截取当前关卡预览`：在已进入关卡的 Play Mode 中使用。只读取当前关卡 ID，重新构造干净的初始棋盘，不截玩家当前布防。
- `取消生成` 或进度框 Cancel：停止后保留已经完成的图片，清理临时场景、相机与渲染纹理。
- `更新选关卡片布局`：仅定点更新 SelectLevelItem.prefab；保留已有根节点状态、文字样式及无关属性。正常 UIPrefabBuilder 重建也使用同一布局函数。

## 图片与加载

- 正式资源：`Assets/_UIAssets/LevelPreviews/LevelPreview_{levelId:D3}.png`。
- 每张 1024×576，完整棋盘等比居中，6% 留边；没有 HUD、玩家塔、敌人、路径指示或建造高亮。
- 截图在 Editor Play Mode 中使用真实 `BoardView.Build`、`CellView`、地图配置及项目精灵生成，独立 preview scene 与 Camera.scene 隔离其他对象。构造器放在未激活对象上，避免替换游戏的 BoardView.Instance。
- PNG 覆盖不删除 .meta，保持 GUID。Sprite Single、无 mipmap、Clamp、Bilinear、不可读、无压缩、最大 1024。
- `LevelPreviewCatalog` 统一路径/逻辑名，`LevelPreviewIds.cs` 保存当前有效关卡 ID 清单；全部生成成功后在退出 Play Mode 时按需更新清单。新增关卡后执行全部生成并退出 Play Mode，等待编译。
- `ResTable` 注册为 `UiHud`，现有 `_UIAssets` 收集器与 `FTBundlePackRule` 收集到 `freetower_ui_hud.bundle`。正式 Player 通过现有 ResLoader 加载，无 AssetDatabase 运行时依赖。

## 卡片行为

- 保留 1150×550、Body/CanvasGroup、列表步长与原有吸附/点击规则。左侧 MapPreview，右侧动态名称、星级、难度/锁定文字。
- 同步加载只发生在条目绑定时；预览引用按可见/活跃条目共享计数，禁用/销毁释放。没有每帧加载或运行时 Texture2D/Sprite.Create。
- 复用先清图。缺失资源显示暗色地图纹理占位，同一缺图每个 Play 会话只警告一次；补图后重新进入 Play Mode。
- Label 的 TextLocalizer 保留但禁用：富文本由 SelectView 生成。切换语言后在 LateUpdate 统一回填，避免静态本地化将名称、星级与难度覆盖。批量多语言绑定器也保留该约定。

## 验证

在独立测试存储、配置已加载的 Play Mode 中，可执行：

```csharp
FTProject.EditorTools.LevelPreviewVerifier.Run("Temp/LevelPreviewAgent/verification");
```

验证全部关卡图片、导入参数、逻辑名唯一性、分包、三种语言、列表正反遍历/重复打开、预览释放、缺图占位、箭头、拖动、图片射线穿透、生产锁定规则、居中/非居中点击及详情窗口，并生成五张选关效果图与 verification.json。

2026-10-25：当前 30 关预览实际生成；YooAsset 编辑器模拟模式验证通过；真实收集器复算得到 30 个 ui_hud 图片资源。未执行 Android Player 或真实 AssetBundle 构建。

截图生成报告：`Temp/LevelPreviewAgent/capture-result.json`。正式维护不需修改 Luban 表、Assets/ConfigJson、Assets/Gen、评级哈希或玩家存档。
