@echo off
echo =========================================================
echo   LOS MANAGER - Gerando o instalador (.exe)
echo =========================================================
echo.

echo [1/3] Instalando PyInstaller (se ainda nao tiver)...
pip install pyinstaller

echo.
echo [2/3] Limpando builds antigos...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo.
echo [3/3] Gerando o executavel...
python -m PyInstaller LosManager.spec --clean

echo.
echo =========================================================
echo   PRONTO!
echo   O programa esta na pasta: dist\LosManager\
echo   Copie a pasta "LosManager" inteira para o pendrive/notebook.
echo   Nao precisa ter Python la.
echo =========================================================
pause
