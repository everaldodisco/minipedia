from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minipedia_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/minipedia'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ----------------- MODELOS -----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(100), nullable=False)
    cor = db.Column(db.String(50))
    ano = db.Column(db.Integer)
    tipo = db.Column(db.String(50))
    lote = db.Column(db.String(50))
    escala = db.Column(db.String(20))
    url_foto = db.Column(db.String(300))

class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    miniatura_id = db.Column(db.Integer, db.ForeignKey('miniatura.id'))
    __table_args__ = (db.UniqueConstraint('user_id', 'miniatura_id', name='_user_miniatura_uc'),)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------- ROTAS -----------------
@app.route('/')
def index():
    miniaturas = Miniatura.query.all()
    return render_template('index.html', miniaturas=miniaturas)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(email=email, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Usuário registrado com sucesso!", "success")
            return redirect(url_for('login'))
        except:
            flash("Erro: esse email já está registrado!", "danger")
    return render_template('register.html')

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
            flash("Credenciais inválidas", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_miniatura', methods=['GET', 'POST'])
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

        existente = Miniatura.query.filter_by(nome=nome, marca=marca).first()
        if existente:
            flash("Essa miniatura já está cadastrada!", "warning")
        else:
            mini = Miniatura(nome=nome, marca=marca, cor=cor, ano=ano, tipo=tipo,
                             lote=lote, escala=escala, url_foto=url_foto)
            db.session.add(mini)
            db.session.commit()
            flash("Miniatura adicionada com sucesso!", "success")
            return redirect(url_for('index'))
    return render_template('add_miniatura.html')

@app.route('/resetdb')
def reset_db():
    try:
        db.drop_all()
        db.create_all()
        return "✅ Banco de dados resetado e recriado com sucesso!"
    except Exception as e:
        return f"❌ Erro ao resetar o banco: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
