# Subir o projeto no GitHub (dados sigilosos)

Este guia explica o que **não** vai para o repositório e como deixar apenas o **código** e o **acesso ao modelo via front-end** disponíveis.

---

## O que NÃO é versionado (fica sigiloso/local)

- **Toda a pasta `data/`** — bases brutas e processadas (utilização, itens não programados, dataset de treino).
- **Arquivos `.csv`, `.xlsx`, `.xls`** — em qualquer pasta do projeto.
- **Pasta `models/`** — modelos treinados (`.keras`), scalers (`.joblib`) e `registry.json`.
- **Arquivo `config.yaml`** — para não expor caminhos internos da sua máquina.

Assim, **a base de dados de treinamento e o modelo em si não entram no GitHub**. Quem clona o repositório vê só o código.

---

## O que VAI no repositório

- Código fonte: `pipeline/`, `app.py`, `train.py`, `run_data_pipeline.py`, `app/index.html`.
- Configuração de exemplo: `config.example.yaml`.
- Documentação: `README.md`, `PLANO_PRE_PROD_E_MLOPS.md`, `MLOPS.md`, `GITHUB.md`.
- Ambiente: `requirements.txt`, `.gitignore`.
- Pasta `models/` vazia (apenas `.gitkeep`) para a estrutura existir ao clonar.
- Notebooks em `notebooks/` (recomendado: limpar outputs antes do commit para não expor dados — Jupyter: Cell → All Output → Clear).

---

## Passos para subir no GitHub

### 1. Garantir que não há dados ou modelo no commit

```bash
cd "TCC - MBA USP/TCC"
git status
```

Confirme que **não** aparecem `data/`, `models/*.keras`, `models/*.joblib`, `*.csv`, `config.yaml`. Se aparecerem, eles já estão no `.gitignore`; não faça `git add` nesses arquivos.

### 2. Config local (só na sua máquina)

- Use `config.yaml` na sua máquina (copie de `config.example.yaml` se for a primeira vez).
- **Não** dê `git add config.yaml`. O `.gitignore` já evita isso.

### 3. Criar o repositório no GitHub

1. No GitHub: **New repository** (pode ser **Private**).
2. **Não** marque "Add a README" se você já tiver um na pasta.
3. Anote a URL do repositório (ex.: `https://github.com/seu-usuario/tcc-previsao-hh.git`).

### 4. Inicializar Git e fazer o primeiro push

```bash
cd "TCC - MBA USP/TCC"
git init
git add .
git status   # conferir: sem data/, sem models/*.keras, sem config.yaml
git commit -m "Código do projeto TCC - Previsão HH (sem dados nem modelo)"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/SEU-REPO.git
git push -u origin main
```

Substitua `SEU-USUARIO/SEU-REPO` pela URL do seu repositório.

---

## O que o usuário final acessa

- **Pelo GitHub:** só o **código** (e a documentação). Nenhum dado de treino e nenhum arquivo de modelo.
- **Em produção:** você sobe o **app** (por exemplo em um servidor, Render, Railway, etc.) com o **modelo** que você treinou (fora do GitHub). O usuário acessa apenas o **front-end** (formulário de previsão) e recebe a resposta do modelo via API, sem ver base de dados nem arquivos de modelo.

Resumo: **dados e modelo ficam sigilosos**; no GitHub fica só o projeto; o acesso ao modelo é só via front-end na sua aplicação em produção.
