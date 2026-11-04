"""
models.py - Capa de Lógica de Negocio y Reglas de Negocio (RB01 - RB17)
Proyecto AutoRent - ESPOL
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import database

class BusinessRuleError(Exception):
    """Excepción para violaciones a las reglas de negocio."""
    def __init__(self, message: str, code: str = "ERR_BUSINESS_RULE"):
        super().__init__(message)
        self.code = code
        self.message = message

# =====================================================================
# GESTIÓN DE CLIENTES (RF01 - RF04, RB01, RB15)
# =====================================================================

def get_clientes(filtro: str = "") -> List[Dict[str, Any]]:
    if filtro:
        query = """
            SELECT * FROM CLIENTE 
            WHERE Numero_Identificacion LIKE ? OR Nombres LIKE ? OR Apellidos LIKE ?
            ORDER BY Apellidos, Nombres
        """
        wildcard = f"%{filtro}%"
        return database.execute_query(query, (wildcard, wildcard, wildcard))
    return database.execute_query("SELECT * FROM CLIENTE ORDER BY Apellidos, Nombres")

def get_cliente_by_id(id_cliente: int) -> Optional[Dict[str, Any]]:
    return database.execute_single("SELECT * FROM CLIENTE WHERE Id_cliente = ?", (id_cliente,))

def create_cliente(data: Dict[str, Any]) -> int:
    num_id = data.get("Numero_Identificacion", "").strip()
    nombres = data.get("Nombres", "").strip()
    apellidos = data.get("Apellidos", "").strip()
    telefono = data.get("Telefono", "").strip()
    direccion = data.get("Direccion", "").strip()

    if not num_id or not nombres or not apellidos:
        raise BusinessRuleError("Identificación, nombres y apellidos son campos obligatorios.")

    # RB01: Unicidad de cliente
    existente = database.execute_single("SELECT Id_cliente FROM CLIENTE WHERE Numero_Identificacion = ?", (num_id,))
    if existente:
        raise BusinessRuleError(f"RB01: Ya existe un cliente registrado con el número de identificación '{num_id}'.")

    return database.execute_dml(
        "INSERT INTO CLIENTE (Numero_Identificacion, Nombres, Apellidos, Telefono, Direccion) VALUES (?, ?, ?, ?, ?)",
        (num_id, nombres, apellidos, telefono, direccion)
    )

def update_cliente(id_cliente: int, data: Dict[str, Any]) -> int:
    cliente = get_cliente_by_id(id_cliente)
    if not cliente:
        raise BusinessRuleError("Cliente no encontrado.")

    num_id = data.get("Numero_Identificacion", cliente["Numero_Identificacion"]).strip()
    nombres = data.get("Nombres", cliente["Nombres"]).strip()
    apellidos = data.get("Apellidos", cliente["Apellidos"]).strip()
    telefono = data.get("Telefono", cliente["Telefono"]).strip()
    direccion = data.get("Direccion", cliente["Direccion"]).strip()

    # RB01 en actualización
    existente = database.execute_single("SELECT Id_cliente FROM CLIENTE WHERE Numero_Identificacion = ? AND Id_cliente != ?", (num_id, id_cliente))
    if existente:
        raise BusinessRuleError(f"RB01: El número de identificación '{num_id}' ya pertenece a otro cliente.")

    return database.execute_dml(
        "UPDATE CLIENTE SET Numero_Identificacion = ?, Nombres = ?, Apellidos = ?, Telefono = ?, Direccion = ? WHERE Id_cliente = ?",
        (num_id, nombres, apellidos, telefono, direccion, id_cliente)
    )

def delete_cliente(id_cliente: int) -> int:
    # RB15: Prohibido eliminar clientes con historial de reservas o alquileres
    reservas = database.execute_single("SELECT COUNT(*) as cnt FROM RESERVA WHERE Id_cliente = ?", (id_cliente,))
    if reservas and reservas["cnt"] > 0:
        raise BusinessRuleError("RB15: No se puede eliminar el cliente porque posee reservas históricas registradas.")

    alquileres = database.execute_single("SELECT COUNT(*) as cnt FROM ALQUILER WHERE Id_cliente = ?", (id_cliente,))
    if alquileres and alquileres["cnt"] > 0:
        raise BusinessRuleError("RB15: No se puede eliminar el cliente porque posee contratos de alquiler registrados.")

    return database.execute_dml("DELETE FROM CLIENTE WHERE Id_cliente = ?", (id_cliente,))

# =====================================================================
# GESTIÓN DE VEHÍCULOS (RF05 - RF08, RB02, RB05, RB06, RB17)
# =====================================================================

def get_vehiculos(estado: str = "", id_categoria: int = None, busqueda: str = "") -> List[Dict[str, Any]]:
    query = """
        SELECT v.*, m.nombre_modelo, ma.nombre_marca, c.nombre_categoria
        FROM VEHICULO v
        JOIN MODELO m ON v.id_modelo = m.Id_modelo
        JOIN MARCA ma ON m.id_marca = ma.Id_marca
        JOIN CATEGORIA c ON v.id_categoria = c.Id_categoria
        WHERE 1=1
    """
    params = []
    if estado:
        query += " AND v.estado = ?"
        params.append(estado)
    if id_categoria:
        query += " AND v.id_categoria = ?"
        params.append(id_categoria)
    if busqueda:
        query += " AND (v.matricula LIKE ? OR ma.nombre_marca LIKE ? OR m.nombre_modelo LIKE ?)"
        wild = f"%{busqueda}%"
        params.extend([wild, wild, wild])

    query += " ORDER BY v.Id_vehiculo DESC"
    return database.execute_query(query, tuple(params))

def get_vehiculo_by_id(id_vehiculo: int) -> Optional[Dict[str, Any]]:
    query = """
        SELECT v.*, m.nombre_modelo, ma.nombre_marca, c.nombre_categoria
        FROM VEHICULO v
        JOIN MODELO m ON v.id_modelo = m.Id_modelo
        JOIN MARCA ma ON m.id_marca = ma.Id_marca
        JOIN CATEGORIA c ON v.id_categoria = c.Id_categoria
        WHERE v.Id_vehiculo = ?
    """
    return database.execute_single(query, (id_vehiculo,))

def create_vehiculo(data: Dict[str, Any]) -> int:
    matricula = data.get("matricula", "").strip().upper()
    año = int(data.get("año", 2024))
    color = data.get("color", "").strip()
    capacidad = int(data.get("capacidad", 5))
    tarifa = float(data.get("tarifa", 0))
    estado = data.get("estado", "Disponible")
    id_modelo = int(data.get("id_modelo", 0))
    id_categoria = int(data.get("id_categoria", 0))

    if not matricula or tarifa <= 0 or capacidad <= 0 or not id_modelo or not id_categoria:
        raise BusinessRuleError("Todos los campos del vehículo deben ser válidos y tarifa/capacidad > 0.")

    # RB02: Unicidad Vehicular
    existente = database.execute_single("SELECT Id_vehiculo FROM VEHICULO WHERE matricula = ?", (matricula,))
    if existente:
        raise BusinessRuleError(f"RB02: Ya existe un vehículo registrado con la placa/matrícula '{matricula}'.")

    return database.execute_dml(
        "INSERT INTO VEHICULO (matricula, año, color, capacidad, tarifa, estado, id_modelo, id_categoria) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (matricula, año, color, capacidad, tarifa, estado, id_modelo, id_categoria)
    )

def update_vehiculo(id_vehiculo: int, data: Dict[str, Any]) -> int:
    v = get_vehiculo_by_id(id_vehiculo)
    if not v:
        raise BusinessRuleError("Vehículo no encontrado.")

    matricula = data.get("matricula", v["matricula"]).strip().upper()
    año = int(data.get("año", v["año"]))
    color = data.get("color", v["color"]).strip()
    capacidad = int(data.get("capacidad", v["capacidad"]))
    tarifa = float(data.get("tarifa", v["tarifa"]))
    estado = data.get("estado", v["estado"])
    id_modelo = int(data.get("id_modelo", v["id_modelo"]))
    id_categoria = int(data.get("id_categoria", v["id_categoria"]))

    # RB02
    existente = database.execute_single("SELECT Id_vehiculo FROM VEHICULO WHERE matricula = ? AND Id_vehiculo != ?", (matricula, id_vehiculo))
    if existente:
        raise BusinessRuleError(f"RB02: La matrícula '{matricula}' ya está asignada a otro vehículo.")

    return database.execute_dml(
        "UPDATE VEHICULO SET matricula = ?, año = ?, color = ?, capacidad = ?, tarifa = ?, estado = ?, id_modelo = ?, id_categoria = ? WHERE Id_vehiculo = ?",
        (matricula, año, color, capacidad, tarifa, estado, id_modelo, id_categoria, id_vehiculo)
    )

def delete_vehiculo(id_vehiculo: int) -> int:
    # RB17: Prohibido eliminar vehículos con historial de reservas, alquileres o mantenimientos
    reservas = database.execute_single("SELECT COUNT(*) as cnt FROM RESERVA WHERE Id_vehiculo = ?", (id_vehiculo,))
    if reservas and reservas["cnt"] > 0:
        raise BusinessRuleError("RB17: No se puede eliminar el vehículo porque tiene reservas asociadas.")

    alquileres = database.execute_single("SELECT COUNT(*) as cnt FROM ALQUILER WHERE Id_vehiculo = ?", (id_vehiculo,))
    if alquileres and alquileres["cnt"] > 0:
        raise BusinessRuleError("RB17: No se puede eliminar el vehículo porque tiene contratos de alquiler registrados.")

    mantenimientos = database.execute_single("SELECT COUNT(*) as cnt FROM MANTENIMIENTO WHERE Id_vehiculo = ?", (id_vehiculo,))
    if mantenimientos and mantenimientos["cnt"] > 0:
        raise BusinessRuleError("RB17: No se puede eliminar el vehículo porque tiene órdenes de mantenimiento registradas.")

    return database.execute_dml("DELETE FROM VEHICULO WHERE Id_vehiculo = ?", (id_vehiculo,))

# =====================================================================
# CATÁLOGOS: MARCAS, MODELOS, CATEGORÍAS (RF09)
# =====================================================================

def get_marcas() -> List[Dict[str, Any]]:
    return database.execute_query("SELECT * FROM MARCA ORDER BY nombre_marca")

def create_marca(nombre: str) -> int:
    nombre = nombre.strip()
    if not nombre:
        raise BusinessRuleError("El nombre de la marca no puede estar vacío.")
    return database.execute_dml("INSERT INTO MARCA (nombre_marca) VALUES (?)", (nombre,))

def delete_marca(id_marca: int) -> int:
    modelos = database.execute_single("SELECT COUNT(*) as cnt FROM MODELO WHERE id_marca = ?", (id_marca,))
    if modelos and modelos["cnt"] > 0:
        raise BusinessRuleError("No se puede eliminar la marca porque tiene modelos asociados.")
    return database.execute_dml("DELETE FROM MARCA WHERE Id_marca = ?", (id_marca,))

def get_modelos(id_marca: int = None) -> List[Dict[str, Any]]:
    if id_marca:
        return database.execute_query("""
            SELECT m.*, ma.nombre_marca 
            FROM MODELO m JOIN MARCA ma ON m.id_marca = ma.Id_marca 
            WHERE m.id_marca = ? ORDER BY m.nombre_modelo
        """, (id_marca,))
    return database.execute_query("""
        SELECT m.*, ma.nombre_marca 
        FROM MODELO m JOIN MARCA ma ON m.id_marca = ma.Id_marca 
        ORDER BY ma.nombre_marca, m.nombre_modelo
    """)

def create_modelo(nombre: str, id_marca: int) -> int:
    nombre = nombre.strip()
    if not nombre or not id_marca:
        raise BusinessRuleError("El modelo y la marca asociada son obligatorios.")
    return database.execute_dml("INSERT INTO MODELO (nombre_modelo, id_marca) VALUES (?, ?)", (nombre, id_marca))

def delete_modelo(id_modelo: int) -> int:
    vehiculos = database.execute_single("SELECT COUNT(*) as cnt FROM VEHICULO WHERE id_modelo = ?", (id_modelo,))
    if vehiculos and vehiculos["cnt"] > 0:
        raise BusinessRuleError("No se puede eliminar el modelo porque tiene vehículos registrados.")
    return database.execute_dml("DELETE FROM MODELO WHERE Id_modelo = ?", (id_modelo,))

def get_categorias() -> List[Dict[str, Any]]:
    return database.execute_query("SELECT * FROM CATEGORIA ORDER BY nombre_categoria")

def create_categoria(nombre: str) -> int:
    nombre = nombre.strip()
    if not nombre:
        raise BusinessRuleError("El nombre de la categoría no puede estar vacío.")
    return database.execute_dml("INSERT INTO CATEGORIA (nombre_categoria) VALUES (?)", (nombre,))

def delete_categoria(id_categoria: int) -> int:
    vehiculos = database.execute_single("SELECT COUNT(*) as cnt FROM VEHICULO WHERE id_categoria = ?", (id_categoria,))
    if vehiculos and vehiculos["cnt"] > 0:
        raise BusinessRuleError("No se puede eliminar la categoría porque tiene vehículos registrados.")
    return database.execute_dml("DELETE FROM CATEGORIA WHERE Id_categoria = ?", (id_categoria,))

# =====================================================================
# GESTIÓN DE RESERVAS (RF10, RB03, RB04, RB06)
# =====================================================================

def get_reservas() -> List[Dict[str, Any]]:
    query = """
        SELECT r.*, 
               c.Nombres || ' ' || c.Apellidos AS cliente_nombre, c.Numero_Identificacion,
               v.matricula, ma.nombre_marca, m.nombre_modelo,
               e.nombres || ' ' || e.apellidos AS empleado_nombre
        FROM RESERVA r
        JOIN CLIENTE c ON r.Id_cliente = c.Id_cliente
        JOIN VEHICULO v ON r.Id_vehiculo = v.Id_vehiculo
        JOIN MODELO m ON v.id_modelo = m.Id_modelo
        JOIN MARCA ma ON m.id_marca = ma.Id_marca
        JOIN EMPLEADO e ON r.Id_empleado = e.Id_empleado
        ORDER BY r.Id_reserva DESC
    """
    return database.execute_query(query)

def create_reserva(data: Dict[str, Any]) -> int:
    id_cliente = int(data.get("Id_cliente", 0))
    id_vehiculo = int(data.get("Id_vehiculo", 0))
    id_empleado = int(data.get("Id_empleado", 0))
    fecha_inicio = data.get("fecha_inicio", "")
    fecha_fin = data.get("fecha_fin", "")
    estado = data.get("estado", "Pendiente")

    if not id_cliente or not id_vehiculo or not id_empleado or not fecha_inicio or not fecha_fin:
        raise BusinessRuleError("Todos los campos de la reserva son obligatorios.")

    if fecha_fin <= fecha_inicio:
        raise BusinessRuleError("La fecha y hora de fin de reserva debe ser posterior a la fecha de inicio.")

    # RB06: Ningún vehículo con estado 'En Mantenimiento' puede ser asignado
    vehiculo = get_vehiculo_by_id(id_vehiculo)
    if not vehiculo:
        raise BusinessRuleError("Vehículo no encontrado.")
    if vehiculo["estado"] == "En Mantenimiento":
        raise BusinessRuleError("RB06: El vehículo seleccionado se encuentra 'En Mantenimiento' y no puede ser reservado.")

    # RB04: Exclusividad temporal de reserva para reservas confirmadas
    if estado == "Confirmada":
        solapadas = database.execute_single("""
            SELECT COUNT(*) as cnt FROM RESERVA
            WHERE Id_vehiculo = ? AND estado = 'Confirmada'
              AND (? < fecha_fin AND ? > fecha_inicio)
        """, (id_vehiculo, fecha_inicio, fecha_fin))
        if solapadas and solapadas["cnt"] > 0:
            raise BusinessRuleError("RB04: Conflicto de disponibilidad. Ya existe una reserva confirmada para este vehículo en las fechas seleccionadas.")

    return database.execute_dml(
        "INSERT INTO RESERVA (fecha_inicio, fecha_fin, estado, Id_cliente, Id_vehiculo, Id_empleado) VALUES (?, ?, ?, ?, ?, ?)",
        (fecha_inicio, fecha_fin, estado, id_cliente, id_vehiculo, id_empleado)
    )

def update_reserva_status(id_reserva: int, nuevo_estado: str) -> int:
    reserva = database.execute_single("SELECT * FROM RESERVA WHERE Id_reserva = ?", (id_reserva,))
    if not reserva:
        raise BusinessRuleError("Reserva no encontrada.")

    if nuevo_estado == "Confirmada":
        # RB04 check
        solapadas = database.execute_single("""
            SELECT COUNT(*) as cnt FROM RESERVA
            WHERE Id_vehiculo = ? AND estado = 'Confirmada' AND Id_reserva != ?
              AND (? < fecha_fin AND ? > fecha_inicio)
        """, (reserva["Id_vehiculo"], id_reserva, reserva["fecha_inicio"], reserva["fecha_fin"]))
        if solapadas and solapadas["cnt"] > 0:
            raise BusinessRuleError("RB04: No se puede confirmar. Conflicto con otra reserva ya confirmada en el mismo período.")

    return database.execute_dml("UPDATE RESERVA SET estado = ? WHERE Id_reserva = ?", (nuevo_estado, id_reserva))

# =====================================================================
# GESTIÓN DE ALQUILERES (RF11, RB05, RB06, RB07, RB08, RB09, RB16)
# =====================================================================

def get_alquileres() -> List[Dict[str, Any]]:
    query = """
        SELECT a.*, 
               c.Nombres || ' ' || c.Apellidos AS cliente_nombre, c.Numero_Identificacion,
               v.matricula, ma.nombre_marca, m.nombre_modelo, v.tarifa,
               e.nombres || ' ' || e.apellidos AS empleado_nombre,
               COALESCE((SELECT SUM(monto) FROM PAGO WHERE Id_alquiler = a.Id_alquiler), 0) AS total_pagado,
               d.Id_devolucion, d.fecha_devolucion, d.estado_recepcion
        FROM ALQUILER a
        JOIN CLIENTE c ON a.Id_cliente = c.Id_cliente
        JOIN VEHICULO v ON a.Id_vehiculo = v.Id_vehiculo
        JOIN MODELO m ON v.id_modelo = m.Id_modelo
        JOIN MARCA ma ON m.id_marca = ma.Id_marca
        JOIN EMPLEADO e ON a.Id_empleado = e.Id_empleado
        LEFT JOIN DEVOLUCION d ON a.Id_alquiler = d.Id_alquiler
        ORDER BY a.Id_alquiler DESC
    """
    return database.execute_query(query)

def get_alquiler_by_id(id_alquiler: int) -> Optional[Dict[str, Any]]:
    query = """
        SELECT a.*, 
               c.Nombres || ' ' || c.Apellidos AS cliente_nombre, c.Numero_Identificacion, c.Telefono,
               v.matricula, ma.nombre_marca, m.nombre_modelo, v.tarifa,
               e.nombres || ' ' || e.apellidos AS empleado_nombre,
               COALESCE((SELECT SUM(monto) FROM PAGO WHERE Id_alquiler = a.Id_alquiler), 0) AS total_pagado,
               d.Id_devolucion, d.fecha_devolucion, d.estado_recepcion, d.observaciones AS obs_devolucion
        FROM ALQUILER a
        JOIN CLIENTE c ON a.Id_cliente = c.Id_cliente
        JOIN VEHICULO v ON a.Id_vehiculo = v.Id_vehiculo
        JOIN MODELO m ON v.id_modelo = m.Id_modelo
        JOIN MARCA ma ON m.id_marca = ma.Id_marca
        JOIN EMPLEADO e ON a.Id_empleado = e.Id_empleado
        LEFT JOIN DEVOLUCION d ON a.Id_alquiler = d.Id_alquiler
        WHERE a.Id_alquiler = ?
    """
    return database.execute_single(query, (id_alquiler,))

def create_alquiler(data: Dict[str, Any]) -> int:
    id_cliente = int(data.get("Id_cliente", 0))
    id_vehiculo = int(data.get("Id_vehiculo", 0))
    id_empleado = int(data.get("Id_empleado", 0))
    id_reserva = data.get("Id_reserva")
    id_reserva = int(id_reserva) if id_reserva else None
    fecha_inicio = data.get("fecha_inicio", "")
    fecha_dev_prevista = data.get("fecha_dev_prevista", "")

    # RB07: Trazabilidad obligatoria: cliente, vehículo, empleado
    if not id_cliente or not id_vehiculo or not id_empleado:
        raise BusinessRuleError("RB07: Todo alquiler debe estar vinculado obligatoriamente a un cliente, vehículo y empleado.")

    # RB08 & RB09: Coherencia temporal
    if not fecha_inicio or not fecha_dev_prevista:
        raise BusinessRuleError("RB08: El contrato debe especificar fecha y hora de inicio y devolución prevista.")
    if fecha_dev_prevista <= fecha_inicio:
        raise BusinessRuleError("RB09: La fecha y hora prevista de devolución debe ser estrictamente posterior a la de inicio.")

    # RB05 y RB06: Vehículo debe estar estrictamente 'Disponible'
    vehiculo = get_vehiculo_by_id(id_vehiculo)
    if not vehiculo:
        raise BusinessRuleError("Vehículo no encontrado.")
    if vehiculo["estado"] == "En Mantenimiento":
        raise BusinessRuleError("RB06: El vehículo está 'En Mantenimiento' y no puede ser alquilado.")
    if vehiculo["estado"] != "Disponible":
        raise BusinessRuleError(f"RB05: El vehículo tiene estado '{vehiculo['estado']}'. Solo se permite alquilar vehículos 'Disponible'.")

    # Si viene de reserva, verificar unicidad de contrato por reserva (1:0..1)
    if id_reserva:
        alquiler_previo = database.execute_single("SELECT Id_alquiler FROM ALQUILER WHERE Id_reserva = ?", (id_reserva,))
        if alquiler_previo:
            raise BusinessRuleError("Esta reserva ya fue formalizada en un contrato de alquiler previo.")

    id_alquiler = database.execute_dml(
        "INSERT INTO ALQUILER (fecha_inicio, fecha_dev_prevista, Id_reserva, Id_cliente, Id_vehiculo, Id_empleado, estado) VALUES (?, ?, ?, ?, ?, ?, 'Activo')",
        (fecha_inicio, fecha_dev_prevista, id_reserva, id_cliente, id_vehiculo, id_empleado)
    )

    # Actualizar estado de vehículo a Alquilado y reserva a Completada
    database.execute_dml("UPDATE VEHICULO SET estado = 'Alquilado' WHERE Id_vehiculo = ?", (id_vehiculo,))
    if id_reserva:
        database.execute_dml("UPDATE RESERVA SET estado = 'Completada' WHERE Id_reserva = ?", (id_reserva,))

    return id_alquiler

# =====================================================================
# GESTIÓN DE PAGOS (RF12, RB10, RB11)
# =====================================================================

def get_pagos_by_alquiler(id_alquiler: int) -> List[Dict[str, Any]]:
    query = """
        SELECT p.*, e.nombres || ' ' || e.apellidos AS empleado_nombre
        FROM PAGO p
        JOIN EMPLEADO e ON p.Id_empleado = e.Id_empleado
        WHERE p.Id_alquiler = ?
        ORDER BY p.Id_pago DESC
    """
    return database.execute_query(query, (id_alquiler,))

def get_todos_pagos() -> List[Dict[str, Any]]:
    query = """
        SELECT p.*, 
               e.nombres || ' ' || e.apellidos AS empleado_nombre,
               c.Nombres || ' ' || c.Apellidos AS cliente_nombre,
               v.matricula
        FROM PAGO p
        JOIN ALQUILER a ON p.Id_alquiler = a.Id_alquiler
        JOIN CLIENTE c ON a.Id_cliente = c.Id_cliente
        JOIN VEHICULO v ON a.Id_vehiculo = v.Id_vehiculo
        JOIN EMPLEADO e ON p.Id_empleado = e.Id_empleado
        ORDER BY p.Id_pago DESC
    """
    return database.execute_query(query)

def create_pago(data: Dict[str, Any]) -> int:
    id_alquiler = int(data.get("Id_alquiler", 0))
    id_empleado = int(data.get("Id_empleado", 0))
    metodo_pago = data.get("metodo_pago", "Efectivo").strip()
    monto = float(data.get("monto", 0))

    if not id_alquiler or not id_empleado:
        raise BusinessRuleError("Alquiler y empleado son obligatorios para registrar un pago.")

    # RB11: Validación de Importes (> 0)
    if monto <= 0:
        raise BusinessRuleError("RB11: El monto registrado en cada transacción de pago debe ser numérico y estrictamente mayor que cero.")

    # RB10: Asociación a un alquiler existente
    alquiler = get_alquiler_by_id(id_alquiler)
    if not alquiler:
        raise BusinessRuleError("El contrato de alquiler indicado no existe.")

    return database.execute_dml(
        "INSERT INTO PAGO (monto, metodo_pago, Id_alquiler, Id_empleado) VALUES (?, ?, ?, ?)",
        (monto, metodo_pago, id_alquiler, id_empleado)
    )

# =====================================================================
# GESTIÓN DE DEVOLUCIONES (RF13, RB12, RB13)
# =====================================================================

def get_devoluciones() -> List[Dict[str, Any]]:
    query = """
        SELECT d.*, 
               a.fecha_inicio, a.fecha_dev_prevista,
               c.Nombres || ' ' || c.Apellidos AS cliente_nombre,
               v.matricula, ma.nombre_marca, m.nombre_modelo
        FROM DEVOLUCION d
        JOIN ALQUILER a ON d.Id_alquiler = a.Id_alquiler
        JOIN CLIENTE c ON a.Id_cliente = c.Id_cliente
        JOIN VEHICULO v ON a.Id_vehiculo = v.Id_vehiculo
        JOIN MODELO m ON v.id_modelo = m.Id_modelo
        JOIN MARCA ma ON m.id_marca = ma.Id_marca
        ORDER BY d.Id_devolucion DESC
    """
    return database.execute_query(query)

def create_devolucion(data: Dict[str, Any]) -> int:
    id_alquiler = int(data.get("Id_alquiler", 0))
    estado_recepcion = data.get("estado_recepcion", "Excelente").strip()
    observaciones = data.get("observaciones", "").strip()

    if not id_alquiler or not estado_recepcion:
        raise BusinessRuleError("El alquiler y el estado de recepción son obligatorios.")

    alquiler = get_alquiler_by_id(id_alquiler)
    if not alquiler:
        raise BusinessRuleError("Alquiler no encontrado.")

    # RB13: Vinculación con contrato activo
    if alquiler["estado"] != "Activo":
        raise BusinessRuleError("RB13: Un registro de devolución sólo puede crearse si está vinculado a un contrato de alquiler activo.")

    # RB12: Unicidad de devolución (1:0..1)
    existente = database.execute_single("SELECT Id_devolucion FROM DEVOLUCION WHERE Id_alquiler = ?", (id_alquiler,))
    if existente:
        raise BusinessRuleError("RB12: Este contrato ya cuenta con un registro final de devolución.")

    id_devolucion = database.execute_dml(
        "INSERT INTO DEVOLUCION (estado_recepcion, observaciones, Id_alquiler) VALUES (?, ?, ?)",
        (estado_recepcion, observaciones, id_alquiler)
    )

    # Actualizar estado de alquiler a Finalizado
    database.execute_dml("UPDATE ALQUILER SET estado = 'Finalizado' WHERE Id_alquiler = ?", (id_alquiler,))

    # Actualizar estado del vehículo: si hubo daño o requiere taller -> 'En Mantenimiento', sino 'Disponible'
    if estado_recepcion in ["Requiere Mantenimiento", "Con Daños"]:
        database.execute_dml("UPDATE VEHICULO SET estado = 'En Mantenimiento' WHERE Id_vehiculo = ?", (alquiler["Id_vehiculo"],))
    else:
        database.execute_dml("UPDATE VEHICULO SET estado = 'Disponible' WHERE Id_vehiculo = ?", (alquiler["Id_vehiculo"],))

    return id_devolucion

# =====================================================================
# GESTIÓN DE MANTENIMIENTOS (RF14, RB06, RB14)
# =====================================================================

def get_mantenimientos() -> List[Dict[str, Any]]:
    query = """
        SELECT man.*, 
               v.matricula, ma.nombre_marca, m.nombre_modelo,
               e.nombres || ' ' || e.apellidos AS empleado_nombre
        FROM MANTENIMIENTO man
        JOIN VEHICULO v ON man.Id_vehiculo = v.Id_vehiculo
        JOIN MODELO m ON v.id_modelo = m.Id_modelo
        JOIN MARCA ma ON m.id_marca = ma.Id_marca
        JOIN EMPLEADO e ON man.Id_empleado = e.Id_empleado
        ORDER BY man.Id_mantenimiento DESC
    """
    return database.execute_query(query)

def create_mantenimiento(data: Dict[str, Any]) -> int:
    id_vehiculo = int(data.get("Id_vehiculo", 0))
    id_empleado = int(data.get("Id_empleado", 0))
    tipo = data.get("tipo_mantenimiento", "Preventivo").strip()
    descripcion = data.get("descripcion", "").strip()
    costo = float(data.get("costo", 0.0))
    cambiar_estado = data.get("poner_en_mantenimiento", False)

    if not id_vehiculo or not id_empleado or not descripcion:
        raise BusinessRuleError("Vehículo, empleado y descripción son requeridos.")

    if costo < 0:
        raise BusinessRuleError("El costo del mantenimiento no puede ser negativo.")

    # Control Financiero: Los costos no deben superar los ingresos acumulados
    total_ingresos = database.execute_single("SELECT COALESCE(SUM(monto), 0) as total FROM PAGO")["total"]
    total_costos_actuales = database.execute_single("SELECT COALESCE(SUM(costo), 0) as total FROM MANTENIMIENTO")["total"]
    if (total_costos_actuales + costo) > total_ingresos:
        raise BusinessRuleError(f"Control Financiero: El costo de la orden (${costo:.2f}) excede el presupuesto disponible. Los costos totales (${total_costos_actuales + costo:.2f}) no deben superar los ingresos generados (${total_ingresos:.2f}).")

    id_mant = database.execute_dml(
        "INSERT INTO MANTENIMIENTO (tipo_mantenimiento, descripcion, costo, Id_vehiculo, Id_empleado) VALUES (?, ?, ?, ?, ?)",
        (tipo, descripcion, costo, id_vehiculo, id_empleado)
    )

    if cambiar_estado:
        database.execute_dml("UPDATE VEHICULO SET estado = 'En Mantenimiento' WHERE Id_vehiculo = ?", (id_vehiculo,))

    return id_mant

def finalizar_mantenimiento_vehiculo(id_vehiculo: int) -> int:
    """Libera el vehículo de mantenimiento y lo deja Disponible."""
    return database.execute_dml("UPDATE VEHICULO SET estado = 'Disponible' WHERE Id_vehiculo = ?", (id_vehiculo,))

# =====================================================================
# GESTIÓN DE EMPLEADOS Y USUARIOS (RF15)
# =====================================================================

def get_empleados() -> List[Dict[str, Any]]:
    return database.execute_query("SELECT Id_empleado, nombres, apellidos, usuario, rol, activo FROM EMPLEADO ORDER BY Id_empleado")

def create_empleado(data: Dict[str, Any]) -> int:
    nombres = data.get("nombres", "").strip()
    apellidos = data.get("apellidos", "").strip()
    usuario = data.get("usuario", "").strip().lower()
    clave = data.get("clave", "").strip()
    rol = data.get("rol", "Empleado")

    if not nombres or not apellidos or not usuario or not clave:
        raise BusinessRuleError("Nombres, apellidos, usuario y contraseña son obligatorios.")

    existente = database.execute_single("SELECT Id_empleado FROM EMPLEADO WHERE usuario = ?", (usuario,))
    if existente:
        raise BusinessRuleError(f"El nombre de usuario '{usuario}' ya está en uso.")

    return database.execute_dml(
        "INSERT INTO EMPLEADO (nombres, apellidos, usuario, clave, rol) VALUES (?, ?, ?, ?, ?)",
        (nombres, apellidos, usuario, clave, rol)
    )

def authenticate_user(usuario: str, clave: str) -> Optional[Dict[str, Any]]:
    return database.execute_single(
        "SELECT Id_empleado, nombres, apellidos, usuario, rol FROM EMPLEADO WHERE usuario = ? AND clave = ? AND activo = 1",
        (usuario.strip().lower(), clave.strip())
    )

# =====================================================================
# REPORTES Y ESTADÍSTICAS (RF16)
# =====================================================================

def get_dashboard_metrics() -> Dict[str, Any]:
    total_vehiculos = database.execute_single("SELECT COUNT(*) as cnt FROM VEHICULO")["cnt"]
    disponibles = database.execute_single("SELECT COUNT(*) as cnt FROM VEHICULO WHERE estado = 'Disponible'")["cnt"]
    alquilados = database.execute_single("SELECT COUNT(*) as cnt FROM VEHICULO WHERE estado = 'Alquilado'")["cnt"]
    mantenimiento = database.execute_single("SELECT COUNT(*) as cnt FROM VEHICULO WHERE estado = 'En Mantenimiento'")["cnt"]

    total_clientes = database.execute_single("SELECT COUNT(*) as cnt FROM CLIENTE")["cnt"]
    total_alquileres = database.execute_single("SELECT COUNT(*) as cnt FROM ALQUILER")["cnt"]
    alquileres_activos = database.execute_single("SELECT COUNT(*) as cnt FROM ALQUILER WHERE estado = 'Activo'")["cnt"]

    total_ingresos = database.execute_single("SELECT COALESCE(SUM(monto), 0) as total FROM PAGO")["total"]
    total_costo_mant = database.execute_single("SELECT COALESCE(SUM(costo), 0) as total FROM MANTENIMIENTO")["total"]

    # Desglose de ingresos por método de pago
    ingresos_por_metodo = database.execute_query("""
        SELECT metodo_pago, SUM(monto) as total 
        FROM PAGO 
        GROUP BY metodo_pago
    """)

    # Desglose de vehículos por categoría
    vehiculos_por_categoria = database.execute_query("""
        SELECT c.nombre_categoria, COUNT(v.Id_vehiculo) as cantidad
        FROM CATEGORIA c
        LEFT JOIN VEHICULO v ON c.Id_categoria = v.id_categoria
        GROUP BY c.Id_categoria
    """)

    # Últimos 5 alquileres con estado actual del vehículo (coincidente con la gráfica circular)
    ultimos_alquileres = database.execute_query("""
        SELECT a.Id_alquiler, a.fecha_inicio, a.estado AS estado_alquiler,
               v.estado AS estado_vehiculo,
               c.Nombres || ' ' || c.Apellidos as cliente,
               v.matricula, ma.nombre_marca, m.nombre_modelo
        FROM ALQUILER a
        JOIN CLIENTE c ON a.Id_cliente = c.Id_cliente
        JOIN VEHICULO v ON a.Id_vehiculo = v.Id_vehiculo
        JOIN MODELO m ON v.id_modelo = m.Id_modelo
        JOIN MARCA ma ON m.id_marca = ma.Id_marca
        ORDER BY a.Id_alquiler DESC LIMIT 5
    """)

    return {
        "vehiculos": {
            "total": total_vehiculos,
            "disponibles": disponibles,
            "alquilados": alquilados,
            "en_mantenimiento": mantenimiento
        },
        "clientes": total_clientes,
        "alquileres": {
            "total": total_alquileres,
            "activos": alquileres_activos
        },
        "financiero": {
            "ingresos_totales": round(total_ingresos, 2),
            "costos_mantenimiento": round(total_costo_mant, 2),
            "balance_neto": round(total_ingresos - total_costo_mant, 2)
        },
        "ingresos_por_metodo": ingresos_por_metodo,
        "vehiculos_por_categoria": vehiculos_por_categoria,
        "ultimos_alquileres": ultimos_alquileres
    }

