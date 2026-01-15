
# 🤖 Agente de IA - Faculdade Nova Aurora

Este projeto é uma **adaptação de um sistema real em produção** que combina **Inteligência Artificial**, **análises automatizadas** e **visualizações interativas** para facilitar a tomada de decisão no setor educacional.

---

## 🚀 Visão Geral

O projeto consiste em um **painel interativo com IA integrada**, desenvolvido em **Streamlit**, com dados processados via **ETL em Python**, armazenados no **Google BigQuery** e integrados ao **Looker Studio** para visualizações avançadas.

Apesar de conter uma base fictícia (gerada com `faker`), a estrutura e funcionalidades replicam fielmente o projeto real.

---

## 🧠 Funcionalidades Principais

- 📊 **Dashboard com os principais KPIs** de inscrições e matrículas.
- 🤔 **Seção de perguntas frequentes** com análises prontas para facilitar a navegação.
- 🗣️ **Campo de pergunta livre** com interpretação em linguagem natural e análises automáticas via ChatGPT.
- 📈 **Geração de resumos inteligentes** com gráficos e texto explicativo sobre dados de inscrições/matrículas.
- 📂 **Exportação personalizada**: selecione filtros, colunas específicas e exporte os dados em `.xlsx`.
- 📜 **Histórico de interações**: todas as perguntas e respostas ficam salvas para posterior análise.
- 📎 **Link direto para dashboards complementares** desenvolvidos em Looker Studio.
- 🌐 **Workflow no GitHub Actions** que mantém o app sempre ativo.

---

## Visão do App

<img width="1904" height="874" alt="image" src="https://github.com/user-attachments/assets/3e39cc70-7dc3-41e9-afe4-68f58397e892" />








## 🧩 Arquitetura

```plaintext
Usuário
   │
   ▼
Streamlit App (Interface com IA)
   │
   ├──> Perguntas frequentes (Consultas SQL pré-definidas)
   ├──> Perguntas livres (Integração com ChatGPT → SQL dinâmico → BigQuery)
   ├──> Resumos analíticos com IA
   └──> Exportações e histórico
        │
        ▼
Google BigQuery ← ETL em Python (Fake Data com Faker)
   │
   └──> Dashboards no Looker Studio
```

---

## 🛠️ Tecnologias Utilizadas

- **Python** e **Streamlit**
- **Google BigQuery**
- **OpenAI (ChatGPT API)**
- **Looker Studio**
- **Faker** (para geração de dados)
- **Plotly** (gráficos interativos)
- **Pandas / NumPy**
- **GitHub Actions** (workflow para manter app online)

---

## 🧪 Como Rodar Localmente

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/agente-ia-faculdade-fuzati.git
cd agente-ia-faculdade-fuzati

# Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Execute o app
streamlit run app.py
```

> ⚠️ Certifique-se de configurar suas **credenciais do Google Cloud** e **API Key do OpenAI** no `.env` ou como variáveis de ambiente.

---

## ☁️ Observações

- O ETL nesta versão é **simplificado e executado localmente**, apenas como referência. No projeto original, ele é mais complexo e roda periodicamente em um **servidor privado na nuvem**.
- A base de dados é **fictícia**, mas simula o comportamento real do sistema.
- O foco está nas **funcionalidades do agente de IA** e **interface do dashboard**.

---

## 📬 Contato

Em caso de dúvidas ou sugestões, entre em contato com o mantenedor do projeto:

- [LinkedIn](https://www.linkedin.com/in/matheus-fuzati-de-carvalho-6a80a11a3/)
- [Email](mailto:fuzatimatheus@gmail.com)

---
