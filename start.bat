@echo off
chcp 65001 >nul
REM Windows启动脚本 - 文件借阅管理系统

echo ========================================
echo    文件借阅管理系统启动脚本
echo ========================================
echo.

REM 设置Python路径（从pip安装路径推断）
set PYTHON_CMD=C:\Users\Lydia\AppData\Local\Python\pythoncore-3.14-64\python.exe

REM 如果上面的路径不存在，尝试其他常见位置
if not exist "%PYTHON_CMD%" (
    for /f "tokens=2*" %%a in ('reg query "HKEY_CURRENT_USER\SOFTWARE\Python\PythonCore" /s /v InstallPath 2^>nul ^| findstr InstallPath') do (
        set PYTHON_CMD=%%b\python.exe
    )
)

if not exist "%PYTHON_CMD%" (
    echo.
    echo [错误] 无法找到Python
    echo 已尝试路径: C:\Users\Lydia\AppData\Local\Python\pythoncore-3.14-64\python.exe
    echo.
    echo 解决方案: 在CMD中手动运行
    echo   cd /d "此文件夹路径"
    echo   python app.py
    echo.
    pause
    exit /b 1
)

echo [✓] 找到Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM 启动应用
echo [进行中] 启动应用...
echo.
echo ================================================
echo  访问地址: 根据app.py中的INTERNAL_IP配置
echo  默认: http://localhost:5000
echo  或用手机扫描二维码
echo.
echo  要停止应用，按 Ctrl+C
echo ================================================
echo.

%PYTHON_CMD% app.py

if errorlevel 1 (
    echo.
    echo [错误] 应用启动失败！
    echo.
    pause
    exit /b 1
)

pause
