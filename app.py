import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Configuração do app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minipedia-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///minipedia.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Corrigir prefixo postgres:// → postgresql://
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)  # Aumentado para suportar hashes longos
    role = db.Column(db.String(50), default="user")

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(150), nullable=False)
    ano = db.Column(db.String(4), nullable=False)
    escala = db.Column(db.String(20), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas
@app.route("/")
def index():
    miniaturas = Miniatura.query.all()
    return render_template("index.html", miniaturas=miniaturas)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Usuário ou senha incorretos.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Usuário ou email já cadastrados.")
            return redirect(url_for("register"))
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role="user"
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Cadastro realizado! Faça login.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar():
    if current_user.role != "admin":
        flash("Apenas administradores podem adicionar miniaturas.")
        return redirect(url_for("index"))
    if request.method == "POST":
        nome = request.form.get("nome")
        marca = request.form.get("marca")
        ano = request.form.get("ano")
        escala = request.form.get("escala")
        nova = Miniatura(nome=nome, marca=marca, ano=ano, escala=escala)
        db.session.add(nova)
        db.session.commit()
        flash("Miniatura adicionada!")
        return redirect(url_for("index"))
    return render_template("adicionar.html")

# Inicialização do banco e admin padrão
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            email="admin@minipedia.com",
            password=generate_password_hash("admin"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
