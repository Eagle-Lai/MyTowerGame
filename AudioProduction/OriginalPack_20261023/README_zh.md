# Freedom Tower 原创音频包：守望微光 / Watchlight

制作日期：2026-10-23。制作工程：D:/FreedomTower_1，Unity 2022.3.62f3c1。
制作交付时本包为独立音频资源，尚未接入游戏。全部音频由原创音符事件、振荡器、滤波噪声及离线混音生成，没有使用第三方录音、采样包或现成旋律。

接入补记（2026-10-27）：`D:/FishTestGame` 已使用 Assets 中的这 93 个母版接入声音服务、设置和资源管线，详见[声音接入实施记录](../../Docs/AudioIntegration_Implementation_2026-10-27.md)。本目录继续保留制作来源、复现与技术 QA 的历史记录；游戏播放、人工听感与 Android 设备结果按实施记录单独验收。

交付：4 首循环音乐、3 段结算短曲、86 个音效 WAV，合计 93 个母版；另含 2 个试听混音 WAV。
全部 WAV 为 48 kHz / 24-bit PCM；音乐和短曲为立体声，音效为单声道。

## 风格与音乐结构

主题“守望微光”使用 D–F–A–G–E / D–C–A 的轮廓，配合有节奏的机械拨弦、柔和合成垫底、晶体钟音和克制打击乐。四首共用主题身份，分别表达菜单、布阵、常规战斗和高压防守。
每首 32 小节，分为主题陈述、编配扩展、对比段、主题回归四部分；和弦、低音、分解音型与乐句有段落变化。

| 曲目 | BPM | 调式 | 时长 | 循环 |
|---|---:|---|---:|---|
| [ft_bgm_menu](BGM/ft_bgm_menu.wav) | 96 | D Dorian / D minor | 80.00s | 整个 WAV；0 到 3840000 样本帧，末端不含 |
| [ft_bgm_prepare](BGM/ft_bgm_prepare.wav) | 88 | D Dorian | 87.27s | 整个 WAV；0 到 4189091 样本帧，末端不含 |
| [ft_bgm_battle](BGM/ft_bgm_battle.wav) | 116 | D natural minor | 66.21s | 整个 WAV；0 到 3177931 样本帧，末端不含 |
| [ft_bgm_pressure](BGM/ft_bgm_pressure.wav) | 128 | D minor with harmonic-minor dominant | 60.00s | 整个 WAV；0 到 2880000 样本帧，末端不含 |

## 试听

- 打开 [试听页面](LISTEN.html)，可播放曲目和所有音效。
- [48 秒密集战斗混音](Previews/ft_dense_battle_mix.mp3)：音乐、多塔开火、爆炸、冰晶光环、敌人及提示。
- [全部音效串听](Previews/ft_sfx_audition_reel.mp3)：各文件之间有静音间隔，索引见下表与 Previews/audition_index.json。
- 四首 *_3passes.mp3 为三遍连续循环试听。WAV 是生产母版，MP3 仅供预览。

## 验证状态

已制作：全部母版、音效变体、MIDI/音符事件、试听文件。
已分析：95 个 WAV 的格式、信号与循环边界，结果见 Quality/QA_zh.md、Quality/audio_quality_report.json 和 asset_manifest.csv。
已试听：本执行环境未提供音频感知能力，因此未进行人工听感验收。最终的音乐审美、刺耳程度、混音掩蔽和反复播放疲劳仍需通过所附预览确认。

## 文件与复现

BGM/、Stingers/、SFX/ 为母版；Previews/ 为试听；Source/ 为合成代码、逐音符编曲 JSON、MIDI 和依赖列表。MIDI 的 GM 音色仅供编辑互换，精确复现使用自带 Python 合成器。
运行命令（在该目录中）：
```powershell
python -m pip install -r Source/requirements.txt
python Source/produce.py
python Source/finish.py
```
每个事件以 SHA256 派生固定随机种子；源脚本在固定依赖环境可复现音符、噪声与音色。
Source/.dependencies 为本机工具安装缓存，不进入交付 ZIP；Source/_work 为临时测量目录，也不进入 ZIP。
声音设计中有意使用滤波噪声作为机械、爆破、虫壳和气流纹理。生物声音为风格化合成，不是真实动物录音。

## 音效串听时间索引

| 时间 | 文件 | 内容 |
|---|---|---|
| 00:00.70 | ft_sfx_ui_click_01.wav | 轻点击 |
| 00:01.16 | ft_sfx_ui_click_02.wav | 轻点击 |
| 00:01.60 | ft_sfx_ui_click_03.wav | 轻点击 |
| 00:02.04 | ft_sfx_ui_confirm_01.wav | 确认 |
| 00:02.61 | ft_sfx_ui_confirm_02.wav | 确认 |
| 00:03.17 | ft_sfx_ui_back_01.wav | 返回或关闭 |
| 00:03.70 | ft_sfx_ui_back_02.wav | 返回或关闭 |
| 00:04.22 | ft_sfx_ui_invalid_01.wav | 无效操作 |
| 00:04.79 | ft_sfx_ui_invalid_02.wav | 无效操作 |
| 00:05.35 | ft_sfx_ui_toggle_01.wav | 切换选项 |
| 00:05.81 | ft_sfx_ui_toggle_02.wav | 切换选项 |
| 00:06.26 | ft_sfx_ui_toggle_03.wav | 切换选项 |
| 00:07.10 | ft_sfx_tower_select_01.wav | 选中防御塔 |
| 00:07.68 | ft_sfx_tower_select_02.wav | 选中防御塔 |
| 00:08.25 | ft_sfx_tower_select_03.wav | 选中防御塔 |
| 00:08.82 | ft_sfx_tower_build_01.wav | 建造成功：装配落地 |
| 00:09.77 | ft_sfx_tower_build_02.wav | 建造成功：装配落地 |
| 00:10.76 | ft_sfx_tower_build_03.wav | 建造成功：装配落地 |
| 00:11.77 | ft_sfx_tower_build_fail_01.wav | 建造失败 |
| 00:12.39 | ft_sfx_tower_build_fail_02.wav | 建造失败 |
| 00:13.02 | ft_sfx_tower_upgrade_01.wav | 升级：能量提升 |
| 00:14.35 | ft_sfx_tower_upgrade_02.wav | 升级：能量提升 |
| 00:15.57 | ft_sfx_tower_upgrade_03.wav | 升级：能量提升 |
| 00:16.90 | ft_sfx_tower_sell_01.wav | 出售：拆卸与回收 |
| 00:17.86 | ft_sfx_tower_sell_02.wav | 出售：拆卸与回收 |
| 00:18.83 | ft_sfx_tower_sell_03.wav | 出售：拆卸与回收 |
| 00:19.86 | ft_sfx_normal_fire_01.wav | 普通塔：机械开火 |
| 00:20.41 | ft_sfx_normal_fire_02.wav | 普通塔：机械开火 |
| 00:20.95 | ft_sfx_normal_fire_03.wav | 普通塔：机械开火 |
| 00:21.52 | ft_sfx_normal_fire_04.wav | 普通塔：机械开火 |
| 00:22.08 | ft_sfx_normal_hit_01.wav | 普通塔：轻量命中 |
| 00:22.59 | ft_sfx_normal_hit_02.wav | 普通塔：轻量命中 |
| 00:23.09 | ft_sfx_normal_hit_03.wav | 普通塔：轻量命中 |
| 00:23.59 | ft_sfx_blast_fire_01.wav | 爆破塔：厚重开火 |
| 00:24.38 | ft_sfx_blast_fire_02.wav | 爆破塔：厚重开火 |
| 00:25.15 | ft_sfx_blast_fire_03.wav | 爆破塔：厚重开火 |
| 00:25.91 | ft_sfx_blast_hit_01.wav | 爆破塔：爆炸命中 |
| 00:27.27 | ft_sfx_blast_hit_02.wav | 爆破塔：爆炸命中 |
| 00:28.53 | ft_sfx_blast_hit_03.wav | 爆破塔：爆炸命中 |
| 00:29.82 | ft_sfx_frost_activate_01.wav | 冰霜塔：冰晶激活 |
| 00:31.05 | ft_sfx_frost_activate_02.wav | 冰霜塔：冰晶激活 |
| 00:32.28 | ft_sfx_frost_activate_03.wav | 冰霜塔：冰晶激活 |
| 00:33.57 | ft_sfx_frost_pulse_01.wav | 冰霜塔：柔和能量脉冲 |
| 00:34.49 | ft_sfx_frost_pulse_02.wav | 冰霜塔：柔和能量脉冲 |
| 00:35.40 | ft_sfx_frost_pulse_03.wav | 冰霜塔：柔和能量脉冲 |
| 00:36.38 | ft_sfx_frost_loop_01.wav | 冰霜塔：持续范围减速光环 |
| 00:41.08 | ft_sfx_light_hit_01.wav | 轻型生物受击 |
| 00:41.61 | ft_sfx_light_hit_02.wav | 轻型生物受击 |
| 00:42.15 | ft_sfx_light_hit_03.wav | 轻型生物受击 |
| 00:42.70 | ft_sfx_light_death_01.wav | 轻型生物死亡 |
| 00:43.53 | ft_sfx_light_death_02.wav | 轻型生物死亡 |
| 00:44.35 | ft_sfx_light_death_03.wav | 轻型生物死亡 |
| 00:45.12 | ft_sfx_wing_hit_01.wav | 鸟或蝙蝠受击 |
| 00:45.69 | ft_sfx_wing_hit_02.wav | 鸟或蝙蝠受击 |
| 00:46.27 | ft_sfx_wing_hit_03.wav | 鸟或蝙蝠受击 |
| 00:46.86 | ft_sfx_wing_death_01.wav | 鸟或蝙蝠死亡 |
| 00:47.70 | ft_sfx_wing_death_02.wav | 鸟或蝙蝠死亡 |
| 00:48.60 | ft_sfx_wing_death_03.wav | 鸟或蝙蝠死亡 |
| 00:49.50 | ft_sfx_insect_hit_01.wav | 虫或蝎受击 |
| 00:50.05 | ft_sfx_insect_hit_02.wav | 虫或蝎受击 |
| 00:50.60 | ft_sfx_insect_hit_03.wav | 虫或蝎受击 |
| 00:51.16 | ft_sfx_insect_death_01.wav | 虫或蝎死亡 |
| 00:51.99 | ft_sfx_insect_death_02.wav | 虫或蝎死亡 |
| 00:52.85 | ft_sfx_insect_death_03.wav | 虫或蝎死亡 |
| 00:53.65 | ft_sfx_heavy_hit_01.wav | 重型生物受击 |
| 00:54.35 | ft_sfx_heavy_hit_02.wav | 重型生物受击 |
| 00:55.07 | ft_sfx_heavy_hit_03.wav | 重型生物受击 |
| 00:55.81 | ft_sfx_heavy_death_01.wav | 重型生物死亡 |
| 00:57.03 | ft_sfx_heavy_death_02.wav | 重型生物死亡 |
| 00:58.32 | ft_sfx_heavy_death_03.wav | 重型生物死亡 |
| 01:00.01 | ft_sfx_round_start_01.wav | 回合开始 |
| 01:01.03 | ft_sfx_round_start_02.wav | 回合开始 |
| 01:02.12 | ft_sfx_round_clear_01.wav | 回合完成 |
| 01:03.24 | ft_sfx_round_clear_02.wav | 回合完成 |
| 01:04.38 | ft_sfx_enemy_leak_01.wav | 敌人漏过终点 |
| 01:05.13 | ft_sfx_enemy_leak_02.wav | 敌人漏过终点 |
| 01:05.90 | ft_sfx_enemy_leak_03.wav | 敌人漏过终点 |
| 01:06.71 | ft_sfx_low_hp_01.wav | 低生命提示 |
| 01:07.73 | ft_sfx_low_hp_02.wav | 低生命提示 |
| 01:08.79 | ft_sfx_pause_01.wav | 暂停 |
| 01:09.39 | ft_sfx_pause_02.wav | 暂停 |
| 01:09.99 | ft_sfx_resume_01.wav | 继续 |
| 01:10.58 | ft_sfx_resume_02.wav | 继续 |
| 01:11.19 | ft_sfx_speed_change_01.wav | 倍速切换 |
| 01:11.76 | ft_sfx_speed_change_02.wav | 倍速切换 |
| 01:12.34 | ft_sfx_speed_change_03.wav | 倍速切换 |
