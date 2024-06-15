from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Dict, Any
import csv
import os
import ast
import numpy as np

app = FastAPI()

# Função para carregar os alunos do arquivo CSV
def load_alunos():
    alunos = []
    if os.path.exists('alunos.csv'):
        with open('alunos.csv', mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                aluno = {
                    "nome": row["nome"],
                    "id": int(row["id"]),
                    "notas": ast.literal_eval(row["notas"]) if row["notas"] else None
                }
                alunos.append(aluno)
    return alunos

# Função para salvar os alunos no arquivo CSV
def save_alunos(alunos):
    with open('alunos.csv', mode='w', newline='') as f:
        fieldnames = ["nome", "id", "notas"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for aluno in alunos:
            writer.writerow({
                "nome": aluno["nome"],
                "id": aluno["id"],
                "notas": str(aluno["notas"]) if aluno["notas"] else ""
            })

alunos = load_alunos()

class Aluno(BaseModel):
    nome: str
    id: int
    notas: Optional[Dict[str, Optional[float]]] = None

@app.get("/alunos")
def read():
    """
    Retorna a lista de todos os alunos.
    """
    return alunos

@app.post("/alunos")
def create(aluno: Aluno):
    """
    Adiciona um novo aluno à lista. Se houver notas, garante que estão entre 0 e 10.
    """
    if aluno.notas:
        aluno.notas = {materia: round(valor, 1) if valor is not None else None for materia, valor in aluno.notas.items()}
        if not verifica_notas(aluno.notas):
            raise HTTPException(status_code=400, detail="Notas precisam estar entre 0 e 10")
    alunos.append(aluno.dict())
    save_alunos(alunos)
    return {"Message": "Aluno adicionado com sucesso"}

def verifica_notas(notas: Dict[str, Optional[float]]):
    """
    Verifica se todas as notas estão entre 0 e 10.
    """
    return all(nota is None or (0 <= nota <= 10) for nota in notas.values())

@app.get("/alunos/{aluno_id}")
def get_aluno_by_id(aluno_id: int):
    """
    Retorna um aluno específico pelo seu ID.
    """
    for aluno in alunos:
        if aluno["id"] == aluno_id:
            return aluno
    raise HTTPException(status_code=404, detail="Aluno não encontrado")

@app.get("/alunos/{aluno_id}/notas") 
def get_notas_by_aluno_id(aluno_id: int):
    """
    Retorna as notas de um aluno específico pelo seu ID.
    """
    for aluno in alunos:
        if aluno["id"] == aluno_id:
            return aluno["notas"]
    raise HTTPException(status_code=404, detail="Aluno não encontrado")

@app.get("/notas/{materia}")
def get_notas_by_materia(materia: str):
    """
    Retorna as notas de todos os alunos em uma matéria específica.
    """
    output = []
    for aluno in alunos:
        notas = aluno["notas"]
        if notas is not None and materia in notas:
            if notas[materia] is not None:
                output.append({"Nome": aluno['nome'], "nota": notas[materia]})
    if not output:
        raise HTTPException(status_code=404, detail="Matéria não encontrada")
    return output

@app.get("/notas/{materia}/estatisticas")
def get_estatisticas_by_materia(materia: str):
    """
    Retorna estatísticas (média, mediana, desvio padrão) das notas de uma matéria específica.
    """
    notas = []
    for aluno in alunos:
        if aluno["notas"] is not None and materia in aluno["notas"] and aluno["notas"][materia] is not None:
            notas.append(aluno["notas"][materia])
    if notas:
        media = np.mean(notas)
        mediana = np.median(notas)
        desvio_padrao = np.std(notas)
        return {"media": media, "mediana": mediana, "desvio_padrao": desvio_padrao}
    else:
        raise HTTPException(status_code=404, detail="Matéria não encontrada")

@app.get("/alunos/desempenho")
def get_alunos_desempenho_baixo():
    output = []
    for aluno in alunos:
            for nota in aluno["notas"].values():
                if nota < 6:
                    output.append(aluno)
    return output

@app.delete("/alunos/sem_notas")
def delete_alunos_sem_notas():
    """
    Remove todos os alunos que não possuem notas.
    """
    global alunos
    alunos_com_notas = [aluno for aluno in alunos if aluno["notas"]]
    alunos = alunos_com_notas
    save_alunos(alunos)
    return {"Message": "Alunos sem notas removidos com sucesso"}

@app.delete("/alunos/{aluno_id}")
def delete_aluno_by_id(aluno_id: int):
    """
    Remove um aluno específico pelo seu ID.
    """
    global alunos
    aluno_existente = next((aluno for aluno in alunos if aluno["id"] == aluno_id), None)
    if aluno_existente is None:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    alunos = [aluno for aluno in alunos if aluno["id"] != aluno_id]
    save_alunos(alunos)
    return {"Message": "Aluno removido com sucesso"}
