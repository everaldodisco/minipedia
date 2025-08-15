# app.py
# -------------------------------------------------------------
# Site de cadastro e visualização de miniaturas de carros
# Adaptado para deploy em serviços como Render/Railway
# Compatível com Flask 3.x
# -------------------------------------------------------------

import os
from datetime import datetime
from typing import Optional

from flask import Flask, request, redirect, url_for, flash
from flask import render_template_string as render
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, logout_user, login_required,
    current_user, UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# -------------------------------------
# Configuração do app
# -------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.abspath('miniaturas.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Banco e login
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# -------------------------------------
# Modelos
# -------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="viewer", nullable=False)  # viewer | editor | admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    miniaturas = db.relationship("Miniatura", backref="autor", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_editor(self) -> bool:
        return self.role in {"editor", "admin"}


class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(80), nullable=False)
    modelo = db.Column(db.String(120), nullable=False)
    escala = db.Column(db.String(20), nullable=False)
    ano = db.Column(db.String(10))
    descricao = db.Column(db.Text)
    imagem_url = db.Column(db.String(500))
    criado_por = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# -------------------------------------
# Inicialização do banco (compatível Flask 3.x)
# -------------------------------------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="admin@miniaturas.local").first():
        admin = User(name="Administrador", email="admin@miniaturas.local", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    return User.query.get(int(user_id))

# -------------------------------------
# Helpers de permissão
# -------------------------------------
def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles and not current_user.is_admin():
                flash("Você não tem permissão para acessar esta página.", "warning")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def is_owner_or_admin(item_user_id: int) -> bool:
    return current_user.is_authenticated and (current_user.id == item_user_id or current_user.is_admin())

# -------------------------------------
# Templates simples
# -------------------------------------
BASE = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>{{ title or 'Miniaturas' }}</title></head>
<body>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul>{% for m in messages %}<li>{{ m }}</li>{% endfor %}</ul>
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</body>
</html>
"""

INDEX = """
{% extends base %}
{% block content %}
<h1>Miniaturas de Carros</h1>
<a href="{{ url_for('listar_miniaturas') }}">Explorar</a> |
{% if current_user.is_authenticated %}
  <a href="{{ url_for('nova_miniatura') }}">Nova</a> |
  <a href="{{ url_for('logout') }}">Sair</a>
{% else %}
  <a href="{{ url_for('login') }}">Entrar</a> |
  <a href="{{ url_for('signup') }}">Cadastrar</a>
{% endif %}
{% endblock %}
"""

LISTAR = """
{% extends base %}
{% block content %}
<h1>Lista</h1>
<ul>
{% for m in miniaturas %}
  <li><a href="{{ url_for('detalhe_miniatura', m_id=m.id) }}">{{ m.marca }} {{ m.modelo }}</a></li>
{% endfor %}
</ul>
{% endblock %}
"""

DETALHE = """
{% extends base %}
{% block content %}
<h1>{{ m.marca }} {{ m.modelo }}</h1>
<p>Escala: {{ m.escala }}</p>
{% if m.ano %}<p>Ano: {{ m.ano }}</p>{% endif %}
{% if m.descricao %}<p>{{ m.descricao }}</p>{% endif %}
{% if current_user.is_authenticated and is_owner_or_admin(m.criado_por) %}
  <a href="{{ url_for('editar_miniatura', m_id=m.id) }}">Editar</a>
  <form method="post" action="{{ url_for('apagar_miniatura', m_id=m.id) }}"><button>Apagar</button></form>
{% endif %}
{% endblock %}
"""

FORM = """
{% extends base %}
{% block content %}
<h1>{{ 'Nova' if is_new else 'Editar' }} miniatura</h1>
<form method="post">
  Marca: <input name="marca" value="{{ m.marca if m else '' }}"><br>
  Modelo: <input name="modelo" value="{{ m.modelo if m else '' }}"><br>
  Escala: <input name="escala" value="{{ m.escala if m else '' }}"><br>
  Ano: <input name="ano" value="{{ m.ano if m else '' }}"><br>
  Imagem: <input name="imagem_url" value="{{ m.imagem_url if m else '' }}"><br>
  Descrição: <textarea name="descricao">{{ m.descricao if m else '' }}</textarea><br>
  <button>Salvar</button>
</form>
{% endblock %}
"""

AUTH = """
{% extends base %}
{% block content %}
<h1>{{ title }}</h1>
<form method="post">
  {% if show_name %}Nome: <input name="name"><br>{% endif %}
  E-mail: <input name="email"><br>
  Senha: <input type="password" name="password"><br>
  <button>{{ button }}</button>
</form>
{% endblock %}
"""

# -------------------------------------
# Rotas
# -------------------------------------
@app.route("/")
def index():
    return render(INDEX, base=BASE)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        u = User(
            name=request.form["name"],
            email=request.form["email"].lower(),
            role="viewer"
        )
        u.set_password(request.form["password"])
        db.session.add(u)
        db.session.commit()
        login_user(u)
        return redirect(url_for("index"))
    return render(AUTH, base=BASE, title="Cadastrar", button="Criar conta", show_name=True)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(email=request.form["email"].lower()).first()
        if u and u.check_password(request.form["password"]):
            login_user(u)
            return redirect(url_for("index"))
        flash("Credenciais inválidas")
    return render(AUTH, base=BASE, title="Entrar", button="Entrar", show_name=False)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/miniaturas")
def listar_miniaturas():
    miniaturas = Miniatura.query.order_by(Miniatura.created_at.desc()).all()
    return render(LISTAR, base=BASE, miniaturas=miniaturas)

@app.route("/miniaturas/<int:m_id>")
def detalhe_miniatura(m_id):
    m = Miniatura.query.get_or_404(m_id)
    return render(DETALHE, base=BASE, m=m, is_owner_or_admin=is_owner_or_admin)

@app.route("/miniaturas/nova", methods=["GET", "POST"])
@login_required
def nova_miniatura():
    if request.method == "POST":
        m = Miniatura(
            marca=request.form["marca"],
            modelo=request.form["modelo"],
            escala=request.form["escala"],
            ano=request.form.get("ano"),
            descricao=request.form.get("descricao"),
            imagem_url=request.form.get("imagem_url"),
            criado_por=current_user.id
        )
        db.session.add(m)
        db.session.commit()
        return redirect(url_for("detalhe_miniatura", m_id=m.id))
    return render(FORM, base=BASE, m=None, is_new=True)

@app.route("/miniaturas/<int:m_id>/editar", methods=["GET", "POST"])
@login_required
def editar_miniatura(m_id):
    m = Miniatura.query.get_or_404(m_id)
    if not is_owner_or_admin(m.criado_por):
        flash("Sem permissão para editar")
        return redirect(url_for("detalhe_miniatura", m_id=m.id))
    if request.method == "POST":
        m.marca = request.form["marca"]
        m.modelo = request.form["modelo"]
        m.escala = request.form["escala"]
        m.ano = request.form.get("ano")
        m.descricao = request.form.get("descricao")
        m.imagem_url = request.form.get("imagem_url")
        db.session.commit()
        return redirect(url_for("detalhe_miniatura", m_id=m.id))
    return render(FORM, base=BASE, m=m, is_new=False)

@app.route("/miniaturas/<int:m_id>/apagar", methods=["POST"])
@login_required
def apagar_miniatura(m_id):
    m = Miniatura.query.get_or_404(m_id)
    if not is_owner_or_admin(m.criado_por):
        flash("Sem permissão para apagar")
        return redirect(url_for("detalhe_miniatura", m_id=m.id))
    db.session.delete(m)
    db.session.commit()
    return redirect(url_for("listar_miniaturas"))

# -------------------------------------
# Execução com Waitress (produção)
# -------------------------------------
if __name__ == "__main__":
    from waitress import serve
    port = int(os.environ.get("PORT", 5000))
    serve(app, host="0.0.0.0", port=port)