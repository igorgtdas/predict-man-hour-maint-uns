# TCC — Previsão de HH (itens não programados)

Projeto de previsão de **Homem-Hora (HH)** de itens não programados em manutenção de aeronaves, com base em utilização da frota (B737NG). Modelo: rede neural (TensorFlow/Keras) sobre dados agregados por semana.

**Repositório GitHub:** as bases de dados e os modelos treinados **não** são versionados (ficam sigilosos). O repositório contém apenas código e documentação. O usuário final acessa apenas o modelo via front-end (formulário de previsão). Ver **`GITHUB.md`** para como subir o projeto sem expor dados.

## Estrutura do projeto (organizada, sem duplicatas)

```
TCC/
├── config.yaml                 # Configuração (caminhos e parâmetros)
├── run_data_pipeline.py       # Pipeline de dados (executar da pasta TCC)
├── train.py                    # Treino do modelo
├── requirements.txt
├── README.md
├── PLANO_PRE_PROD_E_MLOPS.md
├── pipeline/                   # Módulos da pipeline (ingestão, processamento, validação)
├── data/
│   ├── raw/                   # Dados brutos (única cópia)
│   │   └── Utilization/Aircraft utilization/   # 40 CSVs de utilização
│   └── processed/             # Saída da pipeline e datasets canônicos
│       ├── bd_unscheduled_itens.csv
│       ├── dataset_uti_vs_hh_semanal.csv       # Dataset final para o modelo
│       └── (intermediários gerados ao rodar run_data_pipeline.py)
├── models/                     # Modelos treinados, scalers e model_metadata.json
├── app.py                      # API + frontend em produção (Flask)
├── app/index.html              # Página do formulário de previsão
└── notebooks/                  # Notebooks de referência (não duplicam dados)
    ├── Ajuste dos dados/       # Consolidação e ajuste dos dados
    └── Script modelo/          # Desenvolvimento do modelo
```

## Configuração

Se você clonou o repositório, crie o config a partir do exemplo:

```bash
cp config.example.yaml config.yaml
```

Edite **`config.yaml`** e ajuste os caminhos para os seus dados (dados e modelos ficam locais; não são commitados):

- **`paths.unscheduled_all`**: pasta com arquivos Excel de Unscheduled (formato antigo).
- **`paths.unscheduled_2021`**: pasta com arquivos Excel de Unscheduled (formato 2021).
- **`paths.utilization_dir`**: pasta com CSVs de utilização (Dep. Date, A/C, Hours, Cycles, TAH, TAC).
- **`paths.data_processed`**: onde serão salvos os CSVs intermediários e o dataset final.
- **`paths.models_dir`**: onde serão salvos o modelo e os scalers.

Se os dados estiverem em outro lugar (ex.: OneDrive), use caminhos absolutos ou relativos ao `project_root`.

## Pipeline de dados

Gera o arquivo **`dataset_uti_vs_hh_semanal.csv`** (colunas: `date`, `acft`, `sum_daily_hours`, `age_fleet`, `Cycles`, `sum_uti_mensal`, `HH`).

1. Instale as dependências:  
   `pip install -r requirements.txt`
2. Coloque os dados brutos nas pastas configuradas em `config.yaml` (ou aponte as chaves para as pastas corretas).
3. Na pasta **TCC**, execute:

   ```bash
   python run_data_pipeline.py
   ```

   Opcional: `python run_data_pipeline.py --config config.yaml`

   Se já tiver `bd_utilização_agrupado.csv` e `bd_utl_tah.csv` em `data/processed`, pode usar `--skip-utilization` para não reprocessar a utilização.

## Treino do modelo

Treina duas variantes (4 features e 5 features), salva modelo, scalers e metadados em **`models/`**.

1. Gere o dataset com a pipeline acima (ou use um `dataset_uti_vs_hh_semanal.csv` existente).
2. Execute:

   ```bash
   python train.py
   ```

   Ou com dataset e config explícitos:

   ```bash
   python train.py --config config.yaml --dataset data/processed/dataset_uti_vs_hh_semanal.csv
   ```

Saídas em **`models/`**:

- `model_hh_semanal_4features.keras` / `model_hh_semanal_5features.keras`
- `scaler_X_4features.joblib`, `scaler_y_4features.joblib` (e idem para 5features)
- `model_metadata.json` (data do treino, métricas MAE/RMSE/R2, paths dos artefatos)

## Colocar o modelo em produção (front simples)

Depois de treinar (`python train.py`), suba a API e o frontend:

```bash
python app.py
```

Acesse **http://127.0.0.1:5000** no navegador. Na página você informa as 5 features (acft, sum_daily_hours, Cycles, sum_uti_mensal, age_fleet) e clica em **Prever HH** para ver a previsão.

- **API**: `POST /api/predict` com JSON `{"acft": 260, "sum_daily_hours": 2200, "Cycles": 1500, "sum_uti_mensal": 9000, "age_fleet": 10000000}` → resposta `{"HH": 850.1234, ...}`.
- **Info**: `GET /api/info` retorna variante e lista de features.

## Uso do modelo em produção (programático)

- Carregar o modelo: `tf.keras.models.load_model("models/model_hh_semanal_5features.keras")`.
- Carregar os scalers: `joblib.load("models/scaler_X_5features.joblib")` e idem para `scaler_y`.
- Para cada amostra: aplicar **o mesmo pré-processamento** (apenas as features treinadas, na mesma ordem) e `scaler_X.transform(X)` antes de `model.predict()`; depois `scaler_y.inverse_transform(pred)` para obter HH na escala original.

## Pré-produção e MLOps

O arquivo **`PLANO_PRE_PROD_E_MLOPS.md`** descreve o plano completo: o que fazer antes de produção, como operar em produção e como analisar e evoluir o modelo via MLOps (métricas, drift, retreinamento).
