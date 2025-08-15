import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'

# Garante que a pasta para o banco existe
os.makedirs("data", exist_ok=True)

# Banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/miniaturas_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    colecao = db.relationship("Colecao", backref="user", lazy=True)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(50))
    lote = db.Column(db.String(50))
    marca = db.Column(db.String(50))
    cor = db.Column(db.String(50))
    foto = db.Column(db.String(300))

class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    miniatura_id = db.Column(db.Integer, db.ForeignKey('miniatura.id'), nullable=False)
    miniatura = db.relationship("Miniatura", backref="colecoes")

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/", methods=["GET", "HEAD"])
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
        flash("Usuário ou senha inválidos.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            flash("Usuário já existe.")
        else:
            hashed_pw = generate_password_hash(password, method="sha256")
            new_user = User(username=username, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash("Cadastro realizado com sucesso!")
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
    if request.method == "POST":
        nome = request.form.get("nome")
        tipo = request.form.get("tipo")
        lote = request.form.get("lote")
        marca = request.form.get("marca")
        cor = request.form.get("cor")
        foto = request.form.get("foto")
        miniatura = Miniatura(nome=nome, tipo=tipo, lote=lote, marca=marca, cor=cor, foto=foto)
        db.session.add(miniatura)
        db.session.commit()
        flash("Miniatura cadastrada com sucesso!")
        return redirect(url_for("index"))
    return render_template("adicionar.html")

@app.route("/buscar", methods=["GET", "POST"])
@login_required
def buscar():
    resultados = []
    if request.method == "POST":
        termo = request.form.get("termo")
        resultados = Miniatura.query.filter(Miniatura.nome.contains(termo)).all()
    return render_template("buscar.html", resultados=resultados)

@app.route("/adicionar_colecao/<int:miniatura_id>")
@login_required
def adicionar_colecao(miniatura_id):
    ja_tem = Colecao.query.filter_by(user_id=current_user.id, miniatura_id=miniatura_id).first()
    if not ja_tem:
        colecao = Colecao(user_id=current_user.id, miniatura_id=miniatura_id)
        db.session.add(colecao)
        db.session.commit()
        flash("Miniatura adicionada à sua coleção!")
    else:
        flash("Essa miniatura já está na sua coleção!")
    return redirect(url_for("buscar"))

@app.route("/minha_colecao")
@login_required
def minha_colecao():
    colecao = Colecao.query.filter_by(user_id=current_user.id).all()
    return render_template("minha_colecao.html", colecao=colecao)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
