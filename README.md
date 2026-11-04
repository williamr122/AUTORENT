# AutoRent - Sistema de Alquiler de Vehículos

**Institución:** Escuela Superior Politécnica del Litoral (ESPOL)  
**Materia:** Base de Datos - Paralelo 5  
**Fase:** Fase 1 - Diseño e Implementación de Base de Datos Relacional y Sistema Funcional  

### Integrantes del Equipo
- Leonardo Estrada
- María Suarez
- Luis Peñaherrera
- Samantha Vera
- Lady Zuñiga

---

## 1. Descripción del Proyecto

**AutoRent** es una solución integral para la administración y control operativo de una empresa de alquiler de vehículos. El sistema gestiona de manera estructurada y segura la información de clientes, flota de vehículos, marcas, modelos, categorías, reservas temporales, contratos de alquiler, registros de cobros/pagos, devoluciones con inspección física, mantenimiento preventivo/correctivo de taller, y asignación de usuarios con roles diferenciados (**Administrador**, **Gerente**, **Empleado**).

---

## 2. Requerimientos Funcionales Implementados (RF01 - RF16)

| Código | Nombre | Descripción |
| :--- | :--- | :--- |
| **RF01** | Registro de clientes | Captura de identificación, nombres, apellidos, teléfono y dirección. |
| **RF02** | Consulta de clientes | Búsqueda dinámica por número de identificación (cédula/pasaporte) o nombre. |
| **RF03** | Actualización de clientes | Modificación controlada de información de contacto. |
| **RF04** | Eliminación de clientes | Eliminación segura respetando integridad referencial histórica. |
| **RF05** | Registro de vehículos | Alta de vehículos con matrícula/placa única, año, color, capacidad, tarifa diaria y estado. |
| **RF06** | Consulta de vehículos | Catálogo de vehículos con filtros por disponibilidad, estado y categoría. |
| **RF07** | Actualización de vehículos | Modificación de características, tarifas y estados. |
| **RF08** | Eliminación de vehículos | Eliminación protegida contra registros asociados. |
| **RF09** | Marcas, modelos y categorías | Administración CRUD de catálogos relacionales de clasificación. |
| **RF10** | Gestión de reservas | Registro y confirmación con validación temporal de no-solapamiento. |
| **RF11** | Registro de alquileres | Formalización de contratos directos o derivados de una reserva confirmada. |
| **RF12** | Registro de pagos | Cobro y emisión de recibos vinculados al contrato con monto > 0. |
| **RF13** | Registro de devoluciones | Recepción técnica única por contrato activo y actualización de estado vehicular. |
| **RF14** | Gestión de mantenimientos | Historial preventivo y correctivo, costos y técnico responsable. |
| **RF15** | Usuarios y roles | Control de acceso basado en roles: Administrador, Gerente y Empleado. |
| **RF16** | Reportes e informes | Dashboard con KPIs, gráficos de ingresos, distribución de flota y tablas. |

---

## 3. Matriz de Reglas de Negocio (RB01 - RB17)

| Regla | Nombre | Implementación en BD y Código |
| :--- | :--- | :--- |
| **RB01** | Unicidad de cliente | Restricción `UNIQUE` en `Numero_Identificacion` de la tabla `CLIENTE`. |
| **RB02** | Unicidad vehicular | Restricción `UNIQUE` en `matricula` de la tabla `VEHICULO`. |
| **RB03** | Titularidad de reserva | Relación 1:N entre `CLIENTE` y `RESERVA` con FK obligatoria. |
| **RB04** | Exclusividad temporal de reserva | Trigger en BD y validación de rangos que impide reservas solapadas confirmadas para el mismo vehículo. |
| **RB05** | Disponibilidad para alquiler | Trigger que valida que el vehículo esté estrictamente en estado `'Disponible'`. |
| **RB06** | Restricción por mantenimiento | Impide asignar a reservas o alquileres vehículos con estado `'En Mantenimiento'`. |
| **RB07** | Trazabilidad del contrato | Claves foráneas obligatorias (`NOT NULL`) a Cliente, Vehículo y Empleado. |
| **RB08** | Registro temporal de alquiler | Campos `fecha_inicio` y `fecha_dev_prevista` obligatorios. |
| **RB09** | Coherencia temporal | Restricción `CHECK (fecha_dev_prevista > fecha_inicio)`. |
| **RB10** | Asociación de pagos | Relación 1:N entre `ALQUILER` y `PAGO`. |
| **RB11** | Validación de importes | Restricción `CHECK (monto > 0)` en tabla `PAGO`. |
| **RB12** | Unicidad de devolución | Restricción `UNIQUE` en `Id_alquiler` dentro de `DEVOLUCION` (1:0..1). |
| **RB13** | Vinculación de devolución | Verificación en backend que el contrato se encuentre `'Activo'`. |
| **RB14** | Historial mecánico | Relación 1:N entre `VEHICULO` y `MANTENIMIENTO`. |
| **RB15** | Integridad histórica de cliente | Restricción `ON DELETE RESTRICT` y validación en `delete_cliente`. |
| **RB16** | Origen del alquiler | Soporte de alquiler directo o originado de reserva con pase a `'Completada'`. |
| **RB17** | Integridad histórica de vehículo | Restricción `ON DELETE RESTRICT` contra alquileres o mantenimientos. |

---

## 4. Scripts SQL Generados

En la carpeta `/sql/` se incluyen los scripts completos para los diferentes motores de base de datos:

1. `sql/schema_mysql.sql`: Script DDL, Triggers en sintaxis MySQL 8.0+ y datos de prueba.
2. `sql/schema_postgres.sql`: Script DDL, funciones en PL/pgSQL, triggers y datos de prueba para PostgreSQL 14+.
3. `sql/schema_sqlite.sql`: Script DDL y triggers para SQLite 3 (utilizado por defecto para ejecución inmediata local sin dependencias de servicios externos).

---

## 5. Instrucciones para Ejecución Local

### Paso 1: Ejecución directa con Python
Abre una terminal o símbolo del sistema en este directorio y ejecuta:

```bash
python app.py
```

O simplemente haz doble clic en el archivo `run.bat`.

### Paso 2: Acceso en el navegador
Abre tu navegador web e ingresa a:
👉 **http://127.0.0.1:5000**

### Paso 3: Selector de Rol para Evaluadores
En la esquina superior derecha del encabezado encontrarás un menú desplegable para alternar al instante entre los roles:
- **👑 Administrador:** Acceso completo a creación, modificación, eliminación y gestión de usuarios.
- **👔 Gerente:** Modo de supervisión y consulta de reportes, clientes, vehículos y alquileres.
- **💼 Empleado:** Operaciones del día a día (registro de clientes, contratos de alquiler, cobro de pagos y recepción de devoluciones).

