# Importacion de las librerias necesarias
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, send_from_directory
import pyodbc
import uuid
import os
from functools import wraps

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# Crear carpeta si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Aqui creamos la aplicacion usando el Framework Flask
app = Flask(__name__)
app.secret_key = "root123"

# FIX PARA QUE DELETE ENVÍE LA COOKIE
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True  # En producción cámbialo a True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_PERMANENT"] = False

SQL_SERVER_CONFIG = {
    "driver": "{ODBC Driver 17 for SQL Server}",
    "server": "localhost",
    "database": "BD_Okamifit",
    "timeout": 3,
}

def get_connection():
    try:
        conn_str = (
            f"DRIVER={SQL_SERVER_CONFIG['driver']};"
            f"SERVER={SQL_SERVER_CONFIG['server']};"
            f"DATABASE={SQL_SERVER_CONFIG['database']};"
            f"Trusted_Connection=yes;"
            f"ConnectionTimeout={SQL_SERVER_CONFIG['timeout']};"
        )
        conn = pyodbc.connect(conn_str)
        return conn, "sqlserver"
    except pyodbc.Error as ex:
        print(f"❌ FALLO CRÍTICO: SQL Server está caído: {ex}")
        return None, None

# --- Helpers para convertir filas/resultsets a dict ---
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

# decorador de seguridad para administrador
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = obtener_usuario_actual()
        if not user_id:
            return jsonify({"success": False, "message": "Autenticación requerida"}), 401

        conn, _ = get_connection()
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

# --- Autenticación / sesiones ---

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    correo = data.get("correo")
    contrasena = data.get("contrasena")

    conn, _ = get_connection()
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

    conn, _ = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        # Ejecutar el SP que valida la sesión en SQL Server
        cursor.execute("{CALL sp_Validar_SESION1(?)}", (token,))
        row = cursor.fetchone()
        r = row_to_dict_lower(row, cursor)
        # El SP retorna id_usuario
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
    # Quitar token de la sesión
    token = session.pop("token", None)

    if token:
        conn, _ = get_connection()
        if conn:
            try:
                cursor = conn.cursor()

                # Llamar el SP para cerrar sesión en SQL Server
                cursor.execute("{CALL sp_Cerrar_SESION1(?)}", (token,))
                conn.commit()
            except Exception as e:
                print(f"Error al cerrar sesión en BD: {e}")
            finally:
                conn.close()

    # Redirigir al index después de cerrar sesión
    return redirect(url_for("index"))

@app.route("/")
def index():
    return render_template("index.html")



# -----------------------
# MÓDULO CATÁLOGO (productos)
# -----------------------

# GET /api/productos
@app.route("/api/productos", methods=["GET"])
def get_productos():
    conn, _ = get_connection()
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

# GET /api/productos/<idProducto>
@app.route("/api/productos/<int:idProducto>", methods=["GET"])
def get_producto(idProducto):
    conn, _ = get_connection()
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

# GET /api/productos/categoria/<idCategoria>
@app.route("/api/productos/categoria/<int:idCategoria>", methods=["GET"])
def get_productos_por_categoria(idCategoria):
    conn, _ = get_connection()
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

# POST /api/productos
@app.route('/api/productos', methods=['POST'])
def api_crear_producto():
    try:
        # ----------- Campos normales del form ------------
        nombre = request.form.get("nombre")
        precioBase = request.form.get("precioBase")
        descripcion = request.form.get("descripcion")
        enOferta = request.form.get("enOferta", "false") == "true"
        idCategoria = request.form.get("idCategoria")

        # ----------- Imagen recibida ------------
        imagen = request.files.get("imagenFile")
        if imagen:
            # Guarda la imagen en carpeta /uploads
            uploads_path = os.path.join("uploads", imagen.filename)
            imagen.save(uploads_path)
            urlImagen = imagen.filename
        else:
            urlImagen = None

        # ------------------ DEBUGGING ------------------
        print("DATA RECIBIDA FORM:", request.form)
        print("ARCHIVO RECIBIDO:", imagen)
        print("URL IMAGEN GENERADA:", urlImagen)
        # ------------------------------------------------

        # ----------- Validación ------------
        if not nombre or not precioBase or not idCategoria or not urlImagen:
            return jsonify({"success": False, "message": "Faltan campos obligatorios"}), 400

        # ----------- Guardar en BD ------------
        conn, _ = get_connection()   # ← recibe ambos valores
        cursor = conn.cursor()

        print("Nombre enviado a la BD:", urlImagen)


        cursor.execute("""
            EXEC sp_Agregar_PRODUCTOS
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

    # Imagen opcional
    imagen = request.files.get("imagenFile")
    if imagen:
        uploads_path = os.path.join("uploads", imagen.filename)
        imagen.save(uploads_path)
        urlImagen = imagen.filename
    else:
        urlImagen = None  # NO obligar

    if not nombre or precioBase is None or idCategoria is None:
        return jsonify({"success": False, "message": "Faltan campos"}), 400

    conn, _ = get_connection()
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


# DELETE /api/productos/<idProducto>
@app.route("/api/productos/<int:idProducto>", methods=["DELETE"])
#@admin_required
def eliminar_producto(idProducto):
    print("SESSION:", session)
    conn, _ = get_connection()
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

# -----------------------
# MÓDULO INVENTARIO (categorias, variantes, stock)
# -----------------------

# GET /api/categorias
@app.route("/api/categorias", methods=["GET"])
def get_categorias():
    conn, _ = get_connection()
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

# GET /api/variantes
@app.route("/api/variantes", methods=["GET"])
def get_variantes():
    conn, _ = get_connection()
    if not conn:
        return jsonify({"success": False, "message": "No se pudo conectar a la BD"}), 500
    try:
        cur = conn.cursor()
        cur.execute("EXEC sp_Obtener_VARIANTES1 ?, ?", (None, 0))
        variantes = rows_to_dicts(cur)
        return jsonify({"success": True, "data": variantes})
    except Exception as e:
        print("ERROR GET /api/variantes:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# GET /api/inventario/<idProducto>
@app.route("/api/inventario/<int:idProducto>", methods=["GET"])
def get_inventario_producto(idProducto):
    conn, _ = get_connection()
    if not conn:
        return jsonify({"success": False, "message": "No se pudo conectar a la BD"}), 500
    try:
        cur = conn.cursor()
        cur.execute("EXEC sp_Obtener_STOCK_VARIANTE1 ?, ?", (idProducto, None))
        stock = rows_to_dicts(cur)
        return jsonify({"success": True, "data": stock})
    except Exception as e:
        print("ERROR GET /api/inventario:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# PUT /api/inventario/<idProducto>
@app.route("/api/inventario/<int:idProducto>", methods=["PUT"])
@admin_required
def update_inventario_producto(idProducto):
    """
    Espera un JSON con 'stock': [
        {"idVariante": 1, "cantidadStock": 10},
        {"idVariante": 2, "cantidadStock": 5},
        ...
    ]
    """
    payload = request.get_json()
    stock_list = payload.get("stock", [])
    if not isinstance(stock_list, list):
        return jsonify({"success": False, "message": "Formato de stock inválido"}), 400

    conn, _ = get_connection()
    if not conn:
        return jsonify({"success": False, "message": "No se pudo conectar a la BD"}), 500

    try:
        cur = conn.cursor()
        for item in stock_list:
            idVar = item.get("idVariante")
            cantidad = item.get("cantidadStock", 0)
            if idVar is None:
                continue

            # verificar si ya existe registro
            cur.execute("SELECT cantidadStock FROM STOCK_VARIANTE WHERE idProducto = ? AND idVariante = ?", (idProducto, idVar))
            existing = cur.fetchone()
            if existing:
                # actualizar
                cur.execute("EXEC sp_Actualizar_STOCK_VARIANTE ?, ?, ?", (idProducto, idVar, cantidad))
            else:
                # insertar
                cur.execute("EXEC sp_Agregar_STOCK_VARIANTE ?, ?, ?", (idProducto, idVar, cantidad))
        conn.commit()
        return jsonify({"success": True, "message": "Inventario actualizado"})
    except Exception as e:
        conn.rollback()
        print("ERROR PUT /api/inventario:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# SUBIR IMAGEN
@app.route("/api/upload-image", methods=["POST"])
def upload_image():
    try:
        if "imagen" not in request.files:
            return jsonify({"success": False, "message": "No se envió la imagen"}), 400

        file = request.files["imagen"]

        filename = file.filename
        save_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(save_path)

        # la URL que usa el frontend
        url = f"/uploads/{filename}"

        return jsonify({"success": True, "url": url})

        print("Nombre archivo guardado realmente:", filename)

    except Exception as e:
        print("Error subiendo imagen:", e)
        return jsonify({"success": False, "message": "Error interno"}), 500


@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)



# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)
