
# 🤖 Agente de IA - Faculdade Nova Aurora

Este projeto é uma **adaptação de um sistema real em produção** que combina **Inteligência Artificial**, **análises automatizadas** e **visualizações interativas** para facilitar a tomada de decisão no setor educacional.

---

## 🚀 Visão Geral

O projeto consiste em um **painel interativo com IA integrada**, desenvolvido em **Streamlit**, com dados processados via **ETL em Python**, armazenados no **Google BigQuery** e integrados ao **Looker Studio** para visualizações avançadas.

Apesar de conter uma base fictícia (gerada com `faker`), a estrutura e funcionalidades replicam fielmente o projeto real.

---

## 🧠 Funcionalidades Principais

- 📎 **Link direto para dashboards complementares** desenvolvidos em Looker Studio.
- 🌐 **Workflow no GitHub Actions** que mantém o app sempre ativo.

---

## Visão do App

<img width="1889" height="795" alt="image" src="https://github.com/user-attachments/assets/1df57516-0483-49fc-9aa5-983e0ead32ac" />


- 🤔 **Seção de perguntas frequentes** com análises prontas para facilitar a navegação.

<img width="1883" height="677" alt="image" src="https://github.com/user-attachments/assets/5800d99f-ab02-402b-846a-2e61732503ec" />


- 🗣️ **Campo de pergunta livre** com interpretação em linguagem natural e análises automáticas via ChatGPT.

<img width="1888" height="745" alt="image" src="https://github.com/user-attachments/assets/db77669b-3dda-4309-8766-d7e3c9196123" />


- 📈 **Geração de resumos inteligentes** com gráficos e texto explicativo sobre dados de inscrições/matrículas.

<img width="1897" height="892" alt="image" src="https://github.com/user-attachments/assets/e122bbde-046b-499f-b3f4-77d73ee72e22" />

<img width="1896" height="815" alt="image" src="https://github.com/user-attachments/assets/8f00d22d-a3c5-4e72-863a-dae7dedc7cb8" />


- 📂 **Exportação personalizada**: selecione filtros, colunas específicas e exporte os dados em `.xlsx`.

<img width="1912" height="864" alt="image" src="https://github.com/user-attachments/assets/178dc380-d416-40ee-a225-8313e1763c27" />

<img width="1895" height="884" alt="image" src="https://github.com/user-attachments/assets/f4cc6696-60e3-4f20-92ff-f6d44f399576" />


- 📜 **Histórico de interações**: todas as perguntas e respostas ficam salvas para posterior análise.

<img width="1901" height="954" alt="image" src="https://github.com/user-attachments/assets/085648ed-e127-4126-bb21-0131dc3c0ab7" />


- 📊 **Dashboard com os principais KPIs** de inscrições e matrículas.

<img width="1217" height="750" alt="image" src="https://github.com/user-attachments/assets/f8623d71-7234-42f9-97a1-adb2b09dbc00" />

<img width="1249" height="789" alt="image" src="https://github.com/user-attachments/assets/8293e94f-5558-4bff-91f5-af7a45e1a446" />

---

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

## 📬 Contato

Em caso de dúvidas ou sugestões, entre em contato com o mantenedor do projeto:

- [LinkedIn](https://www.linkedin.com/in/matheus-fuzati-de-carvalho-6a80a11a3/)
- [Email](mailto:fuzatimatheus@gmail.com)

---
