from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///biblioteca.db'
db = SQLAlchemy(app)

class Livro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('autor.id'), nullable=False)
    editora = db.Column(db.String(100))
    ano = db.Column(db.Integer)
    volumes = db.Column(db.String(10))
    tema = db.Column(db.String(10))
    titulo_coleccao = db.Column(db.String(100))
    quantidade = db.Column(db.Integer, default=1)
    localizacao = db.Column(db.String(2))
    emprestado_a = db.Column(db.String(20))

    def __repr__(self):
        return f"Livro de {self.autor} de título {self.titulo}"
    
    @staticmethod
    def criar_novo_livro(titulo, autor, editora, titulo_coleccao, quantidade, localizacao):
        """ Create a new record of a book """
        novo_livro = Livro(
            titulo=titulo,
            autor=autor,
            editora=editora,
            titulo_coleccao=titulo_coleccao,
            quantidade=quantidade,
            localizacao=localizacao,
        )
        db.session.add(novo_livro)
        db.session.commit()

    @staticmethod
    def editar_livro(livro, titulo: str, autor: str, editora: str, 
    titulo_coleccao: str, quantidade: int, localizacao: str):
        """ Create a new record of a book """
        print(f"editing")
        livro.titulo=titulo
        livro.autor=autor
        livro.editora=editora
        livro.titulo_coleccao=titulo_coleccao
        livro.quantidade=quantidade
        livro.localizacao=localizacao
        db.session.commit()


class Autor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    livros = db.relationship('Livro', backref='autor', lazy=True)

    def __repr__(self):
        return f"Autor {self.nome}"

    @staticmethod
    def autor_a_partir_to_nome(nome):
        print(nome)
        autor = Autor.query.filter_by(nome=nome)
        if autor.count() == 0:
            autor = Autor(nome=nome)
            db.session.add(autor)
        else:
            autor = autor[0]
        return autor

@app.route('/')
def index():
    livros = Livro.query.all()
    return render_template("pesquisar_livros.html", livros=livros)


@app.route('/adicionar', methods=('POST', 'GET'))
def adicionar():
    if request.method == 'POST':
        if request.form.get("editar_livro"):
            autor = Autor.autor_a_partir_to_nome(request.form["autor"])
            livro_para_editar = Livro.query.get(request.form.get("id"))
            Livro.editar_livro(
                livro=livro_para_editar,
                titulo=request.form.get("titulo", ""),
                autor=autor,
                editora=request.form.get("editora", ""),
                titulo_coleccao=request.form.get("coleccao", ""),
                quantidade=request.form.get("quant", 1),
                localizacao=request.form.get("local", ""),
            )
        elif request.form.get("apagar_livro"):
            livro_para_apagar = Livro.query.get(request.form.get("apagar_livro"))

            # Se autor nao tem mais nenhum livro para alem do que sera apagado, apagar autor
            if Livro.query.filter_by(autor=livro_para_apagar.autor).count() == 1:
                print("deleting autor")
                autor = Autor.query.get(livro_para_apagar.autor.id)
                db.session.delete(autor)

            db.session.delete(livro_para_apagar)
            db.session.commit()
        else:
            autor = Autor.autor_a_partir_to_nome(request.form["autor"])
            Livro.criar_novo_livro(
                titulo=request.form.get("titulo", ""),
                autor=autor,
                editora=request.form.get("editora", ""),
                titulo_coleccao=request.form.get("coleccao", ""),
                quantidade=request.form.get("quant", 1),
                localizacao=request.form.get("local", ""),
            )

    livros = Livro.query.order_by(desc(Livro.id))
    return render_template("adicionar_livros.html", livros=livros)

