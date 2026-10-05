"""
CAMADA DE BANCO (db.py)  —  ESQUELETO, implemente você mesmo
============================================================

Esta é a ÚNICA parte do projeto que "fala SQL". As rotas (main.py) nunca
escrevem SQL: elas chamam as funções daqui. Essa separação em camadas é o
coração do módulo.

REGRA DE OURO (segurança): os VALORES que vêm do cliente vão SEMPRE como %s
+ tupla de parâmetros. Nunca concatene dados do usuário na string SQL
(isso abre SQL Injection).

Ordem sugerida de implementação:
  1. Configuração + conectar()      -> abrir conexão com o PostgreSQL
  2. criar_tabelas()                -> criar alunos, disciplinas, matriculas
  3. CRUD de alunos                 -> inserir / listar / buscar / atualizar / excluir
  4. CRUD de disciplinas            (Desafio 2)
  5. matrículas + JOIN              (Desafio 3)

O modelo de dados (as 3 tabelas) está definido em `esquema.sql` — use como
referência ao escrever criar_tabelas().
"""

# DICA — bibliotecas que você provavelmente vai usar:
#   import os
#   import psycopg2
#   from psycopg2.extras import RealDictCursor   # faz o banco devolver dict, não tupla
#   from dotenv import load_dotenv               # lê o arquivo .env
import os
import psycopg2  # type: ignore[reportMissingModuleSource]
from typing import Optional
from psycopg2.extras import RealDictCursor  # type: ignore[reportMissingModuleSource]
from dotenv import load_dotenv  # type: ignore[reportMissingModuleSource]
# TODO: carregue as variáveis do .env (load_dotenv) e monte um CONFIG lendo
#       DB_HOST, DB_NAME, DB_USER, DB_PASSWORD (dica: os.getenv com um padrão).

load_dotenv() 

CONFIG = {
  "host": os.getenv("DB_HOST"),
  "database": os.getenv("DB_NAME"),
  "user": os.getenv("DB_USER"),
  "password": os.getenv("DB_PASSWORD"),
  "port": os.getenv("DB_PORT"),
}

# TODO: def conectar():
#   Abra e devolva uma conexão psycopg2 usando o CONFIG.
#   Dica: passe cursor_factory=RealDictCursor para as linhas virem como dicts.
def conectar():
  conexao = psycopg2.connect(
    host = CONFIG["host"],
    database = CONFIG["name"],
    user = CONFIG["user"],
    password = CONFIG["password"],
    port = CONFIG["port"],
    cursor_factory=RealDictCursor
  )
  return conexao

def executar_sql(sql, params=None, fetchone=False):
  with psycopg2.connect(**CONFIG) as con, con.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute(sql, params)
    sql_limpo = sql.strip().upper()
    
    if "RETURNING" in sql_limpo:
      dados = cur.fetchone()
      con.commit()
      return dados
    
    if sql_limpo.startswith(("CREATE", "INSERT", "UPDATE", "DELETE", "DROP")):
      con.commit()
      
      if sql_limpo.startswith("DELETE"):
        return cur.rowcount > 0
      return "Alteração realizada com sucesso."
         
    
    else:
      if fetchone:
          return  cur.fetchone()   
      else:
          return  cur.fetchall()
    

# TODO: def criar_tabelas():
#   Crie as 3 tabelas com "CREATE TABLE IF NOT EXISTS ..." (veja esquema.sql).
#   Esta função é chamada no startup da API (main.py).
def criar_tabelas():
  sql = """ CREATE TABLE IF NOT EXISTS alunos (
    id        SERIAL PRIMARY KEY,
    nome      VARCHAR(100) NOT NULL,
    idade     INTEGER,
    matricula SERIAL UNIQUE NOT NULL
  );

    CREATE TABLE IF NOT EXISTS disciplinas (
    id            SERIAL PRIMARY KEY,
    nome          VARCHAR(100) NOT NULL UNIQUE,
    carga_horaria INTEGER NOT NULL
  );

    CREATE TABLE IF NOT EXISTS matriculas (
    id            SERIAL PRIMARY KEY,   
    aluno_id      INTEGER REFERENCES alunos(id) ON DELETE CASCADE,
    disciplina_id INTEGER REFERENCES disciplinas(id) ON DELETE CASCADE,
    UNIQUE (aluno_id, disciplina_id)     -- mesma matrícula só uma vez
  );

    CREATE TABLE IF NOT EXISTS usuarios (
      id SERIAL PRIMARY KEY,
      email VARCHAR(100) NOT NULL UNIQUE,
      senha_hash VARCHAR(72) NOT NULL,
      criado_em TIMESTAMP NOT NULL DEFAULT NOW()
  );
    
    CREATE TABLE IF NOT EXISTS notas (
    id            SERIAL PRIMARY KEY,
    matricula_id  INTEGER NOT NULL REFERENCES matriculas(id) ON DELETE CASCADE UNIQUE,
    nota_1 NUMERIC(4,2) CHECK (nota_1 BETWEEN 0 AND 10),
    nota_2 NUMERIC(4,2) CHECK (nota_2 BETWEEN 0 AND 10),
    nota_3 NUMERIC(4,2) CHECK (nota_3 BETWEEN 0 AND 10),
    media  NUMERIC(4,2) GENERATED ALWAYS AS (ROUND((COALESCE(nota_1, 0) + COALESCE(nota_2, 0) + COALESCE(nota_3, 0)) / 3.0, 2)) STORED
  );"""
  executar_sql(sql)

# --------------------------------------------------------------------------
# CRUD de ALUNOS
# --------------------------------------------------------------------------
# TODO: inserir_aluno(nome, idade, matricula, media=0)
#   INSERT na tabela alunos. Dica: use "RETURNING *" para já receber de volta
#   a linha criada (com o id gerado pelo banco).

def inserir_aluno(nome, idade):
  sql = "INSERT INTO alunos (nome, idade) VALUES (%s, %s) RETURNING id, nome, idade, matricula;"
  aluno_criado = executar_sql(sql, (nome, idade))
  return aluno_criado

#
# TODO: listar_alunos()
#   SELECT de todos os alunos, ordenados por id.
#   (Fazer aceitar filtros é o Desafio 1 — comece simples.)

def listar_alunos(idade=None):
  sql = "SELECT * FROM alunos"
  condicoes = []
  parametros = []
  if idade is not None:
    condicoes.append("idade >= %s")
    parametros.append(idade)  
  if condicoes:
    sql += " WHERE " + " AND ".join(condicoes)
    
  sql += " ORDER BY id ASC"
  lista_alunos = executar_sql(sql, tuple(parametros))
  return lista_alunos

# TODO: buscar_aluno(aluno_id)
#   SELECT de um aluno por id. Devolva None se não existir.

def buscar_aluno(id):
  sql = "SELECT nome, idade, matricula FROM alunos WHERE id = %s;"       
  aluno = executar_sql(sql, (id,), fetchone=True)
  return aluno

# TODO: atualizar_aluno(id, **campos)
#   UPDATE parcial: atualize só os campos recebidos. Dica: nomes de coluna
#   podem entrar por f-string (são do seu código); VALORES vão com %s.

def atualizar_aluno(
  id: int, 
  nome: Optional[str] = None, 
  idade: Optional[int] = None
  ):  
  
  campos_atualizados = {
    "nome": nome,
    "idade": idade
  }
  
  ## k transforma em nome da coluna, v transforma em valor do campo
  campos_validos = {k: v for k, v in campos_atualizados.items() if v is not None}
  if not campos_validos:
    print("Nenhuma informação do aluno foi alterada")
    return False
  
  partes = [f"{campo} = %s" for campo in campos_validos.keys()]
  partes_sql = ", ".join(partes)
  
  sql = f"UPDATE alunos SET {partes_sql} WHERE id= %s;"
  
  entrada = list(campos_validos.values()) + [id]
  
  aluno_atualizado = executar_sql(sql, entrada)
  return aluno_atualizado

# TODO: excluir_aluno(id)
#   DELETE por id. Devolva True/False (dica: cur.rowcount > 0).

def excluir_aluno(id):
  sql = "DELETE FROM alunos WHERE id = %s;"
  aluno_excluido = executar_sql(sql, (id,))
  return aluno_excluido

# --------------------------------------------------------------------------
# CRUD de DISCIPLINAS  (Desafio 2)
# --------------------------------------------------------------------------
# TODO: inserir_disciplina, listar_disciplinas, buscar_disciplina,
#       excluir_disciplina — espelhando o CRUD de alunos.
def inserir_disciplina(nome, carga_horaria):
  sql = "INSERT INTO disciplinas (nome, carga_horaria) VALUES (%s, %s) RETURNING *;"
  disciplina_criada = executar_sql(sql, (nome, carga_horaria))
  return disciplina_criada

def listar_disciplinas():
  sql = "SELECT * FROM disciplinas ORDER BY id ASC"
  lista_disciplinas = executar_sql(sql)
  return lista_disciplinas

def buscar_disciplina(id):
  sql = "SELECT nome, carga_horaria FROM disciplinas WHERE id = %s"       
  disciplina = executar_sql(sql, (id,))
  return disciplina

def atualizar_disciplina(
  id: int, 
  nome: Optional[str] = None, 
  carga_horaria: Optional[int] = None
):  
  
  campos_atualizados = {
    "nome": nome,
    "carga_horaria": carga_horaria
  }
  
  campos_validos = {k: v for k, v in campos_atualizados.items() if v is not None}
  if not campos_validos:
    print("Nenhuma informação do aluno foi alterada")
    return False
  
  partes = [f"{campo} = %s" for campo in campos_validos.keys()]
  partes_sql = ", ".join(partes)
  
  sql = f"UPDATE disciplinas SET {partes_sql} WHERE id= %s;"
  
  entrada = list(campos_validos.values()) + [id]
  
  disciplina_atualizada = executar_sql(sql, entrada)  
  return disciplina_atualizada

def excluir_disciplina(id):
  sql = "DELETE FROM disciplinas WHERE id = %s;"
  disciplina_excluida = executar_sql(sql, (id,))
  return disciplina_excluida

# --------------------------------------------------------------------------
# MATRÍCULAS — relacionamento aluno <-> disciplina  (Desafio 3)
# --------------------------------------------------------------------------
# TODO: matricular(aluno_id, disciplina_id)
#   INSERT na tabela matriculas. Dica: "ON CONFLICT DO NOTHING" evita erro se
#   a matrícula já existir.
#
def matricular_aluno(aluno_id, disciplina_id):
  sql = "INSERT INTO matriculas (aluno_id, disciplina_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;"
  aluno_matriculado = executar_sql(sql, (aluno_id, disciplina_id))
  return aluno_matriculado

# TODO: disciplinas_do_aluno(aluno_id)
#   Liste as disciplinas em que o aluno está matriculado. Dica: use JOIN entre
#   disciplinas e matriculas.
def disciplinas_do_aluno(aluno_id):
  sql = "SELECT matriculas.disciplina_id AS id, disciplinas.nome, disciplinas.carga_horaria FROM matriculas JOIN disciplinas ON disciplinas.id = matriculas.disciplina_id WHERE matriculas.aluno_id = %s;"
  disciplinas_matriculadas = executar_sql(sql, (aluno_id,))
  return disciplinas_matriculadas

def incluir_usuario(email, senha_hash):
    sql = "INSERT INTO usuarios (email, senha_hash) VALUES (%s, %s) RETURNING id, email, criado_em;"
    usuario_criado = executar_sql(sql, (email, senha_hash))
    return usuario_criado

def buscar_usuario_por_email(email):
    sql = "SELECT id, email, senha_hash, criado_em FROM usuarios WHERE email = %s;"
    usuario = executar_sql(sql, (email,), fetchone=True)
    return usuario
  
def listar_usuarios():
    sql = "SELECT id, email, criado_em FROM usuarios ORDER BY id ASC"
    lista_usuarios = executar_sql(sql)
    return lista_usuarios
  
def cadastrar_nota(matricula_id, nota_1=None, nota_2=None, nota_3=None):
    sql = "INSERT INTO notas (matricula_id, nota_1, nota_2, nota_3) VALUES (%s, %s, %s, %s) RETURNING *;"
    nota_criada = executar_sql(sql, (matricula_id, nota_1, nota_2, nota_3))
    return nota_criada

def media_aluno(matricula):
    sql = "SELECT a.nome, a.matricula, nota_1, nota_2, nota_3, media FROM notas n join public.matriculas m on n.matricula_id = m.id join alunos a on m.aluno_id = a.id where a.matricula = %s;"
    media = executar_sql(sql, (matricula,), fetchone=True)
    return media