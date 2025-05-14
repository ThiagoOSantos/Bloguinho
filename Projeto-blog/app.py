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
''').fetchall()
#--------------------- Rota Registro de Usuario ----------------------------------------       

@app.route('/register', methods=['GET', 'POST'])
def register():
    #Exibir o formulario de cadastro e processar os dados enviados.
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        email = request.form['email']
        senha = request.form['senha']
        #validar se a senha digitada possui no minimo 8 caracteres, 1 maiuscula, 1 numero e 1 simbolo
        if len(senha) <8:
            return "Senha fraca. Requisitos: 8+ caracteres, 1 maiuscula, 1 número e 1 símbolo"
        db = get_db()
        try:
            db.execute('INSERT INTO usuarios (nome, cpf, email, senha) VALUES (?,?,?,?)', (nome, cpf, email, senha))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Error: CPF ou Email já cadastrados."
    return render_template('register.html')

#--------------------- Rota de Login ----------------------------------------       

@app.route('/login', methods=('GET', 'POST'))
def login():
    #Exibir e processar o formulario de login
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        db = get_db()
        usuario = db.execute('SELECT * FROM usuarios WHERE email=? AND senha=?', (email, senha).fetchone())
        if usuario:
            session['usuario_id'] = usuario['id']#A sessão vai servir para identificar aquele usuario enquanto ele estiver logado e usando a aplicação
            session['usuario_nome'] = usuario['nome']
            return redirect(url_for('dashboard'))
        else:
            return "Login inválido"
    return render_template('login.html')

#--------------------- Painel do Usuario ----------------------------------------       

@app.route('/dashboard')
#Exibir os posts do usuario logado.
def dashboard():
    if 'usuario.id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    posts = db.execute('SELECT * FROM posts WHERE autor_id=?', (session['usuario_id'])).fetchall() #Vai buscar dentro do banco de dados os posts do usuario q estiver logado
    return render_template('dashboard.html', posts=posts)

#--------------------- Rota para Criar Novo Post ----------------------------------------       

@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    #Permitir que o usuario logado crie um novo post com ou sem imagem
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        imagem = request.form['imagem']

        nome_arquivo = None
        if imagem and extensao_valida(imagem.filename):
            nome_arquivo = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))
        
        db = get_db()
        db.execute('INSERT INTO posts (titulo, conteudo, imagem, autor_id) VALUES(?,?,?,?)', (titulo, conteudo, nome_arquivo, session['usuario_id']))
        db.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('new_post.html')
    
#--------------------- Rota para Logout ----------------------------------------       

@app.route('/logout')
def logout():
    #Remove o usuario da sessão atual
    session.clear()
    return redirect(url_for('index'))    

#--------------------- Rota para execução principal ----------------------------------------       

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok = True) #Cria a pasta uploads se ela não existir
    inicializar_banco() #Garante que o banco e tabelas sejam criados
    app.run(debug = True)
