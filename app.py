from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")

# Configuração do banco
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL").replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="admin@miniaturas.local").first():
        admin = User(
            name="Administrador",
            email="admin@miniaturas.local",
            password=generate_password_hash("admin123", method="scrypt"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

@app.route("/", methods=["GET", "HEAD"])
def home():
    return "<h1>Bem-vindo à Minipedia 🚀</h1><p>Use /login para acessar.</p>"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        flash("Credenciais inválidas", "danger")
    return "<form method='post'><input name='email' placeholder='Email'><input type='password' name='password' placeholder='Senha'><button type='submit'>Login</button></form>"

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
