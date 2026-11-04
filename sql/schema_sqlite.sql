-- =====================================================================
-- PROYECTO DE BASE DE DATOS - PARALELO 5 - ESPOL
-- PROYECTO: AutoRent - Sistema de Alquiler de Vehículos
-- INTEGRANTES:
--   - Leonardo Estrada
--   - María Suarez
--   - Luis Peñaherrera
--   - Samantha Vera
--   - Lady Zuñiga
-- SCRIPT: Creación de Esquema Relacional e Inserción de Datos Iniciales (SQLite 3)
-- =====================================================================

PRAGMA foreign_keys = ON;

-- 1. MARCA
CREATE TABLE IF NOT EXISTS MARCA (
    Id_marca INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_marca TEXT NOT NULL UNIQUE
);

-- 2. MODELO
CREATE TABLE IF NOT EXISTS MODELO (
    Id_modelo INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_modelo TEXT NOT NULL,
    id_marca INTEGER NOT NULL REFERENCES MARCA(Id_marca) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. CATEGORIA
CREATE TABLE IF NOT EXISTS CATEGORIA (
    Id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_categoria TEXT NOT NULL UNIQUE
);

-- 4. EMPLEADO
CREATE TABLE IF NOT EXISTS EMPLEADO (
    Id_empleado INTEGER PRIMARY KEY AUTOINCREMENT,
    nombres TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    usuario TEXT NOT NULL UNIQUE,
    clave TEXT NOT NULL,
    rol TEXT NOT NULL CHECK(rol IN ('Administrador', 'Gerente', 'Empleado')) DEFAULT 'Empleado',
    activo INTEGER NOT NULL DEFAULT 1
);

-- 5. CLIENTE
CREATE TABLE IF NOT EXISTS CLIENTE (
    Id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    Numero_Identificacion TEXT NOT NULL UNIQUE, -- RB01
    Nombres TEXT NOT NULL,
    Apellidos TEXT NOT NULL,
    Telefono TEXT NOT NULL,
    Direccion TEXT NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. VEHICULO
CREATE TABLE IF NOT EXISTS VEHICULO (
    Id_vehiculo INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT NOT NULL UNIQUE, -- RB02
    año INTEGER NOT NULL,
    color TEXT NOT NULL,
    capacidad INTEGER NOT NULL CHECK(capacidad > 0),
    tarifa REAL NOT NULL CHECK(tarifa > 0),
    estado TEXT NOT NULL CHECK(estado IN ('Disponible', 'Alquilado', 'En Mantenimiento')) DEFAULT 'Disponible',
    id_modelo INTEGER NOT NULL REFERENCES MODELO(Id_modelo) ON DELETE RESTRICT ON UPDATE CASCADE,
    id_categoria INTEGER NOT NULL REFERENCES CATEGORIA(Id_categoria) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 7. RESERVA
CREATE TABLE IF NOT EXISTS RESERVA (
    Id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_solicitud DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio DATETIME NOT NULL,
    fecha_fin DATETIME NOT NULL,
    estado TEXT NOT NULL CHECK(estado IN ('Pendiente', 'Confirmada', 'Cancelada', 'Completada')) DEFAULT 'Pendiente',
    Id_cliente INTEGER NOT NULL REFERENCES CLIENTE(Id_cliente) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_vehiculo INTEGER NOT NULL REFERENCES VEHICULO(Id_vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_empleado INTEGER NOT NULL REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CHECK (fecha_fin > fecha_inicio)
);

-- 8. ALQUILER
CREATE TABLE IF NOT EXISTS ALQUILER (
    Id_alquiler INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_inicio DATETIME NOT NULL,
    fecha_dev_prevista DATETIME NOT NULL,
    Id_reserva INTEGER NULL UNIQUE REFERENCES RESERVA(Id_reserva) ON DELETE SET NULL ON UPDATE CASCADE,
    Id_cliente INTEGER NOT NULL REFERENCES CLIENTE(Id_cliente) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_vehiculo INTEGER NOT NULL REFERENCES VEHICULO(Id_vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_empleado INTEGER NOT NULL REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    estado TEXT NOT NULL CHECK(estado IN ('Activo', 'Finalizado')) DEFAULT 'Activo',
    CHECK (fecha_dev_prevista > fecha_inicio) -- RB09
);

-- 9. PAGO
CREATE TABLE IF NOT EXISTS PAGO (
    Id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    monto REAL NOT NULL CHECK(monto > 0), -- RB11
    metodo_pago TEXT NOT NULL,
    Id_alquiler INTEGER NOT NULL REFERENCES ALQUILER(Id_alquiler) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_empleado INTEGER NOT NULL REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 10. DEVOLUCION
CREATE TABLE IF NOT EXISTS DEVOLUCION (
    Id_devolucion INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_devolucion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_recepcion TEXT NOT NULL,
    observaciones TEXT,
    Id_alquiler INTEGER NOT NULL UNIQUE REFERENCES ALQUILER(Id_alquiler) ON DELETE RESTRICT ON UPDATE CASCADE -- RB12
);

-- 11. MANTENIMIENTO
CREATE TABLE IF NOT EXISTS MANTENIMIENTO (
    Id_mantenimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_mantenimiento TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    costo REAL NOT NULL DEFAULT 0.0 CHECK(costo >= 0),
    Id_vehiculo INTEGER NOT NULL REFERENCES VEHICULO(Id_vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_empleado INTEGER NOT NULL REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- =====================================================================
-- TRIGGERS DE CONTROL EN SQLITE
-- =====================================================================

-- RB06: No permitir reserva si vehículo está En Mantenimiento
CREATE TRIGGER IF NOT EXISTS trg_reserva_no_mantenimiento
BEFORE INSERT ON RESERVA
WHEN (SELECT estado FROM VEHICULO WHERE Id_vehiculo = NEW.Id_vehiculo) = 'En Mantenimiento'
BEGIN
    SELECT RAISE(ABORT, 'RB06: El vehículo se encuentra en mantenimiento y no puede ser reservado.');
END;

-- RB04: No permitir superposición de reservas confirmadas para el mismo vehículo
CREATE TRIGGER IF NOT EXISTS trg_reserva_solapamiento
BEFORE INSERT ON RESERVA
WHEN NEW.estado = 'Confirmada' AND EXISTS (
    SELECT 1 FROM RESERVA
    WHERE Id_vehiculo = NEW.Id_vehiculo
      AND estado = 'Confirmada'
      AND (NEW.fecha_inicio < fecha_fin AND NEW.fecha_fin > fecha_inicio)
)
BEGIN
    SELECT RAISE(ABORT, 'RB04: Conflicto de horarios. Ya existe una reserva confirmada para este vehículo en las fechas seleccionadas.');
END;

-- RB05: Solo alquilar sobre vehículos estrictamente Disponibles
CREATE TRIGGER IF NOT EXISTS trg_alquiler_solo_disponible
BEFORE INSERT ON ALQUILER
WHEN (SELECT estado FROM VEHICULO WHERE Id_vehiculo = NEW.Id_vehiculo) <> 'Disponible'
BEGIN
    SELECT RAISE(ABORT, 'RB05: El vehículo debe encontrarse en estado Disponible para formalizar el contrato de alquiler.');
END;

-- Actualizar vehículo a 'Alquilado' al crear contrato
CREATE TRIGGER IF NOT EXISTS trg_alquiler_marca_vehiculo
AFTER INSERT ON ALQUILER
BEGIN
    UPDATE VEHICULO SET estado = 'Alquilado' WHERE Id_vehiculo = NEW.Id_vehiculo;
    UPDATE RESERVA SET estado = 'Completada' WHERE Id_reserva = NEW.Id_reserva;
END;

-- Al devolver vehículo: finalizar alquiler y cambiar estado del vehículo
CREATE TRIGGER IF NOT EXISTS trg_devolucion_marca_estado
AFTER INSERT ON DEVOLUCION
BEGIN
    UPDATE ALQUILER SET estado = 'Finalizado' WHERE Id_alquiler = NEW.Id_alquiler;
    UPDATE VEHICULO 
    SET estado = CASE 
        WHEN NEW.estado_recepcion IN ('Requiere Mantenimiento', 'Con Daños') THEN 'En Mantenimiento' 
        ELSE 'Disponible' 
    END
    WHERE Id_vehiculo = (SELECT Id_vehiculo FROM ALQUILER WHERE Id_alquiler = NEW.Id_alquiler);
END;

