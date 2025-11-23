// =========================================================================
// script.js: LÓGICA PRINCIPAL DEL E-COMMERCE Y PANEL DE ADMINISTRACIÓN
// =========================================================================

// --- 1. BASE DE DATOS DE PRODUCTOS (SIMULADA) ---
const productData = [
    // Datos actualizados para Suplementos OkamiFit
    { id: 1, idProducto: 'P001', name: "Whey Protein Isolate", tag: "Proteína", tagClass: "protein", price: 35000, isOffer: false },
    { id: 2, idProducto: 'C001', name: "Creatina Monohidratada", tag: "¡Oferta!", tagClass: "offer", price: 18000, newPrice: 15500, isOffer: true },
    { id: 1, idProducto: 'P002', name: "Caseína Chocolate", tag: "Noche", tagClass: "night", price: 32000, isOffer: false },
    { id: 3, idProducto: 'A001', name: "BCAAs Limón", tag: "Recuperación", tagClass: "recovery", price: 19500, isOffer: false },
    { id: 2, idProducto: 'C002', name: "Creatina Sab. Frutas", tag: "¡Oferta!", tagClass: "offer", price: 21000, newPrice: 17000, isOffer: true },
    { id: 4, idProducto: 'V001', name: "Multivitamínico Diario", tag: "Salud", tagClass: "health", price: 12000, isOffer: false }
];

// 2. CONFIGURACIÓN, CONSTANTES y SELECTORES DOM
const WHATSAPP_NUMBER = '50688887777';
const ALL_VARIANTS = ['1LB', '2LB', '3LB', '30 Serv', '60 Caps', '120 Caps', '5LB'];

// Credenciales y Token de Administración (SIMULADOS)
const MASTER_USER = 'admin';
const MASTER_PASS = '1234';
const AUTH_TOKEN_KEY = 'masterToken';

// Simulación de Stock
const simulatedStock = {
    'P001': { '1LB': 3, '2LB': 0, '3LB': 10, '30 Serv': 1, '60 Caps': 0, '120 Caps': 5, '5LB': 0 },
    'C001': { '1LB': 5, '2LB': 2, '3LB': 0, '30 Serv': 8, '60 Caps': 1, '120 Caps': 0, '5LB': 0 },
    'P002': { '1LB': 1, '2LB': 4, '3LB': 6, '30 Serv': 2, '60 Caps': 1, '120 Caps': 3, '5LB': 0 },
    'A001': { '1LB': 8, '2LB': 8, '3LB': 8, '30 Serv': 8, '60 Caps': 8, '120 Caps': 8, '5LB': 8 },
    'C002': { '1LB': 2, '2LB': 5, '3LB': 7, '30 Serv': 3, '60 Caps': 0, '120 Caps': 1, '5LB': 0 },
    'V001': { '1LB': 9, '2LB': 9, '3LB': 9, '30 Serv': 9, '60 Caps': 9, '120 Caps': 9, '5LB': 9 },
};

// Selectores del Modelo de Objeto de Documento (DOM)
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

    adminModal: document.getElementById('adminModal'),
    closeAdminBtn: document.querySelector('.close-admin-btn'),
    adminPanel: document.getElementById('admin-panel'),

    showAddFormBtn: document.getElementById('show-add-form-btn'),
    showListBtn: document.getElementById('show-list-btn'),
    addProductFormContainer: document.getElementById('add-product-form-container'),
    newProductForm: document.getElementById('new-product-form'),
    editProductList: document.getElementById('edit-product-list'),
    newProductStockInputs: document.getElementById('new-product-stock-inputs'),
    newProductImageFile: document.getElementById('new-product-image-file'),
};

// Variables de estado
let currentProduct = null;
let selectedVariant = null;


// =========================================================================
// SECCIÓN 2: LÓGICA DE RENDERIZADO Y FILTRADO
// =========================================================================

/**
 * Genera el HTML para una tarjeta de producto.
 */
function createProductCardHTML(product) {
    let priceDisplay;
    const formattedPrice = product.price.toLocaleString();

    if (product.isOffer) {
        const formattedNewPrice = product.newPrice.toLocaleString();
        priceDisplay = `
            <div class="product-price offer-price">
                <span class="old-price">₡${formattedPrice}</span>
                <span class="new-price">₡${formattedNewPrice}</span>
            </div>
        `;
    } else {
        priceDisplay = `<div class="product-price">₡${formattedPrice}</div>`;
    }

    const imageUrl = product.urlImagen ? product.urlImagen : '';

    return `
        <div class="product-card" data-product-id="${product.idProducto}" data-filter-id="${product.id}">
            <div class="product-tag ${product.tagClass}">${product.tag}</div>
            <div class="product-image-placeholder" style="background-image: url('${imageUrl}'); background-size: cover; background-position: center;"></div>
            <div class="product-name">${product.name}</div>
            ${priceDisplay}
        </div>
    `;
}

/**
 * Renderiza los productos en el grid.
 */
function renderProducts(productsToDisplay) {
    DOM.productsGrid.innerHTML = productsToDisplay.map(createProductCardHTML).join('');
    attachCardListeners();
}

/**
 * Maneja el clic en los enlaces de filtro.
 */
function handleFilterClick(event) {
    event.preventDefault();

    const clickedLink = event.currentTarget;
    const filterId = clickedLink.getAttribute('data-filter-id');

    DOM.filterLinks.forEach(link => link.classList.remove('active'));
    clickedLink.classList.add('active');

    let filteredProducts;

    if (filterId === '0') {
        filteredProducts = productData;
    } else {
        filteredProducts = productData.filter(product => product.id.toString() === filterId);
    }

    renderProducts(filteredProducts);
}

/**
 * Asigna el listener para abrir el modal a todas las tarjetas de producto.
 */
function attachCardListeners() {
    DOM.productsGrid.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('click', (event) => {
            if (event.target.closest('.product-tag')) return;

            const uniqueProductId = card.getAttribute('data-product-id');
            const product = productData.find(p => p.idProducto === uniqueProductId);

            if (product) {
                openProductModal(product);
            }
        });
    });
}


// =========================================================================
// SECCIÓN 3: LÓGICA DEL MODAL Y WHATSAPP
// =========================================================================

/**
 * Rellena los detalles del modal, genera las opciones de stock y lo muestra.
 */
function openProductModal(product) {
    currentProduct = product;
    selectedVariant = null;

    // Rellenar datos
    DOM.modalProductName.textContent = product.name;
    const priceDisplayValue = product.isOffer ? product.newPrice : product.price;
    DOM.modalPrice.textContent = `₡${priceDisplayValue.toLocaleString()}`;
    DOM.modalDescription.textContent = product.descripcion || `Suplemento de ${product.name}, ${product.tag}. Producto de alta calidad OkamiFit.`;

    // Rellenar stock por variante (usando ALL_VARIANTS)
    DOM.stockContainer.innerHTML = '';
    const stock = simulatedStock[product.idProducto] || {};

    ALL_VARIANTS.forEach(variant => {
        const count = stock[variant] || 0;
        const isAvailable = count > 0;
        const statusClass = isAvailable ? 'available' : 'unavailable';

        const variantDiv = document.createElement('div');
        variantDiv.className = `size-option ${statusClass}`;

        if (isAvailable) {
            variantDiv.setAttribute('data-variant', variant);
            variantDiv.addEventListener('click', handleVariantSelection);
        }

        variantDiv.innerHTML = `
            <strong>${variant}</strong><br>
            <span style="font-size:0.75em;">${count} disponibles</span>
        `;
        DOM.stockContainer.appendChild(variantDiv);
    });

    // Desactivar el botón de comprar hasta que se seleccione una variante
    DOM.addToCartBtn.disabled = true;
    DOM.addToCartBtn.textContent = 'Selecciona una variante';

    DOM.modal.style.display = 'block';
}

/**
 * Maneja la selección de variante en el modal.
 */
function handleVariantSelection(event) {
    const clickedVariantOption = event.currentTarget;
    const variant = clickedVariantOption.getAttribute('data-variant');

    document.querySelectorAll('.size-option.available').forEach(opt => {
        opt.classList.remove('selected');
    });

    clickedVariantOption.classList.add('selected');

    selectedVariant = variant;

    DOM.addToCartBtn.disabled = false;
    DOM.addToCartBtn.textContent = `Comprar Variante ${variant}`;
}

/**
 * Cierra el modal.
 */
function closeProductModal() {
    DOM.modal.style.display = 'none';
}

/**
 * Construye el mensaje de WhatsApp y redirige (CU04).
 */
function redirectToWhatsApp() {
    if (!currentProduct || !selectedVariant) {
        alert('Error: No hay producto o variante seleccionada.');
        return;
    }

    const productName = currentProduct.name;
    const variant = selectedVariant;
    const price = DOM.modalPrice.textContent;

    let message = `¡Hola! Estoy interesado/a en comprar el siguiente suplemento:\n\n`;
    message += `💊 Producto: ${productName}\n`;
    message += `⚖️ Variante solicitada: ${variant}\n`;
    message += `💰 Precio: ${price}\n\n`;
    message += `Código del Producto: ${currentProduct.idProducto}\n\n`;
    message += `¿Me confirmas la disponibilidad para hacer el pedido?`;

    const encodedMessage = encodeURIComponent(message);
    const whatsappUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodedMessage}`;

    window.open(whatsappUrl, '_blank');

    closeProductModal();
}

// =========================================================================
// SECCIÓN 4: LÓGICA DE AUTENTICACIÓN Y ADMIN (CU05)
// =========================================================================

/**
 * Muestra/Oculta el formulario de login.
 */
function toggleLoginForm(show) {
    if (show) {
        DOM.masterLoginForm.classList.remove('hidden');
        DOM.loginMessage.textContent = '';
    } else {
        DOM.masterLoginForm.classList.add('hidden');
    }
}

/**
 * Maneja el envío del formulario de login (SIMULADO).
 */
function handleLogin(event) {
    event.preventDefault();

    const username = DOM.loginUsername.value;
    const password = DOM.loginPassword.value;

    if (username === MASTER_USER && password === MASTER_PASS) {
        const simulatedToken = 'fake-jwt-token-master-user';
        localStorage.setItem(AUTH_TOKEN_KEY, simulatedToken);

        DOM.loginMessage.textContent = 'Inicio de sesión exitoso.';
        DOM.loginMessage.style.color = 'green';

        setTimeout(() => {
            toggleLoginForm(false);
            showAdminControls(true);
        }, 500);

    } else {
        DOM.loginMessage.textContent = 'Usuario o contraseña incorrectos.';
        DOM.loginMessage.style.color = 'var(--color-accent)';
    }
}

/**
 * Muestra/Oculta los botones flotantes de Edición y Cerrar Sesión.
 */
function showAdminControls(show) {
    if (show) {
        DOM.adminFloatControls.classList.remove('hidden');
    } else {
        DOM.adminFloatControls.classList.add('hidden');
    }
}

/**
 * Cierra la sesión del administrador.
 */
function handleLogout() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    showAdminControls(false); // Oculta los controles de admin flotantes
    closeAdminModal(); // Cierra el modal de admin si está abierto
    alert('Sesión cerrada. Regresando a la vista pública.');
}

/**
 * Inicializa la aplicación: verifica si hay un token almacenado.
 */
function checkAuthOnLoad() {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
        showAdminControls(true);
    } else {
        showAdminControls(false);
    }
}

// =========================================================================
// SECCIÓN 5: PANEL DE ADMINISTRACIÓN (CRUD Implementación Día 1)
// =========================================================================

/**
 * Genera dinámicamente los campos de stock para el formulario de agregar producto.
 */
function generateStockInputs() {
    let html = '';
    ALL_VARIANTS.forEach(variant => {
        html += `
            <div class="stock-input-group">
                <label for="stock-${variant}">${variant}</label>
                <input type="number" id="stock-${variant}" name="stock_${variant}" min="0" value="0">
            </div>
        `;
    });
    DOM.newProductStockInputs.innerHTML = html;
}

/**
 * Renderiza el listado de productos en la vista de administración (CRUD Read - Día 1 Frontend).
 */
function renderAdminProductList() {
    let listHTML = `
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

    productData.forEach(product => {
        const currentStock = simulatedStock[product.idProducto] || {};
        const totalStock = Object.values(currentStock).reduce((sum, count) => sum + count, 0);

        listHTML += `
            <tr data-product-id="${product.idProducto}">
                <td>${product.idProducto}</td>
                <td>${product.name}</td>
                <td>₡${product.price.toLocaleString()}</td>
                <td>${product.tag}</td>
                <td>
                    <button class="action-btn small edit-btn" data-id="${product.idProducto}">✏️ Editar</button>
                    <button class="action-btn small secondary delete-btn" data-id="${product.idProducto}">🗑️ Eliminar</button>
                    <span class="stock-info">(Total Stock: ${totalStock})</span>
                </td>
            </tr>
        `;
    });

    listHTML += `
            </tbody>
        </table>
        <p class="admin-note">Nota: La funcionalidad de Editar/Eliminar se conecta a los endpoints PUT y DELETE.</p>
    `;

    DOM.editProductList.innerHTML = listHTML;
}

/**
 * Abre el modal de administración flotante (CORREGIDO).
 */
function openAdminModal() {
    console.log('--- Intentando abrir el Modal de Administración ---');

    // Ocultar elementos principales de cliente
    DOM.productsGridContainer.classList.add('hidden');
    DOM.filterNavContainer.classList.add('hidden');
    DOM.footer.classList.add('hidden');

    // FIX: Usar style.display para forzar la visibilidad del modal
    DOM.adminModal.style.display = 'block';

    // Inicializar el formulario y mostrar la sección por defecto (Agregar)
    generateStockInputs();
    showAdminSection('add');
}

/**
 * Cierra el modal de administración flotante y restaura la vista del cliente (CORREGIDO).
 */
function closeAdminModal() {
    // FIX: Ocultar el modal usando style.display
    DOM.adminModal.style.display = 'none';

    // Restaurar la interfaz de cliente
    DOM.productsGridContainer.classList.remove('hidden');
    DOM.filterNavContainer.classList.remove('hidden');
    DOM.footer.classList.remove('hidden');
}


/**
 * Maneja el clic en el botón flotante de Editar Catálogo.
 */
function handleEditCatalogClick() {
    // Verificamos que se detecta el click
    console.log('CLICK detectado en botón "Editar Catálogo"');
    openAdminModal();
}

/**
 * Muestra una sección específica del panel de administración (Agregar o Listar).
 */
function showAdminSection(section) {
    DOM.addProductFormContainer.classList.add('hidden');
    DOM.editProductList.classList.add('hidden');

    if (section === 'add') {
        DOM.addProductFormContainer.classList.remove('hidden');
    } else if (section === 'list') {
        DOM.editProductList.classList.remove('hidden');
        renderAdminProductList(); // Llama a la función de renderizado CRUD Read
    }
}

/**
 * Maneja el envío del nuevo formulario de producto con subida de archivo (SIMULADO - CU06).
 */
function handleNewProductSubmit(event) {
    event.preventDefault();

    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) {
        alert("Error: Debes iniciar sesión como administrador para agregar productos.");
        return;
    }

    const formData = new FormData(DOM.newProductForm);

    console.log("SIMULACIÓN DE ENVÍO A API - Tipo de Envío: multipart/form-data");

    // Lógica REAL de la Capa de Aplicación (Backend):
    // fetch('/api/auth/productos', { method: 'POST', body: formData, headers: { 'Authorization': 'Bearer ' + token } })

    alert(`¡Éxito! Producto ${formData.get('nombre')} listo para ser subido (Simulación).`);
    DOM.newProductForm.reset();
    showAdminSection('list');
}


// =========================================================================
// SECCIÓN 6: INICIALIZACIÓN GLOBAL
// =========================================================================

/**
 * Función principal asíncrona que gestiona la carga de datos y la inicialización.
 */
function initializeApp() {

    // 1. Verificar autenticación al cargar
    checkAuthOnLoad();

    // 2. Cargar productos (Usamos data local por ahora)
    renderProducts(productData);

    // 3. Asignar Listeners de Interfaz de Cliente y Auth
    DOM.masterLoginForm.addEventListener('submit', handleLogin);

    // Listeners flotantes de Admin
    DOM.editCatalogBtn.addEventListener('click', handleEditCatalogClick);
    DOM.logoutBtn.addEventListener('click', handleLogout);

    // Listener para cerrar el modal de Admin
    DOM.closeAdminBtn.addEventListener('click', closeAdminModal);

    // Cerrar si el usuario hace click fuera del modal normal
    window.addEventListener('click', (event) => {
        if (event.target === DOM.modal) {
            closeProductModal();
        }
        // Listener para cerrar el modal de Admin si se hace click fuera del contenido
        if (event.target === DOM.adminModal) {
            closeAdminModal();
        }
    });

    // Asignar listeners de filtro
    DOM.filterLinks.forEach(link => {
        link.addEventListener('click', handleFilterClick);
    });

    // Asignar listeners del modal (Cerrar y Comprar)
    DOM.closeBtnTop.addEventListener('click', closeProductModal);
    DOM.closeBtnBottom.addEventListener('click', closeProductModal);
    DOM.addToCartBtn.addEventListener('click', redirectToWhatsApp);

    // 4. Listeners del Panel de Admin (dentro del nuevo modal)
    DOM.newProductForm.addEventListener('submit', handleNewProductSubmit);
    DOM.showAddFormBtn.addEventListener('click', () => showAdminSection('add'));
    DOM.showListBtn.addEventListener('click', () => showAdminSection('list'));

    // 5. Listener para activar el login desde el botón flotante "Al detalle"
    const floatingButton = document.querySelector('.floating-actions .action-btn:nth-child(1)');
    if (floatingButton) {
        floatingButton.addEventListener('click', (event) => {
            if (!localStorage.getItem(AUTH_TOKEN_KEY)) {
                event.preventDefault();
                toggleLoginForm(true);
            }
        });
    }

}

// Conectar la función principal al evento de carga del DOM
document.addEventListener('DOMContentLoaded', initializeApp);