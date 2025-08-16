from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "chave_secreta"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///minipedia.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50), default="user")

class Carro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    marca = db.Column(db.String(100))
    ano = db.Column(db.String(4))
    usuario_id = db.Column(db.Integer, db.ForeignKey("user.id"))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        if User.query.filter_by(email=email).first():
            flash("Email já registrado!")
            return redirect(url_for("register"))
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Cadastro realizado com sucesso!")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Credenciais inválidas!")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/colecao")
@login_required
def colecao():
    carros = Carro.query.filter_by(usuario_id=current_user.id).all()
    return render_template("colecao.html", carros=carros)

@app.route("/adicionar_carro", methods=["GET", "POST"])
@login_required
def adicionar_carro():
    if request.method == "POST":
        nome = request.form["nome"]
        marca = request.form["marca"]
        ano = request.form["ano"]
        carro = Carro(nome=nome, marca=marca, ano=ano, usuario_id=current_user.id)
        db.session.add(carro)
        db.session.commit()
        return redirect(url_for("colecao"))
    return render_template("adicionar_carro.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
