# 逐页 UX 与状态说明

每项对应同名独立画面。线框从最终结构提取为灰阶结构稿，图片区为占位；不是手绘草图。以下说明解释对初始草图的信息优先级调整。动态缺失值仍为“—”，条件示意不作为玩家实况。

## 01_splash · 开屏

- 出现条件：启动游戏；证据：规划界面。
- 用户目标：确认品牌并等待进入。
- 主要信息：品牌标记、中英文名称、启动状态。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：无额外次要提交。
- 返回/关闭：由系统推进，不增加虚构取消。
- 状态变化与误操作：启动游戏；数据需以产品当前状态替换。
- 版式收益：品牌留白与状态分开，避免等待信息争抢注意。
- 文件：[简中PNG](../screens/png/01_splash.png) · [SVG](../screens/svg/01_splash.svg) · [线框PNG](../wireframes/png/01_splash.png) · [线框SVG](../wireframes/svg/01_splash.svg) · [繁中PNG](../localization/png/01_splash-zh-Hant.png) · [English PNG](../localization/png/01_splash-en.png)

## 02_loading_reading · 加载资源

- 出现条件：加载流程处于加载资源；证据：规划界面。
- 用户目标：了解当前等待阶段并处理失败。
- 主要信息：阶段文字、可信等待状态、短玩法提示。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：无额外次要提交。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：无可信进度只显示阶段，完成后进入目标页。
- 版式收益：阶段和失败动作靠近，不以虚构百分比制造进度。
- 文件：[简中PNG](../screens/png/02_loading_reading.png) · [SVG](../screens/svg/02_loading_reading.svg) · [线框PNG](../wireframes/png/02_loading_reading.png) · [线框SVG](../wireframes/svg/02_loading_reading.svg) · [繁中PNG](../localization/png/02_loading_reading-zh-Hant.png) · [English PNG](../localization/png/02_loading_reading-en.png)

## 02_loading_failed · 加载失败

- 出现条件：加载流程处于加载失败；证据：规划界面。
- 用户目标：了解当前等待阶段并处理失败。
- 主要信息：阶段文字、可信等待状态、短玩法提示。
- 首要动作：重试载入。
- 次要动作：返回选关。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：失败保留进度并重试；成功自动进入目标页。
- 版式收益：阶段和失败动作靠近，不以虚构百分比制造进度。
- 文件：[简中PNG](../screens/png/02_loading_failed.png) · [SVG](../screens/svg/02_loading_failed.svg) · [线框PNG](../wireframes/png/02_loading_failed.png) · [线框SVG](../wireframes/svg/02_loading_failed.svg) · [繁中PNG](../localization/png/02_loading_failed-zh-Hant.png) · [English PNG](../localization/png/02_loading_failed-en.png)

## 03_update_checking · 检查更新

- 出现条件：资源服务支持更新且处于检查更新；证据：规划界面 / 条件适用。
- 用户目标：理解资源准备与恢复方式。
- 主要信息：检查、下载、校验、结果和当前可用动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回。
- 返回/关闭：返回启动页；进行中的资源任务中止能力待产品确认。
- 状态变化与误操作：不确定等待；返回启动来源。
- 版式收益：阶段轨与大标题并列；一次只突出当前阶段。
- 不可用项：请稍候；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/03_update_checking.png) · [SVG](../screens/svg/03_update_checking.svg) · [线框PNG](../wireframes/png/03_update_checking.png) · [线框SVG](../wireframes/svg/03_update_checking.svg) · [繁中PNG](../localization/png/03_update_checking-zh-Hant.png) · [English PNG](../localization/png/03_update_checking-en.png)

## 03_update_download · 下载更新

- 出现条件：资源服务支持更新且处于下载更新；证据：规划界面 / 条件适用。
- 用户目标：理解资源准备与恢复方式。
- 主要信息：检查、下载、校验、结果和当前可用动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回；暂停下载。
- 返回/关闭：返回启动页；进行中的资源任务中止能力待产品确认。
- 状态变化与误操作：有实际下载量才显示确定进度；可暂停。
- 版式收益：阶段轨与大标题并列；一次只突出当前阶段。
- 文件：[简中PNG](../screens/png/03_update_download.png) · [SVG](../screens/svg/03_update_download.svg) · [线框PNG](../wireframes/png/03_update_download.png) · [线框SVG](../wireframes/svg/03_update_download.svg) · [繁中PNG](../localization/png/03_update_download-zh-Hant.png) · [English PNG](../localization/png/03_update_download-en.png)

## 03_update_validating · 校验内容

- 出现条件：资源服务支持更新且处于校验内容；证据：规划界面 / 条件适用。
- 用户目标：理解资源准备与恢复方式。
- 主要信息：检查、下载、校验、结果和当前可用动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回。
- 返回/关闭：返回启动页；进行中的资源任务中止能力待产品确认。
- 状态变化与误操作：校验阶段不冒充可进入游戏。
- 版式收益：阶段轨与大标题并列；一次只突出当前阶段。
- 不可用项：请稍候；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/03_update_validating.png) · [SVG](../screens/svg/03_update_validating.svg) · [线框PNG](../wireframes/png/03_update_validating.png) · [线框SVG](../wireframes/svg/03_update_validating.svg) · [繁中PNG](../localization/png/03_update_validating-zh-Hant.png) · [English PNG](../localization/png/03_update_validating-en.png)

## 03_update_complete · 更新完成

- 出现条件：资源服务支持更新且处于更新完成；证据：规划界面 / 条件适用。
- 用户目标：理解资源准备与恢复方式。
- 主要信息：检查、下载、校验、结果和当前可用动作。
- 首要动作：进入游戏。
- 次要动作：返回。
- 返回/关闭：返回启动页；进行中的资源任务中止能力待产品确认。
- 状态变化与误操作：资源可用后才进入游戏。
- 版式收益：阶段轨与大标题并列；一次只突出当前阶段。
- 文件：[简中PNG](../screens/png/03_update_complete.png) · [SVG](../screens/svg/03_update_complete.svg) · [线框PNG](../wireframes/png/03_update_complete.png) · [线框SVG](../wireframes/svg/03_update_complete.svg) · [繁中PNG](../localization/png/03_update_complete-zh-Hant.png) · [English PNG](../localization/png/03_update_complete-en.png)

## 03_update_paused · 暂停下载

- 出现条件：资源服务支持更新且处于暂停下载；证据：规划界面 / 条件适用。
- 用户目标：理解资源准备与恢复方式。
- 主要信息：检查、下载、校验、结果和当前可用动作。
- 首要动作：继续下载。
- 次要动作：返回。
- 返回/关闭：返回启动页；进行中的资源任务中止能力待产品确认。
- 状态变化与误操作：保留已下载量需服务支持；继续后恢复。
- 版式收益：阶段轨与大标题并列；一次只突出当前阶段。
- 文件：[简中PNG](../screens/png/03_update_paused.png) · [SVG](../screens/svg/03_update_paused.svg) · [线框PNG](../wireframes/png/03_update_paused.png) · [线框SVG](../wireframes/svg/03_update_paused.svg) · [繁中PNG](../localization/png/03_update_paused-zh-Hant.png) · [English PNG](../localization/png/03_update_paused-en.png)

## 03_update_resuming · 继续下载

- 出现条件：资源服务支持更新且处于继续下载；证据：规划界面 / 条件适用。
- 用户目标：理解资源准备与恢复方式。
- 主要信息：检查、下载、校验、结果和当前可用动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回。
- 返回/关闭：返回启动页；进行中的资源任务中止能力待产品确认。
- 状态变化与误操作：恢复期间等待，不冒充下载完成。
- 版式收益：阶段轨与大标题并列；一次只突出当前阶段。
- 不可用项：请稍候；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/03_update_resuming.png) · [SVG](../screens/svg/03_update_resuming.svg) · [线框PNG](../wireframes/png/03_update_resuming.png) · [线框SVG](../wireframes/svg/03_update_resuming.svg) · [繁中PNG](../localization/png/03_update_resuming-zh-Hant.png) · [English PNG](../localization/png/03_update_resuming-en.png)

## 03_update_retry · 重试连接

- 出现条件：资源服务支持更新且处于重试连接；证据：规划界面 / 条件适用。
- 用户目标：理解资源准备与恢复方式。
- 主要信息：检查、下载、校验、结果和当前可用动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回。
- 返回/关闭：返回启动页；进行中的资源任务中止能力待产品确认。
- 状态变化与误操作：重试期间避免重复请求；失败回错误分支。
- 版式收益：阶段轨与大标题并列；一次只突出当前阶段。
- 不可用项：请稍候；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/03_update_retry.png) · [SVG](../screens/svg/03_update_retry.svg) · [线框PNG](../wireframes/png/03_update_retry.png) · [线框SVG](../wireframes/svg/03_update_retry.svg) · [繁中PNG](../localization/png/03_update_retry-zh-Hant.png) · [English PNG](../localization/png/03_update_retry-en.png)

## 03_update_failed · 更新失败

- 出现条件：资源服务支持更新且处于更新失败；证据：规划界面 / 条件适用。
- 用户目标：理解资源准备与恢复方式。
- 主要信息：检查、下载、校验、结果和当前可用动作。
- 首要动作：重试连接。
- 次要动作：返回；返回启动页。
- 返回/关闭：返回启动页；进行中的资源任务中止能力待产品确认。
- 状态变化与误操作：解释连接失败，重试或返回；单机本体不凭空依赖联网。
- 版式收益：阶段轨与大标题并列；一次只突出当前阶段。
- 文件：[简中PNG](../screens/png/03_update_failed.png) · [SVG](../screens/svg/03_update_failed.svg) · [线框PNG](../wireframes/png/03_update_failed.png) · [线框SVG](../wireframes/svg/03_update_failed.svg) · [繁中PNG](../localization/png/03_update_failed-zh-Hant.png) · [English PNG](../localization/png/03_update_failed-en.png)

## 04_menu_new · 主菜单·首次开始

- 出现条件：尚无可继续检查点；证据：规划界面。
- 用户目标：从当前进度继续或选择挑战。
- 主要信息：品牌主视觉、有效继续入口、关卡进度、图鉴和设置。
- 首要动作：开始游戏。
- 次要动作：设置；选择关卡；炮塔图鉴；怪物图鉴；退出游戏。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：无检查点显示开始游戏。
- 版式收益：左侧决策、右侧战场气氛；进度统计低于主动作。
- 文件：[简中PNG](../screens/png/04_menu_new.png) · [SVG](../screens/svg/04_menu_new.svg) · [线框PNG](../wireframes/png/04_menu_new.png) · [线框SVG](../wireframes/svg/04_menu_new.svg) · [繁中PNG](../localization/png/04_menu_new-zh-Hant.png) · [English PNG](../localization/png/04_menu_new-en.png)

## 04_menu_continue · 主菜单·继续进度

- 出现条件：存在已保存且有效的波次检查点；证据：规划界面。
- 用户目标：从当前进度继续或选择挑战。
- 主要信息：品牌主视觉、有效继续入口、关卡进度、图鉴和设置。
- 首要动作：继续游戏。
- 次要动作：设置；选择关卡；炮塔图鉴；怪物图鉴；退出游戏。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：有效检查点才显示继续，恢复已保存波次。
- 版式收益：左侧决策、右侧战场气氛；进度统计低于主动作。
- 文件：[简中PNG](../screens/png/04_menu_continue.png) · [SVG](../screens/svg/04_menu_continue.svg) · [线框PNG](../wireframes/png/04_menu_continue.png) · [线框SVG](../wireframes/svg/04_menu_continue.svg) · [繁中PNG](../localization/png/04_menu_continue-zh-Hant.png) · [English PNG](../localization/png/04_menu_continue-en.png)

## 05_select_all · 关卡导航·全部有效关卡

- 出现条件：全量关卡导航，读取玩家进度；证据：已有证据。
- 用户目标：快速定位全部有效关卡与目标关卡。
- 主要信息：全量关卡导航、当前选择、地图、历史评级。
- 首要动作：查看战前简报。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：全量关卡导航，读取玩家进度；数据需以产品当前状态替换。
- 版式收益：全量网格减少翻页，预览独立避免点击后丢失位置。
- 文件：[简中PNG](../screens/png/05_select_all.png) · [SVG](../screens/svg/05_select_all.svg) · [线框PNG](../wireframes/png/05_select_all.png) · [线框SVG](../wireframes/svg/05_select_all.svg) · [繁中PNG](../localization/png/05_select_all-zh-Hant.png) · [English PNG](../localization/png/05_select_all-en.png)

## 06_item_normal · 关卡条目·普通

- 出现条件：同一条目的普通条件示意，非玩家当前进度；证据：已有证据。
- 用户目标：判断同一关卡当前能否挑战。
- 主要信息：关卡身份、状态符号、历史成绩、对应入口。
- 首要动作：查看战前简报。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：普通条目可看简报。
- 版式收益：状态文字与图形组合，锁定不伪装成可挑战按钮。
- 文件：[简中PNG](../screens/png/06_item_normal.png) · [SVG](../screens/svg/06_item_normal.svg) · [线框PNG](../wireframes/png/06_item_normal.png) · [线框SVG](../wireframes/svg/06_item_normal.svg) · [繁中PNG](../localization/png/06_item_normal-zh-Hant.png) · [English PNG](../localization/png/06_item_normal-en.png)

## 06_item_selected · 关卡条目·选中

- 出现条件：同一条目的选中条件示意，非玩家当前进度；证据：已有证据。
- 用户目标：判断同一关卡当前能否挑战。
- 主要信息：关卡身份、状态符号、历史成绩、对应入口。
- 首要动作：查看战前简报。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：选中以边框、勾与标签表达。
- 版式收益：状态文字与图形组合，锁定不伪装成可挑战按钮。
- 文件：[简中PNG](../screens/png/06_item_selected.png) · [SVG](../screens/svg/06_item_selected.svg) · [线框PNG](../wireframes/png/06_item_selected.png) · [线框SVG](../wireframes/svg/06_item_selected.svg) · [繁中PNG](../localization/png/06_item_selected-zh-Hant.png) · [English PNG](../localization/png/06_item_selected-en.png)

## 06_item_complete · 关卡条目·已完成

- 出现条件：同一条目的已完成条件示意，非玩家当前进度；证据：已有证据。
- 用户目标：判断同一关卡当前能否挑战。
- 主要信息：关卡身份、状态符号、历史成绩、对应入口。
- 首要动作：查看战前简报。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：通关标记只在真实进度证实时出现。
- 版式收益：状态文字与图形组合，锁定不伪装成可挑战按钮。
- 文件：[简中PNG](../screens/png/06_item_complete.png) · [SVG](../screens/svg/06_item_complete.svg) · [线框PNG](../wireframes/png/06_item_complete.png) · [线框SVG](../wireframes/svg/06_item_complete.svg) · [繁中PNG](../localization/png/06_item_complete-zh-Hant.png) · [English PNG](../localization/png/06_item_complete-en.png)

## 06_item_locked · 关卡条目·未解锁

- 出现条件：同一条目的未解锁条件示意，非玩家当前进度；证据：已有证据。
- 用户目标：判断同一关卡当前能否挑战。
- 主要信息：关卡身份、状态符号、历史成绩、对应入口。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回；查看解锁条件。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：展示当前解锁原因，不编造门槛。
- 版式收益：状态文字与图形组合，锁定不伪装成可挑战按钮。
- 文件：[简中PNG](../screens/png/06_item_locked.png) · [SVG](../screens/svg/06_item_locked.svg) · [线框PNG](../wireframes/png/06_item_locked.png) · [线框SVG](../wireframes/svg/06_item_locked.svg) · [繁中PNG](../localization/png/06_item_locked-zh-Hant.png) · [English PNG](../localization/png/06_item_locked-en.png)

## 06_item_continue · 关卡条目·可继续

- 出现条件：同一条目的可继续条件示意，非玩家当前进度；证据：已有证据。
- 用户目标：判断同一关卡当前能否挑战。
- 主要信息：关卡身份、状态符号、历史成绩、对应入口。
- 首要动作：继续挑战。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：有效检查点才显示继续。
- 版式收益：状态文字与图形组合，锁定不伪装成可挑战按钮。
- 文件：[简中PNG](../screens/png/06_item_continue.png) · [SVG](../screens/svg/06_item_continue.svg) · [线框PNG](../wireframes/png/06_item_continue.png) · [线框SVG](../wireframes/svg/06_item_continue.svg) · [繁中PNG](../localization/png/06_item_continue-zh-Hant.png) · [English PNG](../localization/png/06_item_continue-en.png)

## 06_item_history · 关卡条目·历史星级

- 出现条件：同一条目的历史星级条件示意，非玩家当前进度；证据：已有证据。
- 用户目标：判断同一关卡当前能否挑战。
- 主要信息：关卡身份、状态符号、历史成绩、对应入口。
- 首要动作：查看战前简报。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：填充星数来自已保存历史成绩。
- 版式收益：状态文字与图形组合，锁定不伪装成可挑战按钮。
- 文件：[简中PNG](../screens/png/06_item_history.png) · [SVG](../screens/svg/06_item_history.svg) · [线框PNG](../wireframes/png/06_item_history.png) · [线框SVG](../wireframes/svg/06_item_history.svg) · [繁中PNG](../localization/png/06_item_history-zh-Hant.png) · [English PNG](../localization/png/06_item_history-en.png)

## 06_item_record · 关卡条目·新纪录

- 出现条件：同一条目的新纪录条件示意，非玩家当前进度；证据：已有证据。
- 用户目标：判断同一关卡当前能否挑战。
- 主要信息：关卡身份、状态符号、历史成绩、对应入口。
- 首要动作：查看战前简报。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：新纪录在实际保存成功后显示。
- 版式收益：状态文字与图形组合，锁定不伪装成可挑战按钮。
- 文件：[简中PNG](../screens/png/06_item_record.png) · [SVG](../screens/svg/06_item_record.svg) · [线框PNG](../wireframes/png/06_item_record.png) · [线框SVG](../wireframes/svg/06_item_record.svg) · [繁中PNG](../localization/png/06_item_record-zh-Hant.png) · [English PNG](../localization/png/06_item_record-en.png)

## 07_detail_challenge · 战前简报·挑战

- 出现条件：所选关卡状态为challenge；证据：已有文档 / 实装未核验。
- 用户目标：在开局前作出布防判断。
- 主要信息：地图、配置波数、初始资源、敌人资料、五星条件、历史最佳。
- 首要动作：开始挑战。
- 次要动作：返回；玩法说明。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：所选关卡状态为challenge；数据需以产品当前状态替换。
- 版式收益：地图与关键资源分区，不再用居中长说明堆叠信息。
- 文件：[简中PNG](../screens/png/07_detail_challenge.png) · [SVG](../screens/svg/07_detail_challenge.svg) · [线框PNG](../wireframes/png/07_detail_challenge.png) · [线框SVG](../wireframes/svg/07_detail_challenge.svg) · [繁中PNG](../localization/png/07_detail_challenge-zh-Hant.png) · [English PNG](../localization/png/07_detail_challenge-en.png)

## 07_detail_continue · 战前简报·继续

- 出现条件：所选关卡状态为continue；证据：已有文档 / 实装未核验。
- 用户目标：在开局前作出布防判断。
- 主要信息：地图、配置波数、初始资源、敌人资料、五星条件、历史最佳。
- 首要动作：继续已保存的波次。
- 次要动作：返回；重新开始本关。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：所选关卡状态为continue；数据需以产品当前状态替换。
- 版式收益：地图与关键资源分区，不再用居中长说明堆叠信息。
- 文件：[简中PNG](../screens/png/07_detail_continue.png) · [SVG](../screens/svg/07_detail_continue.svg) · [线框PNG](../wireframes/png/07_detail_continue.png) · [线框SVG](../wireframes/svg/07_detail_continue.svg) · [繁中PNG](../localization/png/07_detail_continue-zh-Hant.png) · [English PNG](../localization/png/07_detail_continue-en.png)

## 07_detail_restart · 战前简报·重新挑战

- 出现条件：所选关卡状态为restart；证据：已有文档 / 实装未核验。
- 用户目标：在开局前作出布防判断。
- 主要信息：地图、配置波数、初始资源、敌人资料、五星条件、历史最佳。
- 首要动作：开始挑战。
- 次要动作：返回；玩法说明。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：所选关卡状态为restart；数据需以产品当前状态替换。
- 版式收益：地图与关键资源分区，不再用居中长说明堆叠信息。
- 文件：[简中PNG](../screens/png/07_detail_restart.png) · [SVG](../screens/svg/07_detail_restart.svg) · [线框PNG](../wireframes/png/07_detail_restart.png) · [线框SVG](../wireframes/svg/07_detail_restart.svg) · [繁中PNG](../localization/png/07_detail_restart-zh-Hant.png) · [English PNG](../localization/png/07_detail_restart-en.png)

## 08_intro · 玩法说明

- 出现条件：查看建造与路径规则；证据：已有截图 / 运行未核验。
- 用户目标：学会建造与通路规则。
- 主要信息：点选放置、拖动快捷方式、通路连通、波次与胜利。
- 首要动作：开始备战。
- 次要动作：返回；返回战前简报。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：查看建造与路径规则；数据需以产品当前状态替换。
- 版式收益：图示步骤按输入顺序排列；长按不承担唯一关键操作。
- 文件：[简中PNG](../screens/png/08_intro.png) · [SVG](../screens/svg/08_intro.svg) · [线框PNG](../wireframes/png/08_intro.png) · [线框SVG](../wireframes/svg/08_intro.svg) · [繁中PNG](../localization/png/08_intro-zh-Hant.png) · [English PNG](../localization/png/08_intro-en.png)

## 09_hud_prepare · 战斗 HUD·备战

- 出现条件：设计分支：备战；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：开始波次。
- 次要动作：暂停；速度 ×1。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：先布塔后开始第一波；尚未开始不出现迎战状态。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 文件：[简中PNG](../screens/png/09_hud_prepare.png) · [SVG](../screens/svg/09_hud_prepare.svg) · [线框PNG](../wireframes/png/09_hud_prepare.png) · [线框SVG](../wireframes/svg/09_hud_prepare.svg) · [繁中PNG](../localization/png/09_hud_prepare-zh-Hant.png) · [English PNG](../localization/png/09_hud_prepare-en.png)

## 09_hud_combat · 战斗 HUD·战斗

- 出现条件：设计分支：战斗；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：暂停；速度 ×1。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：敌群存在时下一波为迎战中，不可跳过当前波。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 不可用项：迎战中；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/09_hud_combat.png) · [SVG](../screens/svg/09_hud_combat.svg) · [线框PNG](../wireframes/png/09_hud_combat.png) · [线框SVG](../wireframes/svg/09_hud_combat.svg) · [繁中PNG](../localization/png/09_hud_combat-zh-Hant.png) · [English PNG](../localization/png/09_hud_combat-en.png)

## 09_hud_between · 战斗 HUD·波间准备

- 出现条件：设计分支：波间准备；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：下一波。
- 次要动作：暂停；速度 ×1。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：本波结束可调整布防，再主动开始下一波。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 文件：[简中PNG](../screens/png/09_hud_between.png) · [SVG](../screens/svg/09_hud_between.svg) · [线框PNG](../wireframes/png/09_hud_between.png) · [线框SVG](../wireframes/svg/09_hud_between.svg) · [繁中PNG](../localization/png/09_hud_between-zh-Hant.png) · [English PNG](../localization/png/09_hud_between-en.png)

## 09_hud_build · 战斗 HUD·选择炮塔

- 出现条件：设计分支：选择炮塔；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：下一波。
- 次要动作：暂停；速度 ×1；取消建造。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：点塔型后点空地是主路径；拖动为文档支持、运行待核验的快捷方式。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 文件：[简中PNG](../screens/png/09_hud_build.png) · [SVG](../screens/svg/09_hud_build.svg) · [线框PNG](../wireframes/png/09_hud_build.png) · [线框SVG](../wireframes/svg/09_hud_build.svg) · [繁中PNG](../localization/png/09_hud_build-zh-Hant.png) · [English PNG](../localization/png/09_hud_build-en.png)

## 09_hud_drag · 战斗 HUD·拖动至合法位置

- 出现条件：设计分支：拖动至合法位置；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：下一波。
- 次要动作：暂停；速度 ×1；取消建造。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：合法落点显示塔影与范围；松开合法位置才提交建造。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 文件：[简中PNG](../screens/png/09_hud_drag.png) · [SVG](../screens/svg/09_hud_drag.svg) · [线框PNG](../wireframes/png/09_hud_drag.png) · [线框SVG](../wireframes/svg/09_hud_drag.svg) · [繁中PNG](../localization/png/09_hud_drag-zh-Hant.png) · [English PNG](../localization/png/09_hud_drag-en.png)

## 09_hud_invalidpath · 战斗 HUD·封死路线

- 出现条件：设计分支：封死路线；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：暂停；速度 ×1；取消建造。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：不能封死入口到基地通路，保留金币并换位置。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 不可用项：下一波；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/09_hud_invalidpath.png) · [SVG](../screens/svg/09_hud_invalidpath.svg) · [线框PNG](../wireframes/png/09_hud_invalidpath.png) · [线框SVG](../wireframes/svg/09_hud_invalidpath.svg) · [繁中PNG](../localization/png/09_hud_invalidpath-zh-Hant.png) · [English PNG](../localization/png/09_hud_invalidpath-en.png)

## 09_hud_occupied · 战斗 HUD·地块已占用

- 出现条件：设计分支：地块已占用；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：暂停；速度 ×1；取消建造。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：同一地块已有建筑，提示紧邻落点。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 不可用项：下一波；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/09_hud_occupied.png) · [SVG](../screens/svg/09_hud_occupied.svg) · [线框PNG](../wireframes/png/09_hud_occupied.png) · [线框SVG](../wireframes/svg/09_hud_occupied.svg) · [繁中PNG](../localization/png/09_hud_occupied-zh-Hant.png) · [English PNG](../localization/png/09_hud_occupied-en.png)

## 09_hud_entry · 战斗 HUD·入口或基地不可建造

- 出现条件：设计分支：入口或基地不可建造；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：暂停；速度 ×1；取消建造。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：入口或基地不可建造，图形与文字同时解释。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 不可用项：下一波；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/09_hud_entry.png) · [SVG](../screens/svg/09_hud_entry.svg) · [线框PNG](../wireframes/png/09_hud_entry.png) · [线框SVG](../wireframes/svg/09_hud_entry.svg) · [繁中PNG](../localization/png/09_hud_entry-zh-Hant.png) · [English PNG](../localization/png/09_hud_entry-en.png)

## 09_hud_poor · 战斗 HUD·建造金币不足

- 出现条件：设计分支：建造金币不足；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：暂停；速度 ×1；取消建造。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：所需与现有金币靠近价格比较；不提交扣款。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 不可用项：下一波；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/09_hud_poor.png) · [SVG](../screens/svg/09_hud_poor.svg) · [线框PNG](../wireframes/png/09_hud_poor.png) · [线框SVG](../wireframes/svg/09_hud_poor.svg) · [繁中PNG](../localization/png/09_hud_poor-zh-Hant.png) · [English PNG](../localization/png/09_hud_poor-en.png)

## 09_hud_built · 战斗 HUD·建造成功

- 出现条件：设计分支：建造成功；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：开始波次。
- 次要动作：暂停；速度 ×1；取消建造。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：成功后更新地图与经济；确定的结果才使用成功标志。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 文件：[简中PNG](../screens/png/09_hud_built.png) · [SVG](../screens/svg/09_hud_built.svg) · [线框PNG](../wireframes/png/09_hud_built.png) · [线框SVG](../wireframes/svg/09_hud_built.svg) · [繁中PNG](../localization/png/09_hud_built-zh-Hant.png) · [English PNG](../localization/png/09_hud_built-en.png)

## 09_hud_cancel · 战斗 HUD·取消建造

- 出现条件：设计分支：取消建造；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：开始波次。
- 次要动作：暂停；速度 ×1。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：取消后回原战场，不扣建造费用。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 文件：[简中PNG](../screens/png/09_hud_cancel.png) · [SVG](../screens/svg/09_hud_cancel.svg) · [线框PNG](../wireframes/png/09_hud_cancel.png) · [线框SVG](../wireframes/svg/09_hud_cancel.svg) · [繁中PNG](../localization/png/09_hud_cancel-zh-Hant.png) · [English PNG](../localization/png/09_hud_cancel-en.png)

## 09_hud_selected · 战斗 HUD·选中炮塔·显示范围

- 出现条件：设计分支：选中炮塔·显示范围；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：升级 · — 金币；下一波。
- 次要动作：暂停；出售…；隐藏范围；速度 ×1。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：选中框关联地图炮塔；可升级、出售或隐藏范围。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 文件：[简中PNG](../screens/png/09_hud_selected.png) · [SVG](../screens/svg/09_hud_selected.svg) · [线框PNG](../wireframes/png/09_hud_selected.png) · [线框SVG](../wireframes/svg/09_hud_selected.svg) · [繁中PNG](../localization/png/09_hud_selected-zh-Hant.png) · [English PNG](../localization/png/09_hud_selected-en.png)

## 09_hud_hide_range · 战斗 HUD·选中炮塔·隐藏范围

- 出现条件：设计分支：选中炮塔·隐藏范围；数值由真实对局提供；证据：已有证据。
- 用户目标：观察战场并执行当前合法动作。
- 主要信息：金币、生命、波次、地图、塔栏、价格、暂停与当前动作。
- 首要动作：升级 · — 金币；下一波。
- 次要动作：暂停；出售…；显示范围；速度 ×1。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：只隐藏范围圆；保留所选塔高亮和面板。
- 版式收益：资源条和操作条固定；合法性反馈靠近落点，不盖住入口基地。
- 文件：[简中PNG](../screens/png/09_hud_hide_range.png) · [SVG](../screens/svg/09_hud_hide_range.svg) · [线框PNG](../wireframes/png/09_hud_hide_range.png) · [线框SVG](../wireframes/svg/09_hud_hide_range.svg) · [繁中PNG](../localization/png/09_hud_hide_range-zh-Hant.png) · [English PNG](../localization/png/09_hud_hide_range-en.png)

## 10_tower_normal_l1 · 塔操作·速射塔·1级

- 出现条件：所选normal为1级；满足升级条件；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：升级 · 花费 — 金币。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：速射塔，等级1。当前和升级后逐行比较，显示真实价格后提交。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 文件：[简中PNG](../screens/png/10_tower_normal_l1.png) · [SVG](../screens/svg/10_tower_normal_l1.svg) · [线框PNG](../wireframes/png/10_tower_normal_l1.png) · [线框SVG](../wireframes/svg/10_tower_normal_l1.svg) · [繁中PNG](../localization/png/10_tower_normal_l1-zh-Hant.png) · [English PNG](../localization/png/10_tower_normal_l1-en.png)

## 10_tower_normal_l2 · 塔操作·速射塔·2级

- 出现条件：所选normal为2级；满足升级条件；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：升级 · 花费 — 金币。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：速射塔，等级2。当前和升级后逐行比较，显示真实价格后提交。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 文件：[简中PNG](../screens/png/10_tower_normal_l2.png) · [SVG](../screens/svg/10_tower_normal_l2.svg) · [线框PNG](../wireframes/png/10_tower_normal_l2.png) · [线框SVG](../wireframes/svg/10_tower_normal_l2.svg) · [繁中PNG](../localization/png/10_tower_normal_l2-zh-Hant.png) · [English PNG](../localization/png/10_tower_normal_l2-en.png)

## 10_tower_normal_l3 · 塔操作·速射塔·3级

- 出现条件：所选normal为3级；已满级；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：速射塔，等级3。达到当前数据定义的最高等级；显示完成状态，不伪装成按钮。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 不可用项：已达到最高等级；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/10_tower_normal_l3.png) · [SVG](../screens/svg/10_tower_normal_l3.svg) · [线框PNG](../wireframes/png/10_tower_normal_l3.png) · [线框SVG](../wireframes/svg/10_tower_normal_l3.svg) · [繁中PNG](../localization/png/10_tower_normal_l3-zh-Hant.png) · [English PNG](../localization/png/10_tower_normal_l3-en.png)

## 10_tower_power_l1 · 塔操作·火力塔·1级

- 出现条件：所选power为1级；满足升级条件；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：升级 · 花费 — 金币。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：火力塔，等级1。当前和升级后逐行比较，显示真实价格后提交。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 文件：[简中PNG](../screens/png/10_tower_power_l1.png) · [SVG](../screens/svg/10_tower_power_l1.svg) · [线框PNG](../wireframes/png/10_tower_power_l1.png) · [线框SVG](../wireframes/svg/10_tower_power_l1.svg) · [繁中PNG](../localization/png/10_tower_power_l1-zh-Hant.png) · [English PNG](../localization/png/10_tower_power_l1-en.png)

## 10_tower_power_l2 · 塔操作·火力塔·2级

- 出现条件：所选power为2级；满足升级条件；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：升级 · 花费 — 金币。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：火力塔，等级2。当前和升级后逐行比较，显示真实价格后提交。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 文件：[简中PNG](../screens/png/10_tower_power_l2.png) · [SVG](../screens/svg/10_tower_power_l2.svg) · [线框PNG](../wireframes/png/10_tower_power_l2.png) · [线框SVG](../wireframes/svg/10_tower_power_l2.svg) · [繁中PNG](../localization/png/10_tower_power_l2-zh-Hant.png) · [English PNG](../localization/png/10_tower_power_l2-en.png)

## 10_tower_power_l3 · 塔操作·火力塔·3级

- 出现条件：所选power为3级；已满级；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：火力塔，等级3。达到当前数据定义的最高等级；显示完成状态，不伪装成按钮。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 不可用项：已达到最高等级；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/10_tower_power_l3.png) · [SVG](../screens/svg/10_tower_power_l3.svg) · [线框PNG](../wireframes/png/10_tower_power_l3.png) · [线框SVG](../wireframes/svg/10_tower_power_l3.svg) · [繁中PNG](../localization/png/10_tower_power_l3-zh-Hant.png) · [English PNG](../localization/png/10_tower_power_l3-en.png)

## 10_tower_retard_l1 · 塔操作·减速塔·1级

- 出现条件：所选retard为1级；满足升级条件；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：升级 · 花费 — 金币。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：减速塔，等级1。当前和升级后逐行比较，显示真实价格后提交。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 文件：[简中PNG](../screens/png/10_tower_retard_l1.png) · [SVG](../screens/svg/10_tower_retard_l1.svg) · [线框PNG](../wireframes/png/10_tower_retard_l1.png) · [线框SVG](../wireframes/svg/10_tower_retard_l1.svg) · [繁中PNG](../localization/png/10_tower_retard_l1-zh-Hant.png) · [English PNG](../localization/png/10_tower_retard_l1-en.png)

## 10_tower_retard_l2 · 塔操作·减速塔·2级

- 出现条件：所选retard为2级；满足升级条件；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：升级 · 花费 — 金币。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：减速塔，等级2。当前和升级后逐行比较，显示真实价格后提交。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 文件：[简中PNG](../screens/png/10_tower_retard_l2.png) · [SVG](../screens/svg/10_tower_retard_l2.svg) · [线框PNG](../wireframes/png/10_tower_retard_l2.png) · [线框SVG](../wireframes/svg/10_tower_retard_l2.svg) · [繁中PNG](../localization/png/10_tower_retard_l2-zh-Hant.png) · [English PNG](../localization/png/10_tower_retard_l2-en.png)

## 10_tower_retard_l3 · 塔操作·减速塔·3级

- 出现条件：所选retard为3级；已满级；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：减速塔，等级3。达到当前数据定义的最高等级；显示完成状态，不伪装成按钮。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 不可用项：已达到最高等级；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/10_tower_retard_l3.png) · [SVG](../screens/svg/10_tower_retard_l3.svg) · [线框PNG](../wireframes/png/10_tower_retard_l3.png) · [线框SVG](../wireframes/svg/10_tower_retard_l3.svg) · [繁中PNG](../localization/png/10_tower_retard_l3-zh-Hant.png) · [English PNG](../localization/png/10_tower_retard_l3-en.png)

## 10_tower_normal_poor · 塔操作·速射塔·资金不足

- 出现条件：所选塔未满级，但金币不足以支付真实价格；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：速射塔，等级2。升级不可用，显示原因及缺少金币；仍可关闭或出售。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 不可用项：金币不足 · 还需 —；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/10_tower_normal_poor.png) · [SVG](../screens/svg/10_tower_normal_poor.svg) · [线框PNG](../wireframes/png/10_tower_normal_poor.png) · [线框SVG](../wireframes/svg/10_tower_normal_poor.svg) · [繁中PNG](../localization/png/10_tower_normal_poor-zh-Hant.png) · [English PNG](../localization/png/10_tower_normal_poor-en.png)

## 10_tower_power_poor · 塔操作·火力塔·资金不足

- 出现条件：所选塔未满级，但金币不足以支付真实价格；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：火力塔，等级2。升级不可用，显示原因及缺少金币；仍可关闭或出售。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 不可用项：金币不足 · 还需 —；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/10_tower_power_poor.png) · [SVG](../screens/svg/10_tower_power_poor.svg) · [线框PNG](../wireframes/png/10_tower_power_poor.png) · [线框SVG](../wireframes/svg/10_tower_power_poor.svg) · [繁中PNG](../localization/png/10_tower_power_poor-zh-Hant.png) · [English PNG](../localization/png/10_tower_power_poor-en.png)

## 10_tower_retard_poor · 塔操作·减速塔·资金不足

- 出现条件：所选塔未满级，但金币不足以支付真实价格；证据：已有证据。
- 用户目标：判断当前炮塔升级或出售是否值得。
- 主要信息：塔型等级、当前与升级后属性、价格、范围、出售入口。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回；出售此炮塔…；关闭，返回战场。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：减速塔，等级2。升级不可用，显示原因及缺少金币；仍可关闭或出售。
- 版式收益：地图与属性表并列，同列比较减少来回记忆。
- 不可用项：金币不足 · 还需 —；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/10_tower_retard_poor.png) · [SVG](../screens/svg/10_tower_retard_poor.svg) · [线框PNG](../wireframes/png/10_tower_retard_poor.png) · [线框SVG](../wireframes/svg/10_tower_retard_poor.svg) · [繁中PNG](../localization/png/10_tower_retard_poor-zh-Hant.png) · [English PNG](../localization/png/10_tower_retard_poor-en.png)

## 11_pause · 暂停菜单

- 出现条件：玩家已暂停；对局保留在背景；证据：已有证据。
- 用户目标：恢复战斗或有意识地改变当前局。
- 主要信息：暂停说明、继续、重开、设置、返回。
- 首要动作：继续游戏。
- 次要动作：重新开始本关…；设置；返回关卡选择…。
- 返回/关闭：继续回原战场；设置关闭仍回暂停。
- 状态变化与误操作：玩家已暂停；对局保留在背景；数据需以产品当前状态替换。
- 版式收益：继续为唯一首要动作；会丢失内容的操作进入确认。
- 文件：[简中PNG](../screens/png/11_pause.png) · [SVG](../screens/svg/11_pause.svg) · [线框PNG](../wireframes/png/11_pause.png) · [线框SVG](../wireframes/svg/11_pause.svg) · [繁中PNG](../localization/png/11_pause-zh-Hant.png) · [English PNG](../localization/png/11_pause-en.png)

## 12_tip_success · 情境提示·操作成功

- 出现条件：对应操作返回操作成功，提示附着原因位置；证据：已有证据。
- 用户目标：立即理解一次操作结果。
- 主要信息：结果图形、短原因、可执行下一步。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：暂停；速度 ×1。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：对应操作返回操作成功，提示附着原因位置；数据需以产品当前状态替换。
- 版式收益：局部短提示不替代长期错误，不长期遮挡战场。
- 不可用项：迎战中；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/12_tip_success.png) · [SVG](../screens/svg/12_tip_success.svg) · [线框PNG](../wireframes/png/12_tip_success.png) · [线框SVG](../wireframes/svg/12_tip_success.svg) · [繁中PNG](../localization/png/12_tip_success-zh-Hant.png) · [English PNG](../localization/png/12_tip_success-en.png)

## 12_tip_warning · 情境提示·路径警告

- 出现条件：对应操作返回路径警告，提示附着原因位置；证据：已有证据。
- 用户目标：立即理解一次操作结果。
- 主要信息：结果图形、短原因、可执行下一步。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：暂停；速度 ×1。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：对应操作返回路径警告，提示附着原因位置；数据需以产品当前状态替换。
- 版式收益：局部短提示不替代长期错误，不长期遮挡战场。
- 不可用项：迎战中；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/12_tip_warning.png) · [SVG](../screens/svg/12_tip_warning.svg) · [线框PNG](../wireframes/png/12_tip_warning.png) · [线框SVG](../wireframes/svg/12_tip_warning.svg) · [繁中PNG](../localization/png/12_tip_warning-zh-Hant.png) · [English PNG](../localization/png/12_tip_warning-en.png)

## 12_tip_failure · 情境提示·操作失败

- 出现条件：对应操作返回操作失败，提示附着原因位置；证据：已有证据。
- 用户目标：立即理解一次操作结果。
- 主要信息：结果图形、短原因、可执行下一步。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：暂停；速度 ×1。
- 返回/关闭：关闭所选塔/取消建造回原战场；系统返回先处理当前层，再进入暂停。
- 状态变化与误操作：对应操作返回操作失败，提示附着原因位置；数据需以产品当前状态替换。
- 版式收益：局部短提示不替代长期错误，不长期遮挡战场。
- 不可用项：迎战中；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/12_tip_failure.png) · [SVG](../screens/svg/12_tip_failure.svg) · [线框PNG](../wireframes/png/12_tip_failure.png) · [线框SVG](../wireframes/svg/12_tip_failure.svg) · [繁中PNG](../localization/png/12_tip_failure-zh-Hant.png) · [English PNG](../localization/png/12_tip_failure-en.png)

## 13_codex_normal · 塔图鉴·速射塔

- 出现条件：查看对应塔型定位和等级外观；证据：规划界面 / 已有美术参考。
- 用户目标：理解所选炮塔定位。
- 主要信息：既有塔形象、用途、攻击特点、关键属性与切换入口。
- 首要动作：速射塔；比较三种炮塔。
- 次要动作：返回；火力塔；减速塔。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：查看对应塔型定位和等级外观；数据需以产品当前状态替换。
- 版式收益：当前塔突出，三种塔的切换位置固定。
- 文件：[简中PNG](../screens/png/13_codex_normal.png) · [SVG](../screens/svg/13_codex_normal.svg) · [线框PNG](../wireframes/png/13_codex_normal.png) · [线框SVG](../wireframes/svg/13_codex_normal.svg) · [繁中PNG](../localization/png/13_codex_normal-zh-Hant.png) · [English PNG](../localization/png/13_codex_normal-en.png)

## 13_codex_power · 塔图鉴·火力塔

- 出现条件：查看对应塔型定位和等级外观；证据：规划界面 / 已有美术参考。
- 用户目标：理解所选炮塔定位。
- 主要信息：既有塔形象、用途、攻击特点、关键属性与切换入口。
- 首要动作：火力塔；比较三种炮塔。
- 次要动作：返回；速射塔；减速塔。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：查看对应塔型定位和等级外观；数据需以产品当前状态替换。
- 版式收益：当前塔突出，三种塔的切换位置固定。
- 文件：[简中PNG](../screens/png/13_codex_power.png) · [SVG](../screens/svg/13_codex_power.svg) · [线框PNG](../wireframes/png/13_codex_power.png) · [线框SVG](../wireframes/svg/13_codex_power.svg) · [繁中PNG](../localization/png/13_codex_power-zh-Hant.png) · [English PNG](../localization/png/13_codex_power-en.png)

## 13_codex_retard · 塔图鉴·减速塔

- 出现条件：查看对应塔型定位和等级外观；证据：规划界面 / 已有美术参考。
- 用户目标：理解所选炮塔定位。
- 主要信息：既有塔形象、用途、攻击特点、关键属性与切换入口。
- 首要动作：减速塔；比较三种炮塔。
- 次要动作：返回；速射塔；火力塔。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：查看对应塔型定位和等级外观；数据需以产品当前状态替换。
- 版式收益：当前塔突出，三种塔的切换位置固定。
- 文件：[简中PNG](../screens/png/13_codex_retard.png) · [SVG](../screens/svg/13_codex_retard.svg) · [线框PNG](../wireframes/png/13_codex_retard.png) · [线框SVG](../wireframes/svg/13_codex_retard.svg) · [繁中PNG](../localization/png/13_codex_retard-zh-Hant.png) · [English PNG](../localization/png/13_codex_retard-en.png)

## 13_codex_compare · 三塔对比

- 出现条件：比较已知定位；未知数值不参与排序；证据：规划界面。
- 用户目标：比较三塔用途与局限。
- 主要信息：单体、范围、控制的相对定位与属性列。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回；返回炮塔图鉴。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：比较已知定位；未知数值不参与排序；数据需以产品当前状态替换。
- 版式收益：同一行比较同一维度；数值缺失不编造高低。
- 文件：[简中PNG](../screens/png/13_codex_compare.png) · [SVG](../screens/svg/13_codex_compare.svg) · [线框PNG](../wireframes/png/13_codex_compare.png) · [线框SVG](../wireframes/svg/13_codex_compare.svg) · [繁中PNG](../localization/png/13_codex_compare-zh-Hant.png) · [English PNG](../localization/png/13_codex_compare-en.png)

## 14_monster_grid · 怪物浏览

- 出现条件：仅使用项目已有怪物形象，不推断抗性与弱点；证据：规划界面。
- 用户目标：查看项目已有敌人形象与可用资料。
- 主要信息：形象类别、类型、移动与威胁字段、资料缺失反馈。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回；查看详情。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：仅使用项目已有怪物形象，不推断抗性与弱点；数据需以产品当前状态替换。
- 版式收益：先认形象再读资料；不从外形推断抗性、故事或正式名字。
- 文件：[简中PNG](../screens/png/14_monster_grid.png) · [SVG](../screens/svg/14_monster_grid.svg) · [线框PNG](../wireframes/png/14_monster_grid.png) · [线框SVG](../wireframes/svg/14_monster_grid.svg) · [繁中PNG](../localization/png/14_monster_grid-zh-Hant.png) · [English PNG](../localization/png/14_monster_grid-en.png)

## 14_monster_detail · 怪物详情

- 出现条件：仅使用项目已有怪物形象，不推断抗性与弱点；证据：规划界面。
- 用户目标：查看项目已有敌人形象与可用资料。
- 主要信息：形象类别、类型、移动与威胁字段、资料缺失反馈。
- 首要动作：返回怪物浏览。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：类别来自现有形象；资料为空，不推断额外属性。
- 版式收益：先认形象再读资料；不从外形推断抗性、故事或正式名字。
- 文件：[简中PNG](../screens/png/14_monster_detail.png) · [SVG](../screens/svg/14_monster_detail.svg) · [线框PNG](../wireframes/png/14_monster_detail.png) · [线框SVG](../wireframes/svg/14_monster_detail.svg) · [繁中PNG](../localization/png/14_monster_detail-zh-Hant.png) · [English PNG](../localization/png/14_monster_detail-en.png)

## 14_monster_empty · 暂无资料

- 出现条件：仅使用项目已有怪物形象，不推断抗性与弱点；证据：规划界面。
- 用户目标：查看项目已有敌人形象与可用资料。
- 主要信息：形象类别、类型、移动与威胁字段、资料缺失反馈。
- 首要动作：返回。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：没有资料时解释原因，返回仍可用。
- 版式收益：先认形象再读资料；不从外形推断抗性、故事或正式名字。
- 文件：[简中PNG](../screens/png/14_monster_empty.png) · [SVG](../screens/svg/14_monster_empty.svg) · [线框PNG](../wireframes/png/14_monster_empty.png) · [线框SVG](../wireframes/svg/14_monster_empty.svg) · [繁中PNG](../localization/png/14_monster_empty-zh-Hant.png) · [English PNG](../localization/png/14_monster_empty-en.png)

## 15_sell · 出售确认

- 出现条件：所选塔允许出售；返还金额尚未提供；证据：已有文档 / 实装未核验。
- 用户目标：理解具体后果后作出安全决定。
- 主要信息：动作对象、不可逆后果、安全取消、明确动词按钮。
- 首要动作：出售此炮塔。
- 次要动作：保留炮塔。
- 返回/关闭：安全按钮或系统返回回来源；已提交不可中止时等待，取消不能伪装撤销。
- 状态变化与误操作：对象须与所选塔一致；返还未知时不能实际提交。
- 版式收益：窄幅模态保留来源背景，危险与安全项分开。
- 文件：[简中PNG](../screens/png/15_sell.png) · [SVG](../screens/svg/15_sell.svg) · [线框PNG](../wireframes/png/15_sell.png) · [线框SVG](../wireframes/svg/15_sell.svg) · [繁中PNG](../localization/png/15_sell-zh-Hant.png) · [English PNG](../localization/png/15_sell-en.png)

## 15_sell_pending · 出售处理中

- 出现条件：玩家确认出售，等待操作结果；证据：已有文档 / 实装未核验。
- 用户目标：理解具体后果后作出安全决定。
- 主要信息：动作对象、不可逆后果、安全取消、明确动词按钮。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：无额外次要提交。
- 返回/关闭：安全按钮或系统返回回来源；已提交不可中止时等待，取消不能伪装撤销。
- 状态变化与误操作：等待出售结果后更新金币与塔；不允许重复出售。
- 版式收益：窄幅模态保留来源背景，危险与安全项分开。
- 不可用项：请稍候；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/15_sell_pending.png) · [SVG](../screens/svg/15_sell_pending.svg) · [线框PNG](../wireframes/png/15_sell_pending.png) · [线框SVG](../wireframes/svg/15_sell_pending.svg) · [繁中PNG](../localization/png/15_sell_pending-zh-Hant.png) · [English PNG](../localization/png/15_sell_pending-en.png)

## 16_confirm_reset · 重置存档

- 出现条件：确认重置存档及后果；证据：已有文档 / 实装未核验。
- 用户目标：理解具体后果后作出安全决定。
- 主要信息：动作对象、不可逆后果、安全取消、明确动词按钮。
- 首要动作：删除全部存档。
- 次要动作：保留存档。
- 返回/关闭：安全按钮或系统返回回来源；已提交不可中止时等待，取消不能伪装撤销。
- 状态变化与误操作：明确清除本地进度、历史评级、局内存档；安全取消优先。
- 版式收益：窄幅模态保留来源背景，危险与安全项分开。
- 文件：[简中PNG](../screens/png/16_confirm_reset.png) · [SVG](../screens/svg/16_confirm_reset.svg) · [线框PNG](../wireframes/png/16_confirm_reset.png) · [线框SVG](../wireframes/svg/16_confirm_reset.svg) · [繁中PNG](../localization/png/16_confirm_reset-zh-Hant.png) · [English PNG](../localization/png/16_confirm_reset-en.png)

## 16_confirm_resetpending · 正在重置

- 出现条件：确认正在重置及后果；证据：已有文档 / 实装未核验。
- 用户目标：理解具体后果后作出安全决定。
- 主要信息：动作对象、不可逆后果、安全取消、明确动词按钮。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：无额外次要提交。
- 返回/关闭：安全按钮或系统返回回来源；已提交不可中止时等待，取消不能伪装撤销。
- 状态变化与误操作：提交后等待结果，避免二次重置；失败恢复重试。
- 版式收益：窄幅模态保留来源背景，危险与安全项分开。
- 不可用项：请稍候；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/16_confirm_resetpending.png) · [SVG](../screens/svg/16_confirm_resetpending.svg) · [线框PNG](../wireframes/png/16_confirm_resetpending.png) · [线框SVG](../wireframes/svg/16_confirm_resetpending.svg) · [繁中PNG](../localization/png/16_confirm_resetpending-zh-Hant.png) · [English PNG](../localization/png/16_confirm_resetpending-en.png)

## 16_confirm_resetfailed · 重置失败

- 出现条件：确认重置失败及后果；证据：已有文档 / 实装未核验。
- 用户目标：理解具体后果后作出安全决定。
- 主要信息：动作对象、不可逆后果、安全取消、明确动词按钮。
- 首要动作：重试重置。
- 次要动作：返回设置。
- 返回/关闭：安全按钮或系统返回回来源；已提交不可中止时等待，取消不能伪装撤销。
- 状态变化与误操作：没有清除现有进度，返回设置或重试。
- 版式收益：窄幅模态保留来源背景，危险与安全项分开。
- 文件：[简中PNG](../screens/png/16_confirm_resetfailed.png) · [SVG](../screens/svg/16_confirm_resetfailed.svg) · [线框PNG](../wireframes/png/16_confirm_resetfailed.png) · [线框SVG](../wireframes/svg/16_confirm_resetfailed.svg) · [繁中PNG](../localization/png/16_confirm_resetfailed-zh-Hant.png) · [English PNG](../localization/png/16_confirm_resetfailed-en.png)

## 16_confirm_leave · 返回选关

- 出现条件：确认返回选关及后果；证据：已有文档 / 实装未核验。
- 用户目标：理解具体后果后作出安全决定。
- 主要信息：动作对象、不可逆后果、安全取消、明确动词按钮。
- 首要动作：返回关卡选择。
- 次要动作：继续战斗。
- 返回/关闭：安全按钮或系统返回回来源；已提交不可中止时等待，取消不能伪装撤销。
- 状态变化与误操作：未完成波次回已保存检查点；保存或清除失败中止离开。
- 版式收益：窄幅模态保留来源背景，危险与安全项分开。
- 文件：[简中PNG](../screens/png/16_confirm_leave.png) · [SVG](../screens/svg/16_confirm_leave.svg) · [线框PNG](../wireframes/png/16_confirm_leave.png) · [线框SVG](../wireframes/svg/16_confirm_leave.svg) · [繁中PNG](../localization/png/16_confirm_leave-zh-Hant.png) · [English PNG](../localization/png/16_confirm_leave-en.png)

## 16_confirm_restart · 重新开始本关

- 出现条件：确认重新开始本关及后果；证据：已有文档 / 实装未核验。
- 用户目标：理解具体后果后作出安全决定。
- 主要信息：动作对象、不可逆后果、安全取消、明确动词按钮。
- 首要动作：重新开始本关。
- 次要动作：继续战斗。
- 返回/关闭：安全按钮或系统返回回来源；已提交不可中止时等待，取消不能伪装撤销。
- 状态变化与误操作：清除当前布防和未保存结果后重开；清除失败留在原局。
- 版式收益：窄幅模态保留来源背景，危险与安全项分开。
- 文件：[简中PNG](../screens/png/16_confirm_restart.png) · [SVG](../screens/svg/16_confirm_restart.svg) · [线框PNG](../wireframes/png/16_confirm_restart.png) · [线框SVG](../wireframes/svg/16_confirm_restart.svg) · [繁中PNG](../localization/png/16_confirm_restart-zh-Hant.png) · [English PNG](../localization/png/16_confirm_restart-en.png)

## 16_confirm_quit · 退出游戏

- 出现条件：确认退出游戏及后果；证据：已有文档 / 实装未核验。
- 用户目标：理解具体后果后作出安全决定。
- 主要信息：动作对象、不可逆后果、安全取消、明确动词按钮。
- 首要动作：退出游戏。
- 次要动作：返回游戏。
- 返回/关闭：安全按钮或系统返回回来源；已提交不可中止时等待，取消不能伪装撤销。
- 状态变化与误操作：退出前说明检查点回退；返回游戏保留原来源。
- 版式收益：窄幅模态保留来源背景，危险与安全项分开。
- 文件：[简中PNG](../screens/png/16_confirm_quit.png) · [SVG](../screens/svg/16_confirm_quit.svg) · [线框PNG](../wireframes/png/16_confirm_quit.png) · [线框SVG](../wireframes/svg/16_confirm_quit.svg) · [繁中PNG](../localization/png/16_confirm_quit-zh-Hant.png) · [English PNG](../localization/png/16_confirm_quit-en.png)

## 16_confirm_unsaved · 成绩未保存时离开

- 出现条件：确认成绩未保存时离开及后果；证据：已有文档 / 实装未核验。
- 用户目标：理解具体后果后作出安全决定。
- 主要信息：动作对象、不可逆后果、安全取消、明确动词按钮。
- 首要动作：重试保存。
- 次要动作：留在结算页。
- 返回/关闭：安全按钮或系统返回回来源；已提交不可中止时等待，取消不能伪装撤销。
- 状态变化与误操作：保留结果：留在结算页或重试保存；无未经证实的丢弃成绩入口。
- 版式收益：窄幅模态保留来源背景，危险与安全项分开。
- 文件：[简中PNG](../screens/png/16_confirm_unsaved.png) · [SVG](../screens/svg/16_confirm_unsaved.svg) · [线框PNG](../wireframes/png/16_confirm_unsaved.png) · [线框SVG](../wireframes/svg/16_confirm_unsaved.svg) · [繁中PNG](../localization/png/16_confirm_unsaved-zh-Hant.png) · [English PNG](../localization/png/16_confirm_unsaved-en.png)

## 17_settings_zh-Hans · 设置·zh-Hans

- 出现条件：展示语言当前选择；无声音选项；证据：已有截图。
- 用户目标：选择可读语言并管理本地存档。
- 主要信息：三种语言、当前选择勾、重置入口、关闭。
- 首要动作：重置存档…。
- 次要动作：返回；关闭。
- 返回/关闭：返回/关闭回打开设置的来源；重置取消回设置。
- 状态变化与误操作：当前选择为zh-Hans；勾与标签一致，关闭回原来源。
- 版式收益：普通语言项与危险重置分区；无声音项。
- 文件：[简中PNG](../screens/png/17_settings_zh-Hans.png) · [SVG](../screens/svg/17_settings_zh-Hans.svg) · [线框PNG](../wireframes/png/17_settings_zh-Hans.png) · [线框SVG](../wireframes/svg/17_settings_zh-Hans.svg) · [繁中PNG](../localization/png/17_settings_zh-Hans-zh-Hant.png) · [English PNG](../localization/png/17_settings_zh-Hans-en.png)

## 17_settings_zh-Hant · 设置·zh-Hant

- 出现条件：展示语言当前选择；无声音选项；证据：已有截图。
- 用户目标：选择可读语言并管理本地存档。
- 主要信息：三种语言、当前选择勾、重置入口、关闭。
- 首要动作：重置存档…。
- 次要动作：返回；关闭。
- 返回/关闭：返回/关闭回打开设置的来源；重置取消回设置。
- 状态变化与误操作：当前选择为zh-Hant；勾与标签一致，关闭回原来源。
- 版式收益：普通语言项与危险重置分区；无声音项。
- 文件：[简中PNG](../screens/png/17_settings_zh-Hant.png) · [SVG](../screens/svg/17_settings_zh-Hant.svg) · [线框PNG](../wireframes/png/17_settings_zh-Hant.png) · [线框SVG](../wireframes/svg/17_settings_zh-Hant.svg) · [繁中PNG](../localization/png/17_settings_zh-Hant-zh-Hant.png) · [English PNG](../localization/png/17_settings_zh-Hant-en.png)

## 17_settings_en · 设置·en

- 出现条件：展示语言当前选择；无声音选项；证据：已有截图。
- 用户目标：选择可读语言并管理本地存档。
- 主要信息：三种语言、当前选择勾、重置入口、关闭。
- 首要动作：重置存档…。
- 次要动作：返回；关闭。
- 返回/关闭：返回/关闭回打开设置的来源；重置取消回设置。
- 状态变化与误操作：当前选择为en；勾与标签一致，关闭回原来源。
- 版式收益：普通语言项与危险重置分区；无声音项。
- 文件：[简中PNG](../screens/png/17_settings_en.png) · [SVG](../screens/svg/17_settings_en.svg) · [线框PNG](../wireframes/png/17_settings_en.png) · [线框SVG](../wireframes/svg/17_settings_en.svg) · [繁中PNG](../localization/png/17_settings_en-zh-Hant.png) · [English PNG](../localization/png/17_settings_en-en.png)

## 18_result_win · 胜利结算

- 出现条件：设计条件分支：胜利结算；不代表真实成绩；证据：已有证据。
- 用户目标：理解本局结果并选择有效去向。
- 主要信息：胜败、五槽评级、本次/最佳、生命漏怪击杀用时、保存事实。
- 首要动作：进入下一关。
- 次要动作：返回；重玩本关；返回选关。
- 返回/关闭：返回选关；重玩经必要确认；下一关仅保存成功且非末关可用。
- 状态变化与误操作：保存成功后下一关才可用；本稿数值为空，不代表真实获胜记录。
- 版式收益：一次荣誉表达后接四项统计和关键原因，下一步单独成行。
- 文件：[简中PNG](../screens/png/18_result_win.png) · [SVG](../screens/svg/18_result_win.svg) · [线框PNG](../wireframes/png/18_result_win.png) · [线框SVG](../wireframes/svg/18_result_win.svg) · [繁中PNG](../localization/png/18_result_win-zh-Hant.png) · [English PNG](../localization/png/18_result_win-en.png)

## 18_result_record · 胜利·新纪录

- 出现条件：设计条件分支：胜利·新纪录；不代表真实成绩；证据：已有证据。
- 用户目标：理解本局结果并选择有效去向。
- 主要信息：胜败、五槽评级、本次/最佳、生命漏怪击杀用时、保存事实。
- 首要动作：进入下一关。
- 次要动作：返回；重玩本关；返回选关。
- 返回/关闭：返回选关；重玩经必要确认；下一关仅保存成功且非末关可用。
- 状态变化与误操作：只有纪录已实际保存且优于历史时才出现新纪录徽标。
- 版式收益：一次荣誉表达后接四项统计和关键原因，下一步单独成行。
- 文件：[简中PNG](../screens/png/18_result_record.png) · [SVG](../screens/svg/18_result_record.svg) · [线框PNG](../wireframes/png/18_result_record.png) · [线框SVG](../wireframes/svg/18_result_record.svg) · [繁中PNG](../localization/png/18_result_record-zh-Hant.png) · [English PNG](../localization/png/18_result_record-en.png)

## 18_result_low · 胜利·低星原因

- 出现条件：设计条件分支：胜利·低星原因；不代表真实成绩；证据：已有证据。
- 用户目标：理解本局结果并选择有效去向。
- 主要信息：胜败、五槽评级、本次/最佳、生命漏怪击杀用时、保存事实。
- 首要动作：进入下一关。
- 次要动作：返回；重玩本关；返回选关。
- 返回/关闭：返回选关；重玩经必要确认；下一关仅保存成功且非末关可用。
- 状态变化与误操作：只提示未达五星与重玩方向；具体扣星条件需真实结果补入。
- 版式收益：一次荣誉表达后接四项统计和关键原因，下一步单独成行。
- 文件：[简中PNG](../screens/png/18_result_low.png) · [SVG](../screens/svg/18_result_low.svg) · [线框PNG](../wireframes/png/18_result_low.png) · [线框SVG](../wireframes/svg/18_result_low.svg) · [繁中PNG](../localization/png/18_result_low-zh-Hant.png) · [English PNG](../localization/png/18_result_low-en.png)

## 18_result_lose · 失败结算

- 出现条件：设计条件分支：失败结算；不代表真实成绩；证据：已有证据。
- 用户目标：理解本局结果并选择有效去向。
- 主要信息：胜败、五槽评级、本次/最佳、生命漏怪击杀用时、保存事实。
- 首要动作：重试本关。
- 次要动作：返回；返回关卡选择。
- 返回/关闭：返回选关；重玩经必要确认；下一关仅保存成功且非末关可用。
- 状态变化与误操作：用防线失守标题与危险形状表达失败；首要动作重试。
- 版式收益：一次荣誉表达后接四项统计和关键原因，下一步单独成行。
- 文件：[简中PNG](../screens/png/18_result_lose.png) · [SVG](../screens/svg/18_result_lose.svg) · [线框PNG](../wireframes/png/18_result_lose.png) · [线框SVG](../wireframes/svg/18_result_lose.svg) · [繁中PNG](../localization/png/18_result_lose-zh-Hant.png) · [English PNG](../localization/png/18_result_lose-en.png)

## 18_result_saving · 成绩保存中

- 出现条件：设计条件分支：成绩保存中；不代表真实成绩；证据：已有证据。
- 用户目标：理解本局结果并选择有效去向。
- 主要信息：胜败、五槽评级、本次/最佳、生命漏怪击杀用时、保存事实。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：无额外次要提交。
- 返回/关闭：保存处理中无直接离开；完成或失败后恢复明确动作。
- 状态变化与误操作：不显示可绕过的返回按钮；等待结果，不发布新纪录或下一关。
- 版式收益：一次荣誉表达后接四项统计和关键原因，下一步单独成行。
- 不可用项：正在保存…；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/18_result_saving.png) · [SVG](../screens/svg/18_result_saving.svg) · [线框PNG](../wireframes/png/18_result_saving.png) · [线框SVG](../wireframes/svg/18_result_saving.svg) · [繁中PNG](../localization/png/18_result_saving-zh-Hant.png) · [English PNG](../localization/png/18_result_saving-en.png)

## 18_result_savefailed · 成绩保存失败

- 出现条件：设计条件分支：成绩保存失败；不代表真实成绩；证据：已有证据。
- 用户目标：理解本局结果并选择有效去向。
- 主要信息：胜败、五槽评级、本次/最佳、生命漏怪击杀用时、保存事实。
- 首要动作：重试保存。
- 次要动作：返回；查看保存说明…。
- 返回/关闭：保存说明回结果或重试，不丢弃成绩。
- 状态变化与误操作：成绩尚未保存；重试是主动作，保存说明回到安全重试流程。
- 版式收益：一次荣誉表达后接四项统计和关键原因，下一步单独成行。
- 文件：[简中PNG](../screens/png/18_result_savefailed.png) · [SVG](../screens/svg/18_result_savefailed.svg) · [线框PNG](../wireframes/png/18_result_savefailed.png) · [线框SVG](../wireframes/svg/18_result_savefailed.svg) · [繁中PNG](../localization/png/18_result_savefailed-zh-Hant.png) · [English PNG](../localization/png/18_result_savefailed-en.png)

## 18_result_retry · 重试保存

- 出现条件：设计条件分支：重试保存；不代表真实成绩；证据：已有证据。
- 用户目标：理解本局结果并选择有效去向。
- 主要信息：胜败、五槽评级、本次/最佳、生命漏怪击杀用时、保存事实。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：无额外次要提交。
- 返回/关闭：保存处理中无直接离开；完成或失败后恢复明确动作。
- 状态变化与误操作：重试期间保留原结果，避免重复提交或绕过保存。
- 版式收益：一次荣誉表达后接四项统计和关键原因，下一步单独成行。
- 不可用项：正在保存…；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/18_result_retry.png) · [SVG](../screens/svg/18_result_retry.svg) · [线框PNG](../wireframes/png/18_result_retry.png) · [线框SVG](../wireframes/svg/18_result_retry.svg) · [繁中PNG](../localization/png/18_result_retry-zh-Hant.png) · [English PNG](../localization/png/18_result_retry-en.png)

## 18_result_saved · 成绩保存成功

- 出现条件：设计条件分支：成绩保存成功；不代表真实成绩；证据：已有证据。
- 用户目标：理解本局结果并选择有效去向。
- 主要信息：胜败、五槽评级、本次/最佳、生命漏怪击杀用时、保存事实。
- 首要动作：进入下一关。
- 次要动作：返回；重玩本关；返回选关。
- 返回/关闭：返回选关；重玩经必要确认；下一关仅保存成功且非末关可用。
- 状态变化与误操作：明确成绩已保存后，恢复下一关、重玩与返回。
- 版式收益：一次荣誉表达后接四项统计和关键原因，下一步单独成行。
- 文件：[简中PNG](../screens/png/18_result_saved.png) · [SVG](../screens/svg/18_result_saved.svg) · [线框PNG](../wireframes/png/18_result_saved.png) · [线框SVG](../wireframes/svg/18_result_saved.svg) · [繁中PNG](../localization/png/18_result_saved-zh-Hant.png) · [English PNG](../localization/png/18_result_saved-en.png)

## 18_result_final · 末关完成

- 出现条件：设计条件分支：末关完成；不代表真实成绩；证据：已有证据。
- 用户目标：理解本局结果并选择有效去向。
- 主要信息：胜败、五槽评级、本次/最佳、生命漏怪击杀用时、保存事实。
- 首要动作：返回关卡选择。
- 次要动作：返回；重玩末关。
- 返回/关闭：返回选关；重玩经必要确认；下一关仅保存成功且非末关可用。
- 状态变化与误操作：配置的末关结束且没有下一关；返回关卡选择或重玩末关。
- 版式收益：一次荣誉表达后接四项统计和关键原因，下一步单独成行。
- 文件：[简中PNG](../screens/png/18_result_final.png) · [SVG](../screens/svg/18_result_final.svg) · [线框PNG](../wireframes/png/18_result_final.png) · [线框SVG](../wireframes/svg/18_result_final.svg) · [繁中PNG](../localization/png/18_result_final-zh-Hant.png) · [English PNG](../localization/png/18_result_final-en.png)

## 19_common_empty · 暂无历史成绩

- 出现条件：通用组件状态：暂无历史成绩；证据：已有证据。
- 用户目标：理解缺失或处理中状态并恢复。
- 主要信息：空内容/错误/等待、原因、可用动作。
- 首要动作：开始挑战。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：完成一次挑战后查看成绩；开始挑战或返回。
- 版式收益：原因与恢复动作同组，避免空面板让玩家猜测。
- 文件：[简中PNG](../screens/png/19_common_empty.png) · [SVG](../screens/svg/19_common_empty.svg) · [线框PNG](../wireframes/png/19_common_empty.png) · [线框SVG](../wireframes/svg/19_common_empty.svg) · [繁中PNG](../localization/png/19_common_empty-zh-Hant.png) · [English PNG](../localization/png/19_common_empty-en.png)

## 19_common_unavailable · 内容读取失败

- 出现条件：通用组件状态：内容读取失败；证据：已有证据。
- 用户目标：理解缺失或处理中状态并恢复。
- 主要信息：空内容/错误/等待、原因、可用动作。
- 首要动作：重试读取。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：读取失败保留当前选择，重试读取或返回。
- 版式收益：原因与恢复动作同组，避免空面板让玩家猜测。
- 文件：[简中PNG](../screens/png/19_common_unavailable.png) · [SVG](../screens/svg/19_common_unavailable.svg) · [线框PNG](../wireframes/png/19_common_unavailable.png) · [线框SVG](../wireframes/svg/19_common_unavailable.svg) · [繁中PNG](../localization/png/19_common_unavailable-zh-Hant.png) · [English PNG](../localization/png/19_common_unavailable-en.png)

## 19_common_confirming · 等待操作结果

- 出现条件：通用组件状态：等待操作结果；证据：已有证据。
- 用户目标：理解缺失或处理中状态并恢复。
- 主要信息：空内容/错误/等待、原因、可用动作。
- 首要动作：无主动提交；等待系统结果或使用可用浏览入口。
- 次要动作：返回。
- 返回/关闭：左上返回回上一级；同层切换保留浏览位置。
- 状态变化与误操作：未提交的等待可返回；已提交且不可中止时等待结果，最终以产品规则为准。
- 版式收益：原因与恢复动作同组，避免空面板让玩家猜测。
- 不可用项：处理中…；保留原因，不接受重复提交。
- 文件：[简中PNG](../screens/png/19_common_confirming.png) · [SVG](../screens/svg/19_common_confirming.svg) · [线框PNG](../wireframes/png/19_common_confirming.png) · [线框SVG](../wireframes/svg/19_common_confirming.svg) · [繁中PNG](../localization/png/19_common_confirming-zh-Hant.png) · [English PNG](../localization/png/19_common_confirming-en.png)

