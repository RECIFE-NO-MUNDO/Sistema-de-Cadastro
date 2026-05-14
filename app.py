from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import pandas as pd
import os
from reportlab.pdfgen import canvas

app = Flask(__name__)

DB = "alunos.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def conectar():
    return sqlite3.connect(DB)


def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        nascimento TEXT,
        escola TEXT,
        pais TEXT,
        endereco TEXT,
        email TEXT,
        telefone TEXT,
        responsavel TEXT,
        telefone_responsavel TEXT,
        email_responsavel TEXT,
        parentesco TEXT,
        mora_com TEXT,
        pais_residencia TEXT,
        saude TEXT,
        medicamento TEXT,
        status_doc TEXT,
        passaporte TEXT,
        emissao_passaporte TEXT,
        visto TEXT
    )
    """)

    conn.commit()
    conn.close()


@app.route("/")
@app.route("/")
def dashboard():
    busca = request.args.get("busca", "")
    escola = request.args.get("escola", "")
    pais = request.args.get("pais", "")

    conn = conectar()

    query = "SELECT * FROM alunos WHERE 1=1"
    params = []

    if busca:
        query += " AND nome LIKE ?"
        params.append('%' + busca + '%')

    if escola:
        query += " AND escola LIKE ?"
        params.append('%' + escola + '%')

    if pais:
        query += " AND pais LIKE ?"
        params.append('%' + pais + '%')

    alunos = conn.execute(query, params).fetchall()

    conn.close()

    return render_template("dashboard.html", alunos=alunos)


@app.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        d = request.form
        conn = conectar()

        conn.execute("""
        INSERT INTO alunos (
            nome,nascimento,escola,pais,endereco,email,telefone,
            responsavel,telefone_responsavel,email_responsavel,
            parentesco,mora_com,pais_residencia,saude,
            medicamento,status_doc,passaporte,
            emissao_passaporte,visto
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            d["nome"], d["nascimento"], d["escola"], d["pais"],
            d["endereco"], d["email"], d["telefone"], d["responsavel"],
            d["telefone_responsavel"], d["email_responsavel"],
            d["parentesco"], d["mora_com"], d["pais_residencia"],
            d["saude"], d["medicamento"], d["status_doc"],
            d["passaporte"], d["emissao_passaporte"], d["visto"]
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("novo.html")


@app.route("/detalhes/<int:id>")
def detalhes(id):
    conn = conectar()
    aluno = conn.execute(
        "SELECT * FROM alunos WHERE id=?",
        (id,)
    ).fetchone()
    conn.close()

    return render_template("detalhes.html", aluno=aluno)


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = conectar()

    if request.method == "POST":
        d = request.form

        conn.execute("""
        UPDATE alunos SET
        nome=?, nascimento=?, escola=?, pais=?, endereco=?,
        email=?, telefone=?, responsavel=?, telefone_responsavel=?,
        email_responsavel=?, parentesco=?, mora_com=?,
        pais_residencia=?, saude=?, medicamento=?, status_doc=?,
        passaporte=?, emissao_passaporte=?, visto=?
        WHERE id=?
        """, (
            d["nome"], d["nascimento"], d["escola"], d["pais"],
            d["endereco"], d["email"], d["telefone"], d["responsavel"],
            d["telefone_responsavel"], d["email_responsavel"],
            d["parentesco"], d["mora_com"], d["pais_residencia"],
            d["saude"], d["medicamento"], d["status_doc"],
            d["passaporte"], d["emissao_passaporte"], d["visto"],
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    aluno = conn.execute(
        "SELECT * FROM alunos WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template("editar.html", aluno=aluno)


@app.route("/importar", methods=["POST"])
def importar():
    arquivo = request.files["arquivo"]

    caminho = os.path.join(UPLOAD_FOLDER, arquivo.filename)
    arquivo.save(caminho)

    df = pd.read_excel(caminho)

    conn = conectar()

    for _, row in df.iterrows():
        conn.execute("""
        INSERT INTO alunos (
            nome,nascimento,escola,pais,endereco,email,telefone,
            responsavel,telefone_responsavel,email_responsavel,
            parentesco,mora_com,pais_residencia,saude,
            medicamento,status_doc,passaporte,
            emissao_passaporte,visto
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            row.get("Nome completo", ""),
            row.get("Data de nascimento", ""),
            row.get("Escola", ""),
            row.get("País", ""),
            row.get("Endereço", ""),
            row.get("E-mail", ""),
            row.get("Telefone", ""),
            row.get("Responsável", ""),
            row.get("Telefone do responsável", ""),
            row.get("E-mail do responsável", ""),
            row.get("Grau de parentesco", ""),
            row.get("Com quem mora", ""),
            row.get("País (residência)", ""),
            row.get("Observação de saúde", ""),
            row.get("Medicamento", ""),
            row.get("Status Documentação", ""),
            row.get("Possui passaporte", ""),
            row.get("Data de emissão de passaporte", ""),
            row.get("Data de visto", "")
        ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/excel")
def excel():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM alunos", conn)
    conn.close()

    arquivo = "exportado.xlsx"
    df.to_excel(arquivo, index=False)

    return send_file(arquivo, as_attachment=True)


@app.route("/pdf")
def pdf():
    conn = conectar()
    alunos = conn.execute("SELECT nome,pais,escola FROM alunos").fetchall()
    conn.close()

    arquivo = "alunos.pdf"
    c = canvas.Canvas(arquivo)

    y = 800

    for aluno in alunos:
        c.drawString(50, y, f"{aluno[0]} - {aluno[1]} - {aluno[2]}")
        y -= 20

    c.save()

    return send_file(arquivo, as_attachment=True)


@app.route("/excluir/<int:id>")
def excluir(id):
    conn = conectar()

    conn.execute(
        "DELETE FROM alunos WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/pdf_aluno/<int:id>")
def pdf_aluno(id):
    conn = conectar()

    aluno = conn.execute(
        "SELECT * FROM alunos WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    arquivo = f"aluno_{id}.pdf"

    c = canvas.Canvas(arquivo)

    y = 800

    campos = [
        f"Nome: {aluno[1]}",
        f"Nascimento: {aluno[2]}",
        f"Escola: {aluno[3]}",
        f"Pais: {aluno[4]}",
        f"Endereco: {aluno[5]}",
        f"Email: {aluno[6]}",
        f"Telefone: {aluno[7]}",
        f"Responsavel: {aluno[8]}",
        f"Telefone Resp: {aluno[9]}",
        f"Email Resp: {aluno[10]}",
        f"Parentesco: {aluno[11]}",
        f"Mora com: {aluno[12]}",
        f"Pais residencia: {aluno[13]}",
        f"Saude: {aluno[14]}",
        f"Medicamento: {aluno[15]}",
        f"Status doc: {aluno[16]}",
        f"Passaporte: {aluno[17]}",
        f"Emissao: {aluno[18]}",
        f"Visto: {aluno[19]}"
    ]

    for linha in campos:
        c.drawString(50, y, linha)
        y -= 25

    c.save()

    return send_file(arquivo, as_attachment=True)
    
@app.route("/excluir_todos")
    def excluir_todos():
      conn = conectar()

      conn.execute("DELETE FROM alunos")

      conn.commit()
      conn.close()

    return redirect("/")

if __name__ == "__main__":
    criar_banco()
    app.run(host="0.0.0.0", port=int(
        os.environ.get("PORT", 5000)), debug=False)
