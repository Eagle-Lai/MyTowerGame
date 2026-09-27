@echo off
chcp 65001 >nul
setlocal

rem 【重要】工具要求 .NET 6 运行时。若本机只有更高版本（如 .NET 8/10），
rem        必须开启 roll-forward，否则会报 "You must install or update .NET"。
set "DOTNET_ROLL_FORWARD=LatestMajor"

rem ============================================================================
rem  Luban 配置表导出脚本  ——  FreeTower
rem ----------------------------------------------------------------------------
rem  作用：把 Config\Datas\*.xlsx 导出为
rem        ① C# 配置类   → Assets\Gen\                  （命名空间 cfg）
rem        ② JSON 数据    → Assets\ConfigJson\  （编辑器直读 + 打进 config 资源包）
rem
rem  用法：直接双击本脚本即可，不依赖当前工作目录。
rem
rem  注意：
rem   - 新增配置表时必须先在 Config\Datas\__tables__.xlsx 里登记一行，
rem     否则不会被导出。
rem   - Assets\Gen\ 是生成产物，禁止手工修改（重导会覆盖）。
rem   - 导出的 json 文件名 = 表名全小写，必须与 DataTables.cs 里读取的
rem     字符串完全一致。
rem ============================================================================

rem 以脚本自身所在目录为基准（%~dp0 末尾自带反斜杠），避免 CWD 不同导致失效
set "LUBAN_DIR=%~dp0"
set "WORKSPACE=%LUBAN_DIR%.."

set "GEN_CLIENT=%LUBAN_DIR%Tools\Luban.ClientServer\Luban.ClientServer.exe"
set "CONF_ROOT=%LUBAN_DIR%Config"
set "ROOT_XML=%CONF_ROOT%\Defines\__root__.xml"
set "DATA_DIR=%CONF_ROOT%\Datas"
set "OUT_CODE=%WORKSPACE%\Assets\Gen"
set "OUT_DATA=%WORKSPACE%\Assets\ConfigJson"

rem ---------------------------------------------------------------------------
rem 【为什么数据输出到 Assets\ConfigJson 而不是 StreamingAssets\json】
rem   StreamingAssets 下的文件被 Unity 当作"原始文件"（DefaultAsset）处理，
rem   不会导入成 TextAsset —— 用 AssetDatabase.LoadAssetAtPath<TextAsset>() 读不到内容。
rem   而配置表在编辑器下要直读、在真机上要打进 config 资源包，
rem   两者都要求它是普通 Assets 资源。所以输出到 Assets\ConfigJson。
rem ---------------------------------------------------------------------------

rem ---------- 前置校验 ----------
if not exist "%GEN_CLIENT%" (
    echo [错误] 找不到 Luban 导出工具：
    echo        %GEN_CLIENT%
    echo        请确认 Tools\Luban.ClientServer 目录存在。
    pause
    exit /b 1
)
if not exist "%ROOT_XML%" (
    echo [错误] 找不到配置定义文件：
    echo        %ROOT_XML%
    pause
    exit /b 1
)
if not exist "%DATA_DIR%" (
    echo [错误] 找不到配置源表目录：
    echo        %DATA_DIR%
    pause
    exit /b 1
)

if not exist "%OUT_CODE%" mkdir "%OUT_CODE%"
if not exist "%OUT_DATA%" mkdir "%OUT_DATA%"

echo ============================================================================
echo   配置表目录 : %DATA_DIR%
echo   代码输出   : %OUT_CODE%
echo   数据输出   : %OUT_DATA%
echo ============================================================================
echo.

rem ---------- 执行导出 ----------
rem 注意语法：-j cfg 是工具自身参数，job 参数（-d / --input_data_dir 等）
rem 必须放在 `--` 分隔符之后，否则会报 "unknown argument:-d"。
rem -c 固定缓存文件位置，避免在仓库根目录生成 .cache.meta。
"%GEN_CLIENT%" -j cfg -c "%LUBAN_DIR%.cache.meta" -- ^
 -d "%ROOT_XML%" ^
 --input_data_dir "%DATA_DIR%" ^
 --output_code_dir "%OUT_CODE%" ^
 --output_data_dir "%OUT_DATA%" ^
 --gen_types code_cs_unity_json,data_json ^
 -s all

if errorlevel 1 (
    echo.
    echo [失败] 导出过程返回非 0，请检查上方日志。
    pause
    exit /b 1
)

rem ---------- 产物自检 ----------
echo.
echo ---------- 产物自检 ----------
set "MISSING=0"
for %%F in (tbenemydata tbtowerinfo tbenemylist tbrounddata tbsceneinfo tbbulletdata tblevelmap tbglobal) do (
    if exist "%OUT_DATA%\%%F.json" (
        echo   [OK]   %%F.json
    ) else (
        echo   [缺失] %%F.json
        set "MISSING=1"
    )
)

if "%MISSING%"=="1" (
    echo.
    echo [警告] 有配置文件未生成，请检查 __tables__.xlsx 中的登记与分组设置。
)

echo.
echo [完成] 代码 -^> %OUT_CODE%
echo        数据 -^> %OUT_DATA%
echo.
echo 提示：回到 Unity 后会自动重新导入；若未刷新请手动 Ctrl+R。
pause
