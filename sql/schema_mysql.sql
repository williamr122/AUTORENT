-- =====================================================================
-- PROYECTO DE BASE DE DATOS - PARALELO 5 - ESPOL
-- PROYECTO: AutoRent - Sistema de Alquiler de Vehículos
-- INTEGRANTES:
--   - Leonardo Estrada
--   - María Suarez
--   - Luis Peñaherrera
--   - Samantha Vera
--   - Lady Zuñiga
-- SCRIPT: Creación de Esquema Relacional e Inserción de Datos Iniciales (MySQL 8.0+)
-- =====================================================================

DROP DATABASE IF EXISTS autorent_db;
CREATE DATABASE autorent_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE autorent_db;

-- ---------------------------------------------------------------------
-- 1. TABLA: MARCA (RF09)
-- ---------------------------------------------------------------------
CREATE TABLE MARCA (
    Id_marca INT AUTO_INCREMENT PRIMARY KEY,
    nombre_marca VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. TABLA: MODELO (RF09, Relación Marca-Modelo 1:N)
-- ---------------------------------------------------------------------
CREATE TABLE MODELO (
    Id_modelo INT AUTO_INCREMENT PRIMARY KEY,
    nombre_modelo VARCHAR(100) NOT NULL,
    id_marca INT NOT NULL,
    CONSTRAINT fk_modelo_marca FOREIGN KEY (id_marca)
        REFERENCES MARCA(Id_marca) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. TABLA: CATEGORÍA (RF09, Relación Categoría-Vehículo 1:N)
-- ---------------------------------------------------------------------
CREATE TABLE CATEGORIA (
    Id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre_categoria VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. TABLA: EMPLEADO (RF15, Administración de Empleados y Usuarios)
-- ---------------------------------------------------------------------
CREATE TABLE EMPLEADO (
    Id_empleado INT AUTO_INCREMENT PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    clave VARCHAR(255) NOT NULL,
    rol ENUM('Administrador', 'Gerente', 'Empleado') NOT NULL DEFAULT 'Empleado',
    activo BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5. TABLA: CLIENTE (RF01-RF04, RB01: Unicidad de Identificación, RB15)
-- ---------------------------------------------------------------------
CREATE TABLE CLIENTE (
    Id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    Numero_Identificacion VARCHAR(20) NOT NULL UNIQUE, -- Cédula o Pasaporte
    Nombres VARCHAR(100) NOT NULL,
    Apellidos VARCHAR(100) NOT NULL,
    Telefono VARCHAR(20) NOT NULL,
    Direccion VARCHAR(200) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 6. TABLA: VEHÍCULO (RF05-RF08, RB02, RB05, RB06, RB17)
-- ---------------------------------------------------------------------
CREATE TABLE VEHICULO (
    Id_vehiculo INT AUTO_INCREMENT PRIMARY KEY,
    matricula VARCHAR(20) NOT NULL UNIQUE, -- Placa única
    año INT NOT NULL,
    color VARCHAR(50) NOT NULL,
    capacidad INT NOT NULL,
    tarifa DECIMAL(10, 2) NOT NULL,
    estado ENUM('Disponible', 'Alquilado', 'En Mantenimiento') NOT NULL DEFAULT 'Disponible',
    id_modelo INT NOT NULL,
    id_categoria INT NOT NULL,
    CONSTRAINT fk_vehiculo_modelo FOREIGN KEY (id_modelo)
        REFERENCES MODELO(Id_modelo) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_vehiculo_categoria FOREIGN KEY (id_categoria)
        REFERENCES CATEGORIA(Id_categoria) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_vehiculo_tarifa CHECK (tarifa > 0),
    CONSTRAINT chk_vehiculo_capacidad CHECK (capacidad > 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 7. TABLA: RESERVA (RF10, RB03, RB04, RB06)
-- ---------------------------------------------------------------------
CREATE TABLE RESERVA (
    Id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    fecha_solicitud DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio DATETIME NOT NULL,
    fecha_fin DATETIME NOT NULL,
    estado ENUM('Pendiente', 'Confirmada', 'Cancelada', 'Completada') NOT NULL DEFAULT 'Pendiente',
    Id_cliente INT NOT NULL,
    Id_vehiculo INT NOT NULL,
    Id_empleado INT NOT NULL,
    CONSTRAINT fk_reserva_cliente FOREIGN KEY (Id_cliente)
        REFERENCES CLIENTE(Id_cliente) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_reserva_vehiculo FOREIGN KEY (Id_vehiculo)
        REFERENCES VEHICULO(Id_vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_reserva_empleado FOREIGN KEY (Id_empleado)
        REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_reserva_fechas CHECK (fecha_fin > fecha_inicio)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 8. TABLA: ALQUILER (RF11, RB05, RB06, RB07, RB08, RB09, RB16)
-- ---------------------------------------------------------------------
CREATE TABLE ALQUILER (
    Id_alquiler INT AUTO_INCREMENT PRIMARY KEY,
    fecha_inicio DATETIME NOT NULL,
    fecha_dev_prevista DATETIME NOT NULL,
    Id_reserva INT NULL UNIQUE, -- 1:0..1 con reserva
    Id_cliente INT NOT NULL,
    Id_vehiculo INT NOT NULL,
    Id_empleado INT NOT NULL,
    estado ENUM('Activo', 'Finalizado') NOT NULL DEFAULT 'Activo',
    CONSTRAINT fk_alquiler_reserva FOREIGN KEY (Id_reserva)
        REFERENCES RESERVA(Id_reserva) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_alquiler_cliente FOREIGN KEY (Id_cliente)
        REFERENCES CLIENTE(Id_cliente) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_alquiler_vehiculo FOREIGN KEY (Id_vehiculo)
        REFERENCES VEHICULO(Id_vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_alquiler_empleado FOREIGN KEY (Id_empleado)
        REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_alquiler_fechas CHECK (fecha_dev_prevista > fecha_inicio)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 9. TABLA: PAGO (RF12, RB10, RB11)
-- ---------------------------------------------------------------------
CREATE TABLE PAGO (
    Id_pago INT AUTO_INCREMENT PRIMARY KEY,
    fecha_pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    monto DECIMAL(10, 2) NOT NULL,
    metodo_pago VARCHAR(50) NOT NULL, -- Efectivo, Tarjeta de Crédito, Transferencia
    Id_alquiler INT NOT NULL,
    Id_empleado INT NOT NULL,
    CONSTRAINT fk_pago_alquiler FOREIGN KEY (Id_alquiler)
        REFERENCES ALQUILER(Id_alquiler) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_pago_empleado FOREIGN KEY (Id_empleado)
        REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_pago_monto CHECK (monto > 0) -- RB11
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 10. TABLA: DEVOLUCIÓN (RF13, RB12: Unicidad 1:0..1, RB13)
-- ---------------------------------------------------------------------
CREATE TABLE DEVOLUCION (
    Id_devolucion INT AUTO_INCREMENT PRIMARY KEY,
    fecha_devolucion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_recepcion VARCHAR(100) NOT NULL, -- 'Excelente', 'Bueno', 'Con Daños'
    observaciones TEXT,
    Id_alquiler INT NOT NULL UNIQUE, -- RB12: Una sola devolución por contrato
    CONSTRAINT fk_devolucion_alquiler FOREIGN KEY (Id_alquiler)
        REFERENCES ALQUILER(Id_alquiler) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 11. TABLA: MANTENIMIENTO (RF14, RB06, RB14)
-- ---------------------------------------------------------------------
CREATE TABLE MANTENIMIENTO (
    Id_mantenimiento INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_mantenimiento VARCHAR(50) NOT NULL, -- 'Preventivo', 'Correctivo'
    descripcion TEXT NOT NULL,
    costo DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    Id_vehiculo INT NOT NULL,
    Id_empleado INT NOT NULL,
    CONSTRAINT fk_mantenimiento_vehiculo FOREIGN KEY (Id_vehiculo)
        REFERENCES VEHICULO(Id_vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_mantenimiento_empleado FOREIGN KEY (Id_empleado)
        REFERENCES EMPLEADO(Id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_mantenimiento_costo CHECK (costo >= 0)
) ENGINE=InnoDB;

-- =====================================================================
-- TRIGGERS PARA CONTROL DE REGLAS DE NEGOCIO
-- =====================================================================

DELIMITER $$

-- Trigger RB04 y RB06 en RESERVA:
-- Validar que el auto no esté en mantenimiento y que no haya reservas solapadas confirmadas
CREATE TRIGGER trg_reserva_valida BEFORE INSERT ON RESERVA
FOR EACH ROW
BEGIN
    DECLARE v_estado_vehiculo VARCHAR(30);
    DECLARE v_solapados INT;

    SELECT estado INTO v_estado_vehiculo FROM VEHICULO WHERE Id_vehiculo = NEW.Id_vehiculo;
    IF v_estado_vehiculo = 'En Mantenimiento' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'RB06: El vehículo se encuentra en mantenimiento y no puede ser reservado.';
    END IF;

    IF NEW.estado = 'Confirmada' THEN
        SELECT COUNT(*) INTO v_solapados
        FROM RESERVA
        WHERE Id_vehiculo = NEW.Id_vehiculo
          AND estado = 'Confirmada'
          AND (NEW.fecha_inicio < fecha_fin AND NEW.fecha_fin > fecha_inicio);

        IF v_solapados > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'RB04: Conflicto de horarios. Ya existe una reserva confirmada para este vehículo en las fechas seleccionadas.';
        END IF;
    END IF;
END$$

-- Trigger RB05 y RB06 en ALQUILER:
-- Solo formalizar alquiler si el vehículo está 'Disponible'
CREATE TRIGGER trg_alquiler_valida BEFORE INSERT ON ALQUILER
FOR EACH ROW
BEGIN
    DECLARE v_estado_vehiculo VARCHAR(30);

    SELECT estado INTO v_estado_vehiculo FROM VEHICULO WHERE Id_vehiculo = NEW.Id_vehiculo;
    IF v_estado_vehiculo <> 'Disponible' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'RB05: El vehículo debe encontrarse en estado Disponible para formalizar el contrato de alquiler.';
    END IF;
END$$

-- Trigger para actualizar estado del vehículo a 'Alquilado' al insertar alquiler
CREATE TRIGGER trg_alquiler_despues_insert AFTER INSERT ON ALQUILER
FOR EACH ROW
BEGIN
    UPDATE VEHICULO SET estado = 'Alquilado' WHERE Id_vehiculo = NEW.Id_vehiculo;
    IF NEW.Id_reserva IS NOT NULL THEN
        UPDATE RESERVA SET estado = 'Completada' WHERE Id_reserva = NEW.Id_reserva;
    END IF;
END$$

-- Trigger al registrar DEVOLUCION:
-- Marca el contrato de alquiler como 'Finalizado' y el vehículo como 'Disponible' (o 'En Mantenimiento' si aplica)
CREATE TRIGGER trg_devolucion_despues_insert AFTER INSERT ON DEVOLUCION
FOR EACH ROW
BEGIN
    DECLARE v_vehiculo_id INT;

    SELECT Id_vehiculo INTO v_vehiculo_id FROM ALQUILER WHERE Id_alquiler = NEW.Id_alquiler;

    UPDATE ALQUILER SET estado = 'Finalizado' WHERE Id_alquiler = NEW.Id_alquiler;

    IF NEW.estado_recepcion = 'Requiere Mantenimiento' OR NEW.estado_recepcion = 'Con Daños' THEN
        UPDATE VEHICULO SET estado = 'En Mantenimiento' WHERE Id_vehiculo = v_vehiculo_id;
    ELSE
        UPDATE VEHICULO SET estado = 'Disponible' WHERE Id_vehiculo = v_vehiculo_id;
    END IF;
END$$

DELIMITER ;

-- =====================================================================
-- DATOS INICIALES DE PRUEBA (SEED DATA)
-- =====================================================================

-- 1. Marcas
INSERT INTO MARCA (nombre_marca) VALUES 
('Toyota'), 
('Chevrolet'), 
('Hyundai'), 
('Kia'), 
('Nissan');

-- 2. Modelos
INSERT INTO MODELO (nombre_modelo, id_marca) VALUES 
('Corolla', 1),
('Yaris', 1),
('RAV4', 1),
('Aveo', 2),
('Tracker', 2),
('D-Max', 2),
('Tucson', 3),
('Accent', 3),
('Sportage', 4),
('Picanto', 4),
('Frontier', 5);

-- 3. Categorías
INSERT INTO CATEGORIA (nombre_categoria) VALUES 
('Económico'), 
('Sedán Familiar'), 
('SUV Compacta'), 
('Camioneta 4x4'), 
('Ejecutivo');

-- 4. Empleados (Integrantes del equipo ESPOL)
INSERT INTO EMPLEADO (nombres, apellidos, usuario, clave, rol) VALUES 
('Lady', 'Zuñiga', 'admin', 'admin123', 'Administrador'),
('Leonardo', 'Estrada', 'gerente', 'gerente123', 'Gerente'),
('María', 'Suarez', 'empleado1', 'emp123', 'Empleado'),
('Samantha', 'Vera', 'empleado2', 'emp123', 'Empleado'),
('Luis', 'Peñaherrera', 'empleado3', 'emp123', 'Empleado');

-- 5. Clientes
INSERT INTO CLIENTE (Numero_Identificacion, Nombres, Apellidos, Telefono, Direccion) VALUES 
('0923456781', 'Carlos', 'Mendoza', '0991234567', 'Av. 9 de Octubre 412, Guayaquil'),
('0918765432', 'Ana', 'García', '0987654321', 'Urdesa Central, Calle Ilanes, Guayaquil'),
('0934567890', 'Roberto', 'Morán', '0978901234', 'Ceibos, Manzana 14, Guayaquil'),
('0945678901', 'Diana', 'Paredes', '0965432109', 'Samborondón, km 2.5'),
('1712345678', 'Esteban', 'Vargas', '0954321987', 'La Floresta, Quito');

-- 6. Vehículos
INSERT INTO VEHICULO (matricula, año, color, capacidad, tarifa, estado, id_modelo, id_categoria) VALUES 
('GBA-1001', 2023, 'Blanco', 5, 45.00, 'Disponible', 1, 2),   -- Toyota Corolla
('GBA-1002', 2022, 'Gris Plata', 5, 35.00, 'Disponible', 2, 1), -- Toyota Yaris
('GBA-1003', 2024, 'Rojo', 5, 65.00, 'Disponible', 3, 3),        -- Toyota RAV4
('GBA-1004', 2021, 'Azul', 5, 30.00, 'Disponible', 4, 1),       -- Chevrolet Aveo
('GBA-1005', 2023, 'Negro', 5, 55.00, 'Disponible', 5, 3),        -- Chevrolet Tracker
('GBA-1006', 2024, 'Blanco', 5, 75.00, 'Disponible', 6, 4),      -- Chevrolet D-Max
('GBA-1007', 2023, 'Plateado', 5, 60.00, 'Disponible', 7, 3),    -- Hyundai Tucson
('GBA-1008', 2020, 'Gris', 5, 32.00, 'En Mantenimiento', 8, 1), -- Hyundai Accent
('GBA-1009', 2024, 'Blanco', 5, 58.00, 'Disponible', 9, 3),      -- Kia Sportage
('GBA-1010', 2022, 'Amarillo', 4, 28.00, 'Disponible', 10, 1);   -- Kia Picanto

-- 7. Reservas
INSERT INTO RESERVA (fecha_solicitud, fecha_inicio, fecha_fin, estado, Id_cliente, Id_vehiculo, Id_empleado) VALUES 
('2026-11-01 09:00:00', '2026-11-10 10:00:00', '2026-11-15 10:00:00', 'Confirmada', 1, 1, 3),
('2026-11-02 11:30:00', '2026-11-12 08:00:00', '2026-11-14 18:00:00', 'Pendiente', 2, 3, 4),
('2026-10-25 14:00:00', '2026-11-01 09:00:00', '2026-11-05 18:00:00', 'Completada', 3, 5, 3);

-- 8. Alquileres
INSERT INTO ALQUILER (fecha_inicio, fecha_dev_prevista, Id_reserva, Id_cliente, Id_vehiculo, Id_empleado, estado) VALUES 
('2026-11-01 09:00:00', '2026-11-05 18:00:00', 3, 3, 5, 3, 'Activo');

-- 9. Pagos
INSERT INTO PAGO (fecha_pago, monto, metodo_pago, Id_alquiler, Id_empleado) VALUES 
('2026-11-01 09:15:00', 220.00, 'Tarjeta de Crédito', 1, 3);

-- 10. Mantenimientos
INSERT INTO MANTENIMIENTO (fecha, tipo_mantenimiento, descripcion, costo, Id_vehiculo, Id_empleado) VALUES 
('2026-10-20 08:30:00', 'Preventivo', 'Cambio de aceite, filtro y revisión de frenos', 85.50, 1, 5),
('2026-11-02 10:00:00', 'Correctivo', 'Reparación de sistema de embrague y amortiguadores', 240.00, 8, 5);
