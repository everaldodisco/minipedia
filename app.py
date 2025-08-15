# app.py
# -------------------------------------------------------------
# Site simples para cadastro e visualização de miniaturas de carros
# Recursos:
# - Cadastro e login de usuários
# - Perfis de acesso (viewer, editor, admin)
# - Cadastro/listagem/edição de miniaturas (com imagem por URL)
# - Página pública de listagem e detalhe das miniaturas
# - Painel admin para promover/rebaixar papéis de usuários
# -------------------------------------------------------------

from __future__ import annotations
import os
from datetime import datetime
from typing import Optional

from flask import Flask, request, redirect, url_for, flash, abort, session
from flask import render_template_string as render
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
    UserMixin,
)
from werkzeug.security import generate_password_hash, check_password_hash

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
    __tablename__ = "users"
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
    __tablename__ = "miniaturas"
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(80), nullable=False)
    modelo = db.Column(db.String(120), nullable=False)
    escala = db.Column(db.String(20), nullable=False)  # ex.: 1:18, 1:24, 1:64
    ano = db.Column(db.String(10))
    descricao = db.Column(db.Text)
    imagem_url = db.Column(db.String(500))
    criado_por = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# -------------------------------------
# Inicialização do banco
# -------------------------------------
@app.before_first_request
def init_db():
    db.create_all()
    # Cria usuário admin padrão se não existir
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
from functools import wraps

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
# Templates (Jinja2 como string para app de arquivo único)
# -------------------------------------
BASE = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title or 'Miniaturas de Carros' }}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root { --bg:#0f172a; --card:#111827; --muted:#cbd5e1; --text:#e5e7eb; --accent:#22d3ee; }
    *{ box-sizing:border-box; }
    body{ margin:0; font-family:Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:linear-gradient(180deg,#0b1020,#0f172a); color:var(--text); }
    a{ color:var(--accent); text-decoration:none; }
    .container{ max-width:1000px; margin:0 auto; padding:24px; }
    .nav{ display:flex; gap:16px; align-items:center; justify-content:space-between; margin-bottom:16px; }
    .nav .links{ display:flex; gap:12px; align-items:center; }
    .card{ background:rgba(17,24,39,.7); backdrop-filter:saturate(120%) blur(6px); border:1px solid rgba(148,163,184,.18); border-radius:16px; padding:20px; box-shadow:0 10px 30px rgba(0,0,0,.35); }
    .grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:16px; }
    .btn{ display:inline-block; padding:10px 14px; border-radius:12px; border:1px solid rgba(148,163,184,.3); background:#0b1220; color:var(--text); cursor:pointer; }
    .btn.primary{ background:linear-gradient(135deg,#06b6d4,#22d3ee); color:#0b1020; border:none; font-weight:700; }
    .btn.danger{ background:#7f1d1d; border-color:#ef4444; }
    input,select,textarea{ width:100%; padding:10px 12px; border-radius:10px; border:1px solid rgba(148,163,184,.3); background:#0b1220; color:var(--text); }
    label{ display:block; margin:8px 0 6px; font-weight:600; }
    .muted{ color:var(--muted); }
    .title{ font-size:28px; font-weight:800; letter-spacing:.3px; margin:0 0 12px; }
    .subtitle{ font-size:14px; color:var(--muted); margin:0 0 18px; }
    .item{ overflow:hidden; }
    .item img{ width:100%; aspect-ratio:16/10; object-fit:cover; border-radius:12px; border:1px solid rgba(148,163,184,.18); }
    .row{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
    .tag{ font-size:12px; padding:4px 8px; border-radius:999px; border:1px solid rgba(148,163,184,.25); color:var(--muted); }
    .flash{ margin-bottom:12px; padding:12px; border-radius:12px; background:#0f172a; border:1px solid rgba(148,163,184,.25); }
    .header-brand{ font-weight:800; letter-spacing:.5px; }
    .table{ width:100%; border-collapse:collapse; }
    .table th,.table td{ border-bottom:1px solid rgba(148,163,184,.18); padding:10px; text-align:left; }
    @media (max-width:640px){ .nav{ flex-direction:column; align-items:flex-start; gap:8px; } }
  </style>
</head>
<body>
  <div class="container">
    <div class="nav">
      <div class="links">
        <a class="header-brand" href="{{ url_for('index') }}">🚗 Miniaturas</a>
        <a href="{{ url_for('listar_miniaturas') }}">Explorar</a>
        {% if current_user.is_authenticated and (current_user.is_admin() or current_user.is_editor()) %}
          <a href="{{ url_for('nova_miniatura') }}">Adicionar</a>
        {% endif %}
        {% if current_user.is_authenticated and current_user.is_admin() %}
          <a href="{{ url_for('admin_usuarios') }}">Admin</a>
        {% endif %}
      </div>
      <div class="links">
        {% if current_user.is_authenticated %}
          <span class="muted">Olá, {{ current_user.name }} ({{ current_user.role }})</span>
          <a class="btn" href="{{ url_for('logout') }}">Sair</a>
        {% else %}
          <a class="btn" href="{{ url_for('login') }}">Entrar</a>
          <a class="btn primary" href="{{ url_for('signup') }}">Criar conta</a>
        {% endif %}
      </div>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for cat, msg in messages %}
          <div class="flash">{{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <div class="card">
      {% block content %}{% endblock %}
    </div>
  </div>
</body>
</html>
"""

INDEX = """
{% extends base %}
{% block content %}
  <h1 class="title">Coleção colaborativa de miniaturas</h1>
  <p class="subtitle">Cadastre suas miniaturas de carros e explore as de outros colecionadores. A listagem é pública; para cadastrar ou editar, faça login.</p>
  <div class="row" style="margin-bottom:12px;">
    <a class="btn primary" href="{{ url_for('listar_miniaturas') }}">Explorar miniaturas</a>
    {% if current_user.is_authenticated and (current_user.is_admin() or current_user.is_editor()) %}
      <a class="btn" href="{{ url_for('nova_miniatura') }}">Adicionar miniatura</a>
    {% endif %}
  </div>
  <hr style="border-color:rgba(148,163,184,.18); margin:16px 0;">
  <p class="muted">Dica: o usuário <b>admin@miniaturas.local</b> (senha <b>admin123</b>) é criado automaticamente para configurar permissões.</p>
{% endblock %}
"""

LISTAR = """
{% extends base %}
{% block content %}
  <h1 class="title">Explorar miniaturas</h1>
  <form method="get" class="row" style="margin-bottom:12px;">
    <input type="text" name="q" placeholder="Buscar por marca, modelo ou escala" value="{{ request.args.get('q','') }}">
    <button class="btn" type="submit">Buscar</button>
  </form>
  {% if miniaturas %}
    <div class="grid">
      {% for m in miniaturas %}
        <div class="item">
          <a href="{{ url_for('detalhe_miniatura', m_id=m.id) }}">
            <img src="{{ m.imagem_url or 'https://placehold.co/800x500?text=Sem+Imagem' }}" alt="{{ m.marca }} {{ m.modelo }}">
          </a>
          <div style="padding:8px 2px;">
            <div style="font-weight:700;">{{ m.marca }} {{ m.modelo }}</div>
            <div class="row" style="justify-content:space-between;">
              <span class="tag">Escala {{ m.escala }}</span>
              {% if m.ano %}<span class="tag">{{ m.ano }}</span>{% endif %}
            </div>
          </div>
        </div>
      {% endfor %}
    </div>
  {% else %}
    <p class="muted">Nenhuma miniatura encontrada.</p>
  {% endif %}
{% endblock %}
"""

DETALHE = """
{% extends base %}
{% block content %}
  <div class="row" style="align-items:flex-start; gap:20px;">
    <div style="flex:1;">
      <img src="{{ m.imagem_url or 'https://placehold.co/1000x620?text=Sem+Imagem' }}" alt="{{ m.marca }} {{ m.modelo }}" style="width:100%; border-radius:16px; border:1px solid rgba(148,163,184,.18);">
    </div>
    <div style="flex:1;">
      <h1 class="title" style="margin-bottom:4px;">{{ m.marca }} {{ m.modelo }}</h1>
      <p class="subtitle">Escala {{ m.escala }} {% if m.ano %}• Ano {{ m.ano }}{% endif %}</p>
      {% if m.descricao %}<p style="margin-bottom:12px;">{{ m.descricao }}</p>{% endif %}
      <p class="muted">Cadastrado por {{ m.autor.name }} em {{ m.created_at.strftime('%d/%m/%Y') }}</p>
      {% if current_user.is_authenticated and is_owner_or_admin(m.criado_por) %}
        <div class="row" style="margin-top:12px;">
          <a class="btn" href="{{ url_for('editar_miniatura', m_id=m.id) }}">Editar</a>
          <form method="post" action="{{ url_for('apagar_miniatura', m_id=m.id) }}" onsubmit="return confirm('Tem certeza que deseja apagar?');">
            <button class="btn danger" type="submit">Apagar</button>
          </form>
        </div>
      {% endif %}
    </div>
  </div>
{% endblock %}
"""

FORM = """
{% extends base %}
{% block content %}
  <h1 class="title">{{ 'Nova' if is_new else 'Editar' }} miniatura</h1>
  <form method="post">
    <label>Marca</label>
    <input name="marca" required value="{{ m.marca if m else '' }}">
    <label>Modelo</label>
    <input name="modelo" required value="{{ m.modelo if m else '' }}">
    <label>Escala (ex.: 1:64)</label>
    <input name="escala" required value="{{ m.escala if m else '' }}">
    <label>Ano (opcional)</label>
    <input name="ano" value="{{ m.ano if m else '' }}">
    <label>Imagem (URL)</label>
    <input name="imagem_url" placeholder="https://..." value="{{ m.imagem_url if m else '' }}">
    <label>Descrição (opcional)</label>
    <textarea name="descricao" rows="4">{{ m.descricao if m else '' }}</textarea>
    <div class="row" style="margin-top:12px;">
      <button class="btn primary" type="submit">Salvar</button>
      <a class="btn" href="{{ url_for('listar_miniaturas') }}">Cancelar</a>
    </div>
  </form>
{% endblock %}
"""

AUTH = """
{% extends base %}
{% block content %}
  <h1 class="title">{{ title }}</h1>
  <form method="post">
    {% if show_name %}
      <label>Nome</label>
      <input name="name" required>
    {% endif %}
    <label>E-mail</label>
    <input name="email" type="email" required>
    <label>Senha</label>
    <input name="password" type="password" required>
    <div class="row" style="margin-top:12px;">
      <button class="btn primary" type="submit">{{ button }}</button>
      {% if alt_link %}<a class="btn" href="{{ alt_link.href }}">{{ alt_link.text }}</a>{% endif %}
    </div>
  </form>
{% endblock %}
"""

ADMIN = """
{% extends base %}
{% block content %}
  <h1 class="title">Usuários</h1>
  <p class="subtitle">Somente administradores podem alterar papéis. Papéis disponíveis: <b>viewer</b> (somente visualizar), <b>editor</b> (cadastrar/editar), <b>admin</b> (todas as permissões).</p>
  <table class="table">
    <thead>
      <tr><th>Nome</th><th>Email</th><th>Papel</th><th>Ações</th></tr>
    </thead>
    <tbody>
      {% for u in users %}
      <tr>
        <td>{{ u.name }}</td>
        <td>{{ u.email }}</td>
        <td>{{ u.role }}</td>
        <td>
          {% if u.id != current_user.id %}
            <form method="post" action="{{ url_for('alterar_papel', user_id=u.id) }}" class="row">
              <select name="role">
                <option value="viewer" {% if u.role=='viewer' %}selected{% endif %}>viewer</option>
                <option value="editor" {% if u.role=='editor' %}selected{% endif %}>editor</option>
                <option value="admin"  {% if u.role=='admin' %}selected{% endif %}>admin</option>
              </select>
              <button class="btn" type="submit">Atualizar</button>
            </form>
          {% else %}
            <span class="muted">(você)</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
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
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not all([name, email, password]):
            flash("Preencha todos os campos.")
            return redirect(url_for("signup"))
        if User.query.filter_by(email=email).first():
            flash("E-mail já cadastrado. Faça login.")
            return redirect(url_for("login"))
        u = User(name=name, email=email, role="viewer")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        login_user(u)
        flash("Conta criada com sucesso!")
        return redirect(url_for("index"))
    return render(AUTH, base=BASE, title="Criar conta", button="Cadastrar", show_name=True, alt_link={"href":url_for('login'),"text":"Já tenho conta"})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        u = User.query.filter_by(email=email).first()
        if not u or not u.check_password(password):
            flash("Credenciais inválidas.")
            return redirect(url_for("login"))
        login_user(u)
        flash("Bem-vindo!")
        return redirect(url_for("index"))
    return render(AUTH, base=BASE, title="Entrar", button="Entrar", show_name=False, alt_link={"href":url_for('signup'),"text":"Criar conta"})


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.")
    return redirect(url_for("index"))


@app.route("/miniaturas")
def listar_miniaturas():
    q = request.args.get("q", "").strip()
    query = Miniatura.query.order_by(Miniatura.created_at.desc())
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Miniatura.marca.ilike(like),
                Miniatura.modelo.ilike(like),
                Miniatura.escala.ilike(like),
                Miniatura.ano.ilike(like),
            )
        )
    miniaturas = query.all()
    return render(LISTAR, base=BASE, miniaturas=miniaturas)


@app.route("/miniaturas/<int:m_id>")
def detalhe_miniatura(m_id: int):
    m = Miniatura.query.get_or_404(m_id)
    return render(DETALHE, base=BASE, m=m, is_owner_or_admin=is_owner_or_admin)


@app.route("/miniaturas/nova", methods=["GET", "POST"])
@login_required
@role_required("editor")
def nova_miniatura():
    if request.method == "POST":
        m = Miniatura(
            marca=request.form.get("marca", "").strip(),
            modelo=request.form.get("modelo", "").strip(),
            escala=request.form.get("escala", "").strip(),
            ano=request.form.get("ano", "").strip() or None,
            descricao=request.form.get("descricao", "").strip() or None,
            imagem_url=request.form.get("imagem_url", "").strip() or None,
            criado_por=current_user.id,
        )
        if not (m.marca and m.modelo and m.escala):
            flash("Preencha marca, modelo e escala.")
            return render(FORM, base=BASE, m=m, is_new=True)
        db.session.add(m)
        db.session.commit()
        flash("Miniatura cadastrada!")
        return redirect(url_for("detalhe_miniatura", m_id=m.id))
    return render(FORM, base=BASE, m=None, is_new=True)


@app.route("/miniaturas/<int:m_id>/editar", methods=["GET", "POST"])
@login_required
def editar_miniatura(m_id: int):
    m = Miniatura.query.get_or_404(m_id)
    if not is_owner_or_admin(m.criado_por):
        flash("Você não pode editar esta miniatura.")
        return redirect(url_for("detalhe_miniatura", m_id=m.id))
    if request.method == "POST":
        m.marca = request.form.get("marca", m.marca).strip()
        m.modelo = request.form.get("modelo", m.modelo).strip()
        m.escala = request.form.get("escala", m.escala).strip()
        m.ano = request.form.get("ano", "").strip() or None
        m.descricao = request.form.get("descricao", "").strip() or None
        m.imagem_url = request.form.get("imagem_url", "").strip() or None
        db.session.commit()
        flash("Miniatura atualizada!")
        return redirect(url_for("detalhe_miniatura", m_id=m.id))
    return render(FORM, base=BASE, m=m, is_new=False)


@app.route("/miniaturas/<int:m_id>/apagar", methods=["POST"])
@login_required
def apagar_miniatura(m_id: int):
    m = Miniatura.query.get_or_404(m_id)
    if not is_owner_or_admin(m.criado_por):
        flash("Você não pode apagar esta miniatura.")
        return redirect(url_for("detalhe_miniatura", m_id=m.id))
    db.session.delete(m)
    db.session.commit()
    flash("Miniatura removida.")
    return redirect(url_for("listar_miniaturas"))


# --- Admin ---
@app.route("/admin/usuarios")
@login_required
@role_required("admin")
def admin_usuarios():
    users = User.query.order_by(User.created_at.desc()).all()
    return render(ADMIN, base=BASE, users=users)


@app.route("/admin/usuarios/<int:user_id>/papel", methods=["POST"])
@login_required
@role_required("admin")
def alterar_papel(user_id: int):
    if current_user.id == user_id:
        flash("Você não pode alterar seu próprio papel aqui.")
        return redirect(url_for("admin_usuarios"))
    role = request.form.get("role", "viewer")
    if role not in {"viewer", "editor", "admin"}:
        flash("Papel inválido.")
        return redirect(url_for("admin_usuarios"))
    u = User.query.get_or_404(user_id)
    u.role = role
    db.session.commit()
    flash("Papel atualizado!")
    return redirect(url_for("admin_usuarios"))


# -------------------------------------
# Execução
# -------------------------------------
if __name__ == "__main__":
    # Use: FLASK_RUN_PORT ou porta 5000 por padrão
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
