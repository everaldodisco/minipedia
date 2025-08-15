
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miniaturas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Tabela de associação para coleção
colecao_table = db.Table('colecao',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('miniatura_id', db.Integer, db.ForeignKey('miniatura.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    colecao = db.relationship('Miniatura', secondary=colecao_table, backref='colecionadores')

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    tipo = db.Column(db.String(50))
    lote = db.Column(db.String(50))
    marca = db.Column(db.String(50))
    cor = db.Column(db.String(50))
    foto = db.Column(db.String(300))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'HEAD'])
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
        else:
            flash('Login inválido')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado')
        else:
            new_user = User(name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Conta criada com sucesso!')
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
    if request.method == 'POST':
        nome = request.form['nome']
        tipo = request.form['tipo']
        lote = request.form['lote']
        marca = request.form['marca']
        cor = request.form['cor']
        foto = request.form['foto']
        nova_miniatura = Miniatura(nome=nome, tipo=tipo, lote=lote, marca=marca, cor=cor, foto=foto)
        db.session.add(nova_miniatura)
        db.session.commit()
        flash('Miniatura adicionada!')
        return redirect(url_for('index'))
    return render_template('adicionar.html')

@app.route('/buscar', methods=['GET', 'POST'])
@login_required
def buscar():
    miniaturas = []
    if request.method == 'POST':
        termo = request.form['termo']
        miniaturas = Miniatura.query.filter(Miniatura.nome.contains(termo)).all()
    return render_template('buscar.html', miniaturas=miniaturas)

@app.route('/adicionar_colecao/<int:miniatura_id>')
@login_required
def adicionar_colecao(miniatura_id):
    miniatura = Miniatura.query.get(miniatura_id)
    if miniatura not in current_user.colecao:
        current_user.colecao.append(miniatura)
        db.session.commit()
        flash('Miniatura adicionada à sua coleção!')
    else:
        flash('Esta miniatura já está na sua coleção.')
    return redirect(url_for('minha_colecao'))

@app.route('/minha_colecao')
@login_required
def minha_colecao():
    return render_template('minha_colecao.html', miniaturas=current_user.colecao)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
