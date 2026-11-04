-- =====================================================================
-- PROYECTO DE BASE DE DATOS - PARALELO 5 - ESPOL
-- PROYECTO: AutoRent - Sistema de Alquiler de Vehículos
-- INTEGRANTES:
--   - Leonardo Estrada
--   - María Suarez
--   - Luis Peñaherrera
--   - Samantha Vera
--   - Lady Zuñiga
-- SCRIPT: Creación de Esquema Relacional e Inserción de Datos Iniciales (PostgreSQL 14+)
-- =====================================================================

DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

-- 1. TABLA: MARCA
CREATE TABLE MARCA (
    Id_marca SERIAL PRIMARY KEY,
    nombre_marca VARCHAR(100) NOT NULL UNIQUE
);

-- 2. TABLA: MODELO
CREATE TABLE MODELO (
    Id_modelo SERIAL PRIMARY KEY,
    nombre_modelo VARCHAR(100) NOT NULL,
    id_marca INT NOT NULL REFERENCES MARCA(Id_marca) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. TABLA: CATEGORIA
CREATE TABLE CATEGORIA (
    Id_categoria SERIAL PRIMARY KEY,
    nombre_categoria VARCHAR(100) NOT NULL UNIQUE
);

-- 4. TABLA: EMPLEADO
CREATE TABLE EMPLEADO (
    Id_empleado SERIAL PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    clave VARCHAR(255) NOT NULL,
    rol VARCHAR(30) NOT NULL CHECK (rol IN ('Administrador', 'Gerente', 'Empleado')) DEFAULT 'Empleado',
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 5. TABLA: CLIENTE
CREATE TABLE CLIENTE (
    Id_cliente SERIAL PRIMARY KEY,
    Numero_Identificacion VARCHAR(20) NOT NULL UNIQUE,
    Nombres VARCHAR(100) NOT NULL,
    Apellidos VARCHAR(100) NOT NULL,
    Telefono VARCHAR(20) NOT NULL,
    Direccion VARCHAR(200) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. TABLA: VEHICULO
CREATE TABLE VEHICULO (
    Id_vehiculo SERIAL PRIMARY KEY,
    matricula VARCHAR(20) NOT NULL UNIQUE,
    año INT NOT NULL,
    color VARCHAR(50) NOT NULL,
    capacidad INT NOT NULL CHECK (capacidad > 0),
    tarifa NUMERIC(10, 2) NOT NULL CHECK (tarifa > 0),
    estado VARCHAR(30) NOT NULL CHECK (estado IN ('Disponible', 'Alquilado', 'En Mantenimiento')) DEFAULT 'Disponible',
    id_modelo INT NOT NULL REFERENCES MODELO(Id_modelo) ON DELETE RESTRICT ON UPDATE CASCADE,
    id_categoria INT NOT NULL REFERENCES CATEGORIA(Id_categoria) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 7. TABLA: RESERVA
CREATE TABLE RESERVA (
    Id_reserva SERIAL PRIMARY KEY,
    fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP NOT NULL,
    estado VARCHAR(30) NOT NULL CHECK (estado IN ('Pendiente', 'Confirmada', 'Cancelada', 'Completada')) DEFAULT 'Pendiente',
    Id_cliente INT NOT NULL REFERENCES CLIENTE(Id_cliente) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_vehiculo INT NOT NULL REFERENCES VEHICULO(Id_vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_empleado INT NOT NULL REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_reserva_fechas CHECK (fecha_fin > fecha_inicio)
);

-- 8. TABLA: ALQUILER
CREATE TABLE ALQUILER (
    Id_alquiler SERIAL PRIMARY KEY,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_dev_prevista TIMESTAMP NOT NULL,
    Id_reserva INT NULL UNIQUE REFERENCES RESERVA(Id_reserva) ON DELETE SET NULL ON UPDATE CASCADE,
    Id_cliente INT NOT NULL REFERENCES CLIENTE(Id_cliente) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_vehiculo INT NOT NULL REFERENCES VEHICULO(Id_vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_empleado INT NOT NULL REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    estado VARCHAR(30) NOT NULL CHECK (estado IN ('Activo', 'Finalizado')) DEFAULT 'Activo',
    CONSTRAINT chk_alquiler_fechas CHECK (fecha_dev_prevista > fecha_inicio)
);

-- 9. TABLA: PAGO
CREATE TABLE PAGO (
    Id_pago SERIAL PRIMARY KEY,
    fecha_pago TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    monto NUMERIC(10, 2) NOT NULL CHECK (monto > 0),
    metodo_pago VARCHAR(50) NOT NULL,
    Id_alquiler INT NOT NULL REFERENCES ALQUILER(Id_alquiler) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_empleado INT NOT NULL REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 10. TABLA: DEVOLUCION
CREATE TABLE DEVOLUCION (
    Id_devolucion SERIAL PRIMARY KEY,
    fecha_devolucion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_recepcion VARCHAR(100) NOT NULL,
    observaciones TEXT,
    Id_alquiler INT NOT NULL UNIQUE REFERENCES ALQUILER(Id_alquiler) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 11. TABLA: MANTENIMIENTO
CREATE TABLE MANTENIMIENTO (
    Id_mantenimiento SERIAL PRIMARY KEY,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_mantenimiento VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    costo NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (costo >= 0),
    Id_vehiculo INT NOT NULL REFERENCES VEHICULO(Id_vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
    Id_empleado INT NOT NULL REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- =====================================================================
-- FUNCIONES Y TRIGGERS (REGLAS DE NEGOCIO EN POSTGRESQL)
-- =====================================================================

-- RB04 & RB06
CREATE OR REPLACE FUNCTION fn_valida_reserva()
RETURNS TRIGGER AS $$
DECLARE
    v_estado_vehiculo VARCHAR(30);
    v_solapados INT;
BEGIN
    SELECT estado INTO v_estado_vehiculo FROM VEHICULO WHERE Id_vehiculo = NEW.Id_vehiculo;
    IF v_estado_vehiculo = 'En Mantenimiento' THEN
        RAISE EXCEPTION 'RB06: El vehículo se encuentra en mantenimiento y no puede ser reservado.';
    END IF;

    IF NEW.estado = 'Confirmada' THEN
        SELECT COUNT(*) INTO v_solapados
        FROM RESERVA
        WHERE Id_vehiculo = NEW.Id_vehiculo
          AND estado = 'Confirmada'
          AND (NEW.fecha_inicio < fecha_fin AND NEW.fecha_fin > fecha_inicio);

        IF v_solapados > 0 THEN
            RAISE EXCEPTION 'RB04: Conflicto de horarios. Ya existe una reserva confirmada para este vehículo en las fechas seleccionadas.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_valida_reserva
BEFORE INSERT OR UPDATE ON RESERVA
FOR EACH ROW EXECUTE FUNCTION fn_valida_reserva();

-- RB05
CREATE OR REPLACE FUNCTION fn_valida_alquiler()
RETURNS TRIGGER AS $$
DECLARE
    v_estado_vehiculo VARCHAR(30);
BEGIN
    SELECT estado INTO v_estado_vehiculo FROM VEHICULO WHERE Id_vehiculo = NEW.Id_vehiculo;
    IF v_estado_vehiculo <> 'Disponible' THEN
        RAISE EXCEPTION 'RB05: El vehículo debe encontrarse en estado Disponible para formalizar el contrato de alquiler.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_valida_alquiler
BEFORE INSERT ON ALQUILER
FOR EACH ROW EXECUTE FUNCTION fn_valida_alquiler();

-- Actualizar estado al formalizar alquiler
CREATE OR REPLACE FUNCTION fn_alquiler_post_insert()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE VEHICULO SET estado = 'Alquilado' WHERE Id_vehiculo = NEW.Id_vehiculo;
    IF NEW.Id_reserva IS NOT NULL THEN
        UPDATE RESERVA SET estado = 'Completada' WHERE Id_reserva = NEW.Id_reserva;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_alquiler_post_insert
AFTER INSERT ON ALQUILER
FOR EACH ROW EXECUTE FUNCTION fn_alquiler_post_insert();

-- Actualizar estado al devolver vehículo
CREATE OR REPLACE FUNCTION fn_devolucion_post_insert()
RETURNS TRIGGER AS $$
DECLARE
    v_vehiculo_id INT;
BEGIN
    SELECT Id_vehiculo INTO v_vehiculo_id FROM ALQUILER WHERE Id_alquiler = NEW.Id_alquiler;
    UPDATE ALQUILER SET estado = 'Finalizado' WHERE Id_alquiler = NEW.Id_alquiler;

    IF NEW.estado_recepcion IN ('Requiere Mantenimiento', 'Con Daños') THEN
        UPDATE VEHICULO SET estado = 'En Mantenimiento' WHERE Id_vehiculo = v_vehiculo_id;
    ELSE
        UPDATE VEHICULO SET estado = 'Disponible' WHERE Id_vehiculo = v_vehiculo_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_devolucion_post_insert
AFTER INSERT ON DEVOLUCION
FOR EACH ROW EXECUTE FUNCTION fn_devolucion_post_insert();

-- =====================================================================
-- DATOS INICIALES (SEED DATA)
-- =====================================================================

INSERT INTO MARCA (nombre_marca) VALUES 
('Toyota'), ('Chevrolet'), ('Hyundai'), ('Kia'), ('Nissan');

INSERT INTO MODELO (nombre_modelo, id_marca) VALUES 
('Corolla', 1), ('Yaris', 1), ('RAV4', 1),
('Aveo', 2), ('Tracker', 2), ('D-Max', 2),
('Tucson', 3), ('Accent', 3),
('Sportage', 4), ('Picanto', 4),
('Frontier', 5);

INSERT INTO CATEGORIA (nombre_categoria) VALUES 
('Económico'), ('Sedán Familiar'), ('SUV Compacta'), ('Camioneta 4x4'), ('Ejecutivo');

INSERT INTO EMPLEADO (nombres, apellidos, usuario, clave, rol) VALUES 
('Lady', 'Zuñiga', 'admin', 'admin123', 'Administrador'),
('Leonardo', 'Estrada', 'gerente', 'gerente123', 'Gerente'),
('María', 'Suarez', 'empleado1', 'emp123', 'Empleado'),
('Samantha', 'Vera', 'empleado2', 'emp123', 'Empleado'),
('Luis', 'Peñaherrera', 'empleado3', 'emp123', 'Empleado');

INSERT INTO CLIENTE (Numero_Identificacion, Nombres, Apellidos, Telefono, Direccion) VALUES 
('0923456781', 'Carlos', 'Mendoza', '0991234567', 'Av. 9 de Octubre 412, Guayaquil'),
('0918765432', 'Ana', 'García', '0987654321', 'Urdesa Central, Calle Ilanes, Guayaquil'),
('0934567890', 'Roberto', 'Morán', '0978901234', 'Ceibos, Manzana 14, Guayaquil'),
('0945678901', 'Diana', 'Paredes', '0965432109', 'Samborondón, km 2.5'),
('1712345678', 'Esteban', 'Vargas', '0954321987', 'La Floresta, Quito');

INSERT INTO VEHICULO (matricula, año, color, capacidad, tarifa, estado, id_modelo, id_categoria) VALUES 
('GBA-1001', 2023, 'Blanco', 5, 45.00, 'Disponible', 1, 2),
('GBA-1002', 2022, 'Gris Plata', 5, 35.00, 'Disponible', 2, 1),
('GBA-1003', 2024, 'Rojo', 5, 65.00, 'Disponible', 3, 3),
('GBA-1004', 2021, 'Azul', 5, 30.00, 'Disponible', 4, 1),
('GBA-1005', 2023, 'Negro', 5, 55.00, 'Disponible', 5, 3),
('GBA-1006', 2024, 'Blanco', 5, 75.00, 'Disponible', 6, 4),
('GBA-1007', 2023, 'Plateado', 5, 60.00, 'Disponible', 7, 3),
('GBA-1008', 2020, 'Gris', 5, 32.00, 'En Mantenimiento', 8, 1),
('GBA-1009', 2024, 'Blanco', 5, 58.00, 'Disponible', 9, 3),
('GBA-1010', 2022, 'Amarillo', 4, 28.00, 'Disponible', 10, 1);

INSERT INTO RESERVA (fecha_solicitud, fecha_inicio, fecha_fin, estado, Id_cliente, Id_vehiculo, Id_empleado) VALUES 
('2026-11-01 09:00:00', '2026-11-10 10:00:00', '2026-11-15 10:00:00', 'Confirmada', 1, 1, 3),
('2026-11-02 11:30:00', '2026-11-12 08:00:00', '2026-11-14 18:00:00', 'Pendiente', 2, 3, 4),
('2026-10-25 14:00:00', '2026-11-01 09:00:00', '2026-11-05 18:00:00', 'Completada', 3, 5, 3);

INSERT INTO ALQUILER (fecha_inicio, fecha_dev_prevista, Id_reserva, Id_cliente, Id_vehiculo, Id_empleado, estado) VALUES 
('2026-11-01 09:00:00', '2026-11-05 18:00:00', 3, 3, 5, 3, 'Activo');

INSERT INTO PAGO (fecha_pago, monto, metodo_pago, Id_alquiler, Id_empleado) VALUES 
('2026-11-01 09:15:00', 220.00, 'Tarjeta de Crédito', 1, 3);

INSERT INTO MANTENIMIENTO (fecha, tipo_mantenimiento, descripcion, costo, Id_vehiculo, Id_empleado) VALUES 
('2026-10-20 08:30:00', 'Preventivo', 'Cambio de aceite, filtro y revisión de frenos', 85.50, 1, 5),
('2026-11-02 10:00:00', 'Correctivo', 'Reparación de embrague y amortiguadores', 240.00, 8, 5);
