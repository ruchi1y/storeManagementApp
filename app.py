from flask import Flask, render_template, request, redirect, url_for
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

@app.route("/productos/nuevo", methods=["GET", "POST"])
def producto_nuevo():
    if request.method == "POST":
        conn = db.get_conn()
        try:
            store.create_product(
                conn,
                name=request.form.get("name"),
                type=request.form.get("type"),
                cost=float(request.form.get("cost")),
                price=float(request.form.get("price")),
            )
        finally:
            conn.close()
        return redirect(url_for("productos"))
    return render_template("producto_form.html", producto=None)


@app.route("/productos/<int:product_id>/editar", methods=["GET", "POST"])
def producto_editar(product_id):
    conn = db.get_conn()
    try:
        producto = store.get_product(conn, product_id)
        if request.method == "POST":
            store.update_product(
                conn,
                product_id,
                name=request.form.get("name"),
                type=request.form.get("type"),
                cost=float(request.form.get("cost")),
                price=float(request.form.get("price")),
            )
            return redirect(url_for("productos"))
    finally:
        conn.close()
    return render_template("producto_form.html", producto=producto)

@app.route("/productos/<int:product_id>/stock", methods=["POST"])
def producto_stock(product_id):
    quantity = int(request.form.get("quantity"))
    mov_type = request.form.get("mov_type")
    reason = request.form.get("reason", "")

    conn = db.get_conn()
    try:
        if mov_type == "entry":
            store.add_stock(conn, product_id, quantity, reason)
        else:
            store.remove_stock(conn, product_id, quantity, reason)
    finally:
        conn.close()
    return redirect(url_for("productos"))

if __name__ == "__main__":
    app.run(debug=True)