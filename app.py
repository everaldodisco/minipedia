from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minipedia-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minipedia.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Miniatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    marca = db.Column(db.String(100))
    cor = db.Column(db.String(50))
    ano = db.Column(db.String(4))
    tipo = db.Column(db.String(50))
    lote = db.Column(db.String(50))
    escala = db.Column(db.String(20))
    url_foto = db.Column(db.String(250))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas
@app.route('/')
def index():
    miniaturas = Miniatura.query.all()
    return render_template("index.html", miniaturas=miniaturas)

@app.route('/colecao')
@login_required
def colecao():
    minis = Miniatura.query.filter_by(user_id=current_user.id).all()
    return render_template("colecao.html", minis=minis)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        nome = request.form['nome']
        marca = request.form['marca']
        cor = request.form['cor']
        ano = request.form['ano']
        tipo = request.form['tipo']
        lote = request.form['lote']
        escala = request.form['escala']
        url_foto = request.form['url_foto']

        exists = Miniatura.query.filter_by(nome=nome, marca=marca, user_id=current_user.id).first()
        if exists:
            flash("Essa miniatura já está na sua coleção!", "danger")
            return redirect(url_for('add'))

        mini = Miniatura(nome=nome, marca=marca, cor=cor, ano=ano,
                         tipo=tipo, lote=lote, escala=escala, url_foto=url_foto, user_id=current_user.id)
        db.session.add(mini)
        db.session.commit()
        flash("Miniatura adicionada!", "success")
        return redirect(url_for('colecao'))
    return render_template("add.html")

@app.route('/perfil')
@login_required
def perfil():
    minis = Miniatura.query.filter_by(user_id=current_user.id).all()
    total = len(minis)
    return render_template("perfil.html", total=total, user=current_user)

@app.route('/login')
def login():
    return "Tela de Login (placeholder)"

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
