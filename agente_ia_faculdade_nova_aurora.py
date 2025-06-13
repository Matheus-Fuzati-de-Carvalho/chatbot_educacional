import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
from google.oauth2 import service_account
from openai import OpenAI
import datetime
import re
import os
import base64

# --- CONFIGURAÇÕES INICIAIS ---

st.set_page_config(page_title="🤖 Agente de IA - Faculdade Nova Aurora", layout="wide")


st.markdown("""
<style>
/* Cor dos chips de seleção múltipla */
span[data-baseweb="tag"] {
    background-color: #0a2540 !important;   /* azul marinho */
    color: white !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    padding: 4px 10px !important;
}

/* Cor de fundo geral */
[data-testid="stAppViewContainer"] {
    background-color: #f7f6f1;
    font-family: 'Segoe UI', sans-serif;
}

/* Título da página */
h1 {
    color: #0a2540;
}

/* Subtítulos */
h3 {
    color: #1f3b6e;
    margin-top: 1.5rem;
}

/* Caixa de texto (text input, selectbox, etc) */
input, textarea, select {
    background-color: #ffffff !important;
    border: 1px solid #cbd6e2 !important;
    border-radius: 6px !important;
    color: #0a2540 !important;
}

/* Botões */
button {
    background-color: #0a66c2 !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 600 !important;
}

/* Botões ao passar o mouse */
button:hover {
    background-color: #084d9d !important;
}

/* Caixa de sucesso */
[data-testid="stAlert"] {
    background-color: #d0ebff;
    color: #084d9d;
    border-left: 5px solid #0a66c2;
}


/* Estilo dos botões "Remover" e "Limpar histórico" */
div.stButton > button {
    background-color: #0a2540 !important;   /* Fundo azul marinho */
    color: #ffffff !important;              /* Texto branco */
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    border: none !important;
}

/* Hover */
div.stButton > button:hover {
    background-color: #1b3a6b !important;   /* Azul mais claro no hover */
    color: #ffffff !important;             /* Texto branco no hover também */
}   

/* Spinner */
.css-1cpxqw2 {
    color: #0a66c2 !important;
}


/* Divider */
hr {
    border-top: 1px solid #cbd6e2;
}
</style>
""", unsafe_allow_html=True)

# Código de acesso
SECRET_CODE = "senha123"

#Credencial OPENAI
client_openai = OpenAI(api_key=st.secrets["TOKENAPIST"])

# BigQuery
creds_dict = st.secrets["google_service_account"]   # ← já é um dict
credentials = service_account.Credentials.from_service_account_info(creds_dict)
client_bigquery = bigquery.Client(
    credentials=credentials,
    project=creds_dict["project_id"]
)


class BigQueryChatbot:
    def __init__(self, credentials, project_id):
        self.client_bq = bigquery.Client(credentials=credentials, project=project_id)
        self.openai_client = client_openai

    def get_table_schema(self, dataset, table):
        colunas_autorizadas = [
            "dataInscricao", "nome", "processoSeletivo", "etapa",
            "consultor", "objecao", "cidade", "curso", "dataMatricula",
            "idade", "faixaEtaria", "origem", "status", "diaSemanaInscricao"
        ]

        try:
            schema_text = "\n".join([f"- {col}" for col in colunas_autorizadas])
            amostra = self.client_bq.query(
                f"SELECT {', '.join(colunas_autorizadas)} FROM `{dataset}.{table}` LIMIT 5"
            ).to_dataframe()
            return schema_text, amostra
        except Exception as e:
            st.error(f"Erro ao obter o esquema da tabela: {e}")
            return None, None

    def generate_sql_from_question(self, question, schema_info, dataset, table):
        prompt = f"""
    REGRAS MUITO IMPORTANTES – SIGA EXATAMENTE COMO ESCRITO:

    - Aplique o filtro: etapa = 'Matriculado' apenas quando a pergunta do usuário mencionar claramente "matrícula" ou "matriculado".
    - NÃO aplique esse filtro se a pergunta for sobre "inscrição", "inscrições", ou outras etapas.
    - Use apenas as colunas autorizadas
    - Gere APENAS a SQL, sem explicações ou comentários

    BASE DE DADOS: {dataset}.{table}

    COLUNAS PERMITIDAS:
    {schema_info}

    PERGUNTA DO USUÁRIO:
    {question}

    SQL:
    """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=300
            )
            sql_query = response.choices[0].message.content.strip()
            return re.sub(r'^```sql\s*|```\s*$', '', sql_query).strip()
        except Exception as e:
            return f"Erro ao gerar SQL: {e}"

    def executar_query_livre(self, sql):  # ORIGINAL
        try:
            with st.spinner("Buscando informações..."):
                query_job = client_bigquery.query(sql)
                df = query_job.result().to_dataframe()
            return df
        except Exception as e:
            st.error(f"Erro ao executar a consulta: {e}")
            return pd.DataFrame()  # Retorna DataFrame vazio para evitar erros posteriores



    def explain_results(self, question, sql_query, result_df):
        if isinstance(result_df, str):
            return result_df  # já é erro

        resumo_texto = result_df.head(10).to_string(index=False)
        contexto = f"""
        Pergunta original: {question}
        SQL usada: {sql_query}
        Resultados (amostra):
        {resumo_texto}
        Gere uma explicação clara e assertiva sobre os dados acima. 
        Utilize uma linguagem clara, profissional e voltada para gestores da área educacional. 
        Considere regras de negócio como: cursos com maior volume tendem a receber mais investimento; processos seletivos específicos podem impactar a etapa da inscrição; e objeções indicam barreiras na jornada Mas não fique preso a isso apenas. 
        Destaque padrões, alertas e boas oportunidades.
        Destaque os principais padrões, tendências e insights.
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": contexto}],
                temperature=0.3,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Erro na explicação com IA: {e}"


def validar_sql(sql: str) -> bool:
    """
    Verifica se a SQL gerada pela IA é segura e legível para execução no BigQuery.
    """
    sql_limpo = sql.strip().lower()

    # Impede comandos destrutivos
    proibidos = ["drop", "delete", "update", "insert", "alter", "create", "merge"]
    if any(cmd in sql_limpo for cmd in proibidos):
        return False

    # Garante que começa com SELECT
    if not sql_limpo.startswith("select"):
        return False

    # Verifica se tem ponto e vírgula no meio (evita múltiplas queries)
    if ";" in sql_limpo[:-1]:  # último pode ser tolerado
        return False

    # Garante que tenha pelo menos um FROM
    if "from" not in sql_limpo:
        return False

    return True



def executar_query(sql): # ORIGINAL
    try:
        with st.spinner("Buscando informações..."):
            query_job = client_bigquery.query(sql)
            df = query_job.result().to_dataframe()
        return df
    except Exception as e:
        st.error(f"Erro ao executar a consulta: {e}")
        return pd.DataFrame()  # Retorna DataFrame vazio para evitar erros posteriores


def gerar_resposta_openai(pergunta, resultado_query):
    try:
        with st.spinner("Gerando resposta com IA..."):
            prompt = f"""
            Pergunta: {pergunta}
            Resultado: {resultado_query.to_string(index=False)}
            Gere uma resposta clara e resumida com base nos dados acima, como se estivesse explicando para um diretor da área comercial.
            """
            response = client_openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Tratamento específico para limite de requisições
        if "quota" in str(e).lower() or "rate limit" in str(e).lower():
            st.error("Limite de requisições atingido. Por favor, tente novamente mais tarde.")
        else:
            st.error(f"Ocorreu um erro na geração da resposta: {e}")
        return "Não foi possível gerar a análise em ia no momento."


def carregar_dict_perguntas():
    df = pd.read_excel("dictPerguntasChatbot.xlsx")
    df.columns = [col.lower().strip() for col in df.columns]
    return df


# Função para enviar sugestão para BigQuery
def enviar_sugestao_para_bq(sugestao: str):
    tabela = "pessoal.sugestoes"
    linha = [{
        "sugestao": sugestao,
        "timestamp": datetime.datetime.utcnow().isoformat()  # Converte para string ISO 8601
    }]
    errors = client_bigquery.insert_rows_json(tabela, linha)
    if errors:
        raise Exception(f"Erro ao inserir no BigQuery: {errors}")
    return True


# Na função da tela, exemplo de uso:
def tela_sugestoes():
    st.subheader("💡 Envie sua sugestão de melhoria")

    sugestao = st.text_area("Digite sua sugestão aqui:")

    if st.button("Enviar sugestão"):
        if not sugestao.strip():
            st.warning("Por favor, escreva uma sugestão antes de enviar.")
        else:
            try:
                enviar_sugestao_para_bq(sugestao.strip())
                st.success("Sugestão enviada com sucesso! Obrigado pelo seu feedback.")
            except Exception as e:
                st.error(f"Erro ao enviar sugestão: {e}")


def exibir_perguntas_frequentes(dict_df, tipo):
    st.markdown(f"### ❓ Perguntas frequentes sobre {tipo}")
    opcoes = dict_df[dict_df['tipo'] == tipo]['pergunta'].tolist()
    pergunta = st.selectbox("Escolha uma pergunta:", ["Selecione..."] + opcoes, key=f"freq_{tipo}")
    if st.button("Perguntar", key=f"btn_freq_{tipo}") and pergunta != "Selecione...":
        query = dict_df.loc[dict_df['pergunta'] == pergunta, 'query'].values[0]
        df_resultado = executar_query(query)
        resposta = gerar_resposta_openai(pergunta, df_resultado)
        st.success(resposta)
        st.dataframe(df_resultado)
        adicionar_historico(pergunta, resposta)


def gerar_sql_e_resposta_livre(pergunta, tipo):
    prompt = f"""
Você é um assistente que gera queries SQL para análise dos dados da Faculdade Fuzati no BigQuery.
Baseie-se nas seguintes regras importantes:

- Use a tabela "chatbot_educacional"
- Geração da query deve ser adequada para o BigQuery.
- Explique a query em linguagem natural clara após o código.
- Gere também um texto resumo da informação que a query traria.

Pergunta: {pergunta}

Por favor, gere a saída com o formato:

SQL:
<query SQL aqui>

Resposta:
<explicação e resumo em linguagem natural>
"""
    response = client_openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente que gera SQL e explicações para análise de dados."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=600,
    )

    return response.choices[0].message.content




def adicionar_historico(pergunta, resposta):
    st.session_state['historico_perguntas'].append({"pergunta": pergunta, "resposta": resposta})


def perguntas_livres():    # NOVA SEÇÃO: PERGUNTA LIVRE COM IA
    st.subheader("💬 Pergunte livremente sobre os dados")

    pergunta_livre = st.text_input("Digite sua pergunta em linguagem natural (ex: Em quais dias da semana houveram mais inscrições?)")

    if st.button("Perguntar com IA"):
        if not pergunta_livre.strip():
            st.warning("Digite uma pergunta antes de continuar.")
        else:
            with st.spinner("🔎 Analisando sua pergunta..."):
                schema_text, _ = st.session_state.chatbot_bq.get_table_schema("pessoal", "chatbot_educacional")

                if schema_text is None:
                    st.error("❌ Erro ao obter o esquema da tabela.")
                    st.stop()

                sql_gerada = st.session_state.chatbot_bq.generate_sql_from_question(
                    pergunta_livre, schema_text, "pessoal", "chatbot_educacional"
                )

                if sql_gerada.startswith("Erro ao gerar SQL: Error code: 429"):
                    st.error(
                        "❌ Parece que seus créditos da OpenAI foram esgotados. Por favor, revise sua conta ou insira uma nova chave de API com créditos disponíveis.")
                    st.stop()

                # Detecta se a pergunta envolve matrícula
                if re.search(r"\bmatricul[áa]d?[oa]s?\b", pergunta_livre.lower()):
                    if "etapa = 'Matriculado'" not in sql_gerada:
                        if "where" in sql_gerada.lower():
                            sql_gerada = re.sub(r"(where\s+)", r"\1etapa = 'Matriculado' AND ", sql_gerada,
                                                flags=re.IGNORECASE)
                        else:
                            match = re.search(r"(from\s+[`]?\w+\.\w+[`]?)", sql_gerada, flags=re.IGNORECASE)
                            if match:
                                from_clause = match.group(1)
                                sql_gerada = sql_gerada.replace(
                                    from_clause, f"{from_clause} WHERE etapa = 'Matriculado'"
                                )
                    st.info("✅ Filtro automático aplicado: etapa = 'Matriculado'")

                # st.code(sql_gerada, language="sql")

                resultado_df = st.session_state.chatbot_bq.executar_query_livre(sql_gerada)

                if isinstance(resultado_df, pd.DataFrame):
                    st.dataframe(resultado_df)
                    explicacao = st.session_state.chatbot_bq.explain_results(
                        pergunta_livre, sql_gerada, resultado_df
                    )
                    st.markdown(f"**🧐 Análise com IA:**\n\n{explicacao}")
                    adicionar_historico(pergunta_livre, explicacao)
                else:
                    st.error(resultado_df)


def resumo(tipo):
    col, _ = st.columns([4, 1])
    with col:
        if st.checkbox(f"📊 Desejo um resumo de {tipo}.", key=f"check_{tipo}"):
            with st.container():
                st.markdown(
                    f"""
                    <div style="
                        background-color: ##29394a;
                        border-radius: 16px;
                        padding: 0.2rem;
                        border: 1px solid ##29394a;
                        ">
                    """,
                    unsafe_allow_html=True
                )

                if st.button(f"🔍 Gerar resumo dos dados de {tipo}", key=f"resumo_{tipo}"):
                    if tipo == "Inscrições":
                        tela_inscricoes(resumo=True)
                    else:
                        tela_matriculas(resumo=True)

                st.markdown("</div>", unsafe_allow_html=True)


# 1. Inicialização global do histórico (logo no início do script)
if 'historico_perguntas' not in st.session_state:
    st.session_state['historico_perguntas'] = []


# 2. Função global para adicionar perguntas e respostas ao histórico
def adicionar_historico(pergunta, resposta):
    st.session_state['historico_perguntas'].append({"pergunta": pergunta, "resposta": resposta})


# 3. Função para mostrar o histórico
def mostrar_historico():
    st.subheader("🕘 Histórico de perguntas e respostas")
    for item in reversed(st.session_state['historico_perguntas']):
        st.markdown(f"**Pergunta:** {item['pergunta']}")
        st.markdown(f"**Resposta:** {item['resposta']}")
        st.markdown("---")


def estilo_futurista_barras(fig, titulo=''):
    fig.update_traces(
        marker=dict(color='#0a2540', line=dict(width=0), opacity=0.9),
        textposition='outside',
        textfont=dict(size=12),
        width=0.6
    )
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=18, color='#0a2540'), x=0.01),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=False, title='', tickangle=0),
        yaxis=dict(showgrid=False, title=''),
        showlegend=False,
        font=dict(color='#0a2540'),
        height=400,
        margin=dict(l=40, r=20, t=60, b=40),
        bargap=0.25
    )
    return fig


def estilo_futurista_linha(fig, titulo=''):
    fig.update_traces(
        mode='lines+markers',
        marker=dict(color='#0a2540'),
        line=dict(color='#0a2540', width=3)
    )
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=18, color='#0a2540'), x=0.01),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=False, title=''),
        yaxis=dict(showgrid=False, title=''),
        showlegend=False,
        font=dict(color='#0a2540'),
        height=400,
        margin=dict(l=40, r=20, t=60, b=40)
    )
    return fig


def estilo_futurista_pizza(fig, titulo=''):
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=18, color='#0a2540'), x=0.01),
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=True,
        legend=dict(x=1, y=0.5, traceorder='normal', font=dict(color='#0a2540'))
    )
    return fig


def tela_inscricoes(resumo=False):
    df = executar_query("""
        SELECT nome, curso, etapa, turno, processoSeletivo, objecao, dataInscricao
        FROM pessoal.chatbot_educacional
        WHERE nome IS NOT NULL
    """)

    df['dataInscricao'] = pd.to_datetime(df['dataInscricao'])
    df['data'] = df['dataInscricao'].dt.date
    df['hora'] = df['dataInscricao'].dt.hour

    if resumo:
        st.session_state['df_inscricoes'] = df
        st.success("✅ Dados coletados! Prontos para visualização e análise com IA.")
        st.subheader("📊 Gráficos do resumo de inscrições")

        # 1. Processo Seletivo
        df_proc = df['processoSeletivo'].value_counts().reset_index()
        df_proc.columns = ['processoSeletivo', 'count']
        fig_proc = px.bar(df_proc, x='processoSeletivo', y='count', text='count')
        st.plotly_chart(estilo_futurista_barras(fig_proc, "Inscrições por Processo Seletivo"), use_container_width=True)

        # 2. Curso
        df_curso = df['curso'].value_counts().reset_index()
        df_curso.columns = ['curso', 'count']
        fig_curso = px.bar(df_curso, x='curso', y='count', text='count')
        st.plotly_chart(estilo_futurista_barras(fig_curso, "Inscrições por Curso"), use_container_width=True)

        # 3. Turno (pizza)
        df_turno = df[df['turno'].isin(['Diurno', 'Noturno', 'EAD'])]
        fig_turno = px.pie(df_turno, names='turno', title='', hole=0.3)
        st.plotly_chart(estilo_futurista_pizza(fig_turno, "Distribuição por Turno"), use_container_width=True)

        # 4. Etapa
        df_etapa = df['etapa'].value_counts().reset_index()
        df_etapa.columns = ['etapa', 'count']
        fig_etapa = px.bar(df_etapa, x='etapa', y='count', text='count')
        st.plotly_chart(estilo_futurista_barras(fig_etapa, "Inscrições por Etapa"), use_container_width=True)

        # 5. Objeções
        if 'objecao' in df.columns:
            df_objecao = df['objecao'].dropna().value_counts().head(10).reset_index()
            df_objecao.columns = ['objecao', 'count']
            fig_obje = px.bar(df_objecao, x='objecao', y='count', text='count')
            st.plotly_chart(estilo_futurista_barras(fig_obje, "Principais Motivos de Objeção"), use_container_width=True)

        # 6. Evolução diária
        df_data = df['data'].value_counts().sort_index().reset_index()
        df_data.columns = ['data', 'count']
        fig_dia = px.line(df_data, x='data', y='count')
        st.plotly_chart(estilo_futurista_linha(fig_dia, "Evolução das Inscrições ao Longo do Tempo"), use_container_width=True)

        # 7. Resumo com IA
        inscricoes_por_curso = df['curso'].value_counts().head(5)
        inscricoes_por_turno = df['turno'].value_counts()
        inscricoes_por_etapa = df['etapa'].value_counts()
        inscricoes_por_ps = df['processoSeletivo'].value_counts().head(3)
        inscricoes_por_motivo = df['objecao'].value_counts().head(3) if 'objecao' in df.columns else "Não disponível"

        prompt_base = f"""
        Você é um analista de dados da Faculdade Fuzati e precisa apresentar um resumo claro e estratégico para gestores da área.

        Gere um resumo analítico e assertivo sobre os dados de inscrições com base nas informações abaixo. Utilize uma linguagem clara, profissional e voltada para gestores da área educacional. Considere regras de negócio como: cursos com maior volume tendem a receber mais investimento; processos seletivos específicos podem impactar a etapa da inscrição; e objeções indicam barreiras na jornada. Destaque padrões, alertas e boas oportunidades. Os dados estão entre colchetes:

        - Por curso:\n{inscricoes_por_curso.to_string()}
        - Por turno:\n{inscricoes_por_turno.to_string()}
        - Por etapa:\n{inscricoes_por_etapa.to_string()}
        - Por processo seletivo:\n{inscricoes_por_ps.to_string()}
        - Por motivo de objeção:\n{inscricoes_por_motivo if isinstance(inscricoes_por_motivo, str) else inscricoes_por_motivo.to_string()}
        """

        st.markdown("### 📝 Resumo Inteligente com IA")
        with st.spinner("🧠 Gerando resumo com IA..."):
            try:
                response = client_openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt_base}],
                    temperature=0.3,
                    max_tokens=600
                )
                texto_ia = response.choices[0].message.content
                st.success(texto_ia)
            except Exception as e:
                st.error(f"❌ Erro ao gerar o resumo com IA. {e}")

    else:
        exibir_perguntas_frequentes(dict_perguntas, "Inscrições")


def tela_matriculas(resumo=False):
    df = executar_query("""
        SELECT nome, curso, etapa, turno, processoSeletivo, objecao, dataMatricula
        FROM pessoal.chatbot_educacional
        WHERE nome IS NOT NULL
    """)

    df = df[df['etapa'] == 'Matriculado']
    df['dataMatricula'] = pd.to_datetime(df['dataMatricula'])
    df['data'] = df['dataMatricula'].dt.date
    df['hora'] = df['dataMatricula'].dt.hour

    if resumo:
        total_matriculados = len(df)
        media_diaria = round(df.groupby('data').size().mean(), 2)

        resumo_dict = {
            "total_matriculados": total_matriculados,
            "media_diaria": media_diaria,
            "por_curso": df['curso'].value_counts().to_dict(),
            "por_etapa": df['etapa'].value_counts().to_dict(),
            "por_turno": df['turno'].value_counts().to_dict(),
            "por_processo": df['processoSeletivo'].value_counts().to_dict(),
            "por_objeção": df['objecao'].dropna().value_counts().to_dict(),
            "horas": df['hora'].value_counts().sort_index().to_dict(),
            "datas": df['data'].value_counts().sort_index().to_dict(),
        }

        st.session_state['resumo_matriculas'] = resumo_dict
        st.session_state['df_matriculas'] = df

        st.success("✅ Dados coletados! Prontos para visualização e análise com IA.")
        st.subheader("📊 Gráficos do resumo de matrículas")

        # 1. Processo Seletivo
        df_proc = df['processoSeletivo'].value_counts().reset_index()
        df_proc.columns = ['processoSeletivo', 'count']
        fig_proc = px.bar(df_proc, x='processoSeletivo', y='count', text='count')
        st.plotly_chart(estilo_futurista_barras(fig_proc, "Matrículas por Processo Seletivo"), use_container_width=True)

        # 2. Curso
        df_curso = df['curso'].value_counts().reset_index()
        df_curso.columns = ['curso', 'count']
        fig_curso = px.bar(df_curso, x='curso', y='count', text='count')
        st.plotly_chart(estilo_futurista_barras(fig_curso, "Matrículas por Curso"), use_container_width=True)

        # 3. Turno
        df_turno = df[df['turno'].isin(['Diurno', 'Noturno', 'EAD'])]
        fig_turno = px.pie(df_turno, names='turno', title='', hole=0.3)
        st.plotly_chart(estilo_futurista_pizza(fig_turno, "Distribuição por Turno"), use_container_width=True)

        # 4. Evolução diária
        df_data = df['data'].value_counts().sort_index().reset_index()
        df_data.columns = ['data', 'count']
        fig_dia = px.line(df_data, x='data', y='count')
        st.plotly_chart(estilo_futurista_linha(fig_dia, "Evolução das Matrículas ao Longo do Tempo"), use_container_width=True)

        # 5. Resumo com IA
        matriculados_por_curso = df['curso'].value_counts().head(5)
        matriculados_por_turno = df['turno'].value_counts()
        matriculados_por_etapa = df['etapa'].value_counts()
        matriculados_por_ps = df['processoSeletivo'].value_counts().head(3)
        matriculados_por_motivo = df['objecao'].value_counts().head(3) if 'objecao' in df.columns else "Não disponível"

        prompt_base = f"""
        Você é um analista de dados da Faculdade Fuzati e precisa apresentar um resumo claro e estratégico para gestores da área.

        Gere um resumo analítico e assertivo sobre os dados de matriculados com base nas informações abaixo. Utilize uma linguagem clara, profissional e voltada para gestores da área educacional. Considere regras de negócio como: cursos com maior volume tendem a receber mais investimento; processos seletivos específicos podem impactar a etapa da inscrição; e objeções indicam barreiras na jornada. Destaque padrões, alertas e boas oportunidades. Os dados estão entre colchetes:

        - Por curso:\n{matriculados_por_curso.to_string()}
        - Por turno:\n{matriculados_por_turno.to_string()}
        - Por etapa:\n{matriculados_por_etapa.to_string()}
        - Por processo seletivo:\n{matriculados_por_ps.to_string()}
        - Por motivo de objeção:\n{matriculados_por_motivo if isinstance(matriculados_por_motivo, str) else matriculados_por_motivo.to_string()}
        """

        st.markdown("### 📝 Resumo Inteligente com IA")
        with st.spinner("🧠 Gerando resumo com IA..."):
            try:
                response = client_openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt_base}],
                    temperature=0.3,
                    max_tokens=600
                )
                texto_ia = response.choices[0].message.content
                st.success(texto_ia)
            except Exception as e:
                st.error(f"❌ Erro ao gerar o resumo com IA. {e}")

    else:
        exibir_perguntas_frequentes(dict_perguntas, "Matrículas")






def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


def show_logo():
    logo_base64 = get_base64_of_bin_file("Logo.png")
    st.markdown(
        f"""
        <style>
            .logo {{
                position: fixed;
                top: 70px;
                right: 20px;
                width: 100px;
                z-index: 1000;
            }}
        </style>
        <img src="data:image/png;base64,{logo_base64}" class="logo" />
        """,
        unsafe_allow_html=True,
    )


def login():
    logo_base64 = get_base64_of_bin_file("Logo.png")
    st.markdown(
        f"""
        <style>
            .login-container {{
                background-color: #0a2540;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);
                color: white;
                text-align: center;
                max-width: 1200px;
                margin: auto;
            }}
            .login-title {{
                font-size: 2rem;
                font-weight: bold;
                color: #ffffff;
                margin-bottom: 1rem;
            }}
            .login-intro {{
                font-size: 1.1rem;
                color: #cbd6e2;
                margin-bottom: 2rem;
            }}
            .logo {{
                position: fixed;
                top: 70px;
                right: 20px;
                width: 120px;
                z-index: 1000;
            }}
        </style>

        <div class="login-container">
            <div class="login-title">🤖 Agente de IA - Faculdade Nova Aurora</div>
            <div class="login-intro">
                Bem-vindo ao assistente inteligente da Faculdade Nova Aurora!<br>
                Aqui você pode explorar dados de inscrições e matrículas usando linguagem natural.<br>
                Receba respostas claras, visuais e insights detalhados em poucos segundos.
            </div>
        </div>


        <img src="data:image/png;base64,{logo_base64}" class="logo" />
        """,
        unsafe_allow_html=True
    )

    codigo = st.text_input("Digite o código de acesso:", type="password", key="codigo_login")
    if st.button("Entrar"):
        if codigo == SECRET_CODE:
            st.session_state['autenticado'] = True
        else:
            st.error("Código incorreto. Tente novamente.")


def mostrar_kpis(df: pd.DataFrame, titulo="KPIs"):
    if "dataInscricao" in df.columns:
        df['dataInscricao'] = pd.to_datetime(df['dataInscricao'], errors='coerce')
        df['data'] = df['dataInscricao'].dt.date

    total_inscricoes = len(df)
    total_matriculas = len(df[df['etapa'] == 'Matriculado'])

    curso_top_inscricoes = df['curso'].value_counts().idxmax() if not df['curso'].dropna().empty else "-"
    curso_top_matriculas = df[df['etapa'] == 'Matriculado']['curso'].value_counts().idxmax() if not df[df['etapa'] == 'Matriculado']['curso'].dropna().empty else "-"
    processo_top_inscricoes = df['processoSeletivo'].value_counts().idxmax() if not df['processoSeletivo'].dropna().empty else "-"
    processo_top_matriculas = df[df['etapa'] == 'Matriculado']['processoSeletivo'].value_counts().idxmax() if not df[df['etapa'] == 'Matriculado']['processoSeletivo'].dropna().empty else "-"

    # Quantidade associada aos tops
    num_processo_inscricoes = df['processoSeletivo'].value_counts().max() if not df['processoSeletivo'].dropna().empty else 0
    num_processo_matriculas = df[df['etapa'] == 'Matriculado']['processoSeletivo'].value_counts().max() if not df[df['etapa'] == 'Matriculado']['processoSeletivo'].dropna().empty else 0
    num_curso_inscricoes = df['curso'].value_counts().max() if not df['curso'].dropna().empty else 0
    num_curso_matriculas = df[df['etapa'] == 'Matriculado']['curso'].value_counts().max() if not df[df['etapa'] == 'Matriculado']['curso'].dropna().empty else 0

    st.markdown(f"""
    <div style="background-color: #132238; padding: 30px; border-radius: 16px; margin-bottom: 20px;">
        <h3 style="color: #ffffff; margin-bottom: 1.5rem;">📌 Resumo Geral de KPIs</h3>
        <div style="display: flex; flex-wrap: wrap; justify-content: space-around; color: #ffffff; font-size: 1rem;">
            <div style="flex: 1 1 30%; text-align: center; min-width: 180px;">
                <div>Inscritos</div>
                <div style="font-size: 1.8rem; font-weight: bold;">{total_inscricoes:,}</div>
            </div>
            <div style="flex: 1 1 30%; text-align: center; min-width: 180px;">
                <div>Curso com mais Inscrições</div>
                <div style="font-size: 1.3rem;">{curso_top_inscricoes} - {num_curso_inscricoes}</div>
            </div>
            <div style="flex: 1 1 30%; text-align: center; min-width: 180px;">
                <div>Processo seletivo com mais Inscrições</div>
                <div style="font-size: 1.3rem;">{processo_top_inscricoes} - {num_processo_inscricoes}</div>
            </div>
            <div style="flex: 1 1 30%; text-align: center; min-width: 180px;">
                <div>Matrículas</div>
                <div style="font-size: 1.8rem; font-weight: bold;">{total_matriculas}</div>
            </div>
            <div style="flex: 1 1 30%; text-align: center; min-width: 180px;">
                <div>Curso com mais Matrículas</div>
                <div style="font-size: 1.3rem;">{curso_top_matriculas} - {num_curso_matriculas}</div>
            </div>
            <div style="flex: 1 1 30%; text-align: center; min-width: 180px;">
                <div>Processo seletivo com mais Matrículas</div>
                <div style="font-size: 1.3rem;">{processo_top_matriculas} - {num_processo_matriculas}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)



@st.cache_data(ttl=600)
def carregar_opcoes_filtros():
    return executar_query("""
        SELECT DISTINCT nome, email, telefone, processoSeletivo, curso, turno, origem, etapa, objecao, consultor, cidade, faixaEtaria, dataInscricao, dataMatricula,
               EXTRACT(MONTH FROM dataInscricao) AS mesInscricao,
               EXTRACT(MONTH FROM dataMatricula) AS mesMatricula
        FROM pessoal.chatbot_educacional
        WHERE nome IS NOT NULL
    """)

import io

import io

def tabela_por_regra():
    st.subheader("📋 Gerar Tabela com Filtros Avançados")

    # --- Carregamento único dos filtros ---
    if "df_filtros_cache" not in st.session_state:
        with st.spinner("Carregando filtros..."):
            df_opcoes = executar_query("""
                SELECT DISTINCT nome, email, telefone, processoSeletivo, curso, turno, origem, etapa, objecao, consultor, cidade, faixaEtaria, dataInscricao, dataMatricula,
                    EXTRACT(MONTH FROM dataInscricao) AS mesInscricao,
                    EXTRACT(MONTH FROM dataMatricula) AS mesMatricula
                FROM pessoal.chatbot_educacional
                WHERE nome IS NOT NULL
            """)
            st.session_state["df_filtros_cache"] = df_opcoes

    df_opcoes = st.session_state["df_filtros_cache"]

    if df_opcoes.empty:
        st.warning("Não foi possível carregar os dados para os filtros.")
        return

    # --- FILTROS DISPONÍVEIS ---
    with st.expander("🎛️ Filtros disponíveis"):
        col1, col2 = st.columns(2)

        with col1:
            etapas = st.multiselect("Etapa:", sorted(df_opcoes["etapa"].dropna().unique()), placeholder="Selecione...")
            cursos = st.multiselect("Curso:", sorted(df_opcoes["curso"].dropna().unique()), placeholder="Selecione...")
            turnos = st.multiselect("Turno:", sorted(df_opcoes["turno"].dropna().unique()), placeholder="Selecione...")
            processos = st.multiselect("Processo Seletivo:", sorted(df_opcoes["processoSeletivo"].dropna().unique()), placeholder="Selecione...")
            consultores = st.multiselect("Consultor:", sorted(df_opcoes["consultor"].dropna().unique()), placeholder="Selecione...")

        with col2:
            Faixa_Etaria = st.multiselect("Faixa Etária:", sorted(df_opcoes["faixaEtaria"].dropna().unique()), placeholder="Selecione...")
            origens = st.multiselect("Origem:", sorted(df_opcoes["origem"].dropna().unique()), placeholder="Selecione...")
            objeções = st.multiselect("Objeção:", sorted(df_opcoes["objecao"].dropna().unique()), placeholder="Selecione...")
            meses_inscricao = st.multiselect("Mês da inscrição:", sorted(df_opcoes["mesInscricao"].dropna().astype(int).unique()), format_func=lambda m: f"{m:02d}", placeholder="Selecione...")
            meses_matricula = st.multiselect("Mês da matrícula:", sorted(df_opcoes["mesMatricula"].dropna().astype(int).unique()), format_func=lambda m: f"{m:02d}", placeholder="Selecione...")

    # --- COLUNAS A MOSTRAR ---
    st.markdown("### 📌 Escolha as colunas que deseja ver na tabela:")
    colunas_disponiveis = ['nome', 'email', 'telefone', 'processoSeletivo', 'curso', 'turno', 'origem', 'etapa', 'objecao', 'consultor', 'cidade', 'faixaEtaria', 'dataInscricao', 'dataMatricula']
    colunas_selecionadas = st.multiselect("Colunas a exibir:", colunas_disponiveis, default=colunas_disponiveis)

    # --- NOME DO ARQUIVO ---
    nome_tabela = st.text_input("📝 Digite um nome para o arquivo (sem extensão):", placeholder="Ex: Leads_Julho_CursoX")

    # --- BOTÃO PARA GERAR TABELA ---
    if st.button("🔍 Gerar Tabela", key="gerar_tabela_com_filtro"):
        if not nome_tabela.strip():
            st.warning("⚠️ Por favor, digite um nome para o arquivo antes de gerar a tabela.")
            st.stop()

        condicoes = []

        if Faixa_Etaria:
            lista = ','.join([f"'{e}'" for e in Faixa_Etaria])
            condicoes.append(f"faixaEtaria IN ({lista})")
        
        if consultores:
            lista = ','.join([f"'{c}'" for c in consultores])
            condicoes.append(f"consultor IN ({lista})")
        
        if etapas:
            lista = ','.join([f"'{e}'" for e in etapas])
            condicoes.append(f"etapa IN ({lista})")
        
        if cursos:
            lista = ','.join([f"'{c}'" for c in cursos])
            condicoes.append(f"curso IN ({lista})")
        
        if turnos:
            lista = ','.join([f"'{t}'" for t in turnos])
            condicoes.append(f"turno IN ({lista})")
        
        if processos:
            lista = ','.join([f"'{p}'" for p in processos])
            condicoes.append(f"processoSeletivo IN ({lista})")
        
        if origens:
            lista = ','.join([f"'{o}'" for o in origens])
            condicoes.append(f"origem IN ({lista})")
        
        if objeções:
            lista = ','.join([f"'{o}'" for o in objeções])
            condicoes.append(f"objecao IN ({lista})")
        
        if meses_inscricao:
            lista = ','.join([str(m) for m in meses_inscricao])
            condicoes.append(f"EXTRACT(MONTH FROM dataInscricao) IN ({lista})")
        
        if meses_matricula:
            lista = ','.join([str(m) for m in meses_matricula])
            condicoes.append(f"EXTRACT(MONTH FROM dataMatricula) IN ({lista})")


        where_clause = " AND ".join(condicoes)
        sql = f"""
            SELECT {', '.join(colunas_selecionadas)}
            FROM pessoal.chatbot_educacional
            {"WHERE " + where_clause if where_clause else ""}
        """

        df_resultado = executar_query(sql)

        if df_resultado.empty:
            st.info("Nenhum resultado encontrado com os filtros selecionados.")
        else:
            st.success(f"✅ {len(df_resultado)} registros encontrados.")
            st.dataframe(df_resultado)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_resultado.to_excel(writer, index=False, sheet_name="Resultados")
            buffer.seek(0)

            st.download_button(
                label="📥 Baixar Excel",
                data=buffer,
                file_name=f"{nome_tabela.strip()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )



if 'autenticado' not in st.session_state:
    login()
# if 1 == 0:
#     login()
else:
    st.title("🤖 Agente de IA - Faculdade Nova Aurora")
    
    st.divider()

    st.markdown("""
    <div style='padding: 0px 10px 10px 10px;'>
        <p style='color: #000000; font-size: 1.15rem;'>
            Neste painel você tem acesso a um resumo dos principais KPI's do processo de captação da faculdade. <br>
            Também tem acesso às <strong>perguntas mais frequentes</strong> para facilitar a navegação pelos dados.<br>
            Caso prefira, pode <strong>fazer perguntas personalizadas</strong> em linguagem natural, com respostas geradas por IA.<br>
            Por fim, acesse a seção de <strong>resumos de inscrições e matrículas</strong> para obter insights estratégicos com gráficos e análises automáticas.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
    "🔗 [Clique aqui para acessar o dashboard completo no Looker Studio](https://lookerstudio.google.com/u/2/reporting/20a45689-fd6b-4b79-bf2e-76c9d73bb1d8/page/iG4NF)"
)



    st.divider()


    # 1. Garantir que os dados estejam carregados
    if 'df_inscricoes' not in st.session_state:
        df_inscricoes = executar_query("""
            SELECT nome, curso, etapa, turno, processoSeletivo, objecao, dataInscricao
            FROM pessoal.chatbot_educacional
            WHERE nome IS NOT NULL
        """)
        df_inscricoes['dataInscricao'] = pd.to_datetime(df_inscricoes['dataInscricao'])
        df_inscricoes['data'] = df_inscricoes['dataInscricao'].dt.date
        st.session_state['df_inscricoes'] = df_inscricoes
    else:
        df_inscricoes = st.session_state['df_inscricoes']

    if 'df_matriculas' not in st.session_state:
        df_matriculas = executar_query("""
            SELECT nome, curso, etapa, turno, processoSeletivo, objecao, dataInscricao
            FROM pessoal.chatbot_educacional
            WHERE nome IS NOT NULL AND etapa = 'Matriculado'
        """)
        df_matriculas['dataInscricao'] = pd.to_datetime(df_matriculas['dataInscricao'])
        df_matriculas['data'] = df_matriculas['dataInscricao'].dt.date
        st.session_state['df_matriculas'] = df_matriculas
    else:
        df_matriculas = st.session_state['df_matriculas']

    # 2. Resumo dos dados
    resumo_inscricoes = {
        "total_inscritos": len(df_inscricoes),
        "por_curso": df_inscricoes['curso'].value_counts().to_dict(),
        "por_processo": df_inscricoes['processoSeletivo'].value_counts().to_dict()
    }

    resumo_matriculas = {
        "total_inscritos": len(df_matriculas),
        "por_curso": df_matriculas['curso'].value_counts().to_dict(),
        "por_processo": df_matriculas['processoSeletivo'].value_counts().to_dict()
    }

    mostrar_kpis(df_inscricoes, titulo="Resumo")


    show_logo()

    with st.sidebar.expander("🕘 Histórico de perguntas"):
        if 'historico_perguntas' in st.session_state and st.session_state['historico_perguntas']:
            perguntas_para_remover = []

            for i in range(len(st.session_state['historico_perguntas'])):
                item = st.session_state['historico_perguntas'][i]
                st.markdown(f"**❓ {item['pergunta']}**", unsafe_allow_html=True)
                st.markdown(f"🧠 {item['resposta']}", unsafe_allow_html=True)
                if st.button(f"Remover", key=f"remover_{i}"):
                    perguntas_para_remover.append(i)
                st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

            # Remover em ordem reversa para não bagunçar os índices
            for idx in sorted(perguntas_para_remover, reverse=True):
                st.session_state['historico_perguntas'].pop(idx)

            if st.button("🗑️ Limpar todo o histórico", key="limpar_tudo"):
                st.session_state['historico_perguntas'] = []
                st.experimental_rerun()
        else:
            st.info("Nenhuma pergunta registrada ainda.")

    st.divider()


    dict_perguntas = carregar_dict_perguntas()

    col1, col2 = st.columns(2)
    with col1:
        exibir_perguntas_frequentes(dict_perguntas, "Inscrições")
    with col2:
        exibir_perguntas_frequentes(dict_perguntas, "Matrículas")

    st.divider()
    col3, col4 = st.columns(2)

    if 'chatbot_bq' not in st.session_state:
        st.session_state.chatbot_bq = BigQueryChatbot(credentials, credentials.project_id)

    perguntas_livres()

    st.divider()

    resumo("Inscrições")
    resumo("Matrículas")

    st.divider()

    tabela_por_regra()

    st.divider()

    tela_sugestoes()
