from flask import Flask, render_template, request
import db
import store

db.init_db()
app = Flask(__name__)


@app.route("/")
def inicio():
    return "Hola mundo"


@app.route("/productos")
def productos():
    q = request.args.get("q", "")
    conn = db.get_conn()
    try:
        items = store.get_products(conn, q)
    finally:
        conn.close()
    return render_template("productos.html", productos=items, q=q)


if __name__ == "__main__":
    app.run(debug=True)