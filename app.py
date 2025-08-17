from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///miniaturas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(150), nullable=False)
    cor = db.Column(db.String(100), nullable=False)
    ano = db.Column(db.String(4), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)
    lote = db.Column(db.String(100), nullable=True)
    escala = db.Column(db.String(50), nullable=True)
    foto_url = db.Column(db.String(300), nullable=True)

class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    miniatura_id = db.Column(db.Integer, db.ForeignKey('miniatura.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    miniaturas = Miniatura.query.all()
    return render_template('index.html', miniaturas=miniaturas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Login inválido')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(email=email).first():
            flash('Email já registrado.')
            return redirect(url_for('register'))
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Conta criada com sucesso.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    if not current_user.is_admin:
        flash('Apenas administradores podem adicionar miniaturas.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        miniatura = Miniatura(
            nome=request.form['nome'],
            marca=request.form['marca'],
            cor=request.form['cor'],
            ano=request.form['ano'],
            tipo=request.form['tipo'],
            lote=request.form['lote'],
            escala=request.form['escala'],
            foto_url=request.form['foto_url']
        )
        db.session.add(miniatura)
        db.session.commit()
        flash('Miniatura adicionada!')
        return redirect(url_for('index'))
    return render_template('adicionar.html')

@app.route('/colecao')
@login_required
def colecao():
    minhas = db.session.query(Miniatura).join(Colecao).filter(Colecao.user_id == current_user.id).all()
    return render_template('colecao.html', miniaturas=minhas)

@app.route('/colecao/add/<int:miniatura_id>')
@login_required
def add_colecao(miniatura_id):
    if not Colecao.query.filter_by(user_id=current_user.id, miniatura_id=miniatura_id).first():
        nova = Colecao(user_id=current_user.id, miniatura_id=miniatura_id)
        db.session.add(nova)
        db.session.commit()
        flash('Miniatura adicionada à sua coleção!')
    return redirect(url_for('colecao'))

@app.route('/colecao/remove/<int:miniatura_id>')
@login_required
def remove_colecao(miniatura_id):
    item = Colecao.query.filter_by(user_id=current_user.id, miniatura_id=miniatura_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Miniatura removida da sua coleção.')
    return redirect(url_for('colecao'))

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
