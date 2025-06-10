# Criação da base fake

import pandas as pd
import random
import numpy as np
from faker import Faker
from datetime import datetime, timedelta

credencial = 'chave_gcp.json' # Chave fake, apenas demonstração.


# Configurações iniciais
faker = Faker('pt_BR')
random.seed(42)
Faker.seed(42)

# Parâmetros
n_total = random.randint(3000, 5000)
perc_ganho = 0.06
perc_perdido = 0.23
n_ganho = int(n_total * perc_ganho)
n_perdido = int(n_total * perc_perdido)
n_andamento = n_total - n_ganho - n_perdido

# Cursos e turnos
cursos = ['Direito', 'Administração', 'Enfermagem', 'Engenharia Civil', 'Psicologia', 'Biomedicina',
          'Educação Física', 'Arquitetura', 'Engenharia de Produção', 'Ciência da Computação',
          'Matemática', 'História', 'Publicidade', 'Jornalismo', 'Serviço Social', 'Design Gráfico',
          'Nutrição', 'Fisioterapia', 'Química', 'Letras']

turnos = ['Noturno', 'Diurno', 'EAD']

curso_turnos = [f"{curso} - {turno}" for curso in cursos for turno in turnos]

# Processo seletivo
processos = ['ENEM', 'Vestibular', 'FIES', 'Transferência', 'ProUni', 'Segunda Graduação']

# Etapas
etapas_validas = ['Interessado', 'Pré-Inscrito', 'Inscrito', 'Aprovado', 'Reprovado', 'Matriculado']

# Consultores

consultores = [faker.name() for _ in range(8)]

# Remover prefixos indesejados como Sr., Sra., etc
for i in range(len(consultores)):
    while any(prefix in consultores[i].lower() for prefix in ['sr.', 'sra.', 'srta.', 'dr.', 'dra.']):
        consultores[i] = faker.name()

# Objeções
objeções = ['Distância', 'Preço', 'Carga horária', 'Desistência', 'Curso não disponível', 'Problemas pessoais']

# Estados brasileiros
estados_br = ['SP', 'RJ', 'MG', 'BA', 'RS', 'PR', 'SC', 'PE', 'CE', 'GO', 'PA', 'AM', 'ES', 'MA', 'MT']

# Origens
origens = ['google', 'facebook', 'instagram', 'tiktok']

# Datas de inscrição com picos
def gerar_data_inscricao():
    base = datetime(2024, 1, 1)
    datas = []
    for _ in range(n_total):
        if random.random() < 0.25:
            datas.append(base + timedelta(days=random.randint(30, 40)))  # pico em fevereiro
        elif random.random() < 0.25:
            datas.append(base + timedelta(days=random.randint(100, 110)))  # pico em abril
        else:
            datas.append(base + timedelta(days=random.randint(0, 150)))
    return datas

# Gerar dados
dados = []
status_list = ['Ganho'] * n_ganho + ['Perdido'] * n_perdido + ['Em Andamento'] * n_andamento
random.shuffle(status_list)

datas_inscricao = gerar_data_inscricao()

for i in range(n_total):
    nome = faker.name()
    while any(prefix in nome.lower() for prefix in ['sr.', 'sra.', 'srta.', 'dr.', 'dra.']):
        nome = faker.name()
    nome_email = nome.lower().replace(" ", ".").replace("'", "")
    email = f"{nome_email}@email.com"
    telefone = faker.msisdn()
    telefone_formatado = f"+55 ({telefone[2:4]}) {telefone[4:9]}-{telefone[9:]}"
    curso_turno = random.choice(curso_turnos)
    processo = random.choice(processos)
    status = status_list[i]

    if status == 'Ganho':
        etapa = 'Matriculado'
    elif status == 'Perdido':
        etapa = random.choices(['Interessado', 'Pré-Inscrito', 'Inscrito', 'Reprovado'], weights=[0.2, 0.2, 0.4, 0.2])[0]
    else:
        etapa = random.choices(['Interessado', 'Pré-Inscrito', 'Inscrito', 'Aprovado'], weights=[0.3, 0.3, 0.3, 0.1])[0]

    consultor = random.choice(consultores)
    data_inscricao = datas_inscricao[i].date()

    if status == 'Ganho' and etapa == 'Matriculado':
        data_matricula = data_inscricao + timedelta(days=random.randint(1, 20))
    else:
        data_matricula = ''

    objecao = random.choice(objeções) if status == 'Perdido' else ''

    if 'EAD' in curso_turno:
        estado = random.choice(estados_br)
    else:
        estado = 'SP'

    origem = random.choice(origens)
    idade = int(np.clip(np.random.normal(22, 6), 17, 60))

    dados.append([
        i + 1, nome, email, telefone_formatado, curso_turno, processo, status, etapa,
        consultor, data_inscricao.strftime('%Y-%m-%d'),
        data_matricula.strftime('%Y-%m-%d') if data_matricula else '',
        objecao, estado, origem, idade
    ])

# DataFrame final
colunas = ['idRegistro', 'nome', 'email', 'telefone', 'cursoTurno', 'processoSeletivo', 'status',
           'etapa', 'consultor', 'dataInscricao', 'dataMatricula', 'objecao', 'estado', 'origem', 'idade']

df = pd.DataFrame(dados, columns=colunas)


# TRATAMENTO DOS DADOS

# Separando colunas de curso e turno
df['curso'] = df['cursoTurno'].apply(lambda x: x.split(' - ')[0])
df['turno'] = df['cursoTurno'].apply(lambda x: x.split(' - ')[1])
df.drop(columns=['cursoTurno'], inplace=True)

# Criar os intervalos e os rótulos
bins = [0, 18, 21, 25, 30, 40, float('inf')]  # Defini os intervalos
labels = ['Menor de 18', '18 a 21', '21 a 25', '25 a 30', '30 a 40', 'Acima de 40']

# Criar a nova coluna de faixa etária
df['faixaEtaria'] = pd.cut(df['idade'], bins=bins, labels=labels, right=False)

# Extraindo o dia da semana
df['dataInscricao'] = pd.to_datetime(df['dataInscricao'])
df['diaSemanaInscricao'] = df['dataInscricao'].dt.strftime('%A')

dias_semana = {
    "Monday": "Segunda-Feira", "Tuesday": "Terça-Feira", "Wednesday": "Quarta-Feira",
    "Thursday": "Quinta-Feira", "Friday": "Sexta-Feira", "Saturday": "Sábado", "Sunday": "Domingo"
}

df['diaSemanaInscricao'] = df['dataInscricao'].dt.day_name().map(dias_semana)

# DIMINUINDO USO DE MEMÓRIA

mem_mb = df.memory_usage(deep=True).sum() / (1024**2)

# Ajuste de tipos das colunas para diminuição de uso de memória
df['processoSeletivo'] = df['processoSeletivo'].astype('category')
df['status'] = df['status'].astype('category')
df['etapa'] = df['etapa'].astype('category')
df['consultor'] = df['consultor'].astype('category')
df['objecao'] = df['objecao'].astype('category')
df['estado'] = df['estado'].astype('category')
df['origem'] = df['origem'].astype('category')
df['curso'] = df['curso'].astype('category')
df['turno'] = df['turno'].astype('category')
df['diaSemanaInscricao'] = df['diaSemanaInscricao'].astype('category')
df['dataMatricula'] = pd.to_datetime(df['dataMatricula'], errors='coerce')
df['idade'] = df['idade'].astype(int)


# Calculando diferença no uso da memória
mem_mb_novo = df.memory_usage(deep=True).sum() / (1024**2)
print(f"""Uso de memória""")
print(f"""Antes: {mem_mb:.2f} MB""")
print(f"""Depois: {mem_mb_novo:.2f} MB""")
print(f"""Diferença: {((mem_mb_novo - mem_mb) / mem_mb) * 100 :.2f}%""")


# Carregar para o BigQuery
to_gbq(
    dataframe=df,  # Substitua pelo seu DataFrame
    destination_table="pessoal.chatbot_educacional",
    project_id="cloud-engineer-444301-r6",
    if_exists="replace",  # Opções: "fail", "replace", "append"
    credentials=credencial,  # Sua credencial configurada
)