import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miniaturas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Tabela associativa para coleção
colecao_table = db.Table('colecao',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('miniatura_id', db.Integer, db.ForeignKey('miniatura.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    role = db.Column(db.String(50), default="user")
    colecao = db.relationship('Miniatura', secondary=colecao_table, backref='colecionadores')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    tipo = db.Column(db.String(50))
    lote = db.Column(db.String(50))
    marca = db.Column(db.String(100))
    cor = db.Column(db.String(50))
    foto = db.Column(db.String(250))
    ano = db.Column(db.Integer)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Inicializar DB e criar admin
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="admin@miniaturas.local").first():
        admin = User(name="Administrador", email="admin@miniaturas.local", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

@app.route("/", methods=["GET", "HEAD"])
def index():
    miniaturas = Miniatura.query.all()
    return render_template("index.html", miniaturas=miniaturas)

@app.route("/login", methods=["GET", "POST", "HEAD"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Usuário ou senha inválidos", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST", "HEAD"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("E-mail já cadastrado", "danger")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Conta criada com sucesso", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout", methods=["GET", "HEAD"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/adicionar", methods=["GET", "POST", "HEAD"])
@login_required
def adicionar():
    if request.method == "POST":
        nome = request.form["nome"]
        tipo = request.form["tipo"]
        lote = request.form["lote"]
        marca = request.form["marca"]
        cor = request.form["cor"]
        foto = request.form["foto"]
        ano = request.form["ano"]

        nova = Miniatura(nome=nome, tipo=tipo, lote=lote, marca=marca, cor=cor, foto=foto, ano=ano, usuario_id=current_user.id)
        db.session.add(nova)
        db.session.commit()
        flash("Miniatura adicionada com sucesso!", "success")
        return redirect(url_for("index"))
    return render_template("adicionar.html")

@app.route("/buscar", methods=["GET", "POST"])
@login_required
def buscar():
    resultados = []
    if request.method == "POST":
        termo = request.form["termo"]
        resultados = Miniatura.query.filter(Miniatura.nome.contains(termo)).all()
    return render_template("buscar.html", resultados=resultados)

@app.route("/adicionar_colecao/<int:miniatura_id>")
@login_required
def adicionar_colecao(miniatura_id):
    miniatura = Miniatura.query.get_or_404(miniatura_id)
    if miniatura not in current_user.colecao:
        current_user.colecao.append(miniatura)
        db.session.commit()
        flash("Miniatura adicionada à sua coleção!", "success")
    else:
        flash("Essa miniatura já está na sua coleção!", "warning")
    return redirect(url_for("minha_colecao"))

@app.route("/minha_colecao")
@login_required
def minha_colecao():
    return render_template("colecao.html", colecao=current_user.colecao)

if __name__ == "__main__":
    from waitress import serve
    port = int(os.environ.get("PORT", 5000))
    serve(app, host="0.0.0.0", port=port)
