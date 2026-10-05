"""
CAMADA DE VALIDAÇÃO (schemas.py)  —  ESQUELETO, implemente você mesmo
====================================================================

"Schema" = o formato/contrato dos dados. Com Pydantic, você declara COMO os
dados devem ser quando ENTRAM e quando SAEM da API. O Pydantic valida sozinho:
se o cliente mandar idade=200 ou nome vazio, a API responde 422 automaticamente.

Boas práticas que você deve aplicar:
  - Separe ENTRADA (o que o cliente manda) de SAÍDA (o que a API devolve).
  - Na entrada de criação, NÃO inclua o id (quem gera é o banco).
  - Na saída, inclua o id.
  - Campos sensíveis (ex.: senha) podem entrar, mas NUNCA sair.
"""

# DICA — o que você vai importar:
from typing import Optional
from pydantic import BaseModel, Field  # type: ignore[reportMissingImports]
from datetime import datetime
from pydantic import EmailStr  # type: ignore[reportMissingImports]

# --------------------------------------------------------------------------
# ALUNO
# --------------------------------------------------------------------------
# TODO: AlunoEntrada  (POST) — campos: nome, idade, matricula, media (sem id)
#   Dica: valide com Field, ex.: nome=Field(min_length=1, max_length=100),
#   idade=Field(ge=0, le=120), media=Field(default=0, ge=0, le=10).
class AlunoEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    idade: int = Field(ge=0, le=120)
#
# TODO: AlunoAtualizacao  (PATCH) — mesmos campos, mas TODOS Optional (=None),
#   para o cliente enviar só o que quer mudar. (A matrícula não se altera.)

class AlunoAtualizacao(BaseModel):
    nome: Optional[str] = Field(min_length=1, max_length=100)
    idade: Optional[int] = Field(ge=0, le=120)
#
# TODO: AlunoSaida  — o que a API devolve, incluindo o id.

class AlunoSaida(BaseModel):
    id: int
    nome: str
    idade: int
    matricula: str

# --------------------------------------------------------------------------
# DISCIPLINA  (Desafio 2)
# --------------------------------------------------------------------------
# TODO: DisciplinaEntrada (nome, carga_horaria) e DisciplinaSaida (id, nome,
#   carga_horaria). Dica: carga_horaria=Field(gt=0) exige valor positivo.

class DisciplinaEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    carga_horaria: int = Field(gt=0)

class DisciplinaSaida(BaseModel):
    id: int
    nome: str
    carga_horaria: int
    
class UsuarioSaida(BaseModel):
    id: int
    email: EmailStr
    criado_em: datetime
    
class UsuarioEntrada(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)
    
class LoginOk(BaseModel):
    message: str
    usuario: UsuarioSaida
    
class nota(BaseModel):
    matricula_id: int
    nota_1: Optional[float] = Field(ge=0, le=10)
    nota_2: Optional[float] = Field(ge=0, le=10)
    nota_3: Optional[float] = Field(ge=0, le=10)
    
class mediaSaida(BaseModel):
    matricula: str
    nota_1: Optional[float] = Field(ge=0, le=10)
    nota_2: Optional[float] = Field(ge=0, le=10)
    nota_3: Optional[float] = Field(ge=0, le=10)
    media: float = Field(ge=0, le=10)
