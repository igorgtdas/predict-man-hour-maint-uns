# Plano: Pré-Produção, Produção e MLOps — TCC Previsão HH (Itens Não Programados)

Este documento descreve o que fazer **antes de colocar em produção**, como **operar em produção** e como **analisar e evoluir o modelo via MLOps**.

---

## Visão geral do projeto (estado atual)

- **Objetivo:** Previsão de HH (Homem-Hora) de itens não programados em manutenção de aeronaves.
- **Features:** `acft`, `sum_daily_hours`, `age_fleet`, `Cycles`, `sum_uti_mensal`.
- **Target:** `HH` (somatória de mão de obra para itens não programados).
- **Modelo:** Rede neural (TensorFlow/Keras), base semanal.
- **Dados:** Events Unscheduled (Excel) + Aircraft utilization (CSV) → consolidados em `dataset_uti_vs_hh_semanal.csv`.

**Gaps identificados:** pipeline de dados em notebooks com caminhos fixos; modelo não persistido; sem testes automatizados; sem versionamento; sem monitoramento.

---

# Parte 1 — Antes de colocar em produção

## 1.1 Pipeline de ajuste dos dados

### 1.1.1 Objetivo
Transformar o fluxo atual (notebooks manuais com caminhos fixos) em uma **pipeline reproduzível e configurável**.

### 1.1.2 O que fazer

| Etapa | Ação | Detalhes |
|-------|------|----------|
| **Configuração** | Centralizar caminhos e parâmetros | Criar arquivo de config (ex.: `config.yaml` ou `.env`) com: pastas de entrada (Events_Unscheduled, Aircraft utilization), pasta de saída, encoding, colunas obrigatórias. Remover caminhos hardcoded dos notebooks/scripts. |
| **Modularização** | Quebrar o pipeline em etapas reutilizáveis | 1) **Ingestão:** ler Excel (Unscheduled) + CSV (Utilization). 2) **Limpeza Unscheduled:** filtrar PILOT/CABIN, tratar HH (decimal), normalizar nomes de colunas. 3) **Agregação HH:** agrupar por período (dia/semana). 4) **Processamento Utilization:** consolidar CSVs, agrupar por data/frota. 5) **Join e feature engineering:** unir HH + utilização, gerar `date`, `acft`, `sum_daily_hours`, `age_fleet`, `Cycles`, `sum_uti_mensal`, `HH`. 6) **Saída:** escrever `dataset_uti_vs_hh_semanal.csv` (e opcional diário). |
| **Scripts ou DAG** | Automatizar a execução | Converter as etapas em scripts Python (ex.: `scripts/ingest_unscheduled.py`, `scripts/process_utilization.py`, `scripts/build_dataset.py`) ou em um único pipeline orquestrado (ex.: um script `run_pipeline.py` que chama as funções na ordem). Para agendamento futuro: cron, Task Scheduler ou (em prod) Airflow/Prefect. |
| **Validação dos dados** | Garantir qualidade na saída | Após gerar o dataset: checar schema (colunas e tipos), faixas esperadas (ex.: HH > 0, datas contínuas), ausência de nulos nas colunas usadas no modelo. Opcional: usar Great Expectations ou asserts em Python. |
| **Idempotência e datas** | Evitar sobrescrever acidentalmente | Definir convenção de nomes (ex.: `dataset_uti_vs_hh_semanal_YYYYMMDD.csv`) ou pasta “output” com data no nome; ou versionar no mesmo nome e manter backup da última execução. |

### 1.1.3 Entregáveis sugeridos
- `config.yaml` (ou `.env`) com paths e parâmetros.
- Scripts Python modulares na pasta `pipeline/` ou `scripts/`.
- Um script principal, ex.: `python run_data_pipeline.py`, que gera o dataset final.
- (Opcional) `requirements.txt` com pandas, openpyxl, pyyaml, etc.

---

## 1.2 Modelo e treinamento

### 1.2.1 Persistência do modelo
- **Salvar modelo treinado:** usar `model.save("caminho/modelo_hh_semanal.keras")` (ou `.h5`) após o treino.
- **Salvar pré-processamento:** salvar escaler (ex.: StandardScaler/MinMaxScaler) com `joblib` ou `pickle` para usar as mesmas transformações em produção.
- **Documentar versão:** anotar em um arquivo (ex.: `model_metadata.json`) data do treino, versão do dataset, métricas (MAE, RMSE, etc.) e hiperparâmetros (units, layers, epochs).

### 1.2.2 Reproductibilidade
- Fixar seeds: `np.random.seed`, `tf.random.set_seed`.
- Registrar versões de bibliotecas: `requirements.txt` com tensorflow, pandas, numpy, scikit-learn, etc.
- Preferir um script de treino (ex.: `train.py`) que lê config e dataset e gera modelo + metadados, em vez de depender só de notebook.

### 1.2.3 Validação do modelo
- Separar claramente treino/validação/teste (ou treino/validação com período fixo no tempo).
- Registrar métricas em arquivo ou planilha para comparar versões (útil para MLOps depois).

---

## 1.3 Código e ambiente

- **Requirements:** criar `requirements.txt` com todas as dependências e versões usadas (pandas, numpy, tensorflow, openpyxl, seaborn, matplotlib, scikit-learn, etc.).
- **README:** descrever objetivo do projeto, estrutura de pastas, como rodar a pipeline de dados, como treinar o modelo e onde estão os artefatos (dataset, modelo).
- **Estrutura sugerida:** separar pastas como `data/` (raw, processed), `models/` (modelo + scaler + metadata), `pipeline/` ou `scripts/`, `notebooks/` (análises e experimentos).

---

## 1.4 Checklist pré-produção

- [ ] Pipeline de dados configurável (config + scripts), sem caminhos hardcoded.
- [ ] Pipeline gera dataset final de forma reproduzível e com validação básica.
- [ ] Modelo e scaler salvos; metadados do treino registrados.
- [ ] Treino reproduzível (seeds, requirements, script de treino).
- [ ] `requirements.txt` e README atualizados.
- [ ] (Opcional) Testes unitários para funções críticas (ex.: agregação, join).

---

# Parte 2 — Colocando em produção

## 2.1 Forma de uso do modelo

- **Batch:** script que lê o dataset mais recente (ou dados da semana), aplica scaler e modelo e gera previsões (ex.: CSV ou tabela).
- **API (opcional):** serviço REST que recebe features e retorna HH previsto; útil se alguém for consumir sob demanda.

## 2.2 O que garantir

- Usar **exatamente** o mesmo pré-processamento do treino (mesmo scaler, mesmas colunas e ordem).
- Carregar modelo com `tf.keras.models.load_model("caminho/modelo.keras")`.
- Versionar o artefato de modelo (nome do arquivo ou registro em tabela com data/versão).

---

# Parte 3 — Analisar e operar via MLOps

## 3.1 Monitoramento em produção

| O que monitorar | Como | Objetivo |
|-----------------|------|----------|
| **Performance do modelo** | Comparar HH previsto vs realizado (por semana/mês) | Detectar degradação (MAE, RMSE, MAPE aumentando). |
| **Drift de dados** | Estatísticas das features em prod vs treino (média, desvio, distribuição) | Ver se os dados de entrada mudaram (ex.: frota menor, utilização diferente). |
| **Disponibilidade** | Se o job de previsão rodou e gerou saída | Alertas se a pipeline ou o modelo falhar. |

## 3.2 Métricas sugeridas para acompanhar

- **Erro:** MAE, RMSE ou MAPE entre HH previsto e HH realizado (em janelas semanais/mensais).
- **Drift:** diferença de média/desvio das features (ex.: `acft`, `sum_daily_hours`) entre base de treino e dados recentes; ou uso de bibliotecas (evidently, alibi_detect) para drift.
- **Volume:** número de registros por semana; quedas podem indicar problema na coleta.

## 3.3 Onde registrar (prática simples)

- **Planilha ou CSV:** uma linha por execução (data, MAE, RMSE, comentário).
- **Ferramentas:** se quiser evoluir, considerar MLflow (métricas + versão de modelo), Weights & Biases ou mesmo um banco simples (SQLite) com tabela de métricas.

## 3.4 Retreinamento

- **Quando:** agendado (ex.: trimestral) ou quando métricas piorarem (ex.: MAE sobe X% em 2 meses).
- **Como:** rodar de novo a pipeline de dados (com dados atualizados), rodar o script de treino, validar métricas e, se melhores, substituir o modelo em produção e registrar a nova versão.

## 3.5 Análise contínua (MLOps)

- Revisar periodicamente: gráficos de previsão vs realizado; evolução de MAE/RMSE no tempo; alertas de drift.
- Documentar decisões: “modelo X substituído em DD/MM/AAAA por causa de drift em sum_daily_hours”.
- Manter um “modelo em produção” bem identificado (nome do arquivo ou registro em config) para rollback se necessário.

---

# Resumo da ordem sugerida

1. **Pipeline de dados:** config + scripts modulares + validação + script único que gera o dataset.
2. **Modelo:** salvar modelo + scaler + metadados; script de treino reproduzível; requirements e README.
3. **Produção:** definir uso (batch ou API); garantir mesmo pré-processamento e modelo versionado.
4. **MLOps:** métricas de erro e drift; registro em planilha ou ferramenta; política de retreinamento e análise contínua.

Se quiser, na próxima etapa podemos detalhar um exemplo de `config.yaml`, a lista de scripts da pipeline e um esboço de `train.py` com save do modelo e do scaler.
