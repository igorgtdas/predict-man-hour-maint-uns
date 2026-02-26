@echo off
chcp 65001 >nul
title Previsão HH - TCC
echo.
echo Verificando ambiente...
echo.

if not exist "venv\Scripts\activate.bat" (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERRO: Python nao encontrado. Instale Python e tente de novo.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERRO ao instalar dependencias.
    pause
    exit /b 1
)

if not exist "models\model_hh_semanal_5features.keras" (
    echo.
    echo AVISO: Pasta models/ sem modelo treinado.
    echo Coloque na pasta "models" os arquivos:
    echo   - model_hh_semanal_5features.keras
    echo   - scaler_X_5features.joblib
    echo   - scaler_y_5features.joblib
    echo.
    echo Quem mantem o projeto pode te enviar a pasta models/ ou um zip.
    echo.
    pause
    exit /b 1
)

echo.
echo Abrindo o navegador em http://127.0.0.1:5000
echo Para parar o app: feche esta janela ou pressione Ctrl+C.
echo.
start http://127.0.0.1:5000
python app.py
pause
