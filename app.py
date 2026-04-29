from dotenv import load_dotenv
load_dotenv()
from flask import Flask, flash, render_template, request, session, jsonify, redirect, url_for, send_from_directory
import pyodbc
import uuid
import os
from functools import wraps
from onvopay import crear_checkout_session
import uuid
import hmac
import hashlib

ONVO_WEBHOOK_SECRET = os.environ.get('ONVO_WEBHOOK_SECRET', '')

drivers = pyodbc.drivers()

driver = (
    "{ODBC Driver 18 for SQL Server}"
    if "ODBC Driver 18 for SQL Server" in drivers
    else "{ODBC Driver 17 for SQL Server}"
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "root123"

app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True  # En producción cámbialo a True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_PERMANENT"] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Modifica tu diccionario de configuración
SQL_SERVER_CONFIG = {
    "driver": driver, 
    "server": os.environ.get('DB_SERVER'), # Ejemplo: 'tuservidor.database.windows.net'
    "database": os.environ.get('DB_NAME'),
    "user": os.environ.get('DB_USER'),
    "pass": os.environ.get('DB_PASS'),
}

def get_connection():
    try:
        # Cadena de conexión para Azure (requiere Authentication y Encrypt)
        conn_str = (
    f"DRIVER={SQL_SERVER_CONFIG['driver']};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=BD_Okamifit;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None
        conn = pyodbc.connect(conn_str)
        return conn, "sqlserver"
    except pyodbc.Error as ex:
        # Esto saldrá en el "Log Stream" que buscábamos
        print(f"❌ ERROR DE CONEXIÓN: {ex}") 
        return None, None

def row_to_dict_lower(row, cursor):
    """Convierte una fila pyodbc (fetchone) y cursor.description a dict con claves en minúscula."""
    if not row:
        return None
    cols = [c[0] for c in cursor.description] if cursor.description else []
    return {col.lower(): val for col, val in zip(cols, row)}

def rows_to_dicts(cursor):
    """Convierte cursor.fetchall() a lista de dicts con claves en minúscula."""
    cols = [c[0] for c in cursor.description] if cursor.description else []
    return [{col.lower(): val for col, val in zip(cols, row)} for row in cursor.fetchall()]

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = obtener_usuario_actual()
        if not user_id:
            return jsonify({"success": False, "message": "Autenticación requerida"}), 401

        conn = get_connection()
        if not conn:
            return jsonify({"success": False, "message": "Error de conexión"}), 500
        try:
            cur = conn.cursor()
            cur.execute("SELECT rol FROM USUARIOS WHERE idUsuario = ?", (user_id,))
            row = cur.fetchone()
            r = row_to_dict_lower(row, cur)
            rol = r.get("rol") if r else None
            if rol and rol.lower() == "admin":
                return func(*args, **kwargs)
            else:
                return jsonify({"success": False, "message": "Permisos insuficientes"}), 403
        finally:
            conn.close()
    return wrapper

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    correo = data.get("correo")
    contrasena = data.get("contrasena")

    conn = get_connection()
    if not conn:
        return jsonify({
            "success": False,
            "message": "Error crítico: No se pudo conectar a la base de datos."
        })

    try:
        cursor = conn.cursor()

        # Llamada al SP para validar login 
        cursor.execute("{CALL sp_validar_login1(?, ?)}", (correo, contrasena))
        row = cursor.fetchone()
        r = row_to_dict_lower(row, cursor)

        if not r:
            return jsonify({"success": False, "message": "Credenciales incorrectas"})

        is_success = bool(r.get("success"))
        user_id = r.get("customerid")
        message = r.get("message", "Credenciales incorrectas")

        if not is_success:
            return jsonify({"success": False, "message": message})

        # Crear token y registrar sesión
        token = str(uuid.uuid4())
        cursor.execute("{CALL sp_Crear_SESION1(?, ?, ?)}", (user_id, token, 30))
        conn.commit()

        # Guardar token en sesión Flask
        session["token"] = token

        return jsonify({"success": True})

    except Exception as e:
        print(f"ERROR EN /login: {e}")
        return jsonify({"success": False, "message": f"Error interno: {e}"})

    finally:
        conn.close()

def obtener_usuario_actual():
    token = session.get("token")
    if not token:
        return None

    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()


        cursor.execute("{CALL sp_Validar_SESION1(?)}", (token,))
        row = cursor.fetchone()
        r = row_to_dict_lower(row, cursor)

        user_id = r.get("id_usuario") if r else None
        return user_id

    except Exception as e:
        print(f"Error al obtener usuario actual: {e}")
        return None

    finally:
        conn.close()

@app.route('/api/validar-sesion', methods=['GET'])
def api_validar_sesion():
    user_id = obtener_usuario_actual()

    if user_id:
        return jsonify({"success": True, "user_id": user_id})
    else:
        return jsonify({"success": False, "message": "No hay sesión activa"})

@app.route("/logout", methods=["POST"])
def logout():
    token = session.pop("token", None)

    if token:
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()

                cursor.execute("{CALL sp_Cerrar_SESION1(?)}", (token,))
                conn.commit()
            except Exception as e:
                print(f"Error al cerrar sesión en BD: {e}")
            finally:
                conn.close()

    return redirect(url_for("index"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/productos", methods=["GET"])
def get_productos():
    conn = get_connection()
    if not conn:
        return jsonify({"success": False, "message": "No se pudo conectar a la BD"}), 500
    try:
        cur = conn.cursor()
        cur.execute("EXEC sp_Obtener_PRODUCTOS1 ?, ?", (None, 0))
        productos = rows_to_dicts(cur)
        return jsonify({"success": True, "data": productos})
    except Exception as e:
        print("ERROR GET /api/productos:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/productos/<int:idProducto>", methods=["GET"])
def get_producto(idProducto):
    conn = get_connection()
    if not conn:
        return jsonify({"success": False, "message": "No se pudo conectar a la BD"}), 500
    try:
        cur = conn.cursor()
        cur.execute("EXEC sp_Obtener_PRODUCTOS1 ?, ?", (idProducto, 0))
        productos = rows_to_dicts(cur)
        if not productos:
            return jsonify({"success": False, "message": "Producto no encontrado"}), 404
        return jsonify({"success": True, "data": productos[0]})
    except Exception as e:
        print("ERROR GET /api/productos/<id>:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/productos/categoria/<int:idCategoria>", methods=["GET"])
def get_productos_por_categoria(idCategoria):
    conn = get_connection()
    if not conn:
        return jsonify({"success": False, "message": "No se pudo conectar a la BD"}), 500
    try:
        cur = conn.cursor()
        sql = """
            SELECT P.idProducto, P.nombre, P.precioBase, P.descripcion, P.enOferta, C.idCategoria, C.nombreCategoria, P.esBorrado
            FROM PRODUCTOS P
            JOIN CATEGORIAS C ON P.idCategoria = C.idCategoria
            WHERE P.idCategoria = ? AND P.esBorrado = 0
        """
        cur.execute(sql, (idCategoria,))
        productos = rows_to_dicts(cur)
        return jsonify({"success": True, "data": productos})
    except Exception as e:
        print("ERROR GET /api/productos/categoria:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/productos', methods=['POST'])
def api_crear_producto():
    try:
        nombre = request.form.get("nombre")
        precioBase = request.form.get("precioBase")
        descripcion = request.form.get("descripcion")
        enOferta = request.form.get("enOferta", "false") == "true"
        idCategoria = request.form.get("idCategoria")
        imagen = request.files.get("imagenFile")
        if imagen:

            uploads_path = os.path.join("uploads", imagen.filename)
            imagen.save(uploads_path)
            urlImagen = imagen.filename
        else:
            urlImagen = None

        print("DATA RECIBIDA FORM:", request.form)
        print("ARCHIVO RECIBIDO:", imagen)
        print("URL IMAGEN GENERADA:", urlImagen)

        if not nombre or not precioBase or not idCategoria or not urlImagen:
            return jsonify({"success": False, "message": "Faltan campos obligatorios"}), 400

        conn = get_connection()  
        cursor = conn.cursor()

        print("Nombre enviado a la BD:", urlImagen)


        cursor.execute("""
    EXEC sp_Agregar_PRODUCTOS1
        @nombre=?,
        @precioBase=?,
        @descripcion=?,
        @enOferta=?,
        @idCategoria=?,
        @urlImagen=?
""", (nombre, precioBase, descripcion, 1 if enOferta else 0, idCategoria, urlImagen))


        conn.commit()

        return jsonify({"success": True})

    except Exception as e:
        print("Error creando producto:", e)
        return jsonify({"success": False, "message": "Error interno"}), 500

@app.route("/api/productos/<int:idProducto>", methods=["PUT"])
def actualizar_producto(idProducto):
    nombre = request.form.get("nombre")
    precioBase = request.form.get("precioBase")
    descripcion = request.form.get("descripcion")
    enOferta = request.form.get("enOferta") == "true"
    idCategoria = request.form.get("idCategoria")

    imagen = request.files.get("imagenFile")
    if imagen:
        uploads_path = os.path.join("uploads", imagen.filename)
        imagen.save(uploads_path)
        urlImagen = imagen.filename
    else:
        urlImagen = None 

    if not nombre or precioBase is None or idCategoria is None:
        return jsonify({"success": False, "message": "Faltan campos"}), 400

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            EXEC sp_Actualizar_PRODUCTOS1 ?, ?, ?, ?, ?, ?, ?
        """, (idProducto, nombre, precioBase, descripcion, int(enOferta), idCategoria, urlImagen))
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        print("ERROR PUT:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/productos/<int:idProducto>", methods=["DELETE"])
def eliminar_producto(idProducto):
    print("SESSION:", session)
    conn = get_connection()
    if not conn:
        return jsonify({"success": False, "message": "No se pudo conectar a la BD"}), 500
    try:
        cur = conn.cursor()
        cur.execute("EXEC sp_Eliminar_PRODUCTOS1 ?", (idProducto,))
        conn.commit()
        return jsonify({"success": True, "message": "Producto eliminado (borrado lógico)"})
    except Exception as e:
        conn.rollback()
        print("ERROR DELETE /api/productos:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/categorias", methods=["GET"])
def get_categorias():
    conn = get_connection()
    if not conn:
        return jsonify({"success": False, "message": "No se pudo conectar a la BD"}), 500
    try:
        cur = conn.cursor()
        cur.execute("EXEC sp_Obtener_CATEGORIAS1 ?, ?", (None, 0))
        categorias = rows_to_dicts(cur)
        return jsonify({"success": True, "data": categorias})
    except Exception as e:
        print("ERROR GET /api/categorias:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/upload-image", methods=["POST"])
def upload_image():
    try:
        if "imagen" not in request.files:
            return jsonify({"success": False, "message": "No se envió la imagen"}), 400

        file = request.files["imagen"]

        filename = file.filename
        save_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(save_path)

        url = f"/uploads/{filename}"

        return jsonify({"success": True, "url": url})

        print("Nombre archivo guardado realmente:", filename)

    except Exception as e:
        print("Error subiendo imagen:", e)
        return jsonify({"success": False, "message": "Error interno"}), 500


@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)








@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    item_id = str(data.get('idProducto'))
    nombre  = data.get('nombre')
    precio  = float(data.get('precio'))
    imagen  = data.get('imagen', '')   # ← agregar esto

    cart = session.setdefault('cart', {})

    if item_id in cart:
        cart[item_id]['cantidad'] += 1
    else:
        cart[item_id] = {
            'id':       item_id,
            'nombre':   nombre,
            'precio':   precio,
            'imagen':   imagen,           # ← guardarla aquí
            'cantidad': 1
        }

    session.modified = True
    total_items = sum(p['cantidad'] for p in cart.values())
    return jsonify({"status": "success", "cart_count": total_items}), 200


@app.route('/carrito')
def ver_carrito():
    cart = session.get('cart', {})          # ahora es dict, no lista
    productos_carrito = []
    total = 0

    for item in cart.values():
        subtotal = item['precio'] * item['cantidad']
        productos_carrito.append({
            'id':       item['id'],
            'nombre':   item['nombre'],
            'precio':   item['precio'],
            'cantidad': item['cantidad'],
            'subtotal': subtotal,
            'imagen':   item.get('imagen', '')
        })
        total += subtotal

    return render_template('carrito.html', productos=productos_carrito, total=total)


@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    product_id = str(product_id)            # aseguramos que sea string

    if product_id in cart:
        if cart[product_id]['cantidad'] > 1:
            cart[product_id]['cantidad'] -= 1   # resta 1 unidad
        else:
            cart.pop(product_id)                # elimina el producto

        session['cart'] = cart
        session.modified = True

    return redirect(url_for('ver_carrito'))

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('ver_carrito'))


@app.route('/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('ver_carrito'))

    total         = sum(item['precio'] * item['cantidad'] for item in cart.values())
    orden_id      = str(uuid.uuid4())[:12].upper()
    email_cliente = request.form.get('email', '')
    nombres       = ', '.join(item['nombre'] for item in cart.values())
    descripcion   = f"Okami Fit: {nombres[:100]}"

    # 1. Guardar orden pendiente en BD
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ordenes (orden_id, email_cliente, total, estado)
            VALUES (?, ?, ?, 'pendiente')
        """, (orden_id, email_cliente, total))

        for item in cart.values():
            cursor.execute("""
                INSERT INTO orden_detalle
                    (orden_id, producto_id, nombre, precio, cantidad, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                orden_id,
                item['id'],
                item['nombre'],
                item['precio'],
                item['cantidad'],
                item['precio'] * item['cantidad']
            ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f'Error creando la orden: {e}', 'error')
        return redirect(url_for('ver_carrito'))
    finally:
        cursor.close()
        conn.close()

    # 2. Crear sesión de checkout en OnvoPay
    BASE_URL  = request.host_url.rstrip('/')
    resultado = crear_checkout_session(
    items_carrito = list(cart.values()),
    orden_id      = orden_id,
    email_cliente = email_cliente,
    success_url   = f'{BASE_URL}/pago/exitoso?orden={orden_id}',
    cancel_url    = f'{BASE_URL}/pago/cancelado'
)

    if resultado['ok']:
        # Guardamos el ID de sesión OnvoPay para verificarlo después
        session['orden_pendiente'] = {
            'orden_id':   orden_id,
            'total':      total,
            'session_id': resultado['id']
        }
        session.modified = True
        return redirect(resultado['url'])  # → página de pago de OnvoPay
    else:
        flash(f"Error al procesar el pago: {resultado['error']}", 'error')
        return redirect(url_for('ver_carrito'))


@app.route('/pago/exitoso')
def pago_exitoso():
    orden_id = request.args.get('orden', '')
    orden    = session.pop('orden_pendiente', None)
    # Vaciamos el carrito solo si la orden coincide
    if orden and orden.get('orden_id') == orden_id:
        session.pop('cart', None)
        session.modified = True
    return render_template('pago_exitoso.html', orden=orden)


@app.route('/pago/cancelado')
def pago_cancelado():
    return render_template('pago_cancelado.html')


@app.route('/pago/webhook', methods=['POST'])
def pago_webhook():
    # 1. Verificar que la petición viene de OnvoPay
    webhook_secret = request.headers.get('X-Webhook-Secret', '')
    if webhook_secret != ONVO_WEBHOOK_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    data  = request.get_json()
    tipo  = data.get('type')
    pago  = data.get('data', {})

    if tipo == 'payment-intent.succeeded' or tipo == 'checkout-session.succeeded':
        orden_id    = pago.get('description', '').replace('Okami Fit: ', '').split(',')[0].strip()
        referencia  = pago.get('id', '')
        monto       = pago.get('amount', 0)

        # Extraemos el orden_id de la descripción o del metadata si lo agregaste
        # Aquí usamos una forma más robusta buscando por monto y estado pendiente
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE ordenes
                SET estado = 'aprobado',
                    referencia_pago = ?,
                    fecha_pago = GETDATE()
                WHERE orden_id = ? AND estado = 'pendiente'
            """, (referencia, orden_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()

    return jsonify({'received': True}), 200









if __name__ == "__main__":
    # Azure requiere que la app escuche en 0.0.0.0
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
