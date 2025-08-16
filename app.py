import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Banco PostgreSQL no Render (DATABASE_URL)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    colecao = db.relationship("Colecao", backref="dono", lazy=True)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(100), nullable=False)
    cor = db.Column(db.String(50), nullable=False)
    ano = db.Column(db.String(10), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    escala = db.Column(db.String(50), nullable=False)
    url_foto = db.Column(db.String(250), nullable=True)

class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    miniatura_id = db.Column(db.Integer, db.ForeignKey("miniatura.id"), nullable=False)
    miniatura = db.relationship("Miniatura")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas
@app.route("/")
def index():
    miniaturas = Miniatura.query.all()
    return render_template("index.html", miniaturas=miniaturas)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password, method="sha256")
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Cadastro realizado com sucesso! Faça login.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Login inválido.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        nome = request.form["nome"]
        marca = request.form["marca"]
        cor = request.form["cor"]
        ano = request.form["ano"]
        tipo = request.form["tipo"]
        lote = request.form["lote"]
        escala = request.form["escala"]
        url_foto = request.form["url_foto"]

        miniatura = Miniatura(nome=nome, marca=marca, cor=cor, ano=ano, tipo=tipo, lote=lote, escala=escala, url_foto=url_foto)
        db.session.add(miniatura)
        db.session.commit()
        flash("Miniatura adicionada!")
        return redirect(url_for("index"))
    return render_template("add.html")

@app.route("/colecao")
@login_required
def colecao():
    colecao = Colecao.query.filter_by(user_id=current_user.id).all()
    return render_template("colecao.html", colecao=colecao)

@app.route("/add_colecao/<int:miniatura_id>")
@login_required
def add_colecao(miniatura_id):
    existente = Colecao.query.filter_by(user_id=current_user.id, miniatura_id=miniatura_id).first()
    if existente:
        flash("Esta miniatura já está na sua coleção!")
    else:
        nova = Colecao(user_id=current_user.id, miniatura_id=miniatura_id)
        db.session.add(nova)
        db.session.commit()
        flash("Miniatura adicionada à coleção!")
    return redirect(url_for("colecao"))

# Criar tabelas automaticamente
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
