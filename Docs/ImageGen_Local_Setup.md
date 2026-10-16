# 本机 ImageGen CLI/API 配置

配置日期：2026-10-16。用户已授权使用 imagegen 技能的 CLI/API 后备方式。

当前已按用户指定的 AIHub 中转站配置并保存密钥。鉴权成功，但该密钥所属分组尚未开放图片模型，真实上下视角补绘仍受中转站权限限制；详细结果见下方验证记录。

## 本机入口

| 项目 | 路径 / 设置 |
| --- | --- |
| 独立 Python 环境 | `C:\Users\78296\.codex\tools\imagegen\.venv\Scripts\python.exe` |
| 官方生图 CLI | `C:\Users\78296\.codex\skills\.system\imagegen\scripts\image_gen.py` |
| 隐藏输入密钥 | `C:\Users\78296\.codex\tools\imagegen\Set-OpenAIKey.ps1` |
| 加载环境 | `C:\Users\78296\.codex\tools\imagegen\Use-ImageGen.ps1` |
| 透明底处理 | `C:\Users\78296\.codex\skills\.system\imagegen\scripts\remove_chroma_key.py` |
| 本项目生成输出 | `D:\FreedomTower_1\output\imagegen\AdvancedHen\` |
| 模型 | `gpt-image-2`，沿用已安装技能的 CLI 默认值 |
| 图片格式 / 正式稿质量 | PNG / high |
| 中转站 | [AIHub](https://aihub.dog) |
| 当前 `OPENAI_BASE_URL` | `https://aihub.top/v1`，来自站点首页标注的 API 地址，已验证鉴权 |
| 当前 `OPENAI_API_KEY` | 用户提供的中转站密钥，已保存到用户环境变量；不在文档中记录 |

独立环境已安装 Python 3.12.14、`openai==3.31.0` 与 `Pillow==12.3.0`；完整依赖版本见本机 `C:\Users\78296\.codex\tools\imagegen\requirements.lock.txt`。没有修改技能内的官方脚本。未向 Unity 工程写入密钥，也没有将这套 CLI 注册为 MCP 或更改 Codex 的 MCP 配置。

## 设置密钥

当前密钥与中转站地址已经配置，无需再次输入。以后需要更换密钥时，可在本机 PowerShell 执行以下命令；输入内容不会显示，也不需要把密钥发到聊天中。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\tools\imagegen\Set-OpenAIKey.ps1" -BaseUrl 'https://aihub.top/v1'
```

此命令兼容 Windows PowerShell 5.1，只对本次启动的 PowerShell 进程指定执行策略，不需要管理员权限，也不更改用户或系统的长期执行策略。它避免直接运行 `.ps1` 时出现“在此系统上禁止运行脚本”的报错。

脚本将密钥与 API 地址写入当前 Windows 用户的 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 环境变量，并加载到脚本所在的子进程。不写入脚本、仓库、提示词或 `.env` 文件。空输入或含空白的输入会被拒绝，不覆盖旧设置。原终端窗口可用下面的环境加载步骤读取新配置。

`OPENAI_API_KEY` 是 SDK 读取密钥的变量名，也可以保存兼容中转站的密钥；配合 `OPENAI_BASE_URL` 即可指定服务地址。当前使用 AIHub 密钥，无需原生 OpenAI 平台密钥。

## 每次调用前加载环境

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. "$env:USERPROFILE\.codex\tools\imagegen\Use-ImageGen.ps1"
Set-Location 'D:\FreedomTower_1'
```

第一条命令只对当前终端进程生效，关闭该窗口后失效。加载脚本会重新读取用户环境变量中的密钥与 API 地址，因此已打开的 Codex 会话也可以读取后来设置的配置。它只打印密钥是否已配置和 API 地址，不打印密钥内容。它准备 `$ImageGenPython`、`$ImageGenCli`、`$ImageGenRemoveChromaKey` 三个路径变量，随后直接调用官方 CLI。

## 无密钥试运行

以下命令校验上下视角现有参考图、提示词、模型参数及输出路径，不调用生图 API，不产生图片。

```powershell
foreach ($direction in @('up', 'down')) {
    & $ImageGenPython $ImageGenCli edit `
        --model gpt-image-2 `
        --image 'Docs/EnemyDirectionReview/AdvancedHen/reference_original.png' `
        --image 'Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.png' `
        --prompt-file "Docs/EnemyDirectionReview/AdvancedHen/generation_$direction.txt" `
        --size 1536x1024 --quality high --output-format png --no-augment `
        --out "output/imagegen/AdvancedHen/$direction-magenta.png" `
        --dry-run
    if ($LASTEXITCODE -ne 0) { throw "Dry-run failed: $direction" }
}
```

第 1 张输入是完整角色参考，第 2 张是原始分件图集。现有提示词要求依据参考重绘正面/背面视角，并按 3 列 × 2 行组织正常头、愤怒头、死亡头、身体、翅膀、腿六个分件。

## 密钥配置后的真实生成

先让中转站为当前密钥分组开放 `gpt-image-2` 及 `/v1/images/edits` 接口，再运行以上加载环境命令。随后执行以下命令生成 AdvancedHen 上下两张分件图集；这会通过中转站调用兼容 Images API。当前分组会返回 `model_not_found`，在权限开放前不应将这些命令视为已经可用的真实生图链路。

```powershell
foreach ($direction in @('up', 'down')) {
    & $ImageGenPython $ImageGenCli edit `
        --model gpt-image-2 `
        --image 'Docs/EnemyDirectionReview/AdvancedHen/reference_original.png' `
        --image 'Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.png' `
        --prompt-file "Docs/EnemyDirectionReview/AdvancedHen/generation_$direction.txt" `
        --size 1536x1024 --quality high --output-format png --no-augment `
        --out "output/imagegen/AdvancedHen/$direction-magenta.png"
    if ($LASTEXITCODE -ne 0) { throw "Generation failed: $direction" }
}
```

命令没有 `--force`，重复执行时会拒绝覆盖同名产物。需要保留多个版本时，使用 `up-magenta-v2.png`、`down-magenta-v2.png` 等新文件名。

## 转为透明 PNG

技能当前说明 `gpt-image-2` 不支持 `background=transparent`。沿用项目现有提示词的纯洋红色背景方案，用技能自带脚本去色后得到具有真实 alpha 通道的 PNG：

```powershell
foreach ($direction in @('up', 'down')) {
    & $ImageGenPython $ImageGenRemoveChromaKey `
        --input "output/imagegen/AdvancedHen/$direction-magenta.png" `
        --out "output/imagegen/AdvancedHen/$direction-transparent.png" `
        --key-color '#ff00ff'
    if ($LASTEXITCODE -ne 0) { throw "Alpha extraction failed: $direction" }
}
```

生成后仍需检查角色一致性、正背面结构、分件布局、描边完整性与透明边缘，合格后再裁切、导入 Unity；未生成的图片和未经审核的自动输出不算完成品。此配置没有切换到 `gpt-image-1.5`。

## 验证范围

本机已实际完成以下检查：

| 检查 | 结果 |
| --- | --- |
| 独立环境安装及 `pip check` | 通过，无依赖冲突 |
| OpenAI SDK / Pillow 导入 | 通过 |
| SDK 客户端离线初始化、Images generate/edit 方法 | 通过，没有发送生图请求 |
| 两份 PowerShell 脚本语法检查 | 通过，Windows PowerShell 5.1 可解析 |
| Windows PowerShell 5.1 进程级执行策略及环境加载 | 通过，没有更改用户或系统的长期策略 |
| 完整角色参考图 | PNG / RGBA / 768×768，文件校验通过 |
| 原始分件图集 | PNG / RGBA / 960×800，文件校验通过 |
| Up / Down 两次官方 CLI `edit --dry-run` | 通过，输出参数对应各自提示词 |
| 官方去色脚本入口 | `--help` 通过 |
| `https://api.openai.com/v1/models` 网络连通 | 匿名请求返回 HTTP 401，尚未验证认证 |
| 当前用户 `OPENAI_API_KEY` / `OPENAI_BASE_URL` | 已设置，SDK 读取地址确认为 `https://aihub.top/v1/` |
| AIHub `.dog/v1/models`、`.top/v1/models` 鉴权 | 均返回 HTTP 200 |
| 当前分组公开模型 | `gpt-5.6-sol`、`gpt-6-astra`、`gpt-6-sol`、`gpt-6.1-sol`，未列出图片模型 |
| `.dog/v1/images/generations`、`.dog/v1/images/edits` 能力检查 | 均返回 HTTP 404 / `model_not_found`，提示当前分组无 `gpt-image-2` |
| 站点标注的 `.top/v1/images/edits` 能力检查 | 同样返回 HTTP 404 / `model_not_found` |

图片接口能力检查仅提交模型名，没有提示词和图片输入，没有生成图片。密钥鉴权已验证成功；图片模型权限检查被服务端明确拒绝，错误为 `Model "gpt-image-2" is not available for this group`。当前不需要更换本机安装或申请原生 OpenAI Key，应由中转站开放分组图片权限，或改用支持图片生成与编辑的兼容服务。

中转站权限开通后还需验证实际生图、输入参考图的 multipart 编辑请求、返回的 `b64_json` 图片数据及透明边缘，账户图片额度也尚未验证。没有切换或冒用其他模型来替代 `gpt-image-2`。

本次配置没有生成上下视角图片，也没有完成 Unity 美术接入或运行验收。Unity MCP 的连接状态与 Python CLI 的可用性是两条独立链路。

尝试读取 OpenAI 官方在线文档时，该网络环境返回 HTTP 403；本机 CLI 参数与默认模型以已安装的 [imagegen 技能](C:/Users/78296/.codex/skills/.system/imagegen/SKILL.md) 和脚本帮助为依据。官方参考入口：[API Quickstart](https://developers.openai.com/api/docs/quickstart)、[Image generation](https://developers.openai.com/api/docs/guides/image-generation)。
