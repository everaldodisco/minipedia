
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

def _normalize_db_url(url: str) -> str:
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = _normalize_db_url(
    os.getenv('DATABASE_URL', 'sqlite:///minipedia.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Models ---

# relationship table for user's collection/selection of minis
colecao = db.Table(
    'colecao',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('miniatura_id', db.Integer, db.ForeignKey('miniatura.id'), primary_key=True),
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    # 300 to avoid truncation for long password hashes on Postgres
    password = db.Column(db.String(300), nullable=False)
    role = db.Column(db.String(50), default='user')

    # many-to-many: user's collection of minis
    colecao_miniaturas = db.relationship(
        'Miniatura',
        secondary=colecao,
        backref=db.backref('colecionadores', lazy='dynamic'),
        lazy='dynamic'
    )

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(150), nullable=False)
    ano = db.Column(db.String(4), nullable=False)
    escala = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---

@app.route('/')
@login_required
def index():
    miniaturas = Miniatura.query.order_by(Miniatura.id.desc()).all()
    # set of ids in user's collection for quick lookup
    colecao_ids = set()
    if current_user.is_authenticated:
        colecao_ids = {m.id for m in current_user.colecao_miniaturas.all()}
    return render_template('index.html', miniaturas=miniaturas, colecao_ids=colecao_ids)

# Auth

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Usuário ou senha inválidos!', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Usuário ou email já existe!', 'error')
            return redirect(url_for('register'))
        new_user = User(username=username, email=email, password=generate_password_hash(password), role='user')
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário registrado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Miniaturas (CRUD)

def _require_admin():
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Acesso negado. Somente admin.', 'error')
        return False
    return True

@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    if not _require_admin():
        return redirect(url_for('index'))
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        marca = request.form['marca'].strip()
        ano = request.form['ano'].strip()
        escala = request.form['escala'].strip()
        if not nome or not marca or not ano or not escala:
            flash('Todos os campos são obrigatórios.', 'error')
            return redirect(url_for('adicionar'))
        mini = Miniatura(nome=nome, marca=marca, ano=ano, escala=escala)
        db.session.add(mini)
        db.session.commit()
        flash('Miniatura adicionada!', 'success')
        return redirect(url_for('index'))
    return render_template('adicionar.html')

@app.route('/editar/<int:mini_id>', methods=['GET', 'POST'])
@login_required
def editar(mini_id):
    if not _require_admin():
        return redirect(url_for('index'))
    mini = Miniatura.query.get_or_404(mini_id)
    if request.method == 'POST':
        mini.nome = request.form['nome'].strip()
        mini.marca = request.form['marca'].strip()
        mini.ano = request.form['ano'].strip()
        mini.escala = request.form['escala'].strip()
        db.session.commit()
        flash('Miniatura atualizada!', 'success')
        return redirect(url_for('index'))
    return render_template('editar.html', mini=mini)

@app.route('/excluir/<int:mini_id>', methods=['POST'])
@login_required
def excluir(mini_id):
    if not _require_admin():
        return redirect(url_for('index'))
    mini = Miniatura.query.get_or_404(mini_id)
    # remove from all collections first due to FK
    for user in mini.colecionadores.all():
        user.colecao_miniaturas.remove(mini)
    db.session.delete(mini)
    db.session.commit()
    flash('Miniatura excluída!', 'success')
    return redirect(url_for('index'))

# Coleção (seleção) do usuário

@app.route('/colecao')
@login_required
def ver_colecao():
    minis = current_user.colecao_miniaturas.order_by(Miniatura.id.desc()).all()
    return render_template('colecao.html', miniaturas=minis)

@app.route('/colecao/adicionar/<int:mini_id>', methods=['POST'])
@login_required
def colecao_adicionar(mini_id):
    mini = Miniatura.query.get_or_404(mini_id)
    if not current_user.colecao_miniaturas.filter(Miniatura.id == mini.id).first():
        current_user.colecao_miniaturas.append(mini)
        db.session.commit()
        flash('Adicionada à sua coleção.', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/colecao/remover/<int:mini_id>', methods=['POST'])
@login_required
def colecao_remover(mini_id):
    mini = Miniatura.query.get_or_404(mini_id)
    if current_user.colecao_miniaturas.filter(Miniatura.id == mini.id).first():
        current_user.colecao_miniaturas.remove(mini)
        db.session.commit()
        flash('Removida da sua coleção.', 'success')
    return redirect(request.referrer or url_for('ver_colecao'))

# --- App bootstrap ---

with app.app_context():
    db.create_all()
    # bootstrap admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@minipedia.com',
            password=generate_password_hash('admin'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

# entrypoint for Render: waitress calls "app:app"
if __name__ == '__main__':
    app.run(debug=True)
