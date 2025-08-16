from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minipedia-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///minipedia.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    colecao = db.relationship('Colecao', backref='dono', lazy=True)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(100), nullable=False)
    cor = db.Column(db.String(50), nullable=False)
    ano = db.Column(db.String(4), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)
    lote = db.Column(db.String(100), nullable=True)
    escala = db.Column(db.String(50), nullable=False)
    url_foto = db.Column(db.String(300), nullable=True)

class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    miniatura_id = db.Column(db.Integer, db.ForeignKey('miniatura.id'), nullable=False)
    miniatura = db.relationship('Miniatura', backref='colecoes')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    miniaturas = Miniatura.query.all()
    return render_template('index.html', miniaturas=miniaturas)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe')
        else:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            flash('Cadastro realizado com sucesso!')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/miniaturas')
def miniaturas():
    miniaturas = Miniatura.query.all()
    return render_template('miniaturas.html', miniaturas=miniaturas)

@app.route('/miniaturas/add', methods=['GET','POST'])
@login_required
def add_miniatura():
    if request.method == 'POST':
        nome = request.form['nome']
        marca = request.form['marca']
        cor = request.form['cor']
        ano = request.form['ano']
        tipo = request.form['tipo']
        lote = request.form['lote']
        escala = request.form['escala']
        url_foto = request.form['url_foto']
        mini = Miniatura(nome=nome, marca=marca, cor=cor, ano=ano, tipo=tipo, lote=lote, escala=escala, url_foto=url_foto)
        db.session.add(mini)
        db.session.commit()
        flash('Miniatura cadastrada com sucesso!')
        return redirect(url_for('miniaturas'))
    return render_template('add_miniatura.html')

@app.route('/colecao')
@login_required
def colecao():
    colecao = Colecao.query.filter_by(user_id=current_user.id).all()
    return render_template('colecao.html', colecao=colecao)

@app.route('/colecao/add/<int:miniatura_id>')
@login_required
def add_to_colecao(miniatura_id):
    existe = Colecao.query.filter_by(user_id=current_user.id, miniatura_id=miniatura_id).first()
    if not existe:
        item = Colecao(user_id=current_user.id, miniatura_id=miniatura_id)
        db.session.add(item)
        db.session.commit()
        flash('Miniatura adicionada à sua coleção!')
    else:
        flash('Essa miniatura já está na sua coleção.')
    return redirect(url_for('colecao'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
