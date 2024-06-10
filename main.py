from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

alunos = []

class Nota(BaseModel):
    Linguagem_de_Programacao : float
    Engenharia_de_Software : float
    Algoritmos : float
    Estrutura_de_Dados : float
class Aluno(BaseModel):
    nome: str
    id: int
    notas: Nota

@app.get("/alunos")
def read():
    return alunos

@app.post("/alunos")
def create(aluno: Aluno):
    aluno.notas = Nota(**{materia: round(valor, 1) for materia, valor in aluno.notas.model_dump().items()})
    if verifica_notas(aluno.notas):
        alunos.append(aluno.__dict__)
        return {"Message": "Aluno adicionado com sucesso"}
    else:
        raise HTTPException(status_code=400, detail="Notas precisam estar entre 0 e 10")

def verifica_notas(notas: Nota):
    return all(0 <= getattr(notas, materia) <= 10 for materia in notas.model_fields)


@app.get("/alunos/{aluno_id}")
def get_aluno_by_id(aluno_id: int):
    for aluno in alunos:
        if aluno["id"] == aluno_id:
            return aluno
    raise HTTPException(status_code=404, detail="Aluno não encontrado")

@app.get("/alunos/{aluno_id}/notas") 
def get_notas_by_aluno_id(aluno_id: int):
    for aluno in alunos:
        if aluno["id"] == aluno_id:
            return aluno["notas"]
    raise HTTPException(status_code=404, detail="Aluno não encontrado")


@app.get("/notas/{materia}")
def get_notas_by_materia(materia: str):
    output = []
    for aluno in alunos:
        notas = aluno["notas"]
        if hasattr(notas, materia):
            output.append({"Nome": aluno['nome'], "nota": getattr(notas, materia)})

    if not output:
        raise HTTPException(status_code=404, detail="Matéria não encontrada")

    return output
