# TCC — Previsão de HH (itens não programados)

Projeto de previsão de **Homem-Hora (HH)** de itens não programados em manutenção de aeronaves **Boeing 737NG**, com base na utilização da frota. Desenvolvido no contexto de TCC/MBA, usando dados reais de uma **empresa de aviação civil**. O modelo em produção é uma **rede neural** (TensorFlow/Keras) treinada sobre dados agregados por semana.

---

## Contexto e origem dos dados

- **Problema de negócio:** estimar a demanda de mão de obra (HH) para **itens não programados** em manutenção da frota, para apoiar planejamento e capacidade.
- **Origem dos dados:** bases internas da **empresa de aviação civil** (sigilosas):
  - **Events Unscheduled** — planilhas Excel com itens de manutenção não programada (incluindo HH por evento, aeronave, data).
  - **Aircraft utilization** — CSVs de utilização da frota (data, aeronave, horas, ciclos, TAH, TAC).
- **Sigilo:** dados e modelos treinados **não** são versionados no repositório. O código e a documentação são públicos; quem quiser **só ver o modelo funcionando** pode usar um modelo pré-treinado (pasta `models/`) sem ter acesso aos dados. Ver **`GITHUB.md`** para subir o projeto sem expor dados.

---

## Como o modelo foi construído (do dado bruto ao app)

### 1. Dados brutos

- **Unscheduled:** vários Excel (formatos antigo e 2021) com eventos de manutenção não programada e HH.
- **Utilization:** dezenas de CSVs com colunas como Dep. Date, A/C, Hours, Cycles, TAH, TAC.

### 2. Pipeline de dados (reproduzível)

O pipeline transforma os dados brutos em um **dataset único por semana**, pronto para o modelo:

| Etapa | O que faz |
|-------|-----------|
| **Ingestão** | Lê todos os Excel (Unscheduled) e CSVs (Utilization). |
| **Processamento Unscheduled** | Filtra (ex.: PILOT/CABIN), trata HH em decimal, normaliza colunas, agrupa por data/aeronave. |
| **Processamento Utilization** | Consolida CSVs, agrega por data e aeronave (horas, ciclos, TAH). |
| **Join e agregação** | Junta HH com utilização por chave (data + aeronave); agrega em **base semanal** e calcula utilização mensal. |
| **Validação** | Checa schema, faixas e nulos no dataset final. |

**Saída:** arquivo **`dataset_uti_vs_hh_semanal.csv`** com colunas: `date`, `acft`, `sum_daily_hours`, `age_fleet`, `Cycles`, `sum_uti_mensal`, `HH`.

### 3. Features e target

- **Target:** `HH` (soma de Homem-Hora de itens não programados na semana).
- **Variante 4 features:** `acft`, `sum_daily_hours`, `Cycles`, `sum_uti_mensal`.
- **Variante 5 features (usada no app):** as 4 acima + `age_fleet` (idade da frota, ex.: TAH).

### 4. Arquitetura e treino

- **Modelo:** rede neural (MLP) com **2 camadas densas** (100–100 unidades, ReLU) e saída linear.
- **Pré-processamento:** `MinMaxScaler` em X e em y (inverse_transform na previsão).
- **Treino:** divisão treino/teste (ex.: 75/25), validação 20%, otimizador Adam, loss MSE. Seeds fixos para reprodutibilidade.
- **Artefatos salvos:** modelo `.keras`, scalers `.joblib`, `model_metadata.json` (métricas MAE, RMSE, R²). Versionamento opcional por pasta (ex.: `models/1.0.0/`) e `registry.json` (MLOps).

### 5. App (produção / demonstração)

- **API Flask** carrega o modelo (por `config.yaml` ou, na ausência, direto da pasta `models/`).
- **Frontend** em `app/index.html`: formulário com as 5 entradas e botão **Prever HH**; exibe a previsão e breve descrição das features.

---

## Estrutura do projeto

```
TCC/
├── config.yaml / config.example.yaml   # Configuração (caminhos, mlops)
├── run_data_pipeline.py               # Roda a pipeline de dados
├── train.py                            # Treino do modelo (4 e 5 features)
├── app.py                              # API + frontend (Flask)
├── app/index.html                      # Página do formulário de previsão
├── rodar_app.bat                       # [Windows] Rodar o app de forma lúdica (2 cliques)
├── requirements.txt
├── pipeline/                           # Módulos da pipeline (ingestão, processamento, validação)
├── data/
│   ├── raw/                            # Dados brutos (Unscheduled, Utilization)
│   └── processed/                      # dataset_uti_vs_hh_semanal.csv e intermediários
├── models/                             # Modelos treinados, scalers, registry (opcional)
├── notebooks/                          # Referência (ajuste dos dados, script do modelo)
├── COMO_TESTAR_SEM_TREINO.md           # Guia: só ver o modelo sem dados/treino
├── PLANO_PRE_PROD_E_MLOPS.md
└── MLOPS.md
```

---

## Como rodar (quem tem dados e quer treinar)

1. **Config:** copie `config.example.yaml` para `config.yaml` e ajuste os caminhos das pastas de dados e de modelos.
2. **Pipeline:** `pip install -r requirements.txt` e depois `python run_data_pipeline.py` (gera o dataset semanal).
3. **Treino:** `python train.py` (ou `python train.py --version 1.0.0`). Saídas em `models/` (ou `models/<versão>/`).
4. **App:** `python app.py` e acesse **http://127.0.0.1:5000**.

Detalhes de pipeline (flags, skip-utilization) e treino (--config, --dataset) estão nas seções abaixo e em **`PLANO_PRE_PROD_E_MLOPS.md`**.

---

## Rodar de forma lúdica (só ver o modelo funcionando)

Para quem **não tem os dados**, **não vai treinar** e **não quer config**: basta ter o **código do projeto** e a pasta **`models/`** com o modelo já treinado (arquivos `.keras` e `.joblib` da variante 5 features). Nada de `config.yaml`, Excel ou pipeline.

- **Windows (recomendado):** coloque a pasta `models/` dentro do projeto e dê **dois cliques** em **`rodar_app.bat`**. O script cria o ambiente virtual (se precisar), instala as dependências, verifica se o modelo existe e abre o navegador em **http://127.0.0.1:5000** para você testar o formulário.
- **Manual:** veja o passo a passo completo em **`COMO_TESTAR_SEM_TREINO.md`** (inclui comandos para criar venv, instalar deps e rodar `python app.py`).

Resumo: **só é preciso** a pasta `models/` (recebida de quem mantém o projeto ou de um Release) + **`rodar_app.bat`** ou os comandos do guia. Assim qualquer pessoa pode **experimentar o modelo na prática** sem acesso aos dados nem ao treino.

---

## Configuração (quem vai rodar pipeline e treino)

Se você clonou o repositório e vai usar dados locais:

```bash
cp config.example.yaml config.yaml
```

Edite **`config.yaml`** e ajuste os caminhos:

- **`paths.unscheduled_all`** / **`paths.unscheduled_2021`**: pastas com Excel de Unscheduled.
- **`paths.utilization_dir`**: pasta com CSVs de utilização.
- **`paths.data_processed`**: saída da pipeline (dataset e intermediários).
- **`paths.models_dir`**: onde serão salvos o modelo e os scalers.
- **`mlops.production_version`**: `"latest"` ou uma versão fixa (ex.: `"1.0.0"`) para o app.

---

## Pipeline de dados (detalhes)

1. Instale as dependências: `pip install -r requirements.txt`.
2. Coloque os dados brutos nas pastas indicadas no `config.yaml`.
3. Na pasta **TCC**: `python run_data_pipeline.py` (ou `--config config.yaml`).
4. Opcional: se já tiver arquivos de utilização processados, use `--skip-utilization` para pular essa etapa.

O resultado é o **`dataset_uti_vs_hh_semanal.csv`** em `data/processed/`.

---

## Treino do modelo (detalhes)

1. Gere o dataset com a pipeline acima (ou use um `dataset_uti_vs_hh_semanal.csv` existente).
2. Execute: `python train.py` ou, com opções:  
   `python train.py --config config.yaml --dataset data/processed/dataset_uti_vs_hh_semanal.csv --version 1.0.0`

Saídas em **`models/`** (ou **`models/<versão>/`**):

- `model_hh_semanal_4features.keras` / `model_hh_semanal_5features.keras`
- `scaler_X_*` e `scaler_y_*` (joblib)
- `model_metadata.json` (data do treino, métricas, paths)

---

## App em produção / demonstração

Depois de treinar (ou com a pasta `models/` pronta para modo lúdico):

```bash
python app.py
```

Acesse **http://127.0.0.1:5000**. No formulário você informa as 5 features (acft, sum_daily_hours, Cycles, sum_uti_mensal, age_fleet) e clica em **Prever HH** para ver a previsão.

- **API:** `POST /api/predict` com JSON das 5 features → resposta com `HH` previsto.
- **Info:** `GET /api/info` retorna variante e lista de features.

---

## Uso programático do modelo

- Carregar: `tf.keras.models.load_model("models/model_hh_semanal_5features.keras")` e os scalers com `joblib.load(...)`.
- Para cada amostra: mesmo pré-processamento (features na mesma ordem), `scaler_X.transform(X)`, `model.predict()`, depois `scaler_y.inverse_transform(pred)` para obter HH na escala original.

---

## Documentação adicional

- **`COMO_TESTAR_SEM_TREINO.md`** — Passo a passo para rodar só o app com modelo pré-treinado (sem dados nem config).
- **`PLANO_PRE_PROD_E_MLOPS.md`** — Plano de pré-produção, produção e MLOps.
- **`MLOPS.md`** — Versionamento do modelo, registry e uso pela API.
- **`GITHUB.md`** — Como subir o projeto no GitHub sem expor dados nem modelos.
