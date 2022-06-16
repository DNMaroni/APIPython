from flask import Flask, jsonify, request, Response
import sqlite3, json, requests
from sqlite3 import Error

app = Flask(__name__)


def response(resposta):
	return jsonify({
   	'resposta': resposta
	})

def connectDatabase(command):
    sqliteConnection = sqlite3.connect('database.db')
    cursor = sqliteConnection.cursor()
    print("Database created and Successfully Connected to SQLite")
    sqlite_select_Query = "CREATE TABLE IF NOT EXISTS contas (codigo INTEGER PRIMARY KEY AUTOINCREMENT, nomeproprietario CHAR, tipo CHAR, saldo NUMERIC);"
    cursor.execute(sqlite_select_Query)

    cursor.execute(command)
    sqliteConnection.commit()

    return cursor

@app.route("/")
def hello_world():
	return response("Para acessar a api utilize o endpoint /contas. Para acessar os serviços utilize /servicos")

@app.route('/contas/', methods=['GET'])
def list():


    try:
        cursor = connectDatabase("SELECT * FROM contas")
        record = cursor.fetchall()
        cursor.close()

        if(record == []):
            return response('Ainda não existem contas no banco de dados'), 404
        else:
            return response(record), 200

    except sqlite3.Error as er:
        return response('Erro ao selecionar do banco de dados: %s' % (' '.join(er.args))), 404
    
    


@app.route('/contas/<int:pk>/', methods=['GET'])
def retrieve(pk):
    try:
        cursor = connectDatabase("SELECT * FROM contas WHERE codigo = "+str(pk))
        record = cursor.fetchall()
        cursor.close()

        if(record == []):
            return response('Conta não encontrada'), 404
        else:
            return response(record), 200

    except sqlite3.Error as er:
        return response('Erro ao selecionar do banco de dados: %s' % (' '.join(er.args))), 404


@app.route("/contas", methods=['POST'])
def cadastrar():

    try:
        nomeprop = request.form['nomeproprietario']
        tipo = request.form['tipo']
        saldo = request.form['saldo']
    except:
        return response('Alguns dos atributos não está presente: nomeproprietario, tipo ou saldo.'), 400

    try:

        cursor = connectDatabase("INSERT INTO contas (nomeproprietario, tipo, saldo) VALUES ('"+nomeprop+"', '"+tipo+"', "+saldo+");")
        cursor.close()

        return response('Conta criada com sucesso.'), 201

    except sqlite3.Error as er:
        return response('Erro ao criar conta: %s' % (' '.join(er.args))), 404


@app.route("/contas/<int:pk>/", methods=['PUT'])
def atualizar(pk):

    cursor = connectDatabase("SELECT * FROM contas WHERE codigo = "+str(pk))
    record = cursor.fetchall()
    cursor.close()

    if(record == []):
        return response('Conta não encontrada'), 404

    nomeproprietario = ''
    tipo = ''
    saldo = ''
    sqlcolumns = []
    sqlstring = ''

    count = 0
    if request.form.get("nomeproprietario", None):
        nomeproprietario = request.form['nomeproprietario']
        sqlcolumns.append("nomeproprietario = '"+nomeproprietario+"'")
        count+=1
    
    if request.form.get("tipo", None):
        tipo = request.form['tipo']
        sqlcolumns.append("tipo = '"+tipo+"'")
        count+=1
    
    if request.form.get("saldo", None):
        saldo = request.form['saldo']
        sqlcolumns.append("saldo = '"+saldo+"'")
        count+=1

    if(count == 0):
        return response('Pelo menos um dos atributos precisa estar presente: nomeproprietario, tipo ou saldo'), 400

    sqlstring = ', '.join(sqlcolumns)

    try:

        cursor = connectDatabase('UPDATE contas SET '+sqlstring+' WHERE codigo = '+str(pk))
        cursor.close()

        return response('Conta atualizada com sucesso.'), 200

    except sqlite3.Error as er:
        return response('Erro ao atualizar conta: %s' % (' '.join(er.args))), 404


@app.route("/contas/<int:pk>/", methods=['DELETE'])
def deletar(pk):    
    
    cursor = connectDatabase("SELECT * FROM contas WHERE codigo = "+str(pk))
    record = cursor.fetchall()
    cursor.close()

    if(record == []):
        return response('Conta não encontrada'), 404

    try:

        cursor = connectDatabase("DELETE FROM contas WHERE codigo = "+ str(pk))
        cursor.close()

        return response('Conta deletada com sucesso.'), 200

    except sqlite3.Error as er:
        return response('Erro ao deletar conta: %s' % (' '.join(er.args))), 404


@app.route("/servicos", methods=['GET'])
def servicos(): 
    return response('Esses são os seguintes serviços: /servicos/lesaldo, /servicos/deposita, /servicos/retira')

@app.route("/servicos/lesaldo/", methods=['POST'])
def lesaldo():    
    
    try:
        codigo = request.form['codigo']
    except:
        return response('Alguns dos atributos não está presente: codigo'), 400
    

    resposta = requests.get("http://localhost:5000/contas/"+codigo)
        
    if(resposta.status_code == 404):
        return response('Conta não encontrada'), 404
    
    conteudo = json.loads(resposta.text)

    return response('Saldo da conta de código '+ str(codigo) + ': R$ '+ str(conteudo['resposta'][0][3])), 200

@app.route("/servicos/deposita/", methods=['POST'])
def deposita():
    try:
        codigo = request.form['codigo']
        valor = request.form['valor']
    except:
        return response('Alguns dos atributos não está presente: codigo, valor'), 400
    
    resposta = requests.get("http://localhost:5000/contas/"+codigo)

    if(resposta.status_code == 404):
        return response('Conta não encontrada'), 404

    conteudo = json.loads(resposta.text)
    saldo = conteudo['resposta'][0][3] + float(valor)

    dados={"saldo":saldo}
    resposta = requests.put("http://localhost:5000/contas/"+codigo, data=dados)
        
    if(resposta.status_code == 404):
        return response('Conta não encontrada'), 404
    
    return response('Valor depositado com sucesso.')


@app.route("/servicos/retira/", methods=['POST'])
def retira():
    try:
        codigo = request.form['codigo']
        valor = request.form['valor']
    except:
        return response('Alguns dos atributos não está presente: codigo, valor'), 400
    
    resposta = requests.get("http://localhost:5000/contas/"+codigo)

    if(resposta.status_code == 404):
        return response('Conta não encontrada'), 404

    conteudo = json.loads(resposta.text)

    if(conteudo['resposta'][0][3] < float(valor)):
        return response('Saldo insuficiente para retirar'), 400

    saldo = conteudo['resposta'][0][3] - float(valor)

    dados={"saldo":saldo}
    resposta = requests.put("http://localhost:5000/contas/"+codigo, data=dados)
        
    if(resposta.status_code == 404):
        return response('Conta não encontrada'), 404
    
    return response('Valor retirado com sucesso.')