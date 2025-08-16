from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

# Configuração do banco (Postgres no Render)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3").replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    miniaturas = db.relationship("Colecao", backref="user", lazy=True)

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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    miniatura_id = db.Column(db.Integer, db.ForeignKey("miniatura.id"), nullable=False)
    miniatura = db.relationship("Miniatura", backref="colecoes")

# Inicializar banco automaticamente
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            flash("Usuário já existe!")
            return redirect(url_for("register"))
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Conta criada com sucesso!")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("Credenciais inválidas.")
            return redirect(url_for("login"))
        login_user(user)
        return redirect(url_for("index"))
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
        nome = request.form.get("nome")
        marca = request.form.get("marca")
        cor = request.form.get("cor")
        ano = request.form.get("ano")
        tipo = request.form.get("tipo")
        lote = request.form.get("lote")
        escala = request.form.get("escala")
        url_foto = request.form.get("url_foto")

        mini = Miniatura(nome=nome, marca=marca, cor=cor, ano=ano,
                         tipo=tipo, lote=lote, escala=escala, url_foto=url_foto)
        db.session.add(mini)
        db.session.commit()

        # Impedir duplicados na coleção
        if not Colecao.query.filter_by(user_id=current_user.id, miniatura_id=mini.id).first():
            colecao = Colecao(user_id=current_user.id, miniatura_id=mini.id)
            db.session.add(colecao)
            db.session.commit()

        flash("Miniatura adicionada à sua coleção!")
        return redirect(url_for("colecao"))

    return render_template("add.html")

@app.route("/colecao")
@login_required
def colecao():
    colecao = Colecao.query.filter_by(user_id=current_user.id).all()
    return render_template("colecao.html", colecao=colecao)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
