# AssetBundle 音效资源目录

把音效文件（`.wav` / `.ogg` / `.mp3` / `.aiff`）直接放进本目录（可以带子目录），
然后二选一：

- 命令行：`python .workbuddy/tools/gen_audio_catalog.py`
- 或直接跑 Unity 菜单 `Tools ▸ 塔防 ▸ 3. 导出配置表（Luban）` 之前手动执行上面的命令

## 命名约定

- **文件名（不含扩展名）就是逻辑名**，必须与 `Luban/Config/Datas/AudioData.xlsx`（表名 `TBAudio`）
  的 `logicalName` 列**完全一致**。
  例：`sfx_tower_fire_normal.wav` ⇄ `logicalName = sfx_tower_fire_normal`
- 生成器会写出 `Assets/Scripts/Data/AudioCatalog.cs`，
  `ResTable` 据此登记逻辑名 `Audio_<文件名>`。

## 为什么代码不用改

`AudioManager.Play("sfx_tower_fire_normal")` 的行为是：
查 `TBAudio` 取音量/音高/循环 → 经 `ResLoader` 取 `Audio_<逻辑名>` 的 `AudioClip` → 播放。

**任一环节缺失都静默跳过**（只打印一次限流警告），所以：
- 现在工程里 0 个音频文件 → 游戏照常跑，只是没有声音；
- 把文件放进来 + 跑一次生成器 → 立刻有声，**不需要改任何 .cs**。
