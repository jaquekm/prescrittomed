import os
import sys
from sqlalchemy import create_engine, text
from decouple import config
from openai import OpenAI

print("💉 Iniciando injeção de dados NO PADRÃO CORRETO...")

# 1. Configuração do Banco
host = config('POSTGRES_HOST', default='localhost')
port = config('POSTGRES_PORT', default=5432, cast=int)
database = config('POSTGRES_DB', default='prescrittomed_db')
user = config('POSTGRES_USER', default='prescrittomed')
password = config('POSTGRES_PASSWORD', default='prescrittomed_pass')
db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

engine = create_engine(db_url)
conn = engine.connect()
client = OpenAI(api_key=config('OPENAI_API_KEY'))

def get_embedding(text):
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding

# 2. Dados Detalhados (Para preencher o seu JSON)
dados = [
    {
        "title": "Dipirona Monohidratada",
        "content": """
        BULA SIMPLIFICADA: Dipirona (metamizol). Fonte: MDSaúde. URL: https://www.mdsaude.com/bulas/dipirona-metamizol/.
        INDICAÇÕES: Analgésico (dor), antipirético (febre). Usada para dor de cabeça, corpo e febre.
        POSOLOGIA: Comprimidos ou Gotas (500mg/ml). Adultos: 500mg a 1g a cada 6 horas. Crianças: conforme peso (ver tabela bula).
        CONTRAINDICAÇÕES: Gravidez, amamentação, alergia a dipirona, bebês < 3 meses, deficiência de G6PD.
        EFEITOS COLATERAIS: Queda de pressão, reações alérgicas. Raro: agranulocitose.
        ADVERTÊNCIAS: Não usar se tiver alergia a AAS ou anti-inflamatórios.
        """,
        "source": "MDSaúde"
    },
    {
        "title": "Amoxicilina",
        "content": """
        BULA SIMPLIFICADA: Amoxicilina. Fonte: Minha Vida. URL: https://www.minhavida.com.br/saude/bulas/amoxicilina.
        INDICAÇÕES: Infecções bacterianas, amigdalite bacteriana (placas na garganta), sinusite.
        POSOLOGIA: Adultos: 500mg de 8 em 8 horas por 7 a 10 dias.
        CONTRAINDICAÇÕES: Alergia a penicilina ou cefalosporinas. Mononucleose.
        EFEITOS COLATERAIS: Diarreia, náusea, candidíase, rash cutâneo.
        ADVERTÊNCIAS: O uso prolongado pode causar superinfecção. Corta efeito do anticoncepcional em alguns casos.
        """,
        "source": "Minha Vida"
    },
    {
        "title": "Ibuprofeno",
        "content": """
        BULA SIMPLIFICADA: Ibuprofeno. Fonte: Bulário Anvisa. URL: https://consultas.anvisa.gov.br/.
        INDICAÇÕES: Febre e dores inflamatórias (garganta).
        POSOLOGIA: Adultos: 600mg de 8/8h. Crianças: 10mg/kg dose.
        CONTRAINDICAÇÕES: Dengue, úlcera gástrica, insuficiência renal, alergia a AAS.
        EFEITOS COLATERAIS: Dor de estômago, azia.
        """,
        "source": "Anvisa"
    }
]

# 3. Limpar e Inserir
print("🧹 Limpando dados antigos...")
conn.execute(text("DELETE FROM knowledge_base")) # Limpa para não duplicar
conn.commit()

print("🧠 Gerando inteligência nova...")
try:
    for item in dados:
        vetor = str(get_embedding(item['content']))
        sql = text("""
            INSERT INTO knowledge_base (content, source_type, source_title, embedding, validity_status)
            VALUES (:content, 'Bula/Protocolo', :title, :embedding, 'ACTIVE');
        """)
        conn.execute(sql, {"content": item['content'], "title": item['title'], "embedding": vetor})
        print(f"✅ Inserido: {item['title']}")
    
    conn.commit()
    print("\n🎉 DADOS ATUALIZADOS COM SUCESSO!")
except Exception as e:
    print(f"❌ Erro: {e}")
finally:
    conn.close()