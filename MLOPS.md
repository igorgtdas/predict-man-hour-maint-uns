# MLOps — Versionamento e operação do modelo

Este documento descreve o **versionamento** do modelo de previsão de HH e sugestões para evoluir com MLOps (monitoramento, drift, retreinamento).

---

## 1. Versionamento atual (implementado)

### 1.1 Como funciona

- **Cada treino** gera uma **versão** do modelo. A versão é:
  - o valor passado em `--version` (ex.: `1.0.0`), ou
  - a **data do dia** no formato `YYYYMMDD` (ex.: `20240226`), se `--version` for omitido.

- Os artefatos são salvos em **uma pasta por versão**:
  ```
  models/
  ├── 20240226/                    # versão por data
  │   ├── model_hh_semanal_4features.keras
  │   ├── model_hh_semanal_5features.keras
  │   ├── scaler_X_4features.joblib
  │   ├── scaler_y_4features.joblib
  │   ├── scaler_X_5features.joblib
  │   ├── scaler_y_5features.joblib
  │   └── model_metadata.json
  ├── 1.0.0/                       # versão semântica (ex.: python train.py --version 1.0.0)
  │   └── ...
  └── registry.json                # lista de todas as versões (MLOps)
  ```

- O **registry** (`models/registry.json`) guarda, para cada versão:
  - `version`, `trained_at`, `path`, `dataset`
  - métricas (MAE, RMSE, R²) das variantes 4 e 5 features.

### 1.2 Comandos

```bash
# Treinar e gerar versão com data de hoje (ex.: 20240226)
python train.py

# Treinar e dar um nome de versão (ex.: 1.0.0, release-prod)
python train.py --version 1.0.0
```

### 1.3 Qual versão a API usa?

No **`config.yaml`**, na seção **`mlops`**:

```yaml
mlops:
  production_version: "latest"   # ou "1.0.0", "20240226", etc.
  registry_file: "models/registry.json"
```

- **`production_version: "latest"`**  
  A API (`app.py`) usa a **última entrada** do `registry.json` (último treino).

- **`production_version: "1.0.0"`** (ou outra string)  
  A API usa só a pasta **`models/1.0.0/`**. Útil para fixar produção em uma versão estável.

Depois de alterar `production_version`, reinicie o `app.py`.

### 1.4 Consultar versão em produção

- **Terminal:** ao subir o app, é impresso algo como `Modelo carregado (versão: models/20240226).`
- **API:** `GET http://127.0.0.1:5000/api/info` retorna, entre outros, `model_version` (ex.: `models/20240226`).

---

## 2. Promover uma versão para produção

1. Treine e gere uma versão:  
   `python train.py --version 1.0.0`
2. Confira métricas em `models/1.0.0/model_metadata.json` e, se quiser, em `models/registry.json`.
3. No `config.yaml`, defina:
   ```yaml
   mlops:
     production_version: "1.0.0"
   ```
4. Reinicie a API: `python app.py`.

Assim você mantém histórico de versões e escolhe qual está “em produção” pela config.

---

## 3. Próximos passos MLOps (sugestões)

| Próximo passo | O que fazer | Ferramenta sugerida |
|---------------|-------------|----------------------|
| **Experimentos e métricas** | Registrar cada treino (parâmetros, métricas, artefato) e comparar runs. | **MLflow** (local: `mlflow ui` após `mlflow.log_*` no `train.py`). |
| **Model registry central** | Registrar modelo “em produção” e trocar versão sem editar config à mão. | **MLflow Model Registry** ou manter `registry.json` + `production_version` no config. |
| **Monitoramento em produção** | Medir erro (ex.: MAE) entre HH previsto e HH realizado por semana/mês. | Planilha/CSV, ou **MLflow** / **Weights & Biases** para métricas. |
| **Drift de dados** | Comparar distribuição das features (média, desvio) entre base de treino e dados recentes. | Script com **pandas** ou libs como **evidently**. |
| **Retreinamento agendado** | Rodar pipeline de dados + treino em intervalo fixo (ex.: trimestral). | **Cron**, **Task Scheduler** ou orquestrador (ex.: **Prefect**). |
| **Validação antes de promover** | Exigir que uma nova versão tenha métrica melhor (ex.: RMSE menor) antes de virar `production_version`. | Script que compara métricas no `registry.json` e só então atualiza o config (ou chama API de registry). |

---

## 4. Exemplo rápido com MLflow (opcional)

Para começar a registrar runs e modelos:

```bash
pip install mlflow
```

No `train.py`, após treinar e salvar o modelo, adicionar (exemplo):

```python
import mlflow
mlflow.set_tracking_uri("file:./mlruns")
mlflow.log_params({"epochs": epochs, "batch_size": batch_size})
mlflow.log_metrics({"MAE_5f": mae, "RMSE_5f": rmse, "R2_5f": r2})
mlflow.tensorflow.log_model(model, artifact_path="model_5features")
```

Depois: `mlflow ui` e acessar a interface para ver runs e artefatos.

---

## 5. Resumo

- **Versionamento:** um treino = uma versão (nome ou data), pasta em `models/<versão>/` e entrada no `registry.json`.
- **Produção:** definida por `config.yaml` → `mlops.production_version` ("latest" ou versão fixa).
- **API:** carrega sempre o modelo da versão configurada (ou da última do registry, se `latest`).
- **Evolução:** usar o mesmo esquema de versões e registry e, quando quiser, acrescentar MLflow, monitoramento e retreinamento agendado conforme a tabela acima.

Para o plano geral (pré-prod, produção, métricas, drift), consulte **`PLANO_PRE_PROD_E_MLOPS.md`**.
