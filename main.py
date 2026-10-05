"""
CAMADA DE ROTAS (main.py)  —  ESQUELETO, implemente você mesmo
==============================================================

É o "cardápio" da API: cada rota é um endpoint. Mantenha as rotas FINAS —
elas só devem:
  1. receber/validar a entrada (via schemas do Pydantic);
  2. chamar UMA função do db.py;
  3. traduzir o resultado em resposta HTTP (status code + corpo).

Nenhuma regra de negócio ou SQL mora aqui.

Depois de implementar, rode (com o venv ativado e o PostgreSQL no ar):
    uvicorn main:app --reload
E explore em: http://127.0.0.1:8000/docs
"""

# DICA — o que você vai importar:
from typing import List
from fastapi import FastAPI, HTTPException, status  # type: ignore[import-not-found]
from fastapi.responses import RedirectResponse  # type: ignore[import-not-found]
from psycopg2.errors import UniqueViolation  # type: ignore[reportMissingModuleSource]  # para tratar duplicidade
import db
from schemas import AlunoEntrada, AlunoAtualizacao, AlunoSaida, DisciplinaEntrada, DisciplinaSaida, UsuarioEntrada, UsuarioSaida, LoginOk, nota, mediaSaida
import auth


# TODO: crie a aplicação -> app = FastAPI(title="Gestão de Alunos")
#       (a variável PRECISA se chamar `app` — é o que o uvicorn procura.)
app = FastAPI(title="Gestão de Alunos", version="0.1.0")

# TODO: registre o startup para criar as tabelas:
#   @app.on_event("startup")
#   def ao_iniciar():
#       db.criar_tabelas()
@app.on_event("startup")
def ao_iniciar():
    db.criar_tabelas()

# TODO: GET /  -> uma mensagem de boas-vindas (ex.: aponte para /docs).
@app.get("/")
def boas_vindas():
    return RedirectResponse(url="/docs")


# ========================= ALUNOS =========================
# Verbo/rota/status que você deve implementar (o "coração" do REST):
#
#   POST   /alunos            -> 201 Created; devolva o objeto criado.
#                                Trate matrícula duplicada com 409 Conflict
#                                (except UniqueViolation).
#   GET    /alunos            -> 200; lista. (Filtros = Desafio 1.)
#   GET    /alunos/{id}       -> 200 com o aluno, ou 404 se não existir.
#   PATCH  /alunos/{id}       -> 200; atualização parcial. Dica:
#                                payload.model_dump(exclude_unset=True).
#   DELETE /alunos/{id}       -> 204 No Content; 404 se não existir.
#
# Lembre: use response_model=AlunoSaida e status_code=status.HTTP_201_CREATED etc.
@app.post("/registrar", response_model=UsuarioSaida, status_code=status.HTTP_201_CREATED)
def registrar(usuario: UsuarioEntrada):
    senha_hash = auth.gerar_hash(usuario.senha)
    try:
        usuario_criado = db.incluir_usuario(usuario.email, senha_hash)
        return usuario_criado
    except UniqueViolation:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já registrado.")

@app.get("/usuarios", response_model=List[UsuarioSaida])
def listar_usuarios():
    return db.listar_usuarios()    

@app.post("/login", response_model=LoginOk)
def login(dados: UsuarioEntrada):
    usuario = db.buscar_usuario_por_email(dados.email)
    
    if usuario is None:
        auth.conferir_senha(dados.senha, auth.HASH_FALSO)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos.")
    
    if not auth.conferir_senha(dados.senha, usuario["senha_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos.")
    
    usuario_dict = dict(usuario)
    usuario_dict.pop("senha_hash", None)  # Remover a senha do dicionário antes de retornar 
    return {"message": "Login bem-sucedido", "usuario": usuario_dict}

@app.post("/alunos", status_code=status.HTTP_201_CREATED, response_model=AlunoSaida)
def criar_aluno(aluno: AlunoEntrada):
    try:
        aluno_criado = db.inserir_aluno(**aluno.model_dump())
        return aluno_criado
    except UniqueViolation:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Matrícula duplicada.")

@app.get("/alunos", status_code=status.HTTP_200_OK)
def listar_alunos():
    return db.listar_alunos()

@app.get("/alunos/{id}")
def buscar_aluno(id: int):
    aluno = db.buscar_aluno(id)
    if aluno is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    return aluno

@app.patch("/alunos/{id}")
def atualizar_aluno(id: int, aluno: AlunoAtualizacao):
    campos_atualizados = aluno.model_dump(exclude_unset=True)
    if not campos_atualizados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum campo para atualizar.")
    
    aluno_atualizado = db.atualizar_aluno(id, **campos_atualizados)
    if aluno_atualizado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    
    return aluno_atualizado

@app.delete("/alunos/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_aluno(id: int):
    sucesso = db.excluir_aluno(id)
    if not sucesso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    return None  # 204 No Content

# ========================= DISCIPLINAS (Desafio 2) =========================
# POST /disciplinas (201, 409 se duplicado) · GET /disciplinas (200) ·
# DELETE /disciplinas/{id} (204, 404 se não existir).

@app.post("/disciplinas", status_code=status.HTTP_201_CREATED, response_model=DisciplinaSaida)
def criar_disciplina(disciplina: DisciplinaEntrada):
    try:
        disciplina_criada = db.inserir_disciplina(**disciplina.model_dump())
        return disciplina_criada
    except UniqueViolation:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Disciplina duplicada.")
    
@app.get("/disciplinas")
def listar_disciplinas():
    return db.listar_disciplinas()

# ========================= MATRÍCULAS (Desafio 3) =========================
# POST /alunos/{aluno_id}/matricular/{disciplina_id}
#      -> 404 se aluno OU disciplina não existir; senão matricula.
# GET  /alunos/{aluno_id}/disciplinas
#      -> lista as disciplinas do aluno (usa db.disciplinas_do_aluno / JOIN).
@app.post("/alunos/{aluno_id}/matricular/{disciplina_id}", status_code=status.HTTP_201_CREATED)
def matricular_aluno(aluno_id: int, disciplina_id: int):
    try:
        db.matricular_aluno(aluno_id, disciplina_id)
        return {"message": "Aluno matriculado com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@app.get("/alunos/{aluno_id}/disciplinas", response_model=List[DisciplinaSaida])
def listar_disciplinas_do_aluno(aluno_id: int):
    disciplinas = db.disciplinas_do_aluno(aluno_id)
    if disciplinas is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    return disciplinas

@app.post("/notas", status_code=status.HTTP_201_CREATED)
def cadastrar_nota(nota: nota):
    nota_criada = db.cadastrar_nota(nota.matricula_id, nota.nota_1, nota.nota_2, nota.nota_3)
    return {"message": "Nota cadastrada com sucesso.", "nota": nota_criada}

@app.get("/media/{matricula}", response_model=mediaSaida)
def listar_media(matricula: str):
    media = db.media_aluno(matricula)
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    return media