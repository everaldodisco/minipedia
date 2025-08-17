from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# Secret key & DB URL
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "minipedia-secret")
db_url = os.getenv("DATABASE_URL", "sqlite:///minipedia.db")
# Normalize postgres:// to postgresql:// (Render sometimes provides the old scheme)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------------------- Models ----------------------
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    # 300 to avoid truncation with hashed passwords
    password = db.Column(db.String(300), nullable=False)
    role = db.Column(db.String(50), default="user")

class Miniatura(db.Model):
    __tablename__ = "miniatura"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(150), nullable=False)
    ano = db.Column(db.String(4), nullable=False)
    escala = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

# ---------------------- Routes ----------------------
@app.route("/")
@login_required
def index():
    miniaturas = Miniatura.query.order_by(Miniatura.id.desc()).all()
    return render_template("index.html", miniaturas=miniaturas)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Usuário ou senha inválidos!", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("register"))
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Usuário ou e-mail já existe.", "error")
            return redirect(url_for("register"))
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role="user"
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Usuário registrado com sucesso!", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar():
    if current_user.role != "admin":
        flash("Acesso negado. Somente admin pode adicionar.", "error")
        return redirect(url_for("index"))
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        marca = request.form.get("marca", "").strip()
        ano = request.form.get("ano", "").strip()
        escala = request.form.get("escala", "").strip()
        if not nome or not marca or not ano or not escala:
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("adicionar"))
        item = Miniatura(nome=nome, marca=marca, ano=ano, escala=escala)
        db.session.add(item)
        db.session.commit()
        flash("Miniatura adicionada com sucesso!", "success")
        return redirect(url_for("index"))
    return render_template("adicionar.html")

# ---------------------- Bootstrap DB on import (Render) ----------------------
with app.app_context():
    db.create_all()
    # seed admin if not exists
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            email="admin@minipedia.com",
            password=generate_password_hash("admin"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()

# If running locally
if __name__ == "__main__":
    app.run(debug=True)
