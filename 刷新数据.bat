@echo off
title 请勿在此目录运行 - 部署仓库仅用于托管
chcp 936 > nul
echo ==========================================================
echo   此目录不用于数据刷新，请勿在此运行
echo ==========================================================
echo.
echo   当前目录：_github_repo
echo   本目录只用于 GitHub Pages 静态托管，仅存放：
echo       product_dashboard.html / channel_dashboard.html / *.json
echo   本目录内的 .py 仅为项目根目录脚本的历史镜像，不参与生成。
echo.
echo   正确的刷新入口在【项目根目录】：
echo       D:\E盘文件\电商渠道业绩看板\刷新数据.bat
echo.
echo   在根目录运行会依次：同步数据源 -> 重出两个看板 HTML
echo   -> 自动 commit + push 到 GitHub Pages。
echo.
echo   为什么停用本目录入口：
echo   若在仓库目录内运行，脚本会把 HTML 写进本目录并覆盖
echo   仓库内的正确文件；一旦根目录脚本与仓库镜像不同步，
echo   就会重出缺少新功能（如 SKU 退货率矩阵）的旧版页面。
echo   为杜绝此类误操作，本入口已改为提示壳。
echo.
pause
exit /b 1
