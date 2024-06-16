from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import csv
# OS utilizado para verificar a exsitencia do arquivo alunos.csv, para evitar o uso de um try except
import os
# ast foi utilizado para Converter string do csv em um dicionario python na hora de trazer todos os alunos de volta
import ast
# numpy utilizado para fazer as estatisticas como média, mediana e desvio padrão
import numpy as np

app = FastAPI()

# Carregar os alunos do arquivo CSV e salvar eles dentro de uma lista alunos
def load_alunos():
    alunos = []
    # Se o arquivo não existir a função vai criar ele, caso exista, vai apenas abrir o arquivo
    if os.path.exists('alunos.csv'):
        with open('alunos.csv', mode='r') as f:
            reader = csv.DictReader(f)
            # Cria um dicionario python para cada linha do arquivo CSV, pois cada linha dele armazena um aluno
            for row in reader:
                aluno = {
                    "nome": row["nome"],
                    "id": int(row["id"]),
                    # ast.literal_eval(row["notas"]) converte a string row["notas"] 
                    # de volta para um dicionário Python ({'matematica': 8.5, 'portugues': 7.0}).
                    "notas": ast.literal_eval(row["notas"]) if row["notas"] else None
                }
                alunos.append(aluno)
    return alunos

# Salvar os alunos no arquivo CSV
# Pega a lista de alunos e adiciona ela ao arquivo
def save_alunos(alunos):
    with open('alunos.csv', mode='w', newline='') as f:
        fieldnames = ["nome", "id", "notas"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # Write header, pois os arquivos csv tem titulos para cada coluna, nesse caso coluna 1 nome, 2 id, e 3 notas
        writer.writeheader()
        for aluno in alunos:
            writer.writerow({
                "nome": aluno["nome"],
                "id": aluno["id"],
                "notas": str(aluno["notas"]) if aluno["notas"] else ""
            })
# Carrega o CSV para dentro da lista
alunos = load_alunos()

class Aluno(BaseModel):
    nome: str
    id: int
    notas: Optional[Dict[str, Optional[float]]] = None

#Retorna a lista de todos os alunos.
@app.get("/alunos")
def read():
    return alunos



# Adiciona um novo aluno à lista. Se houver notas, garante que estão entre 0 e 10 com a função verifica notas.
@app.post("/alunos")
def create(aluno: Aluno):
    if aluno.notas:
        # Arredondando todas as notas para ter apenas 1 casa decimal
        aluno.notas = {materia: round(valor, 1) if valor is not None else None for materia, valor in aluno.notas.items()}
        if not verifica_notas(aluno.notas):
            # Caso verifica_notas retorne falso, ocorre o erro abaixo
            raise HTTPException(status_code=400, detail="Notas precisam estar entre 0 e 10")
    alunos.append(aluno.model_dump())
    save_alunos(alunos)
    return {"Message": "Aluno adicionado com sucesso"}


# Verifica se todas as notas estão entre 0 e 10.
def verifica_notas(notas: Dict[str, Optional[float]]):
    # A função faz basicamente isso abaixo
    '''  for nota in notas.values():
        if nota is not None and not (0 <= nota <= 10):
            return False
    return True'''
    return all(nota is None or (0 <= nota <= 10) for nota in notas.values())


# Retorna um aluno específico pelo seu ID.
@app.get("/alunos/{aluno_id}")
def get_aluno_by_id(aluno_id: int):
    # Itera sobre a lista alunos e verifica se o campo ID é igual ao id passado na URL
    for aluno in alunos:
        if aluno["id"] == aluno_id:
            return aluno
    raise HTTPException(status_code=404, detail="Aluno não encontrado")

# Retorna as notas de um aluno específico pelo seu ID.
@app.get("/alunos/{aluno_id}/notas") 
def get_notas_by_aluno_id(aluno_id: int):
    # funciona exatamente igual a função get_aluno_by_id porem dessa vez retorna apenas as notas
    for aluno in alunos:
        if aluno["id"] == aluno_id:
            return aluno["notas"]
    raise HTTPException(status_code=404, detail="Aluno não encontrado")


# Retorna as notas de todos os alunos em uma matéria específica.
@app.get("/notas/{materia}")
def get_notas_by_materia(materia: str):
    output = []
    # Itera sobre a lista de alunos
    for aluno in alunos:
        # Passa o dicionario aluno["notas"] que contem "Materia": valor, para uma variavel "notas"
        notas = aluno["notas"]
        # Itera sobre "notas" e retorna o nome do aluno e apenas o valor de cada materia
        if notas is not None and materia in notas:
            if notas[materia] is not None:
                output.append({"Nome": aluno['nome'], "nota": notas[materia]})
    if not output:
        raise HTTPException(status_code=404, detail="Matéria não encontrada")
    return output

# Retorna estatísticas (média, mediana, desvio padrão) das notas de uma matéria específica.
@app.get("/notas/{materia}/estatisticas")
def get_estatisticas_by_materia(materia: str):
    notas = []
    for aluno in alunos:
        # Verifica se notas não está vazio, e se a materia tem algum valor, e adiciona esse valor na lista "notas"
        # depois utilizamos o numpy para trazer as estatisticas 
        if aluno["notas"] is not None and materia in aluno["notas"] and aluno["notas"][materia] is not None:
            notas.append(aluno["notas"][materia])
    if notas:
        media = np.mean(notas)
        mediana = np.median(notas)
        desvio_padrao = np.std(notas)
        return {"media": media, "mediana": mediana, "desvio_padrao": desvio_padrao}
    else:
        raise HTTPException(status_code=404, detail="Matéria não encontrada")

# Retorna alunos que tenham 1 nota ou mais abaixo de 6
@app.get("/desempenho")
def get_alunos_desempenho_baixo():
    # Apenas itera sobre alunos e verifica cada nota
###### DEV: ARRUMAR A ROTA POIS QUANDO A ROTA É ALUNOS/DESEMPENHO A FUNÇÃO NÃO FUNCIONA ######
    output = []
    for aluno in alunos:
        notas = aluno.get("notas", {}) 
        if notas:
            if any(nota is not None and nota < 6 for nota in notas.values()):
                output.append(aluno)
    return output

# Deleta alunos em que não tiverem nenhuma nota cadastrada em nenhuma materia Ex:
'''
{
  "nome": "João",
  "id": 2,
  "notas": {}
}
'''
@app.delete("/alunos/sem_notas")
def delete_alunos_sem_notas():
    # Itera sob todos os alunos e salva apenas os que possuem materias cadastradas novamente
    # é necessario o uso da variavel global alunos,caso contrario o python não consegue acessar 
    global alunos
    alunos_com_notas = [aluno for aluno in alunos if aluno["notas"]]
    alunos = alunos_com_notas
    save_alunos(alunos)
    return {"Message": "Alunos sem notas removidos com sucesso"}


# Remove um aluno pelo seu ID.
@app.delete("/alunos/{aluno_id}")
def delete_aluno_by_id(aluno_id: int):
    # A linha abaixo faz o seguinte
    '''aluno_existente = None
    for aluno in alunos:
    if aluno["id"] == aluno_id:
        aluno_existente = aluno
        break
    '''
    # Verifica  em toda a lista aluno se alguem possui o ID igual o ID passado, e salva apenas os que tem o id diferente 
    # é necessario o uso da variavel global alunos,caso contrario o python não consegue acessar 
    global alunos
    aluno_existente = next((aluno for aluno in alunos if aluno["id"] == aluno_id), None)
    if aluno_existente is None:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    alunos = [aluno for aluno in alunos if aluno["id"] != aluno_id]
    save_alunos(alunos)
    return {"Message": "Aluno removido com sucesso"}