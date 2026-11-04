"""
database.py - Módulo de Gestión de Base de Datos para AutoRent (ESPOL)
Implementa la conexión, creación de esquema y seed data inicial.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autorent.db")
SQL_SCHEMA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql", "schema_sqlite.sql")

def get_db_connection() -> sqlite3.Connection:
    """Retorna una conexión a SQLite con foreign_keys habilitadas y formato diccionario."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SELECT y retorna una lista de diccionarios."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def execute_single(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """Ejecuta una consulta SELECT y retorna un solo registro o None."""
    rows = execute_query(query, params)
    return rows[0] if rows else None

def execute_dml(query: str, params: tuple = ()) -> int:
    """Ejecuta INSERT, UPDATE o DELETE y retorna el lastrowid o cursor.rowcount."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

def init_db(force: bool = False):
    """Inicializa la base de datos ejecutando el esquema DDL y cargando datos de prueba si no existen."""
    if force and os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except Exception:
            pass

    conn = get_db_connection()
    with open(SQL_SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()

    # Verificar si ya existen empleados (seed data)
    cursor.execute("SELECT COUNT(*) as cnt FROM EMPLEADO")
    row = cursor.fetchone()
    if row and row["cnt"] == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn: sqlite3.Connection):
    """Inserta datos de prueba basados en el contexto de ESPOL y Ecuador."""
    cursor = conn.cursor()

    # 1. Marcas
    marcas = [('Toyota',), ('Chevrolet',), ('Hyundai',), ('Kia',), ('Nissan',)]
    cursor.executemany("INSERT OR IGNORE INTO MARCA (nombre_marca) VALUES (?)", marcas)

    # 2. Modelos
    modelos = [
        ('Corolla', 1), ('Yaris', 1), ('RAV4', 1),
        ('Aveo', 2), ('Tracker', 2), ('D-Max', 2),
        ('Tucson', 3), ('Accent', 3),
        ('Sportage', 4), ('Picanto', 4),
        ('Frontier', 5)
    ]
    cursor.executemany("INSERT INTO MODELO (nombre_modelo, id_marca) VALUES (?, ?)", modelos)

    # 3. Categorías
    categorias = [
        ('Económico',), ('Sedán Familiar',), ('SUV Compacta',), ('Camioneta 4x4',), ('Ejecutivo',)
    ]
    cursor.executemany("INSERT OR IGNORE INTO CATEGORIA (nombre_categoria) VALUES (?)", categorias)

    # 4. Empleados (Integrantes del equipo de ESPOL)
    empleados = [
        ('Lady', 'Zuñiga', 'admin', 'admin123', 'Administrador'),
        ('Leonardo', 'Estrada', 'gerente', 'gerente123', 'Gerente'),
        ('María', 'Suarez', 'empleado1', 'emp123', 'Empleado'),
        ('Samantha', 'Vera', 'empleado2', 'emp123', 'Empleado'),
        ('Luis', 'Peñaherrera', 'empleado3', 'emp123', 'Empleado')
    ]
    cursor.executemany("INSERT OR IGNORE INTO EMPLEADO (nombres, apellidos, usuario, clave, rol) VALUES (?, ?, ?, ?, ?)", empleados)

    # 5. Clientes
    clientes = [
        ('0923456781', 'Carlos', 'Mendoza', '0991234567', 'Av. 9 de Octubre 412, Guayaquil'),
        ('0918765432', 'Ana', 'García', '0987654321', 'Urdesa Central, Calle Ilanes, Guayaquil'),
        ('0934567890', 'Roberto', 'Morán', '0978901234', 'Ceibos, Mz 14, Guayaquil'),
        ('0945678901', 'Diana', 'Paredes', '0965432109', 'Samborondón, km 2.5'),
        ('1712345678', 'Esteban', 'Vargas', '0954321987', 'La Floresta, Quito')
    ]
    cursor.executemany("INSERT OR IGNORE INTO CLIENTE (Numero_Identificacion, Nombres, Apellidos, Telefono, Direccion) VALUES (?, ?, ?, ?, ?)", clientes)

    # 6. Vehículos
    vehiculos = [
        ('GBA-1001', 2023, 'Blanco', 5, 45.00, 'Disponible', 1, 2),
        ('GBA-1002', 2022, 'Gris Plata', 5, 35.00, 'Disponible', 2, 1),
        ('GBA-1003', 2024, 'Rojo', 5, 65.00, 'Disponible', 3, 3),
        ('GBA-1004', 2021, 'Azul', 5, 30.00, 'Disponible', 4, 1),
        ('GBA-1005', 2023, 'Negro', 5, 55.00, 'Disponible', 5, 3),
        ('GBA-1006', 2024, 'Blanco', 5, 75.00, 'Disponible', 6, 4),
        ('GBA-1007', 2023, 'Plateado', 5, 60.00, 'Disponible', 7, 3),
        ('GBA-1008', 2020, 'Gris', 5, 32.00, 'En Mantenimiento', 8, 1),
        ('GBA-1009', 2024, 'Blanco', 5, 58.00, 'Disponible', 9, 3),
        ('GBA-1010', 2022, 'Amarillo', 4, 28.00, 'Disponible', 10, 1)
    ]
    cursor.executemany("INSERT OR IGNORE INTO VEHICULO (matricula, año, color, capacidad, tarifa, estado, id_modelo, id_categoria) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", vehiculos)

    # 7. Reservas
    reservas = [
        ('2026-11-01 09:00:00', '2026-11-10 10:00:00', '2026-11-15 10:00:00', 'Confirmada', 1, 1, 3),
        ('2026-11-02 11:30:00', '2026-11-12 08:00:00', '2026-11-14 18:00:00', 'Pendiente', 2, 3, 4),
        ('2026-10-25 14:00:00', '2026-11-01 09:00:00', '2026-11-05 18:00:00', 'Completada', 3, 5, 3)
    ]
    cursor.executemany("INSERT INTO RESERVA (fecha_solicitud, fecha_inicio, fecha_fin, estado, Id_cliente, Id_vehiculo, Id_empleado) VALUES (?, ?, ?, ?, ?, ?, ?)", reservas)

    # 8. Alquileres
    alquileres = [
        ('2026-11-01 09:00:00', '2026-11-05 18:00:00', 3, 3, 5, 3, 'Activo')
    ]
    cursor.executemany("INSERT INTO ALQUILER (fecha_inicio, fecha_dev_prevista, Id_reserva, Id_cliente, Id_vehiculo, Id_empleado, estado) VALUES (?, ?, ?, ?, ?, ?, ?)", alquileres)

    # 9. Pagos
    pagos = [
        ('2026-11-01 09:15:00', 220.00, 'Tarjeta de Crédito', 1, 3)
    ]
    cursor.executemany("INSERT INTO PAGO (fecha_pago, monto, metodo_pago, Id_alquiler, Id_empleado) VALUES (?, ?, ?, ?, ?)", pagos)

    # 10. Mantenimientos
    mantenimientos = [
        ('2026-10-20 08:30:00', 'Preventivo', 'Cambio de aceite, filtros y revisión de frenos', 85.50, 1, 5),
        ('2026-11-02 10:00:00', 'Correctivo', 'Reparación de embrague y amortiguadores delanteros', 240.00, 8, 5)
    ]
    cursor.executemany("INSERT INTO MANTENIMIENTO (fecha, tipo_mantenimiento, descripcion, costo, Id_vehiculo, Id_empleado) VALUES (?, ?, ?, ?, ?, ?)", mantenimientos)

    conn.commit()

if __name__ == "__main__":
    init_db(force=True)
    print("Base de datos SQLite creada y poblada exitosamente.")
