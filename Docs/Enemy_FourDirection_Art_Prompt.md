# 敌人上下方向美术补全与四方向接入：可执行 Prompt

请直接在 Unity 工程 `D:/FreedomTower_1` 中完成以下工作。目标是参考现有敌人美术，补齐朝上、朝下的图片与动画表现，并让它们随实际移动方向正确显示。本次只完成一个示例，交付效果后等待我明确审核通过，再继续其他敌人。

## 一、工程事实与检查入口

以下信息已经过检查，执行时请以当前磁盘内容复核，不要仅凭文件名猜测引用关系：

- Unity 版本为 `2022.3.62f3c1`。
- `D:/FreedomTower_1/Assets/Prefabs/Enemy` 当前有 119 个 `.prefab`。将该目录直属 `.prefab` 按文件名升序排列，忽略 `.meta`，第一个是 `Enemy_AdvancedHen.prefab`；本次示例固定使用它，不按 MonsterCatalog 的数组顺序选择。
- 示例战斗预制体：`D:/FreedomTower_1/Assets/Prefabs/Enemy/Enemy_AdvancedHen.prefab`。
- 对应源预制体：`D:/FreedomTower_1/Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.prefab`。
- 对应原始图集：`D:/FreedomTower_1/Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.png`，尺寸 960×800，Sprite Mode 为 Multiple，PPU 为 100。图集中有 `HeadNormal`、`HeadAngry`、`HeadDead`、`Body`、`Wing`、`Leg` 六个分件；战斗预制体还包含 `LegL`、`LegR`、`Shadow`、`HpBar` 等节点。这是分件组合和 Transform 动画资源，不能将其当作完整角色的逐帧行走图集。
- 示例实际引用的共享控制器是 `D:/FreedomTower_1/Assets/_UIAssets/Monsters/_Common/Animations/Rooster/Controller.controller`，不是根据角色名称猜测的 Chicken 控制器。该目录包含 `Ready.anim`、`Walk.anim`、`Attack.anim`、`Death.anim`。
- 移动与朝向逻辑：`D:/FreedomTower_1/Assets/Scripts/Enemy/BaseEnemy.cs`。重点检查 `Init`、`SetPath`、`MoveAlongPath`、`MoveStraight`、`FaceMoveDirection`、`OnRecycle`。当前 `FaceMoveDirection` 仅修改根节点 X 缩放；纯纵向移动时保持旧朝向。`SetPath` 还会向后寻找第一段横向路径来设置出生朝向，接入四方向时需要调整这一行为。
- 动画事件接收：`D:/FreedomTower_1/Assets/Scripts/Enemy/MonsterAnimEventReceiver.cs`。`SetHead(int)` 会切换正常、愤怒、死亡头；新增方向资源必须与这套事件兼容。
- 生成和寻址链路：`D:/FreedomTower_1/Assets/Editor/MonsterPrefabBuilder.cs`、`D:/FreedomTower_1/Assets/Scripts/Data/MonsterCatalog.cs`、`D:/FreedomTower_1/Assets/Scripts/Core/Res/ResTable.cs`、`D:/FreedomTower_1/Assets/Scripts/Enemy/EnemyManager.cs`、`D:/FreedomTower_1/Assets/Scripts/Data/EnemyConfig.cs`。
- 配置入口：`D:/FreedomTower_1/Assets/ConfigJson/tbenemydata.json` 中 `AdvancedHen` 当前为 id=15、resName=`Enemy_AdvancedHen`、animController 为空，运行时沿用预制体控制器。数值配置来自 Luban，不要为了美术接入修改敌人数值或手工改生成代码。

## 二、本次执行边界

先完成 AdvancedHen 的真实可运行示例，包括图片、必要动画、预制体接入、方向切换和效果验证；不要只交方案或概念图。

允许新增通用方向组件、方向资源配置及必要的最小公共代码改动，但只对示例预制体启用。没有方向配置的其他敌人继续使用现有水平表现。

本轮不得生成其他敌人的上下图片，不得修改其他 118 个战斗预制体，不得直接修改会影响其他敌人的共享 Rooster 控制器或共享动画。若需要改变控制器或动画，制作示例专用资源。不要运行“导入全部怪物”等全量重建操作来验证示例。

## 三、参考原图补全美术

1. 调用可用的图像生成或图像编辑能力，使用原图集和从原预制体渲染的完整角色图作为视觉参考。实际使用 imagegen 等技能时，先读取相应技能说明。参考图应能清楚展示原角色的完整形象，而不只是零散分件。
2. 保留 AdvancedHen 的角色特征：粗黑描边、红色鸡冠、棕色头颈、浅米色身体和翅膀、黄色喙和脚，以及原有眼睛、比例、配色、明暗和卡通风格。
3. 新增 Up 和 Down 两套真实视角：Up 为角色朝屏幕上方移动时的背向表现，Down 为朝屏幕下方移动时的正向表现。根据实际场景相机核对世界坐标与屏幕方向，并保持现有战场机位和透视风格。
4. 上下视角必须有合理的身体、头部、翅膀和腿部遮挡关系；不能用侧面图片旋转 90°、上下翻转或拉伸充当新增方向。
5. 优先沿用分件方案；若现有侧面动画的分件位移和旋转不适合上下视角，应配套新增方向姿态或专用动画，不要仅替换图片后强行沿用不合适的运动。其他实现方案可以采用，但必须保留角色风格、现有动画状态和战斗表现，并说明选择原因。
6. 保留原始图集。建议将新增资源放入 `D:/FreedomTower_1/Assets/_UIAssets/Monsters/Birds/AdvancedHen/Directions/`，清楚命名 Up、Down 及各分件或动作。采用真实透明背景 PNG，检查透明边缘、裁切和描边完整性，导入参数与原美术兼容，并正确设置 Pivot、PPU 和渲染顺序。
7. 上下方向必须有可循环的行走表现，并正确承接现有待机、准备、奔跑、攻击和死亡状态。允许沿用原控制器中 Idle/Ready、Walk/Run 的复用关系，不要求凭空增加原工程没有的独立动作；必须处理正常、愤怒、死亡头的方向对应关系，避免攻击或死亡事件把头换回侧面。
8. 如图像生成能力不可用，应明确说明能力缺口，保留已完成的分析、参考图和可复用接入工作，准确列出尚未完成的美术；不得将旋转图、占位图或未验证结果作为完成品交付。

## 四、代码与预制体接入

1. 方向由实际世界移动向量决定，使用四方向枚举或等价的清晰设计。区分 Left、Right、Up、Down；斜向移动采用主轴判断，并给方向切换添加合理容差或滞回，避免在轴分界附近反复跳动。移动量接近零时保留最后有效方向。
2. 兼容地面寻路和飞行直线移动。出生、重新寻路和对象池复用时，应根据当前第一段有效移动设置方向；对启用四方向的示例，不再向后寻找未来的横向路径来代替当前方向。
3. 左右沿用原始美术和水平镜像机制，兼容 `Global.ArtFaceLeft`。切到上下方向时清理此前水平镜像带来的影响，避免正背面被错误镜像、残留错误缩放或发生额外旋转。
4. 保持已有调用契约：`State` 的 0=Idle、1=Ready、2=Walk、3=Run、9=Death，`Speed` 为 float，`Attack` 为 Trigger，兼容控制器中既有的 `Action` 参数。若使用方向专用 Animator，确保状态、播放速度及事件传递完整；普通转向不要反复重播行走动画。
5. 检查 `BaseEnemy` 的身体 SpriteRenderer 缓存、闪白、死亡淡出和收缩、`MonsterAnimEventReceiver` 的头部引用及对象池重置。新增的方向渲染器必须参与应有的表现；每次 Init/OnRecycle 后恢复正确方向、正常头、透明度和可见性，不能遗留死亡状态或显示两套身体。
6. 保持血条正常显示、从正确方向扣血，并处理现有 `CompensateHpBarFlip` 的关联。角色转向不能使血条倒置；阴影和脚底接地点应稳定，各方向视觉尺寸应协调，避免明显跳位、漂浮或缩放突变。
7. 沿用 `BaseEnemy.Tick` 的集中驱动方式，不为每只怪增加不必要的独立 Update 或每帧层级查找。
8. 保持现有资源逻辑名和战斗预制体路径。新增美术、配置和动画应通过序列化引用或既有寻址体系被加载；如需主动寻址，再最小化扩展 ResTable 和对应打包规则。检查当前启用的 YooAsset/AssetBundle 链路，避免只有编辑器中能看到新增图片。
9. 提供可重复执行的单预制体接入入口，并让 `MonsterPrefabBuilder` 后续重建示例时能保留或重新应用方向配置，避免再次导入怪物后丢失本次成果。不要为此批量改写其他预制体，不要无故改变现有资源 GUID。

## 五、验证与交付

完成后进行与改动相称的编译和实际运行验证：

- 在 Unity 中分别展示 Left、Right、Up、Down 的完整角色和连续行走效果。
- 通过一条包含上下左右和连续转弯的路径验证真实移动；覆盖纯纵向出生、横纵转向、接近零位移和斜向判断。
- 验证已有动画状态、攻击/死亡事件、受击、血条、暂停与倍速、回收后再次生成，以及路径刷新后的方向。
- 抽查未启用方向资源的敌人，确认公共代码改动没有改变它们的既有表现。
- 检查 Console 中本次引入的编译错误、Missing 引用和 AnimationEvent 接收错误，并核对新增资源依赖。

将审核材料放入 `D:/FreedomTower_1/Docs/EnemyDirectionReview/AdvancedHen/`。至少交付：原始参考与新增方向的对照图、四方向静态预览、能看清行走和转弯的 GIF 或视频、修改文件清单、Unity 中复现效果的入口或步骤，以及验证结果。准确区分已实际运行验证的项目和受环境限制未验证的项目，不得声称通过未运行的检查。

完成示例所需的制作、接入、修复和验证后，再停下向我展示成果并等待审核；不要在只有方案时就让我批准。只有我明确回复“通过”或“继续批量处理”等同义指令后，才能进入下一阶段。若我提出修改，先迭代这个示例，不得自行视为通过。

## 六、审核通过后的批量阶段

收到我明确批准后，重新按文件名升序枚举 `D:/FreedomTower_1/Assets/Prefabs/Enemy` 中的 `.prefab`，跳过已完成的 AdvancedHen，按顺序逐个处理其余资源。沿用获批的画风、方向规则、目录约定和接入方式，但针对每种怪物的原始图集、分件层级、地面/飞行特征、控制器和动画事件分别适配，不把鸡的结构套给其他怪物。

维护已完成、待处理、异常及原因的进度记录，保证可以中断后继续。单个异常需记录并清楚报告，不能静默使用占位图冒充完成。批量结束后交付全部资源与验证报告。
