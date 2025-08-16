from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minipedia-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///minipedia.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    colecao = db.relationship("Colecao", backref="dono", lazy=True)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(100), nullable=False)
    cor = db.Column(db.String(50), nullable=False)
    ano = db.Column(db.String(10), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    escala = db.Column(db.String(20), nullable=False)
    url_foto = db.Column(db.String(255), nullable=False)

class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    miniatura_id = db.Column(db.Integer, db.ForeignKey("miniatura.id"), nullable=False)
    miniatura = db.relationship("Miniatura")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/")
def index():
    miniaturas = Miniatura.query.all()
    return render_template("index.html", miniaturas=miniaturas)

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
        mini = Miniatura(nome=nome, marca=marca, cor=cor, ano=ano, tipo=tipo, lote=lote, escala=escala, url_foto=url_foto)
        db.session.add(mini)
        db.session.commit()
        flash("Miniatura cadastrada com sucesso!", "success")
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
    item = Colecao(user_id=current_user.id, miniatura_id=miniatura_id)
    db.session.add(item)
    db.session.commit()
    flash("Miniatura adicionada à sua coleção!", "success")
    return redirect(url_for("colecao"))

if __name__ == "__main__":
    app.run(debug=True)
