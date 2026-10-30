# 敌人方向 GIF 集中目录

打开 `index.html` 默认选择“四方向移动（最终成品）”，按预制体名称排序，每个角色仅展示一份最终四向移动 GIF。也可选择“全部最终成品 GIF”查看最终动作。浏览列表排除过渡版本、前后对比、被否决方案和重复移动轮次。

目前 110 个预制体的最终四方向移动 GIF 可查看。另有 9 个预制体缺少最终四向移动媒体：Bat、BattlePanther、Bear、BearMounted、BlackBear、BlackBoar、BlackWolf、Boar、BoarMounted；不在浏览列表中放置占位卡片。来源及缺失列表见 `four_direction_moves.json`，全部最终动作索引见 `final_gifs.json`。

筛选依据为 `Remaining_20261024/progress.json` 的最终选定运行版本、首批批准的组合版本和 AdvancedHen R3。只收录明确动作文件，不按模糊的“当前审核版本”标签选图。

生成器为 `../Remaining_20261024/collect_gifs.py`。使用 `--render-only` 仅重建页面、说明和四向索引，复用原归档清单，不重新复制媒体或改写 `manifest.json`。补回有效版本的移动 GIF 后再次运行即可收录。
