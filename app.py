import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configuração do banco (Render usa DATABASE_URL)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL').replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ================= MODELOS =================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    colecao = db.relationship('Colecao', backref='dono', lazy=True)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(100))
    cor = db.Column(db.String(50))
    ano = db.Column(db.String(10))
    tipo = db.Column(db.String(100))
    lote = db.Column(db.String(100))
    escala = db.Column(db.String(50))
    url_foto = db.Column(db.String(300))

class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    miniatura_id = db.Column(db.Integer, db.ForeignKey('miniatura.id'), nullable=False)
    miniatura = db.relationship('Miniatura', backref='colecoes')

# ================= LOGIN =================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================= ROTAS =================
@app.route('/')
def index():
    miniaturas = Miniatura.query.all()
    return render_template('index.html', miniaturas=miniaturas)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe!', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Usuário registrado com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        nome = request.form['nome']
        marca = request.form['marca']
        cor = request.form['cor']
        ano = request.form['ano']
        tipo = request.form['tipo']
        lote = request.form['lote']
        escala = request.form['escala']
        url_foto = request.form['url_foto']

        miniatura = Miniatura(nome=nome, marca=marca, cor=cor, ano=ano, tipo=tipo, lote=lote, escala=escala, url_foto=url_foto)
        db.session.add(miniatura)
        db.session.commit()
        flash('Miniatura adicionada!', 'success')
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/colecao')
@login_required
def colecao():
    colecao = Colecao.query.filter_by(user_id=current_user.id).all()
    return render_template('colecao.html', colecao=colecao)

@app.route('/add_colecao/<int:miniatura_id>')
@login_required
def add_colecao(miniatura_id):
    existente = Colecao.query.filter_by(user_id=current_user.id, miniatura_id=miniatura_id).first()
    if existente:
        flash('Essa miniatura já está na sua coleção!', 'warning')
    else:
        item = Colecao(user_id=current_user.id, miniatura_id=miniatura_id)
        db.session.add(item)
        db.session.commit()
        flash('Miniatura adicionada à sua coleção!', 'success')
    return redirect(url_for('colecao'))

# ================= DB INIT =================
@app.before_request
def init_db():
    db.create_all()

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get("PORT", 5000))
    print("App Minipedia v5 corrigida rodando 🚀")
    serve(app, host="0.0.0.0", port=port)
