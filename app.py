from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
<<<<<<< HEAD
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")

# Config do banco
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///minipedia.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Ajuste para compatibilidade com o PostgreSQL no Render
if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres://"):
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"].replace(
        "postgres://", "postgresql://", 1
    )

# DB + Login
=======
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minipedia.db'
>>>>>>> 12a4e9b (Ajustes no projeto Minipedia)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

<<<<<<< HEAD
# ---------------------
# MODELOS
# ---------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # espaço suficiente p/ hash scrypt
    role = db.Column(db.String(20), default="user")

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
=======
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
>>>>>>> 12a4e9b (Ajustes no projeto Minipedia)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

<<<<<<< HEAD
# ---------------------
# SETUP INICIAL (tabelas + admin)
# ---------------------
with app.app_context():
    db.create_all()
    # cria admin padrão se não existir
    if not User.query.filter_by(email="admin@miniaturas.local").first():
        admin = User(
            name="Administrador",
            email="admin@miniaturas.local",
            password=generate_password_hash("admin", method="scrypt"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        print("👤 Usuário admin criado: admin@miniaturas.local / admin")

# ---------------------
# ROTAS PÚBLICAS
# ---------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return redirect(url_for("index"))

@app.route("/health")
def health():
    return {"status": "ok"}

# ---------------------
# AUTENTICAÇÃO
# ---------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("index"))
        flash("Credenciais inválidas!", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout realizado com sucesso!", "info")
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST"]:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        raw_password = request.form.get("password", "")

        if not name or not email or not raw_password:
            flash("Preencha todos os campos.", "warning")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("E-mail já registrado!", "danger")
        else:
            password_hash = generate_password_hash(raw_password, method="scrypt")
            new_user = User(name=name, email=email, password=password_hash)
            db.session.add(new_user)
            db.session.commit()
            flash("Cadastro realizado com sucesso! Faça login.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

# ---------------------
# COLEÇÃO (PROTEGIDA)
# ---------------------
@app.route("/colecao")
@login_required
def colecao():
    cars = Car.query.order_by(Car.brand, Car.model).all()
    return render_template("colecao.html", cars=cars)

@app.route("/colecao/add", methods=["POST"])
@login_required
def add_car():
    brand = request.form.get("brand", "").strip()
    model = request.form.get("model", "").strip()
    year = request.form.get("year", "").strip()

    if not brand or not model or not year.isdigit():
        flash("Informe marca, modelo e ano (número).", "warning")
        return redirect(url_for("colecao"))

    car = Car(brand=brand, model=model, year=int(year))
    db.session.add(car)
    db.session.commit()
    flash("Carro adicionado!", "success")
    return redirect(url_for("colecao"))

@app.route("/colecao/delete/<int:car_id>")
@login_required
def delete_car(car_id):
    car = db.session.get(Car, car_id)
    if car:
        db.session.delete(car)
        db.session.commit()
        flash("Carro removido!", "info")
    else:
        flash("Carro não encontrado.", "warning")
    return redirect(url_for("colecao"))

# ---------------------
# ERROS
# ---------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("base.html", content="Página não encontrada."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("base.html", content="Erro interno do servidor."), 500

# ---------------------
# MAIN
# ---------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
=======
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
        flash('Login inválido')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário registrado com sucesso!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/colecao')
@login_required
def colecao():
    cars = Car.query.all()
    return render_template('colecao.html', cars=cars)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
>>>>>>> 12a4e9b (Ajustes no projeto Minipedia)
