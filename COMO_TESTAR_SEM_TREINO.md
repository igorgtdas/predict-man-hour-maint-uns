# Só quero ver o modelo funcionando (teste/demo)

Você **não** tem os dados, **não** vai treinar e **não** precisa de `config.yaml`.  
Só quer abrir o formulário, colocar os números e ver a previsão de HH.

---

## O que você precisa

1. **O código do projeto** (esta pasta com `app.py`, `app/`, `pipeline/`, etc.).
2. **A pasta `models/`** com o modelo já treinado (quem mantém o projeto te envia ou você baixa de um *Release*).

A pasta `models/` deve conter pelo menos:

- `model_hh_semanal_5features.keras`
- `scaler_X_5features.joblib`
- `scaler_y_5features.joblib`

(Nada de dados, Excel, CSV ou config é necessário.)

---

## Passo a passo (Windows)

### Opção 1 — Script automático (recomendado)

1. Coloque a pasta `models/` (com os 3 arquivos acima) dentro da pasta do projeto (junto de `app.py`).
2. Dê **dois cliques** em **`rodar_app.bat`**.
3. Aguarde abrir o navegador em **http://127.0.0.1:5000**. Use o formulário para testar.

### Opção 2 — Manual

1. Coloque a pasta **`models/`** (com o modelo e os scalers) dentro da pasta do projeto.
2. Abra o **Prompt de Comando** ou **PowerShell** nesta pasta e rode:

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```

3. Abra o navegador em: **http://127.0.0.1:5000**.

---

## Resumo

| Você precisa | Não precisa |
|-------------|-------------|
| Pasta do projeto (código) | `config.yaml` |
| Pasta `models/` com modelo + scalers | Dados (CSV, Excel) |
| Python instalado | Treinar o modelo |
| | Git |

O app usa a **última versão** do modelo que estiver dentro de `models/` (ou na subpasta indicada pelo `registry.json`, se existir). Não é necessário config para treinamento nem para rodar o app em modo teste.
