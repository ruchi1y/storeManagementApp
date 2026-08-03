from flask import Flask, render_template, request, redirect, url_for, flash
import db
import store

db.init_db()

app = Flask(__name__)
app.secret_key = "123"

@app.route("/")
def inicio():
    conn = db.get_conn()
    try:
        summary = store.get_daily_summary(conn)
        abierta = store.is_cash_open(conn)
        bajos = store.get_low_stock(conn)
    finally:
        conn.close()
    return render_template("index.html", summary=summary, abierta=abierta, bajos=bajos)

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

@app.route("/vender")
def vender():
    q = request.args.get("q", "")
    conn = db.get_conn()
    try:
        items = store.get_products(conn, q)
    finally:
        conn.close()
    return render_template("vender.html", productos=items, q=q)

@app.route("/vender", methods=["POST"])
def vender_confirmar():
    product_ids = request.form.getlist("product_id")
    quantities = request.form.getlist("quantity")
    payment_method = request.form.get("payment_method")

    items = []
    for pid, qty in zip(product_ids, quantities):
        if int(qty) > 0:
            items.append((int(pid), int(qty)))

    conn = db.get_conn()
    try:
        if not store.is_cash_open(conn):
            flash("La caja está cerrada. Abrí la caja antes de vender.")
            return redirect(url_for("vender"))
        store.register_sale(conn, items, payment_method)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("vender"))
    finally:
        conn.close()

    flash("Venta registrada")
    return redirect(url_for("vender"))

@app.route("/cierre")
def cierre():
    conn = db.get_conn()
    try:
        summary = store.get_daily_summary(conn)
        abierta = store.is_cash_open(conn)
    finally:
        conn.close()
    return render_template("cierre.html", summary=summary, abierta=abierta)

@app.route("/cierre/cerrar", methods=["POST"])
def cierre_cerrar():
    conn = db.get_conn()
    try:
        store.close_cash(conn)
    finally:
        conn.close()
    flash("Caja cerrada. Resumen del día guardado.")
    return redirect(url_for("cierre"))

@app.route("/cierre/abrir", methods=["POST"])
def cierre_abrir():
    conn = db.get_conn()
    try:
        store.open_cash(conn)
    finally:
        conn.close()
    flash("Caja abierta.")
    return redirect(url_for("cierre"))

@app.route("/historial")
def historial():
    conn = db.get_conn()
    try:
        ventas = store.get_sales(conn)
        cierres = store.get_closings(conn)
    finally:
        conn.close()
    return render_template("historial.html", ventas=ventas, cierres=cierres)

if __name__ == "__main__":
    app.run(debug=True)