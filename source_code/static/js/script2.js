const API_BASE = "http://127.0.0.1:5000";
const WHATSAPP_NUMBER = '50689381855';
const ALL_VARIANTS = ['Disponibles'];
const AUTH_TOKEN_KEY = 'masterToken';

let products = [];
let categories = [];
let variants = [];

const DOM = {
    // Cliente
    productsGrid: document.querySelector('.products-grid'),
    productsGridContainer: document.querySelector('.products-grid-container'),
    filterLinks: document.querySelectorAll('.filter-nav a.filter-link'),
    filterNavContainer: document.querySelector('.filter-nav-container'),
    floatingActions: document.querySelector('.floating-actions'),
    footer: document.querySelector('footer'),
    // Modal de Cliente
    modal: document.getElementById('productModal'),
    closeBtnTop: document.querySelector('.close-btn'),
    closeBtnBottom: document.getElementById('close-modal-bottom'),
    stockContainer: document.getElementById('stock-container'),
    addToCartBtn: document.getElementById('add-to-cart-btn'),
    modalProductName: document.getElementById('modal-product-name'),
    modalPrice: document.getElementById('modal-price'),
    modalDescription: document.getElementById('modal-description'),
    // Admin
    loginFormContainer: document.getElementById('login-form-container'),
    masterLoginForm: document.getElementById('master-login-form'),
    loginUsername: document.getElementById('login-username'),
    loginPassword: document.getElementById('login-password'),
    loginMessage: document.getElementById('login-message'),
    // Selectores para Botones Flotantes y Modal de Admin
    adminFloatControls: document.getElementById('admin-controls-container'),
    editCatalogBtn: document.getElementById('edit-catalog-btn'),
    logoutBtn: document.getElementById('logout-btn'),
    closeLoginFormBtn: document.querySelector('.close-login-btn'),

    adminModal: document.getElementById('adminModal'),
    closeAdminBtn: document.querySelector('.close-admin-btn'),
    adminPanel: document.getElementById('admin-panel'),

    showListBtn: document.getElementById('show-list-btn'),
    addProductFormContainer: document.getElementById('add-product-form-container'),
    newProductForm: document.getElementById('new-product-form'),
    editProductList: document.getElementById('edit-product-list'),
    newProductStockInputs: document.getElementById('new-product-stock-inputs'),
    newProductImageFile: document.getElementById('new-product-image-file'),
};

let currentProduct = null;
let selectedVariant = null;


function safeLowerClass(str) {
    if (!str) return '';
    return String(str).toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
}

function formatPrice(value) {
    if (value == null) return '';
    return `₡${Number(value).toLocaleString()}`;
}

function defaultImageFor(idProducto) {
    return `/images/product_${idProducto}.png`;
}


async function apiFetch(path, opts = {}) {
    const url = `${API_BASE}${path}`;
    const defaultOpts = {
        credentials: "include",
        headers: {}
    };
    const finalOpts = Object.assign({}, defaultOpts, opts);

    if (finalOpts.body && !(finalOpts.body instanceof FormData) && !finalOpts.headers['Content-Type']) {
        finalOpts.headers['Content-Type'] = 'application/json';
    }
    try {
        const res = await fetch(url, finalOpts);
        const text = await res.text();
        try {
            const json = JSON.parse(text);
            return { ok: res.ok, status: res.status, json };
        } catch {
            return { ok: res.ok, status: res.status, text };
        }
    } catch (err) {
        console.error("apiFetch error:", err);
        return { ok: false, error: err };
    }
}

async function loadProducts() {
    const r = await apiFetch("/api/productos", { method: "GET" });
    if (!r.ok) {
        console.error("Error cargando productos:", r);
        return;
    }
    const payload = r.json || {};
    const list = payload.data || [];
    
// Dentro de tu función loadProducts, cambia el objeto 'mapped'
products = list.map(item => {
    const mapped = {
        // Probamos todas las combinaciones posibles de nombres de columna
        idProducto: item.idproducto || item.idProducto || item.id || null,
        
        // AQUÍ ESTÁ EL ARREGLO:
        idCategoria: item.idcategoria || item.idCategoria || item.id_categoria || null, 
        
        name: item.nombre || item.name || '',
        tag: item.nombrecategoria || item.tag || '',
        tagClass: safeLowerClass(item.nombrecategoria || item.tag || ''),
        price: item.preciobase || item.precioBase || 0,
         isOffer: !!item.enoferta,
            descripcion: item.descripcion || '',
            esBorrado: !!item.esborrado,
            nombreCategoria: item.nombrecategoria || '',
            urlImagen: item.urlimagen || item.urlImagen || defaultImageFor(item.idproducto || item.idProducto || item.id)
    };
    return mapped;
});

    renderProducts(products);
    if (!DOM.editProductList.classList.contains('hidden')) {
        renderAdminProductList();
    }
}

async function loadCategories() {
    const r = await apiFetch("/api/categorias", { method: "GET" });
    if (r.ok && r.json && Array.isArray(r.json.data)) {
        categories = r.json.data;
    } else {
        categories = [];
    }
    fillCategorySelects();
}

async function loadVariants() {
    const r = await apiFetch("/api/variantes", { method: "GET" });
    if (r.ok && r.json && Array.isArray(r.json.data)) {
        variants = r.json.data;
    } else {
        variants = [];
    }

}

async function apiCreateProduct(payload) {
    const formData = new FormData();
    formData.append("nombre", payload.nombre);
    formData.append("precioBase", payload.precioBase);
    formData.append("descripcion", payload.descripcion);
    formData.append("enOferta", payload.enOferta);
    formData.append("idCategoria", payload.idCategoria);


    if (payload.imagenFile) {
        formData.append("imagenFile", payload.imagenFile);
    }

    const r = await fetch("/api/productos", {
        method: "POST",
        body: formData,
        credentials: "include"
    });

    return await r.json();
}


async function apiUpdateProduct(idProducto, payload) {

    const formData = new FormData();
    formData.append("nombre", payload.nombre);
    formData.append("precioBase", payload.precioBase);
    formData.append("descripcion", payload.descripcion);
    formData.append("enOferta", payload.enOferta);
    formData.append("idCategoria", payload.idCategoria);

    if (payload.imagenFile) {
        formData.append("imagenFile", payload.imagenFile);
    }

    const r = await fetch(`/api/productos/${idProducto}`, {
        method: "PUT",
        body: formData,
        credentials: "include"
    });

    return await r.json();
}


async function apiDeleteProduct(idProducto) {
    const r = await apiFetch(`/api/productos/${idProducto}`, {
        method: "DELETE",
        credentials: "include"  
    });
    return r;
}


function createProductCardHTML(product) {
    const formattedPrice = (product.price || 0).toLocaleString();
    const priceDisplay = `<div class="product-price">₡${formattedPrice}</div>`;
    const imageUrl = product.urlImagen 
    ? `/uploads/${product.urlImagen}` 
    : defaultImageFor(product.idProducto);

    return `
        <div class="product-card" data-product-id="${product.idProducto}" data-filter-id="${product.idCategoria}">
            <div class="product-tag ${product.tagClass}">${product.tag}</div>
            <div class="product-image-placeholder" style="background-image: url('${imageUrl}'); background-size: cover; background-position: center;"></div>
            <div class="product-name">${product.name}</div>
            ${priceDisplay}
        </div>
    `;
}

function renderProducts(productsToDisplay) {
    if (!DOM.productsGrid) return;
    DOM.productsGrid.innerHTML = productsToDisplay.map(createProductCardHTML).join('');
    attachCardListeners();
}

function attachCardListeners() {
    if (!DOM.productsGrid) return;
    DOM.productsGrid.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('click', (event) => {
            if (event.target.closest('.product-tag')) return;
            const uniqueProductId = card.getAttribute('data-product-id');
            const product = products.find(p => String(p.idProducto) === String(uniqueProductId));
            if (product) openProductModal(product);
        });
    });
}

function handleFilterClick(event) {
    event.preventDefault();
    const clickedLink = event.currentTarget;
    const filterId = clickedLink.getAttribute('data-filter-id'); // Viene del HTML
    
    DOM.filterLinks.forEach(link => link.classList.remove('active'));
    clickedLink.classList.add('active');

    if (filterId === '0') {
        renderProducts(products);
    } else {
        // Forzamos a ambos a ser números para evitar el error de "2" vs 2
        const filtered = products.filter(p => Number(p.idCategoria) === Number(filterId));
        console.log("Filtrando por ID:", filterId, "Encontrados:", filtered.length); // DEBUG
        renderProducts(filtered);
    }
}

function openProductModal(product) {
    currentProduct = product;
    selectedVariant = null;

    DOM.modalProductName.textContent = product.name;
    DOM.modalPrice.textContent = formatPrice(product.price);
    DOM.modalDescription.textContent = product.descripcion || `Suplemento ${product.name}`;

    document.getElementById("modal-image-placeholder").style.backgroundImage =
    `url('/uploads/${product.urlImagen}')`;
    DOM.addToCartBtn.disabled = false;
    //DOM.addToCartBtn.textContent = 'Selecciona una variante';
    DOM.modal.style.display = 'block';
}


async function fillModalStock(product) {
    DOM.stockContainer.innerHTML = '';
    try {
        const r = await apiFetch(`/api/inventario/${product.idProducto}`, { method: "GET" });
        if (r.ok && r.json && Array.isArray(r.json.data) && r.json.data.length > 0) {
            const stockRows = r.json.data;
            stockRows.forEach(row => {
                const variantLabel = (row.presentacion || row.presentacion || 'Disponibles');
                const count = row.cantidadstock || row.cantidadStock || 0;
                createVariantOption(variantLabel, count);
            });
            return;
        }
    } catch (e) {
        console.warn("No se pudo cargar stock via API, usando stock simulado/fallback", e);
    }

    // Fallback: usar ALL_VARIANTS y un contador por defecto (0)
    const stock = {}; // no tenemos simulatedStock global fiable ahora
    ALL_VARIANTS.forEach(variant => {
        const count = stock[variant] || 0;
        createVariantOption(variant, count);
    });
}

function createVariantOption(variantLabel, count) {
    const isAvailable = count > 0;
    const statusClass = isAvailable ? 'available' : 'unavailable';
    const variantDiv = document.createElement('div');
    variantDiv.className = `size-option ${statusClass}`;
    if (isAvailable) {
        variantDiv.setAttribute('data-variant', variantLabel);
        variantDiv.addEventListener('click', handleVariantSelection);
    }
    variantDiv.innerHTML = `<strong>${variantLabel}</strong><br><span style="font-size:0.75em;">${count} disponibles</span>`;
    DOM.stockContainer.appendChild(variantDiv);
}

function handleVariantSelection(event) {
    const clickedVariantOption = event.currentTarget;
    const variant = clickedVariantOption.getAttribute('data-variant');
    document.querySelectorAll('.size-option.available').forEach(opt => opt.classList.remove('selected'));
    clickedVariantOption.classList.add('selected');
    selectedVariant = variant;
    DOM.addToCartBtn.disabled = false;
    DOM.addToCartBtn.textContent = `Comprar Variante ${variant}`;
}

function closeProductModal() {
    DOM.modal.style.display = 'none';
}

function redirectToWhatsApp() {

    const messageLines = [
        '¡Hola! Estoy interesado/a en comprar el siguiente suplemento:',
        '',
        `Producto: ${currentProduct.name}`,
        `Variante: ${selectedVariant}`,
        `Precio: ${formatPrice(currentProduct.price)}`,
        `Código del Producto: ${currentProduct.idProducto}`,
        '',
        '¿Me confirmas la disponibilidad para hacer el pedido?'
    ];
    const encodedMessage = encodeURIComponent(messageLines.join('\n'));
    const whatsappUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodedMessage}`;
    window.open(whatsappUrl, '_blank');
    closeProductModal();
}

async function handleLogin(event) {
    event.preventDefault();
    const username = DOM.loginUsername.value.trim();
    const password = DOM.loginPassword.value.trim();

    try {
        const r = await apiFetch("/login", {
            method: "POST",
            body: JSON.stringify({ correo: username, contrasena: password })
        });
        if (!r.ok) {
            const message = (r.json && r.json.message) || "Error de autenticación";
            DOM.loginMessage.textContent = message;
            DOM.loginMessage.style.color = "var(--color-accent)";
            return;
        }
        const payload = r.json || {};
        if (payload.success) {
            DOM.loginMessage.textContent = "Inicio de sesión exitoso.";
            DOM.loginMessage.style.color = "green";
            showAdminControls(true);
            setTimeout(() => toggleLoginForm(false), 400);
            await loadProducts();
        } else {
            DOM.loginMessage.textContent = payload.message || "Credenciales incorrectas";
            DOM.loginMessage.style.color = "var(--color-accent)";
        }
    } catch (err) {
        console.error("Login error:", err);
        DOM.loginMessage.textContent = "No se pudo conectar al servidor";
        DOM.loginMessage.style.color = "red";
    }
}

async function handleLogout() {
    try {
        await apiFetch("/logout", { method: "POST" });
    } catch (e) {
        console.warn("Logout error", e);
    } finally {
        showAdminControls(false);
        alert("Sesión cerrada. Regresando a la vista pública.");
        await loadProducts();
    }
}

function toggleLoginForm(show) {
    if (!DOM.masterLoginForm) return;
    if (show) {
        DOM.masterLoginForm.classList.remove('hidden');
        DOM.loginMessage.textContent = '';
    } else {
        DOM.masterLoginForm.classList.add('hidden');
    }
}

function checkAuthOnLoad() {
    (async () => {
        try {
            const r = await apiFetch("/api/validar-sesion", { method: "GET" });
            if (r.ok && r.json && r.json.success) {
                showAdminControls(true);
            } else {
                showAdminControls(false);
            }
        } catch {
            showAdminControls(false);
        }
    })();
}











function fillCategorySelects() {
    const select = DOM.newProductForm ? DOM.newProductForm.querySelector('select[name="categoria"]') : null;
    if (!select) return;
    select.innerHTML = `<option value="">-- Seleccione categoría --</option>`;
    categories.forEach(c => {
        const id = c.idcategoria || c.idCategoria || c.id;
        const name = c.nombrecategoria || c.nombreCategoria || c.nombre || c.name;
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = name;
        select.appendChild(opt);
    });
}











function renderAdminProductList() {
    let listHTML = `
        <div class="admin-list-header">
            <h3>Lista de Productos</h3>
            <button id="add-product-from-list-btn" class="action-btn primary">+ Añadir Producto</button>
        </div>
        <table class="admin-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nombre</th>
                    <th>Precio</th>
                    <th>Categoría</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
    `;

products.forEach(product => {
    listHTML += `
        <tr data-product-id="${product.idProducto}">
            <td class="text-center"><strong>#${product.idProducto}</strong></td>
            <td>${product.name}</td>
            <td class="text-bold">${formatPrice(product.price)}</td>
            <td><span class="badge">${product.tag}</span></td>
            <td>
                <div class="actions-container">
                    <button class="btn-action edit" data-id="${product.idProducto}">
                        <i></i> Editar
                    </button>
                    <button class="btn-action delete" data-id="${product.idProducto}">
                        <i></i> Eliminar
                    </button>
                </div>
            </td>
        </tr>
    `;
});
    DOM.editProductList.innerHTML = listHTML;

    const addProductFromListBtn = document.getElementById('add-product-from-list-btn');
    if (addProductFromListBtn) addProductFromListBtn.addEventListener('click', () => showAdminSection('add'));

    // editar
    DOM.editProductList.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', async (event) => {
            const id = event.currentTarget.getAttribute('data-id');
            await openEditProductForm(id);
        });
    });

    // eliminar
    DOM.editProductList.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async (event) => {
            const id = event.currentTarget.getAttribute('data-id');
            if (!confirm(`¿Estás seguro de eliminar el producto ${id}?`)) return;
            const r = await apiDeleteProduct(id);
            if (r.ok && r.json && r.json.success) {
                alert("Producto eliminado correctamente.");
                await loadProducts();
                renderAdminProductList();
            } else {
                alert("Error eliminando producto: " + ((r.json && r.json.message) || r.status || 'Error'));
            }
        });
    });
}

async function openEditProductForm(idProducto) {
    const product = products.find(p => String(p.idProducto) === String(idProducto));
    if (!product) {
        alert("Producto no encontrado en memoria");
        return;
    }
    showAdminSection('add', { mode: 'edit', id: idProducto });
    if (!DOM.newProductForm) return;
    DOM.newProductForm.querySelector('[name="nombre"]').value = product.name || '';
    DOM.newProductForm.querySelector('[name="precio"]').value = product.price || '';
    DOM.newProductForm.querySelector('[name="descripcion"]').value = product.descripcion || '';
    const catSelect = DOM.newProductForm.querySelector('[name="categoria"]');
    if (catSelect) catSelect.value = product.idCategoria || product.categoria || '';
    DOM.newProductForm.setAttribute('data-edit-id', idProducto);
}

function showAdminControls(show) {
    if (!DOM.adminFloatControls) return;
    if (show) DOM.adminFloatControls.classList.remove('hidden'); else DOM.adminFloatControls.classList.add('hidden');
}

function showAdminSection(section, options = {}) {
    const manageBtn = document.getElementById("show-list-btn");

    DOM.addProductFormContainer.classList.add('hidden');
    DOM.editProductList.classList.add('hidden');

    if (section === 'add') {
        DOM.addProductFormContainer.classList.remove('hidden');

        const formTitle = DOM.addProductFormContainer.querySelector('h3');

        if (options.mode === 'edit') {
            formTitle.textContent = `Editar Producto #${options.id}`;
        } else {
            formTitle.textContent = 'Agregar Nuevo Producto';
            if (DOM.newProductForm) DOM.newProductForm.removeAttribute('data-edit-id');
        }

        manageBtn.style.display = "inline-block";

    } else if (section === 'list') {
        DOM.editProductList.classList.remove('hidden');
        renderAdminProductList();

        manageBtn.style.display = "none";
    }
}

async function handleNewProductSubmit(event) {
    event.preventDefault();
    if (!DOM.newProductForm) return;

    const form = DOM.newProductForm;

    const nombre = form.querySelector('[name="nombre"]').value.trim();
    const precioBase = form.querySelector('[name="precio"]').value;
    const descripcion = form.querySelector('[name="descripcion"]').value.trim();
    const idCategoria = form.querySelector('[name="idCategoria"]').value;
    const fileInput = document.getElementById("new-product-image-file");
    const file = fileInput.files[0];

    if (!nombre || !precioBase || !idCategoria || !file) {
        alert("Faltan campos requeridos (nombre, precio, categoría, imagen).");
        return;
    }

    // ------------------------------
    // ARMAR EL FormData COMPLETO
    // ------------------------------
    const fd = new FormData();
    fd.append("nombre", nombre);
    fd.append("precioBase", precioBase);
    fd.append("descripcion", descripcion);
    fd.append("enOferta", "false");
    fd.append("idCategoria", idCategoria);
    fd.append("imagenFile", file);  // 🔥 IMPORTANTE 🔥

    const editId = form.getAttribute('data-edit-id');

    try {
        let url = "/api/productos";
        let method = "POST";

        if (editId) {
            url = `/api/productos/${editId}`;
            method = "PUT";
        }

        const res = await fetch(url, {
            method,
            body: fd   // 🔥 SIN HEADERS. FormData pone los headers solos.
        });

        const json = await res.json();

        if (json.success) {
            alert(editId ? "Producto actualizado." : "Producto creado.");
            form.reset();
            await loadProducts();
            showAdminSection('list');
        } else {
            alert("Error: " + json.message);
        }

    } catch (err) {
        console.error("Error guardando producto:", err);
        alert("Error en el servidor.");
    }
}

function initializeApp() {
    checkAuthOnLoad();
    loadCategories();  
    loadProducts();  

    if (DOM.masterLoginForm) DOM.masterLoginForm.addEventListener('submit', handleLogin);
    if (DOM.closeLoginFormBtn) DOM.closeLoginFormBtn.addEventListener('click', (e) => { e.preventDefault(); toggleLoginForm(false); });

    if (DOM.editCatalogBtn) DOM.editCatalogBtn.addEventListener('click', () => {
        openAdminModal();
    });
    if (DOM.logoutBtn) DOM.logoutBtn.addEventListener('click', () => { handleLogout(); });

    if (DOM.closeAdminBtn) DOM.closeAdminBtn.addEventListener('click', closeAdminModal);

    window.addEventListener('click', (event) => {
        if (event.target === DOM.modal) closeProductModal();
        if (event.target === DOM.adminModal) closeAdminModal();
    });

    DOM.filterLinks.forEach(link => link.addEventListener('click', handleFilterClick));

    if (DOM.closeBtnTop) DOM.closeBtnTop.addEventListener('click', closeProductModal);
    if (DOM.closeBtnBottom) DOM.closeBtnBottom.addEventListener('click', closeProductModal);
    if (DOM.addToCartBtn) DOM.addToCartBtn.addEventListener('click', redirectToWhatsApp);

    if (DOM.newProductForm) DOM.newProductForm.addEventListener('submit', handleNewProductSubmit);
    if (DOM.showListBtn) DOM.showListBtn.addEventListener('click', () => showAdminSection('list'));

    const floatingButton = document.querySelector('.floating-actions .action-btn:nth-child(1)');
    if (floatingButton) {
        floatingButton.addEventListener('click', (event) => {
            event.preventDefault();
            toggleLoginForm(true);
        });
    }
}

function openAdminModal() {
    DOM.productsGridContainer.classList.add('hidden');
    DOM.filterNavContainer.classList.add('hidden');
    DOM.footer.classList.add('hidden');
    DOM.adminModal.style.display = 'block';
    showAdminSection('list');
}
function closeAdminModal() {
    DOM.adminModal.style.display = 'none';
    DOM.productsGridContainer.classList.remove('hidden');
    DOM.filterNavContainer.classList.remove('hidden');
    DOM.footer.classList.remove('hidden');
}

document.addEventListener('DOMContentLoaded', initializeApp);
