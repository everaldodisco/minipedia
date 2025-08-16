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

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    role = db.Column(db.String(50), default="user")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    marca = db.Column(db.String(150))
    ano = db.Column(db.Integer)
    tipo = db.Column(db.String(50))
    lote = db.Column(db.String(50))
    foto_url = db.Column(db.String(300))
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

# Rotas
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
        marca = request.form["marca"]
        ano = request.form["ano"]
        tipo = request.form["tipo"]
        lote = request.form["lote"]
        foto_url = request.form["foto_url"]

        nova = Miniatura(
            nome=nome, marca=marca, ano=ano, tipo=tipo, lote=lote,
            foto_url=foto_url, usuario_id=current_user.id
        )
        db.session.add(nova)
        db.session.commit()
        flash("Miniatura adicionada com sucesso!", "success")
        return redirect(url_for("index"))
    return render_template("adicionar.html")

if __name__ == "__main__":
    from waitress import serve
    port = int(os.environ.get("PORT", 5000))
    serve(app, host="0.0.0.0", port=port)
