# app.py — Minipedia v6.6 (corrigido schema User)

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Extensões
login_manager = LoginManager()
login_manager.login_view = 'login'

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'minipedia-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///minipedia.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="user")

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html', title="Minipedia")

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('Bem-vindo de volta, ' + user.username + '!', 'success')
                return redirect(url_for('index'))
            flash('Usuário ou senha inválidos', 'danger')
        return render_template('login.html', title="Login - Minipedia")

    @app.route('/logout')
    def logout():
        logout_user()
        flash('Você saiu da sua conta.', 'info')
        return redirect(url_for('index'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form.get('email')
            password = request.form['password']
            if User.query.filter_by(username=username).first():
                flash('Usuário já existe!', 'warning')
            else:
                hashed_pw = generate_password_hash(password, method='sha256')
                new_user = User(username=username, email=email, password=hashed_pw)
                db.session.add(new_user)
                db.session.commit()
                flash('Cadastro realizado com sucesso! Faça login.', 'success')
                return redirect(url_for('login'))
        return render_template('register.html', title="Cadastro - Minipedia")

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
                flash('Essa miniatura já está na sua coleção!', 'warning')
            else:
                colecao = Colecao(user_id=current_user.id, miniatura_id=mini.id)
                db.session.add(colecao)
                db.session.commit()
                flash('Miniatura adicionada à sua coleção!', 'success')

            return redirect(url_for('colecao'))
        return render_template('adicionar.html', title="Adicionar Miniatura - Minipedia")

    @app.route('/colecao')
    @login_required
    def colecao():
        itens = Colecao.query.filter_by(user_id=current_user.id).all()
        return render_template('colecao.html', itens=itens, title="Minha Coleção - Minipedia")

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
