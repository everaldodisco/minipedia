from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minipedia-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///miniaturas.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------------- MODELOS ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    miniaturas = db.relationship("Miniatura", secondary="colecao", back_populates="colecionadores")

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(100))
    cor = db.Column(db.String(50))
    ano = db.Column(db.String(10))
    tipo = db.Column(db.String(100))
    lote = db.Column(db.String(50))
    escala = db.Column(db.String(50))
    url_foto = db.Column(db.String(300))
    colecionadores = db.relationship("User", secondary="colecao", back_populates="miniaturas")

class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    miniatura_id = db.Column(db.Integer, db.ForeignKey("miniatura.id"))
    __table_args__ = (db.UniqueConstraint("user_id", "miniatura_id", name="uq_user_miniatura"),)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROTAS ----------------
@app.route("/")
def index():
    miniaturas = Miniatura.query.all()
    return render_template("index.html", miniaturas=miniaturas)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            flash("Usuário já existe.", "danger")
            return redirect(url_for("register"))
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

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
            flash("Usuário ou senha inválidos.", "danger")
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
        mini = Miniatura(
            nome=request.form.get("nome"),
            marca=request.form.get("marca"),
            cor=request.form.get("cor"),
            ano=request.form.get("ano"),
            tipo=request.form.get("tipo"),
            lote=request.form.get("lote"),
            escala=request.form.get("escala"),
            url_foto=request.form.get("url_foto"),
        )
        db.session.add(mini)
        db.session.commit()
        flash("Miniatura adicionada com sucesso!", "success")
        return redirect(url_for("index"))
    return render_template("add.html")

@app.route("/colecao")
@login_required
def colecao():
    return render_template("colecao.html", miniaturas=current_user.miniaturas)

@app.route("/add_to_colecao/<int:miniatura_id>")
@login_required
def add_to_colecao(miniatura_id):
    mini = Miniatura.query.get_or_404(miniatura_id)
    if mini not in current_user.miniaturas:
        current_user.miniaturas.append(mini)
        db.session.commit()
        flash("Miniatura adicionada à sua coleção!", "success")
    else:
        flash("Essa miniatura já está na sua coleção!", "warning")
    return redirect(url_for("colecao"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
