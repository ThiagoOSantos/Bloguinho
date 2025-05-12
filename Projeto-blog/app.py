import os #biblioteca para lidar com arquivos e diretorios
import re #biblioteca para validações com expressões regulares, ou seja, (senha)
import sqlite3 #biblioteca padrão do Python para Banco de dados SQLite
from flask import Flask, render_template, request, redirect, url_for, session, g #bibiliotecas importantes do Flask
from werkzeug.utils import secure_filename #biblioteca que garante nomes seguros para arquivos enviados

#--------------------- Configuração Inicial do App ----------------------------------------

app = Flask(__name__) #serve para criação da aplicação flask
app.config['SECRET_KEY'] = 'chave_mauri' #chave secreta utilizada nas sessões
app.config['UPLOAD_FOLDER'] = 'static/uploads' #pasta para onde imagens serão salvas
app.config['MAX_CONTENT_LENGTH'] = 2*1024 * 1024 #Limite do tamanho de uploads para 2mb

EXTENSOES = ['png', 'jpg', 'jpeg', 'gif'] #Extensões permitidas

DATABASE = 'users.db' #Nome do banco SQLite

#--------------------- Configuração Inicial do App ----------------------------------------

def get_db():
    # Estabelecer e retornar a conexão com o banco de dados SQLite.
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row #Permite acessar os dados como dicionario (ex: linha['email'])
    return g.db

@app.teardown_appcontext #Automatiza a execução após cada execução por conta desse decorador
def close_db(error):
    # Fechar a conexão com o banco após cada requisição
    #Esse 'g'é um objeto especial do Flask usado para armazenar dados globais da aplicação durante uma requisição (como variaveis)
    ''' da aplicaçção durante uma requisição como variaveis q vc quer acessar em varios lugares durante uma requisiscao http - se n existir retorna none'''
    db = g.pop('db', None) #Remove a conexão com o banco de g e armazena em db. Se não existir, retorna None
    if db is not None: #Se havia uma conexão, ela é fechada
        db.close()

 #--------------------- Função auxiliar para Verificar Extensão da Imagem ----------------------------------------       

def extensao_valida(nome_arquivo):
    # Vverificar se a extensao do arquivo enviado é uma das permitidas
    #Verifica se o nome do arquivo possui um ponto
    #'nome_arquivo.rsplit('.',1): separa o nome do aqruivo da extensao, da direita para a esquerda, uma vez só
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1).lower in EXTENSOES

 #--------------------- Criação das Tabelas (executar uma única vez) ----------------------------------------       

def inicializar_banco():
    # Criar as tabelas do banco caso não existam
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS usuarios(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   nome TEXT NOT NULL,
                   cpf TEXT UNIQUE NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   senha TEXT NOT NULL
            );
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS posts(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   titulo TEXT NOT NULL,
                   conteudo TEXT NOT NULL,
                   imagem TEXT, 
                   autor_id INTEGER NOT NULL,
                   FOREING KEY (autor_id) REFERENCES usuarios(id)
                );
            ''')
        db.commit()

#--------------------- Rota Principal(index) ----------------------------------------       

@app.route('/')
def index():
    # Exibir todos os posts públicos na página inicial
    db = get_db()
    posts = db.execute('''
        SELECT p.titulo, p.conteudo, p.imagem, u.nome FROM posts p
        JOIN usuarios u ON p.autor_id = u.id
''')
#--------------------- Rota Registro de Usuario ----------------------------------------       

@app.route('/register', methods=['GET', 'POST'])