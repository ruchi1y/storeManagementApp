const cart = {};

document.querySelectorAll(".btn-agregar").forEach(btn => {
    btn.addEventListener("click", () => {
        addToCart(btn.dataset.id, btn.dataset.name, btn.dataset.price);
    });
});

function addToCart(id, name, price) {
    id = String(id);
    if (cart[id]) {
        cart[id].quantity++;
    } else {
        cart[id] = { name: name, price: Number(price), quantity: 1 };
    }
    renderCart();
}

function renderCart() {
    const ul = document.getElementById("carrito");
    ul.innerHTML = "";
    let total = 0;
    for (const id in cart) {
        const item = cart[id];
        total += item.price * item.quantity;
        const li = document.createElement("li");
        li.textContent = item.name + " x" + item.quantity + " = $" + (item.price * item.quantity);
        ul.appendChild(li);
    }
    document.getElementById("total").textContent = "$" + total;
}

function confirmSale() {
    if (Object.keys(cart).length === 0) {
        alert("El carrito está vacío");
        return;
    }
    const form = document.getElementById("sale-form");
    form.innerHTML = "";
    for (const id in cart) {
        const item = cart[id];
        const h1 = document.createElement("input");
        h1.type = "hidden"; h1.name = "product_id"; h1.value = id;
        const h2 = document.createElement("input");
        h2.type = "hidden"; h2.name = "quantity"; h2.value = item.quantity;
        form.appendChild(h1);
        form.appendChild(h2);
    }
    const pm = document.querySelector('input[name="pm"]:checked');
    const hpm = document.createElement("input");
    hpm.type = "hidden"; hpm.name = "payment_method"; hpm.value = pm.value;
    form.appendChild(hpm);
    form.submit();
}