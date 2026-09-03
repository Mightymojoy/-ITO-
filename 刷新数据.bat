@echo off
REM █████ 指定系统 Python 路径（修正：环境默认 Python 无 pandas 导致脚本崩溃）█████
set PYTHON=C:\Users\QwQ\.workbuddy\binaries\python\envs\default\Scripts\python.exe

REM █████ 修复：强制用 cmd.exe 运行，避免 Windows 11 默认终端用 PowerShell 执行 █████
%comspec% /c title 电商渠道看板 - 数据刷新

echo ============================================
echo  电商渠道业绩看板 - 数据刷新工具
echo ============================================
echo.

REM █████ 修复：用 pushd 替代 cd /d，cmd 和 PS 都兼容 █████
pushd "%~dp0"
if errorlevel 1 (
    echo ? 无法进入脚本目录，尝试绝对路径...
    set SCRIPT_DIR=%~dp0
    %SCRIPT_DIR:~0,2%
    cd %~dp0
)


echo [1/5] 正在同步数据源 ...
%PYTHON% -X utf8 _sync_sales.py
if errorlevel 1 (
    echo ? _sync_sales.py 执行失败
    echo  按任意键退出查看错误信息...
    pause
    exit /b 1
)

echo.
echo [2/5] 正在生成渠道看板 ...
%PYTHON% -X utf8 gen_channel_data.py
if errorlevel 1 (
    echo ? gen_channel_data.py 执行失败
    echo  按任意键退出查看错误信息...
    pause
    exit /b 1
)
%PYTHON% -X utf8 _gen_premium_demo.py
if errorlevel 1 (
    echo ? _gen_premium_demo.py 执行失败
    echo  按任意键退出查看错误信息...
    pause
    exit /b 1
)

echo.
echo [3/5] 正在生成产品看板 ...
%PYTHON% -X utf8 gen_prod_data.py
if errorlevel 1 (
    echo ? gen_prod_data.py 执行失败
    echo  按任意键退出查看错误信息...
    pause
    exit /b 1
)
%PYTHON% -X utf8 _gen_product_html.py
if errorlevel 1 (
    echo ? _gen_product_html.py 执行失败
    echo  按任意键退出查看错误信息...
    pause
    exit /b 1
)

echo.
echo [4/5] 正在写入更新时间轴并推送至 GitHub Pages ...
REM ===== 更新时间轴：记录本次生成（先记录生成中，推送成功后再覆盖为成功） =====
%PYTHON% -X utf8 "C:\Users\QwQ\WorkBuddy\2026-08-12-13-26-00\update_timeline\update_timeline.py" "%~dp0channel_dashboard.html" --status ok --note "电商渠道看板更新"
%PYTHON% -X utf8 "C:\Users\QwQ\WorkBuddy\2026-08-12-13-26-00\update_timeline\update_timeline.py" "%~dp0product_dashboard.html" --status ok --note "电商产品看板更新"
copy /Y channel_dashboard.html _github_repo\channel_dashboard.html > nul
if errorlevel 1 (
    echo ? 复制 channel_dashboard.html 失败
    echo  按任意键退出查看错误信息...
    pause
    exit /b 1
)
copy /Y product_dashboard.html _github_repo\product_dashboard.html > nul
if errorlevel 1 (
    echo ? 复制 product_dashboard.html 失败
    echo  按任意键退出查看错误信息...
    pause
    exit /b 1
)

pushd _github_repo
set GIT_TERMINAL_PROMPT=0
"C:\Users\QwQ\.workbuddy\binaries\PortableGit\versions\1.2.0\mingw64\bin\git.exe" add channel_dashboard.html product_dashboard.html index.html
"C:\Users\QwQ\.workbuddy\binaries\PortableGit\versions\1.2.0\mingw64\bin\git.exe" commit -m "自动更新看板数据" || echo   无新变更，跳过提交
"C:\Users\QwQ\.workbuddy\binaries\PortableGit\versions\1.2.0\mingw64\bin\git.exe" push origin main
if errorlevel 1 (
    echo ? git push 失败！可能是远程有新提交，请先 git pull
    popd
    echo  按任意键退出查看错误信息...
    pause
    exit /b 1
)
popd

echo.
echo [5/5] ============ 全部完成！数据已更新到 GitHub Pages ============
echo  https://mightymojoy.github.io/-ITO-/channel_dashboard.html
echo  https://mightymojoy.github.io/-ITO-/product_dashboard.html
echo.
pause
