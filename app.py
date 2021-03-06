import csv
import os
from io import StringIO

from flask import Flask, render_template, request, make_response, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug.utils import secure_filename


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(basedir, 'biblioteca.db')
print(app.config["SQLALCHEMY_DATABASE_URI"])
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Livro(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('autor.id'), nullable=False)
    editora = db.Column(db.String(100), default="")
    ano = db.Column(db.String, default="")
    volumes = db.Column(db.String(20), default="")
    tema = db.Column(db.String(20), default="")
    titulo_coleccao = db.Column(db.String(100), default="")
    quantidade = db.Column(db.Integer, default=1)
    localizacao = db.Column(db.String(10), default="")
    emprestado_a = db.Column(db.String(40), default="")

    def __repr__(self):
        return f"Livro de {self.autor} de título {self.titulo}"
    
    @staticmethod
    def criar_novo_livro(titulo, autor, editora, ano, tema, volumes, 
    titulo_coleccao, quantidade, localizacao):
        """ Create a new record of a book """
        novo_livro = Livro(
            titulo=titulo,
            autor=autor,
            editora=editora,
            ano=ano,
            tema=tema,
            volumes=volumes,
            titulo_coleccao=titulo_coleccao,
            quantidade=quantidade,
            localizacao=localizacao,
        )
        db.session.add(novo_livro)
        db.session.commit()


class Autor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    livros = db.relationship('Livro', backref='autor', lazy=True)

    def __repr__(self):
        return self.nome

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

@app.route("/export/", methods=['POST'])
def export_csv():
    if request.method == 'POST':
        response = export_books_to_csv(request)
        return response

@app.route("/importar/", methods=['POST'])
def import_csv():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)
        
        nao_adicionados = import_books_from_csv(file)
        alert = {}
        if nao_adicionados:
            alert = {
                "type": "warning",
                "message": "Os seguintes livros nao foram adicionados: %s." % ", ".join(nao_adicionados),
            }

        livros = Livro.query.order_by(desc(Livro.id))
        autores = [autor.nome for autor in Autor.query.all()]
        editoras = list(set([livro.editora for livro in livros]))
        return render_template("adicionar_livros.html", livros=livros, 
        alert=alert, autores=autores, editoras=editoras)
    return redirect(request.url)

@app.route('/adicionar', methods=('POST', 'GET'))
def adicionar():
    alert = None
    if request.method == 'POST':
        if request.form.get("editar_livro"):
            if request.form.get("autor") and request.form.get("titulo"):
                if Livro.query.filter_by(titulo=request.form["titulo"]).count() == 0 or \
                    str(Livro.query.filter_by(titulo=request.form["titulo"])[0].id) == request.form["livro_id"]:
                    autor = Autor.autor_a_partir_to_nome(request.form["autor"])
                    livro_para_editar = Livro.query.get(request.form["livro_id"])
                    livro_para_editar.titulo=request.form.get("titulo", "")
                    livro_para_editar.autor=autor
                    livro_para_editar.editora=request.form.get("editora", "")
                    livro_para_editar.ano=request.form.get("ano", "")
                    livro_para_editar.tema=request.form.get("tema", "")
                    livro_para_editar.volumes=request.form.get("volumes", "")
                    livro_para_editar.titulo_coleccao=request.form.get("coleccao", "")
                    livro_para_editar.quantidade=request.form.get("quantidade", 1)
                    livro_para_editar.localizacao=request.form.get("localizacao", "")
                    livro_para_editar.emprestado_a=request.form.get("emprestado_a", "")
                    db.session.commit()
                else:
                    alert = {
                        "type": "warning",
                        "message": "Já existe um livro com esse título e autor.",
                    }
            else:
                alert = {
                    "type": "warning",
                    "message": "Não pode editar um livro sem lhe dar um título e autor.",
                }

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
            if request.form.get("autor") and request.form.get("titulo"):
                if Livro.query.filter_by(titulo=request.form["titulo"]).count() == 0:
                    autor = Autor.autor_a_partir_to_nome(request.form["autor"])
                    print("Adding a new book...")
                    Livro.criar_novo_livro(
                        titulo=request.form.get("titulo", ""),
                        autor=autor,
                        editora=request.form.get("editora", ""),
                        ano=request.form.get("ano", ""),
                        tema=request.form.get("tema", ""),
                        volumes=request.form.get("volumes", ""),
                        titulo_coleccao=request.form.get("coleccao", ""),
                        quantidade=request.form.get("quant", 1),
                        localizacao=request.form.get("local", ""),
                    )
                else:
                    alert = {
                        "type": "warning",
                        "message": "Já existe um livro com esse título.",
                    }
            else:
                alert = {
                    "type": "warning",
                    "message": "Por favor adicione um autor e um título ao seu novo livro",
                }

    livros = Livro.query.order_by(desc(Livro.id))
    autores = [autor.nome for autor in Autor.query.all()]
    editoras = list(set([livro.editora for livro in livros]))
    return render_template("adicionar_livros.html", livros=livros, 
    alert=alert, autores=autores, editoras=editoras)


def export_books_to_csv():
    """ Exporta a informacao de todos livros da biblioteca virtual para um csv """
    si = StringIO()
    cw = csv.writer(si)

    livros = Livro.query.all()
    rows = [[column.key for column in Livro.__table__.columns]]
    for livro in livros:
        rows.append([
            livro.id,
            livro.titulo,
            livro.autor.nome,
            livro.editora,
            livro.ano,
            livro.volumes,
            livro.tema,
            livro.titulo_coleccao,
            livro.quantidade,
            livro.localizacao,
            livro.emprestado_a
        ])

    cw.writerows(rows)
    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=biblioteca.csv'
    response.headers["Content-type"] = "text/csv"
    return response


def import_books_from_csv(file):
    file_data = file.read().decode("latin-1")
    csv_data = StringIO(file_data)
    csvReader = csv.reader(csv_data)

    header = next(csvReader)
    print(header)

    nao_adicionados = []
    for row in csvReader:
        print(row)
        titulo = row[header.index("titulo")]
        autor_nome = row[header.index("autor_id")]
        editora = row[header.index("editora")]
        ano = row[header.index("ano")]
        tema = row[header.index("tema")]
        volumes = row[header.index("volumes")]
        titulo_coleccao = row[header.index("titulo_coleccao")]
        quantidade = row[header.index("quantidade")]
        localizacao = row[header.index("localizacao")]

        if Livro.query.filter_by(titulo=titulo).count() == 0:
            autor = Autor.autor_a_partir_to_nome(autor_nome)
            print("Adding a new book...")
            Livro.criar_novo_livro(
                titulo=titulo,
                autor=autor,
                editora=editora,
                ano=ano,
                tema=tema,
                volumes=volumes,
                titulo_coleccao=titulo_coleccao,
                quantidade=quantidade,
                localizacao=localizacao,
            )
        else:
            nao_adicionados.append(titulo)
            print("livro ja existe na biblioteca, nao foi adicionado...")

    return nao_adicionados

if __name__ == '__main__':
    import random, threading, webbrowser
    port = 5000 + random.randint(0, 999)
    url = "http://127.0.0.1:{0}".format(port)
    threading.Timer(1.25, lambda: webbrowser.open(url) ).start()
    app.run(port=port, debug=False)
