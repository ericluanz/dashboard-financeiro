# 🚀 Como fazer o Deploy do Dashboard

Este guia explica como colocar o dashboard online de forma **gratuita**,
para que qualquer pessoa com o link possa acessar.

---

## Pré-requisitos

- Conta no **GitHub** (você já tem ✅)
- Conta no **Streamlit Community Cloud** (gratuita)
- **Git** instalado no seu computador

---

## Passo 1 — Criar um repositório no GitHub

1. Acesse [github.com](https://github.com) e clique em **"New repository"**
2. Dê um nome, ex.: `dashboard-financeiro`
3. Deixe como **Public**
4. Clique em **"Create repository"**

---

## Passo 2 — Enviar os arquivos para o GitHub

Abra o terminal (Prompt de Comando ou PowerShell) na pasta `dashboard/` e execute:

```bash
git init
git add .
git commit -m "Dashboard financeiro inicial"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/dashboard-financeiro.git
git push -u origin main
```

> ⚠️ Substitua `SEU_USUARIO` pelo seu usuário do GitHub.

---

## Passo 3 — Criar conta no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Clique em **"Sign up"** e entre com sua conta do GitHub
3. Autorize o acesso ao GitHub quando solicitado

---

## Passo 4 — Fazer o Deploy

1. No Streamlit Cloud, clique em **"New app"**
2. Selecione o repositório: `dashboard-financeiro`
3. Branch: `main`
4. Main file path: `app.py`
5. Clique em **"Deploy!"**

Aguarde alguns minutos. O Streamlit vai instalar as dependências automaticamente
usando o `requirements.txt`.

---

## Resultado

Você receberá uma URL pública no formato:

```
https://SEU_USUARIO-dashboard-financeiro-app-XXXX.streamlit.app
```

Compartilhe esse link com qualquer pessoa! O dashboard ficará disponível 24/7
(enquanto houver acesso, o Streamlit Cloud mantém ativo).

---

## Atualizações futuras

Sempre que quiser atualizar o dashboard:

```bash
git add .
git commit -m "Atualização: descrição da mudança"
git push
```

O Streamlit Cloud detecta automaticamente e faz o redeploy.

---

## Estrutura dos arquivos

```
dashboard/
├── app.py                  ← Página inicial (Home)
├── pages/
│   ├── 1_Acoes_BR.py       ← Dashboard Ações BR
│   ├── 2_Acoes_Globais.py  ← Dashboard Ações Globais
│   ├── 3_Criptos.py        ← Dashboard Criptomoedas
│   └── 4_FIIs.py           ← Dashboard FIIs
├── utils/
│   ├── data_fetchers.py    ← Busca de dados e indicadores
│   └── charts.py           ← Criação de gráficos
├── requirements.txt        ← Dependências Python
└── .streamlit/
    └── config.toml         ← Tema e configurações
```

---

## Fontes de dados

| Mercado          | Fonte         | Atualização  |
|------------------|---------------|--------------|
| Ações BR         | Yahoo Finance | A cada 5 min |
| Ações Globais    | Yahoo Finance | A cada 5 min |
| FIIs             | Yahoo Finance | A cada 5 min |
| Criptomoedas     | Yahoo Finance | A cada 1 min |
| Fear & Greed     | Alternative.me| A cada 1 min |

---

## Dúvidas?

Em caso de dúvidas, abra uma issue no seu repositório do GitHub ou consulte a
documentação em [docs.streamlit.io](https://docs.streamlit.io).
