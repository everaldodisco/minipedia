# app.py — Minipedia v6.3

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minipedia-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///minipedia.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configuração do Login Manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(50), nullable=False)
    cor = db.Column(db.String(30))
    ano = db.Column(db.String(10))
    tipo = db.Column(db.String(50))
    lote = db.Column(db.String(50))
    escala = db.Column(db.String(20))
    foto_url = db.Column(db.String(200))

class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    miniatura_id = db.Column(db.Integer, db.ForeignKey('miniatura.id'))
    user = db.relationship('User', backref=db.backref('colecao', lazy=True))
    miniatura = db.relationship('Miniatura', backref=db.backref('colecoes', lazy=True))

# Função obrigatória para o Flask-Login carregar o usuário
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Criação automática das tabelas no deploy
with app.app_context():
    db.create_all()

# Rotas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        flash('Usuário ou senha inválidos')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    if request.method == 'POST':
        nome = request.form['nome']
        marca = request.form['marca']
        cor = request.form['cor']
        ano = request.form['ano']
        tipo = request.form['tipo']
        lote = request.form['lote']
        escala = request.form['escala']
        foto_url = request.form['foto_url']

        mini = Miniatura.query.filter_by(nome=nome, marca=marca, lote=lote, escala=escala).first()
        if not mini:
            mini = Miniatura(nome=nome, marca=marca, cor=cor, ano=ano, tipo=tipo, lote=lote, escala=escala, foto_url=foto_url)
            db.session.add(mini)
            db.session.commit()

        ja_tem = Colecao.query.filter_by(user_id=current_user.id, miniatura_id=mini.id).first()
        if ja_tem:
            flash('Essa miniatura já está na sua coleção!')
        else:
            colecao = Colecao(user_id=current_user.id, miniatura_id=mini.id)
            db.session.add(colecao)
            db.session.commit()
            flash('Miniatura adicionada à sua coleção!')

        return redirect(url_for('colecao'))
    return render_template('adicionar.html')

@app.route('/colecao')
@login_required
def colecao():
    itens = Colecao.query.filter_by(user_id=current_user.id).all()
    return render_template('colecao.html', itens=itens)

if __name__ == '__main__':
    app.run(debug=True)
