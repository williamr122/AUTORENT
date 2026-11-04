"""
app.py - Servidor Web Flask para AutoRent (ESPOL)
Implementa la interfaz web y la API REST para los 16 Requerimientos Funcionales
y la observancia de las 17 Reglas de Negocio.
"""

from flask import Flask, render_template, request, jsonify, session
import os
import database
import models
from models import BusinessRuleError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)
app.secret_key = "autorent_secret_key_espol_paralelo_5"

# Inicializar BD al arrancar
database.init_db()

# Middleware para simular sesión por defecto de Administrador (para facilidad de prueba)
@app.before_request
def ensure_session():
    if "user" not in session:
        session["user"] = {
            "Id_empleado": 1,
            "nombres": "Lady",
            "apellidos": "Zuñiga",
            "usuario": "admin",
            "rol": "Administrador"
        }

# =====================================================================
# RUTA PRINCIPAL
# =====================================================================
@app.route("/")
def index():
    return render_template("index.html")

# =====================================================================
# AUTENTICACIÓN Y ROLES (RF15)
# =====================================================================
@app.route("/api/auth/current", methods=["GET"])
def current_user():
    return jsonify({"success": True, "user": session.get("user")})

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    usuario = data.get("usuario", "")
    clave = data.get("clave", "")
    user = models.authenticate_user(usuario, clave)
    if user:
        session["user"] = user
        return jsonify({"success": True, "user": user, "message": f"Bienvenido, {user['nombres']} ({user['rol']})"})
    return jsonify({"success": False, "error": "Credenciales inválidas."}), 401

@app.route("/api/auth/switch-role", methods=["POST"])
def switch_role():
    """Permite alternar rápidamente el rol para probar los permisos de Administrador, Gerente y Empleado."""
    data = request.json or {}
    rol = data.get("rol", "Administrador")
    
    # Buscar un empleado que tenga ese rol
    empleado = database.execute_single("SELECT Id_empleado, nombres, apellidos, usuario, rol FROM EMPLEADO WHERE rol = ? AND activo = 1 LIMIT 1", (rol,))
    if empleado:
        session["user"] = empleado
        return jsonify({"success": True, "user": empleado, "message": f"Rol cambiado a {rol} ({empleado['nombres']} {empleado['apellidos']})"})
    return jsonify({"success": False, "error": "No se encontró usuario con ese rol"}), 404

# =====================================================================
# CLIENTES (RF01 - RF04, RB01, RB15)
# =====================================================================
@app.route("/api/clientes", methods=["GET"])
def api_get_clientes():
    filtro = request.args.get("q", "")
    clientes = models.get_clientes(filtro)
    return jsonify({"success": True, "data": clientes})

@app.route("/api/clientes", methods=["POST"])
def api_create_cliente():
    try:
        data = request.json or {}
        id_c = models.create_cliente(data)
        return jsonify({"success": True, "id": id_c, "message": "Cliente registrado exitosamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/clientes/<int:id_cliente>", methods=["PUT"])
def api_update_cliente(id_cliente):
    try:
        data = request.json or {}
        models.update_cliente(id_cliente, data)
        return jsonify({"success": True, "message": "Cliente actualizado correctamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/clientes/<int:id_cliente>", methods=["DELETE"])
def api_delete_cliente(id_cliente):
    # Verificar permisos (Gerente no puede eliminar)
    if session.get("user", {}).get("rol") == "Gerente":
        return jsonify({"success": False, "error": "El rol Gerente tiene acceso de solo consulta y supervisión."}), 403
    try:
        models.delete_cliente(id_cliente)
        return jsonify({"success": True, "message": "Cliente eliminado exitosamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================================================
# VEHÍCULOS (RF05 - RF08, RB02, RB05, RB06, RB17)
# =====================================================================
@app.route("/api/vehiculos", methods=["GET"])
def api_get_vehiculos():
    estado = request.args.get("estado", "")
    id_cat = request.args.get("id_categoria")
    id_cat = int(id_cat) if id_cat else None
    q = request.args.get("q", "")
    vehiculos = models.get_vehiculos(estado=estado, id_categoria=id_cat, busqueda=q)
    return jsonify({"success": True, "data": vehiculos})

@app.route("/api/vehiculos", methods=["POST"])
def api_create_vehiculo():
    try:
        data = request.json or {}
        id_v = models.create_vehiculo(data)
        return jsonify({"success": True, "id": id_v, "message": "Vehículo registrado correctamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/vehiculos/<int:id_vehiculo>", methods=["PUT"])
def api_update_vehiculo(id_vehiculo):
    try:
        data = request.json or {}
        models.update_vehiculo(id_vehiculo, data)
        return jsonify({"success": True, "message": "Vehículo actualizado correctamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/vehiculos/<int:id_vehiculo>", methods=["DELETE"])
def api_delete_vehiculo(id_vehiculo):
    if session.get("user", {}).get("rol") == "Gerente":
        return jsonify({"success": False, "error": "El rol Gerente tiene acceso de solo consulta y supervisión."}), 403
    try:
        models.delete_vehiculo(id_vehiculo)
        return jsonify({"success": True, "message": "Vehículo eliminado exitosamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/vehiculos/<int:id_vehiculo>/liberar", methods=["POST"])
def api_liberar_vehiculo(id_vehiculo):
    try:
        models.finalizar_mantenimiento_vehiculo(id_vehiculo)
        return jsonify({"success": True, "message": "Vehículo liberado de taller y colocado como Disponible."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================================================
# CATÁLOGOS: MARCAS, MODELOS, CATEGORÍAS (RF09)
# =====================================================================
@app.route("/api/marcas", methods=["GET", "POST"])
def api_marcas():
    if request.method == "GET":
        return jsonify({"success": True, "data": models.get_marcas()})
    data = request.json or {}
    try:
        id_m = models.create_marca(data.get("nombre_marca", ""))
        return jsonify({"success": True, "id": id_m, "message": "Marca creada exitosamente."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/marcas/<int:id_marca>", methods=["DELETE"])
def api_delete_marca(id_marca):
    try:
        models.delete_marca(id_marca)
        return jsonify({"success": True, "message": "Marca eliminada exitosamente."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/modelos", methods=["GET", "POST"])
def api_modelos():
    if request.method == "GET":
        id_marca = request.args.get("id_marca")
        id_marca = int(id_marca) if id_marca else None
        return jsonify({"success": True, "data": models.get_modelos(id_marca)})
    data = request.json or {}
    try:
        id_m = models.create_modelo(data.get("nombre_modelo", ""), int(data.get("id_marca", 0)))
        return jsonify({"success": True, "id": id_m, "message": "Modelo creado exitosamente."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/modelos/<int:id_modelo>", methods=["DELETE"])
def api_delete_modelo(id_modelo):
    try:
        models.delete_modelo(id_modelo)
        return jsonify({"success": True, "message": "Modelo eliminado exitosamente."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/categorias", methods=["GET", "POST"])
def api_categorias():
    if request.method == "GET":
        return jsonify({"success": True, "data": models.get_categorias()})
    data = request.json or {}
    try:
        id_c = models.create_categoria(data.get("nombre_categoria", ""))
        return jsonify({"success": True, "id": id_c, "message": "Categoría creada exitosamente."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/categorias/<int:id_categoria>", methods=["DELETE"])
def api_delete_categoria(id_categoria):
    try:
        models.delete_categoria(id_categoria)
        return jsonify({"success": True, "message": "Categoría eliminada exitosamente."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# =====================================================================
# RESERVAS (RF10, RB03, RB04, RB06)
# =====================================================================
@app.route("/api/reservas", methods=["GET", "POST"])
def api_reservas():
    if request.method == "GET":
        return jsonify({"success": True, "data": models.get_reservas()})
    try:
        data = request.json or {}
        # Asignar empleado actual si no viene especificado
        if not data.get("Id_empleado"):
            data["Id_empleado"] = session.get("user", {}).get("Id_empleado", 1)
        id_r = models.create_reserva(data)
        return jsonify({"success": True, "id": id_r, "message": "Reserva creada exitosamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/reservas/<int:id_reserva>/status", methods=["PUT"])
def api_update_reserva_status(id_reserva):
    try:
        data = request.json or {}
        estado = data.get("estado", "")
        models.update_reserva_status(id_reserva, estado)
        return jsonify({"success": True, "message": f"Estado de reserva actualizado a {estado}."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================================================
# ALQUILERES (RF11, RB05, RB06, RB07, RB08, RB09, RB16)
# =====================================================================
@app.route("/api/alquileres", methods=["GET", "POST"])
def api_alquileres():
    if request.method == "GET":
        return jsonify({"success": True, "data": models.get_alquileres()})
    try:
        data = request.json or {}
        if not data.get("Id_empleado"):
            data["Id_empleado"] = session.get("user", {}).get("Id_empleado", 1)
        id_a = models.create_alquiler(data)
        return jsonify({"success": True, "id": id_a, "message": "Contrato de alquiler formalizado exitosamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/alquileres/<int:id_alquiler>", methods=["GET"])
def api_get_alquiler_detalle(id_alquiler):
    alquiler = models.get_alquiler_by_id(id_alquiler)
    if not alquiler:
        return jsonify({"success": False, "error": "Alquiler no encontrado."}), 404
    pagos = models.get_pagos_by_alquiler(id_alquiler)
    return jsonify({"success": True, "data": alquiler, "pagos": pagos})

# =====================================================================
# PAGOS (RF12, RB10, RB11)
# =====================================================================
@app.route("/api/pagos", methods=["GET", "POST"])
def api_pagos():
    if request.method == "GET":
        return jsonify({"success": True, "data": models.get_todos_pagos()})
    try:
        data = request.json or {}
        if not data.get("Id_empleado"):
            data["Id_empleado"] = session.get("user", {}).get("Id_empleado", 1)
        id_p = models.create_pago(data)
        return jsonify({"success": True, "id": id_p, "message": "Pago registrado exitosamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================================================
# DEVOLUCIONES (RF13, RB12, RB13)
# =====================================================================
@app.route("/api/devoluciones", methods=["GET", "POST"])
def api_devoluciones():
    if request.method == "GET":
        return jsonify({"success": True, "data": models.get_devoluciones()})
    try:
        data = request.json or {}
        id_d = models.create_devolucion(data)
        return jsonify({"success": True, "id": id_d, "message": "Devolución registrada exitosamente. Vehículo reintegrado."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================================================
# MANTENIMIENTOS (RF14, RB06, RB14)
# =====================================================================
@app.route("/api/mantenimientos", methods=["GET", "POST"])
def api_mantenimientos():
    if request.method == "GET":
        return jsonify({"success": True, "data": models.get_mantenimientos()})
    try:
        data = request.json or {}
        if not data.get("Id_empleado"):
            data["Id_empleado"] = session.get("user", {}).get("Id_empleado", 1)
        id_m = models.create_mantenimiento(data)
        return jsonify({"success": True, "id": id_m, "message": "Orden de mantenimiento registrada exitosamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================================================
# EMPLEADOS Y USUARIOS (RF15)
# =====================================================================
@app.route("/api/empleados", methods=["GET", "POST"])
def api_empleados():
    if request.method == "GET":
        return jsonify({"success": True, "data": models.get_empleados()})
    if session.get("user", {}).get("rol") != "Administrador":
        return jsonify({"success": False, "error": "Solo los Administradores pueden gestionar usuarios y empleados."}), 403
    try:
        data = request.json or {}
        id_e = models.create_empleado(data)
        return jsonify({"success": True, "id": id_e, "message": "Empleado y credenciales creados correctamente."})
    except BusinessRuleError as e:
        return jsonify({"success": False, "error": e.message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================================================
# REPORTES Y DASHBOARD (RF16)
# =====================================================================
@app.route("/api/reportes/dashboard", methods=["GET"])
def api_dashboard_metrics():
    metrics = models.get_dashboard_metrics()
    return jsonify({"success": True, "data": metrics})

if __name__ == "__main__":
    print("=" * 60)
    print("AutoRent - Sistema de Alquiler de Vehículos (ESPOL)")
    print("Iniciando servidor local en http://127.0.0.1:5000 ...")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)

