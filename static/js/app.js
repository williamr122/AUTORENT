/**
 * app.js - Lógica Frontend para AutoRent (ESPOL)
 * Manejo interactivo de todos los módulos y reglas de negocio.
 */

let currentUser = { rol: "Administrador", nombres: "Lady", apellidos: "Zuñiga" };
let chartFlotaInstance = null;
let chartCategoriasInstance = null;

// Caché de listas para selects en modales
let cacheClientes = [];
let cacheVehiculos = [];
let cacheAlquileres = [];

// =====================================================================
// INICIALIZACIÓN
// =====================================================================
document.addEventListener("DOMContentLoaded", () => {
    checkCurrentUser();
    navigateTab("dashboard");
    initReglasMatriz();
});

function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    
    let bg = "bg-emerald-600";
    let icon = "fa-check-circle";
    if (type === "error") {
        bg = "bg-rose-600";
        icon = "fa-triangle-exclamation";
    } else if (type === "info") {
        bg = "bg-indigo-600";
        icon = "fa-circle-info";
    }

    toast.className = `${bg} text-white px-4 py-3 rounded-xl shadow-lg flex items-center space-x-3 text-sm pointer-events-auto transition-all transform duration-300`;
    toast.innerHTML = `
        <i class="fa-solid ${icon} text-lg"></i>
        <span class="flex-grow font-medium">${message}</span>
        <button onclick="this.parentElement.remove()" class="text-white/80 hover:text-white"><i class="fa-solid fa-xmark"></i></button>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// =====================================================================
// AUTENTICACIÓN Y ROLES (RF15)
// =====================================================================
async function checkCurrentUser() {
    try {
        const res = await fetch("/api/auth/current");
        const data = await res.json();
        if (data.success && data.user) {
            currentUser = data.user;
            document.getElementById("current-user-name").innerText = `${currentUser.nombres} ${currentUser.apellidos}`;
            document.getElementById("role-switcher").value = currentUser.rol;
            applyRolePermissions();
        }
    } catch (e) {
        console.error("Error verificando usuario:", e);
    }
}

async function switchRole(newRole) {
    try {
        const res = await fetch("/api/auth/switch-role", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rol: newRole })
        });
        const data = await res.json();
        if (data.success) {
            currentUser = data.user;
            document.getElementById("current-user-name").innerText = `${currentUser.nombres} ${currentUser.apellidos}`;
            showToast(data.message, "info");
            applyRolePermissions();
            // Refrescar vista actual
            const activeTab = document.querySelector(".nav-tab.active-tab").id.replace("tab-btn-", "");
            navigateTab(activeTab);
        } else {
            showToast(data.error, "error");
        }
    } catch (e) {
        showToast("Error de conexión al cambiar rol", "error");
    }
}

function applyRolePermissions() {
    const isGerente = currentUser.rol === "Gerente";
    const isEmpleado = currentUser.rol === "Empleado";
    const isAdmin = currentUser.rol === "Administrador";

    // Botones protegidos
    document.querySelectorAll(".admin-only").forEach(el => {
        el.style.display = isAdmin ? "" : "none";
    });
}

// =====================================================================
// NAVEGACIÓN ENTRE TABS
// =====================================================================
function navigateTab(tabName) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".nav-tab").forEach(el => el.classList.remove("active-tab"));

    const tabElement = document.getElementById(`tab-${tabName}`);
    const btnElement = document.getElementById(`tab-btn-${tabName}`);

    if (tabElement) tabElement.classList.remove("hidden");
    if (btnElement) btnElement.classList.add("active-tab");

    // Cargar datos según tab
    switch (tabName) {
        case "dashboard": loadDashboard(); break;
        case "clientes": loadClientes(); break;
        case "vehiculos": loadVehiculos(); break;
        case "catalogos": loadCatalogos(); break;
        case "reservas": loadReservas(); break;
        case "alquileres": loadAlquileres(); break;
        case "pagos": loadPagos(); break;
        case "devoluciones": loadDevoluciones(); break;
        case "mantenimientos": loadMantenimientos(); break;
        case "empleados": loadEmpleados(); break;
        case "reglas": break;
    }
}

// =====================================================================
// 1. DASHBOARD Y REPORTES (RF16)
// =====================================================================
async function loadDashboard() {
    try {
        const res = await fetch("/api/reportes/dashboard");
        const json = await res.json();
        if (!json.success) return;
        const d = json.data;

        document.getElementById("kpi-total-vehiculos").innerText = d.vehiculos.total;
        document.getElementById("kpi-disponibles-txt").innerText = `${d.vehiculos.disponibles} Disponibles`;
        document.getElementById("kpi-alquileres-activos").innerText = d.alquileres.activos;
        document.getElementById("kpi-alquileres-total-txt").innerText = `${d.alquileres.total} Totales`;
        document.getElementById("kpi-ingresos-totales").innerText = `$${d.financiero.ingresos_totales.toFixed(2)}`;
        document.getElementById("kpi-costos-mantenimiento").innerText = `$${d.financiero.costos_mantenimiento.toFixed(2)}`;
        document.getElementById("kpi-en-mantenimiento-txt").innerText = `${d.vehiculos.en_mantenimiento} En taller hoy`;

        // Render gráfico de estado de flota
        const ctxFlota = document.getElementById("chart-flota").getContext("2d");
        if (chartFlotaInstance) chartFlotaInstance.destroy();
        chartFlotaInstance = new Chart(ctxFlota, {
            type: "doughnut",
            data: {
                labels: ["Disponibles", "Alquilados", "En Mantenimiento"],
                datasets: [{
                    data: [d.vehiculos.disponibles, d.vehiculos.alquilados, d.vehiculos.en_mantenimiento],
                    backgroundColor: ["#10b981", "#3b82f6", "#f59e0b"]
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });

        // Render gráfico por categoría
        const ctxCat = document.getElementById("chart-categorias").getContext("2d");
        if (chartCategoriasInstance) chartCategoriasInstance.destroy();
        chartCategoriasInstance = new Chart(ctxCat, {
            type: "bar",
            data: {
                labels: d.vehiculos_por_categoria.map(c => c.nombre_categoria),
                datasets: [{
                    label: "Vehículos",
                    data: d.vehiculos_por_categoria.map(c => c.cantidad),
                    backgroundColor: "#6366f1"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });

        // Tabla recientes
        const tbody = document.getElementById("dashboard-recent-rentals");
        if (!d.ultimos_alquileres || d.ultimos_alquileres.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-slate-400">Sin alquileres registrados aún.</td></tr>`;
        } else {
            tbody.innerHTML = d.ultimos_alquileres.map(a => `
                <tr class="hover:bg-slate-50 transition">
                    <td class="px-4 py-3 font-semibold text-indigo-700">#${a.Id_alquiler}</td>
                    <td class="px-4 py-3 font-medium text-slate-900">${a.cliente}</td>
                    <td class="px-4 py-3">${a.nombre_marca} ${a.nombre_modelo} <span class="text-xs text-slate-400">(${a.matricula})</span></td>
                    <td class="px-4 py-3 text-slate-600 text-xs">${a.fecha_inicio}</td>
                    <td class="px-4 py-3">
                        <span class="text-xs px-2.5 py-1 rounded-full font-semibold ${a.estado === 'Activo' ? 'badge-alquilado' : 'badge-completada'}">${a.estado}</span>
                    </td>
                </tr>
            `).join("");
        }

    } catch (e) {
        console.error("Error al cargar dashboard:", e);
    }
}

// =====================================================================
// 2. CLIENTES (RF01 - RF04, RB01, RB15)
// =====================================================================
async function loadClientes() {
    try {
        const q = document.getElementById("filtro-cliente").value;
        const res = await fetch(`/api/clientes?q=${encodeURIComponent(q)}`);
        const json = await res.json();
        if (!json.success) return;
        cacheClientes = json.data;

        const tbody = document.getElementById("table-clientes-body");
        if (cacheClientes.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-slate-400">No se encontraron clientes.</td></tr>`;
            return;
        }

        tbody.innerHTML = cacheClientes.map(c => `
            <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                <td class="px-5 py-3.5 text-xs text-slate-400 font-mono">#${c.Id_cliente}</td>
                <td class="px-5 py-3.5 font-bold text-slate-900 font-mono flex items-center gap-1.5">
                    <i class="fa-solid fa-id-card text-indigo-500"></i> ${c.Numero_Identificacion}
                </td>
                <td class="px-5 py-3.5 font-semibold text-slate-800">${c.Nombres} ${c.Apellidos}</td>
                <td class="px-5 py-3.5 text-slate-600"><i class="fa-solid fa-phone text-xs text-slate-400 mr-1"></i>${c.Telefono}</td>
                <td class="px-5 py-3.5 text-slate-600 text-xs max-w-xs truncate">${c.Direccion}</td>
                <td class="px-5 py-3.5 text-right space-x-1 whitespace-nowrap">
                    <button onclick='editarCliente(${JSON.stringify(c)})' title="Modificar datos (RF03)" class="text-slate-600 hover:text-indigo-600 p-1.5 rounded-lg hover:bg-slate-100">
                        <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                    ${currentUser.rol !== 'Gerente' ? `
                    <button onclick="eliminarCliente(${c.Id_cliente})" title="Eliminar cliente (RF04 / RB15)" class="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-rose-50">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>` : ''}
                </td>
            </tr>
        `).join("");
    } catch (e) {
        showToast("Error al cargar clientes", "error");
    }
}

let timeoutBusqueda = null;
function buscarClientes(val) {
    clearTimeout(timeoutBusqueda);
    timeoutBusqueda = setTimeout(loadClientes, 250);
}

function openModalCliente() {
    document.getElementById("modal-cliente-title").innerText = "Registrar Cliente (RF01)";
    document.getElementById("cliente-id").value = "";
    document.getElementById("cliente-cedula").value = "";
    document.getElementById("cliente-nombres").value = "";
    document.getElementById("cliente-apellidos").value = "";
    document.getElementById("cliente-telefono").value = "";
    document.getElementById("cliente-direccion").value = "";
    openModal("modal-cliente");
}

function editarCliente(c) {
    document.getElementById("modal-cliente-title").innerText = "Modificar Datos de Cliente (RF03)";
    document.getElementById("cliente-id").value = c.Id_cliente;
    document.getElementById("cliente-cedula").value = c.Numero_Identificacion;
    document.getElementById("cliente-nombres").value = c.Nombres;
    document.getElementById("cliente-apellidos").value = c.Apellidos;
    document.getElementById("cliente-telefono").value = c.Telefono;
    document.getElementById("cliente-direccion").value = c.Direccion;
    openModal("modal-cliente");
}

async function guardarCliente(e) {
    e.preventDefault();
    const id = document.getElementById("cliente-id").value;
    const payload = {
        Numero_Identificacion: document.getElementById("cliente-cedula").value,
        Nombres: document.getElementById("cliente-nombres").value,
        Apellidos: document.getElementById("cliente-apellidos").value,
        Telefono: document.getElementById("cliente-telefono").value,
        Direccion: document.getElementById("cliente-direccion").value
    };

    try {
        const url = id ? `/api/clientes/${id}` : "/api/clientes";
        const method = id ? "PUT" : "POST";
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            closeModal("modal-cliente");
            loadClientes();
        } else {
            showToast(json.error, "error");
        }
    } catch (err) {
        showToast("Error al procesar cliente", "error");
    }
}

async function eliminarCliente(id) {
    if (!confirm("¿Está seguro de eliminar este cliente? Se verificará la regla RB15 (no poseer reservas ni alquileres asociados).")) return;
    try {
        const res = await fetch(`/api/clientes/${id}`, { method: "DELETE" });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            loadClientes();
        } else {
            showToast(json.error, "error");
        }
    } catch (e) {
        showToast("Error al eliminar cliente", "error");
    }
}

// =====================================================================
// 3. VEHÍCULOS (RF05 - RF08, RB02, RB05, RB06, RB17)
// =====================================================================
async function loadVehiculos() {
    try {
        const q = document.getElementById("filtro-vehiculo-q").value;
        const estado = document.getElementById("filtro-vehiculo-estado").value;
        const idCat = document.getElementById("filtro-vehiculo-categoria").value;

        const res = await fetch(`/api/vehiculos?q=${encodeURIComponent(q)}&estado=${encodeURIComponent(estado)}&id_categoria=${idCat}`);
        const json = await res.json();
        if (!json.success) return;
        cacheVehiculos = json.data;

        // Cargar categorías en el select si está vacío
        const catSelect = document.getElementById("filtro-vehiculo-categoria");
        if (catSelect.children.length <= 1) {
            const catRes = await fetch("/api/categorias");
            const catJson = await catRes.json();
            if (catJson.success) {
                catJson.data.forEach(c => {
                    catSelect.innerHTML += `<option value="${c.Id_categoria}">${c.nombre_categoria}</option>`;
                });
            }
        }

        const tbody = document.getElementById("table-vehiculos-body");
        if (cacheVehiculos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-400">No se encontraron vehículos con los filtros especificados.</td></tr>`;
            return;
        }

        tbody.innerHTML = cacheVehiculos.map(v => {
            let badgeClass = "badge-disponible";
            if (v.estado === "Alquilado") badgeClass = "badge-alquilado";
            else if (v.estado === "En Mantenimiento") badgeClass = "badge-mantenimiento";

            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="px-5 py-3.5 font-black text-slate-800 font-mono tracking-wider">
                        <span class="bg-slate-200 px-2 py-1 rounded border border-slate-300 text-xs">${v.matricula}</span>
                    </td>
                    <td class="px-5 py-3.5 font-bold text-slate-900">${v.nombre_marca} ${v.nombre_modelo}</td>
                    <td class="px-5 py-3.5 text-xs text-slate-600">${v.año} • ${v.color} • ${v.capacidad} pasajeros</td>
                    <td class="px-5 py-3.5 text-xs"><span class="bg-indigo-50 text-indigo-700 font-semibold px-2.5 py-1 rounded-full">${v.nombre_categoria}</span></td>
                    <td class="px-5 py-3.5 font-bold text-emerald-600">$${parseFloat(v.tarifa).toFixed(2)}/día</td>
                    <td class="px-5 py-3.5">
                        <span class="text-xs px-2.5 py-1 rounded-full font-bold ${badgeClass}">
                            ${v.estado}
                        </span>
                    </td>
                    <td class="px-5 py-3.5 text-right space-x-1 whitespace-nowrap">
                        ${v.estado === 'En Mantenimiento' ? `
                            <button onclick="liberarVehiculoTaller(${v.Id_vehiculo})" title="Liberar de taller y pasar a Disponible" class="text-amber-700 hover:text-emerald-700 p-1.5 rounded-lg hover:bg-amber-100 text-xs font-bold">
                                <i class="fa-solid fa-circle-check"></i> Liberar
                            </button>
                        ` : ''}
                        <button onclick='editarVehiculo(${JSON.stringify(v)})' title="Editar información (RF07)" class="text-slate-600 hover:text-indigo-600 p-1.5 rounded-lg hover:bg-slate-100">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        ${currentUser.rol !== 'Gerente' ? `
                        <button onclick="eliminarVehiculo(${v.Id_vehiculo})" title="Eliminar vehículo (RF08 / RB17)" class="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-rose-50">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>` : ''}
                    </td>
                </tr>
            `;
        }).join("");

    } catch (e) {
        showToast("Error al cargar vehículos", "error");
    }
}

async function openModalVehiculo() {
    document.getElementById("modal-vehiculo-title").innerText = "Registrar Vehículo (RF05)";
    document.getElementById("vehiculo-id").value = "";
    document.getElementById("vehiculo-matricula").value = "";
    document.getElementById("vehiculo-año").value = 2024;
    document.getElementById("vehiculo-color").value = "Blanco";
    document.getElementById("vehiculo-capacidad").value = 5;
    document.getElementById("vehiculo-tarifa").value = "45.00";
    document.getElementById("vehiculo-estado").value = "Disponible";

    // Cargar selects
    await poblarSelectModelos("vehiculo-modelo");
    await poblarSelectCategorias("vehiculo-categoria");

    openModal("modal-vehiculo");
}

async function editarVehiculo(v) {
    document.getElementById("modal-vehiculo-title").innerText = "Actualizar Vehículo (RF07)";
    document.getElementById("vehiculo-id").value = v.Id_vehiculo;
    document.getElementById("vehiculo-matricula").value = v.matricula;
    document.getElementById("vehiculo-año").value = v.año;
    document.getElementById("vehiculo-color").value = v.color;
    document.getElementById("vehiculo-capacidad").value = v.capacidad;
    document.getElementById("vehiculo-tarifa").value = v.tarifa;
    document.getElementById("vehiculo-estado").value = v.estado;

    await poblarSelectModelos("vehiculo-modelo", v.id_modelo);
    await poblarSelectCategorias("vehiculo-categoria", v.id_categoria);

    openModal("modal-vehiculo");
}

async function guardarVehiculo(e) {
    e.preventDefault();
    const id = document.getElementById("vehiculo-id").value;
    const payload = {
        matricula: document.getElementById("vehiculo-matricula").value,
        año: parseInt(document.getElementById("vehiculo-año").value),
        color: document.getElementById("vehiculo-color").value,
        capacidad: parseInt(document.getElementById("vehiculo-capacidad").value),
        tarifa: parseFloat(document.getElementById("vehiculo-tarifa").value),
        estado: document.getElementById("vehiculo-estado").value,
        id_modelo: parseInt(document.getElementById("vehiculo-modelo").value),
        id_categoria: parseInt(document.getElementById("vehiculo-categoria").value)
    };

    try {
        const url = id ? `/api/vehiculos/${id}` : "/api/vehiculos";
        const method = id ? "PUT" : "POST";
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            closeModal("modal-vehiculo");
            loadVehiculos();
        } else {
            showToast(json.error, "error");
        }
    } catch (err) {
        showToast("Error al procesar vehículo", "error");
    }
}

async function eliminarVehiculo(id) {
    if (!confirm("¿Está seguro de eliminar este vehículo? Se verificará la regla RB17 (sin alquileres, reservas ni mantenimientos).")) return;
    try {
        const res = await fetch(`/api/vehiculos/${id}`, { method: "DELETE" });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            loadVehiculos();
        } else {
            showToast(json.error, "error");
        }
    } catch (e) {
        showToast("Error al eliminar vehículo", "error");
    }
}

async function liberarVehiculoTaller(id) {
    try {
        const res = await fetch(`/api/vehiculos/${id}/liberar`, { method: "POST" });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            loadVehiculos();
        } else {
            showToast(json.error, "error");
        }
    } catch (e) {
        showToast("Error al liberar vehículo", "error");
    }
}

// =====================================================================
// 4. CATÁLOGOS (RF09: MARCAS, MODELOS, CATEGORÍAS)
// =====================================================================
async function loadCatalogos() {
    try {
        // Marcas
        const rM = await fetch("/api/marcas");
        const jM = await rM.json();
        const listaMarcas = document.getElementById("lista-marcas");
        const selectMarcaParaMod = document.getElementById("select-marca-para-modelo");
        selectMarcaParaMod.innerHTML = `<option value="">Seleccione Marca...</option>`;

        if (jM.success) {
            listaMarcas.innerHTML = jM.data.map(m => `
                <li class="py-2.5 flex justify-between items-center text-slate-700">
                    <span class="font-medium"><i class="fa-solid fa-car text-indigo-400 mr-2"></i>${m.nombre_marca}</span>
                    <button onclick="eliminarMarca(${m.Id_marca})" class="text-slate-400 hover:text-rose-600"><i class="fa-solid fa-trash-can"></i></button>
                </li>
            `).join("");

            jM.data.forEach(m => {
                selectMarcaParaMod.innerHTML += `<option value="${m.Id_marca}">${m.nombre_marca}</option>`;
            });
        }

        // Modelos
        const rMod = await fetch("/api/modelos");
        const jMod = await rMod.json();
        const listaModelos = document.getElementById("lista-modelos");
        if (jMod.success) {
            listaModelos.innerHTML = jMod.data.map(m => `
                <li class="py-2.5 flex justify-between items-center text-slate-700">
                    <div>
                        <span class="font-semibold text-slate-900">${m.nombre_modelo}</span>
                        <span class="text-xs text-slate-400 block">${m.nombre_marca}</span>
                    </div>
                    <button onclick="eliminarModelo(${m.Id_modelo})" class="text-slate-400 hover:text-rose-600"><i class="fa-solid fa-trash-can"></i></button>
                </li>
            `).join("");
        }

        // Categorías
        const rCat = await fetch("/api/categorias");
        const jCat = await rCat.json();
        const listaCat = document.getElementById("lista-categorias");
        if (jCat.success) {
            listaCat.innerHTML = jCat.data.map(c => `
                <li class="py-2.5 flex justify-between items-center text-slate-700">
                    <span class="font-medium"><i class="fa-solid fa-folder text-indigo-400 mr-2"></i>${c.nombre_categoria}</span>
                    <button onclick="eliminarCategoria(${c.Id_categoria})" class="text-slate-400 hover:text-rose-600"><i class="fa-solid fa-trash-can"></i></button>
                </li>
            `).join("");
        }
    } catch (e) {
        showToast("Error al cargar catálogos", "error");
    }
}

async function crearMarca(e) {
    e.preventDefault();
    const nombre = document.getElementById("input-nueva-marca").value;
    const res = await fetch("/api/marcas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre_marca: nombre })
    });
    const j = await res.json();
    if (j.success) {
        document.getElementById("input-nueva-marca").value = "";
        showToast(j.message);
        loadCatalogos();
    } else showToast(j.error, "error");
}

async function eliminarMarca(id) {
    if (!confirm("¿Eliminar marca?")) return;
    const res = await fetch(`/api/marcas/${id}`, { method: "DELETE" });
    const j = await res.json();
    if (j.success) { showToast(j.message); loadCatalogos(); }
    else showToast(j.error, "error");
}

async function crearModelo(e) {
    e.preventDefault();
    const idMarca = document.getElementById("select-marca-para-modelo").value;
    const nombre = document.getElementById("input-nuevo-modelo").value;
    const res = await fetch("/api/modelos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre_modelo: nombre, id_marca: idMarca })
    });
    const j = await res.json();
    if (j.success) {
        document.getElementById("input-nuevo-modelo").value = "";
        showToast(j.message);
        loadCatalogos();
    } else showToast(j.error, "error");
}

async function eliminarModelo(id) {
    if (!confirm("¿Eliminar modelo?")) return;
    const res = await fetch(`/api/modelos/${id}`, { method: "DELETE" });
    const j = await res.json();
    if (j.success) { showToast(j.message); loadCatalogos(); }
    else showToast(j.error, "error");
}

async function crearCategoria(e) {
    e.preventDefault();
    const nombre = document.getElementById("input-nueva-cat").value;
    const res = await fetch("/api/categorias", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre_categoria: nombre })
    });
    const j = await res.json();
    if (j.success) {
        document.getElementById("input-nueva-cat").value = "";
        showToast(j.message);
        loadCatalogos();
    } else showToast(j.error, "error");
}

async function eliminarCategoria(id) {
    if (!confirm("¿Eliminar categoría?")) return;
    const res = await fetch(`/api/categorias/${id}`, { method: "DELETE" });
    const j = await res.json();
    if (j.success) { showToast(j.message); loadCatalogos(); }
    else showToast(j.error, "error");
}

// =====================================================================
// 5. RESERVAS (RF10, RB03, RB04, RB06)
// =====================================================================
async function loadReservas() {
    try {
        const res = await fetch("/api/reservas");
        const json = await res.json();
        if (!json.success) return;

        const tbody = document.getElementById("table-reservas-body");
        if (json.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-400">No hay reservas registradas.</td></tr>`;
            return;
        }

        tbody.innerHTML = json.data.map(r => {
            let badgeClass = "badge-pendiente";
            if (r.estado === "Confirmada") badgeClass = "badge-confirmada";
            else if (r.estado === "Completada") badgeClass = "badge-completada";
            else if (r.estado === "Cancelada") badgeClass = "badge-cancelada";

            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="px-5 py-3.5 font-bold text-slate-900">#${r.Id_reserva}</td>
                    <td class="px-5 py-3.5">
                        <div class="font-semibold text-slate-800">${r.cliente_nombre}</div>
                        <div class="text-xs text-slate-400 font-mono">${r.Numero_Identificacion}</div>
                    </td>
                    <td class="px-5 py-3.5">
                        <div class="font-bold text-slate-900">${r.nombre_marca} ${r.nombre_modelo}</div>
                        <div class="text-xs text-slate-500 font-mono">${r.matricula}</div>
                    </td>
                    <td class="px-5 py-3.5 text-xs">
                        <div class="text-emerald-700 font-medium"><i class="fa-regular fa-calendar-check mr-1"></i>${r.fecha_inicio}</div>
                        <div class="text-slate-500"><i class="fa-regular fa-calendar-xmark mr-1"></i>${r.fecha_fin}</div>
                    </td>
                    <td class="px-5 py-3.5 text-xs text-slate-600">${r.empleado_nombre}</td>
                    <td class="px-5 py-3.5">
                        <span class="text-xs px-2.5 py-1 rounded-full font-bold ${badgeClass}">
                            ${r.estado}
                        </span>
                    </td>
                    <td class="px-5 py-3.5 text-right space-x-1 whitespace-nowrap">
                        ${r.estado === 'Confirmada' ? `
                            <button onclick='convertirReservaEnAlquiler(${JSON.stringify(r)})' title="Convertir a contrato de alquiler (RB16)" class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs px-3 py-1.5 rounded-lg font-semibold shadow-sm">
                                <i class="fa-solid fa-key mr-1"></i> Alquilar
                            </button>
                        ` : ''}
                        ${r.estado === 'Pendiente' ? `
                            <button onclick="cambiarEstadoReserva(${r.Id_reserva}, 'Confirmada')" title="Confirmar (valida RB04)" class="text-emerald-600 hover:text-emerald-800 p-1.5 rounded-lg hover:bg-emerald-50">
                                <i class="fa-solid fa-check"></i>
                            </button>
                            <button onclick="cambiarEstadoReserva(${r.Id_reserva}, 'Cancelada')" title="Cancelar reserva" class="text-rose-500 hover:text-rose-700 p-1.5 rounded-lg hover:bg-rose-50">
                                <i class="fa-solid fa-xmark"></i>
                            </button>
                        ` : ''}
                    </td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        showToast("Error al cargar reservas", "error");
    }
}

async function openModalReserva() {
    await poblarSelectClientes("reserva-cliente");
    await poblarSelectVehiculos("reserva-vehiculo", true); // solo vehículos no en mantenimiento

    // Default dates: mañana y +3 días
    const hoy = new Date();
    const manana = new Date(hoy.setDate(hoy.getDate() + 1)).toISOString().slice(0, 16);
    const fin = new Date(hoy.setDate(hoy.getDate() + 3)).toISOString().slice(0, 16);
    document.getElementById("reserva-inicio").value = manana;
    document.getElementById("reserva-fin").value = fin;

    openModal("modal-reserva");
}

async function guardarReserva(e) {
    e.preventDefault();
    const payload = {
        Id_cliente: parseInt(document.getElementById("reserva-cliente").value),
        Id_vehiculo: parseInt(document.getElementById("reserva-vehiculo").value),
        fecha_inicio: document.getElementById("reserva-inicio").value.replace("T", " ") + ":00",
        fecha_fin: document.getElementById("reserva-fin").value.replace("T", " ") + ":00",
        estado: document.getElementById("reserva-estado").value
    };

    try {
        const res = await fetch("/api/reservas", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            closeModal("modal-reserva");
            loadReservas();
        } else {
            showToast(json.error, "error");
        }
    } catch (err) {
        showToast("Error al procesar reserva", "error");
    }
}

async function cambiarEstadoReserva(id, estado) {
    try {
        const res = await fetch(`/api/reservas/${id}/status`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ estado })
        });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            loadReservas();
        } else {
            showToast(json.error, "error");
        }
    } catch (e) {
        showToast("Error al actualizar reserva", "error");
    }
}

function convertirReservaEnAlquiler(r) {
    openModalAlquilerDesdeReserva(r);
}

// =====================================================================
// 6. ALQUILERES (RF11, RB05, RB06, RB07, RB08, RB09, RB16)
// =====================================================================
async function loadAlquileres() {
    try {
        const res = await fetch("/api/alquileres");
        const json = await res.json();
        if (!json.success) return;
        cacheAlquileres = json.data;

        const tbody = document.getElementById("table-alquileres-body");
        if (cacheAlquileres.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-slate-400">No hay contratos de alquiler registrados.</td></tr>`;
            return;
        }

        tbody.innerHTML = cacheAlquileres.map(a => {
            const isActivo = a.estado === "Activo";
            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="px-5 py-3.5 font-bold text-indigo-700">
                        #${a.Id_alquiler}
                        ${a.Id_reserva ? `<span class="block text-[10px] text-amber-600 font-normal">Reserva #${a.Id_reserva}</span>` : ''}
                    </td>
                    <td class="px-5 py-3.5">
                        <div class="font-semibold text-slate-800">${a.cliente_nombre}</div>
                        <div class="text-xs text-slate-400 font-mono">${a.Numero_Identificacion}</div>
                    </td>
                    <td class="px-5 py-3.5">
                        <div class="font-bold text-slate-900">${a.nombre_marca} ${a.nombre_modelo}</div>
                        <div class="text-xs text-slate-500 font-mono">${a.matricula}</div>
                    </td>
                    <td class="px-5 py-3.5 text-xs text-slate-700">${a.fecha_inicio}</td>
                    <td class="px-5 py-3.5 text-xs text-slate-700">${a.fecha_dev_prevista}</td>
                    <td class="px-5 py-3.5 text-xs">
                        <div class="font-bold text-emerald-600">$${parseFloat(a.total_pagado).toFixed(2)} pagado</div>
                        <div class="text-slate-400">Tarifa: $${parseFloat(a.tarifa).toFixed(2)}/d</div>
                    </td>
                    <td class="px-5 py-3.5">
                        <span class="text-xs px-2.5 py-1 rounded-full font-bold ${isActivo ? 'badge-alquilado' : 'badge-completada'}">
                            ${a.estado}
                        </span>
                    </td>
                    <td class="px-5 py-3.5 text-right space-x-1 whitespace-nowrap">
                        ${isActivo ? `
                            <button onclick="registrarPagoParaAlquiler(${a.Id_alquiler})" title="Registrar Pago (RF12)" class="bg-emerald-50 text-emerald-700 hover:bg-emerald-100 px-2.5 py-1.5 rounded-lg text-xs font-semibold border border-emerald-200">
                                <i class="fa-solid fa-hand-holding-dollar"></i> Cobrar
                            </button>
                            <button onclick="registrarDevolucionParaAlquiler(${a.Id_alquiler})" title="Registrar Devolución (RF13)" class="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 px-2.5 py-1.5 rounded-lg text-xs font-semibold border border-indigo-200">
                                <i class="fa-solid fa-rotate-left"></i> Devolver
                            </button>
                        ` : `
                            <span class="text-xs text-slate-400"><i class="fa-solid fa-check-double text-emerald-500"></i> Finalizado</span>
                        `}
                    </td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        showToast("Error al cargar alquileres", "error");
    }
}

async function openModalAlquilerDirecto() {
    document.getElementById("modal-alquiler-title").innerText = "Formalizar Contrato Directo (Sin Reserva Previa - RB16)";
    document.getElementById("alquiler-id-reserva").value = "";
    document.getElementById("alquiler-reserva-info").classList.add("hidden");

    await poblarSelectClientes("alquiler-cliente");
    await poblarSelectVehiculosDisponibles("alquiler-vehiculo");

    const ahora = new Date();
    const manana = new Date();
    manana.setDate(manana.getDate() + 3);

    document.getElementById("alquiler-inicio").value = ahora.toISOString().slice(0, 16);
    document.getElementById("alquiler-fin").value = manana.toISOString().slice(0, 16);

    openModal("modal-alquiler");
}

async function openModalAlquilerDesdeReserva(r) {
    document.getElementById("modal-alquiler-title").innerText = `Formalizar Alquiler desde Reserva #${r.Id_reserva}`;
    document.getElementById("alquiler-id-reserva").value = r.Id_reserva;
    document.getElementById("txt-id-reserva-origen").innerText = r.Id_reserva;
    document.getElementById("alquiler-reserva-info").classList.remove("hidden");

    await poblarSelectClientes("alquiler-cliente", r.Id_cliente);
    await poblarSelectVehiculos("alquiler-vehiculo", false, r.Id_vehiculo);

    // Fechas de la reserva
    document.getElementById("alquiler-inicio").value = r.fecha_inicio.replace(" ", "T").slice(0, 16);
    document.getElementById("alquiler-fin").value = r.fecha_fin.replace(" ", "T").slice(0, 16);

    openModal("modal-alquiler");
}

async function guardarAlquiler(e) {
    e.preventDefault();
    const idReserva = document.getElementById("alquiler-id-reserva").value;
    const payload = {
        Id_cliente: parseInt(document.getElementById("alquiler-cliente").value),
        Id_vehiculo: parseInt(document.getElementById("alquiler-vehiculo").value),
        fecha_inicio: document.getElementById("alquiler-inicio").value.replace("T", " ") + ":00",
        fecha_dev_prevista: document.getElementById("alquiler-fin").value.replace("T", " ") + ":00",
        Id_reserva: idReserva ? parseInt(idReserva) : null
    };

    try {
        const res = await fetch("/api/alquileres", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            closeModal("modal-alquiler");
            loadAlquileres();
        } else {
            showToast(json.error, "error");
        }
    } catch (err) {
        showToast("Error al formalizar alquiler", "error");
    }
}

// =====================================================================
// 7. PAGOS (RF12, RB10, RB11)
// =====================================================================
async function loadPagos() {
    try {
        const res = await fetch("/api/pagos");
        const json = await res.json();
        if (!json.success) return;

        const tbody = document.getElementById("table-pagos-body");
        if (json.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-400">No hay pagos registrados.</td></tr>`;
            return;
        }

        tbody.innerHTML = json.data.map(p => `
            <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                <td class="px-5 py-3.5 font-bold text-slate-900 font-mono">REC-${p.Id_pago}</td>
                <td class="px-5 py-3.5 font-bold text-indigo-700">Contrato #${p.Id_alquiler}</td>
                <td class="px-5 py-3.5 font-medium text-slate-800">${p.cliente_nombre}</td>
                <td class="px-5 py-3.5 text-xs text-slate-600">${p.fecha_pago}</td>
                <td class="px-5 py-3.5 text-xs">
                    <span class="bg-slate-100 text-slate-700 px-2 py-1 rounded font-medium border border-slate-200">
                        <i class="fa-solid fa-credit-card mr-1 text-slate-500"></i>${p.metodo_pago}
                    </span>
                </td>
                <td class="px-5 py-3.5 text-xs text-slate-600">${p.empleado_nombre}</td>
                <td class="px-5 py-3.5 text-right font-black text-emerald-600 text-base">$${parseFloat(p.monto).toFixed(2)}</td>
            </tr>
        `).join("");
    } catch (e) {
        showToast("Error al cargar pagos", "error");
    }
}

async function openModalNuevoPago(idAlquilerPreseleccionado = null) {
    const sel = document.getElementById("pago-alquiler");
    sel.innerHTML = `<option value="">Seleccione Contrato...</option>`;

    // Traer todos los alquileres
    const res = await fetch("/api/alquileres");
    const json = await res.json();
    if (json.success) {
        json.data.forEach(a => {
            const isSelected = idAlquilerPreseleccionado && a.Id_alquiler === idAlquilerPreseleccionado;
            sel.innerHTML += `<option value="${a.Id_alquiler}" ${isSelected ? 'selected' : ''}>Contrato #${a.Id_alquiler} - ${a.cliente_nombre} (${a.matricula}) [${a.estado}]</option>`;
        });
    }

    document.getElementById("pago-monto").value = "";
    openModal("modal-pago");
}

function registrarPagoParaAlquiler(idAlquiler) {
    openModalNuevoPago(idAlquiler);
}

async function guardarPago(e) {
    e.preventDefault();
    const payload = {
        Id_alquiler: parseInt(document.getElementById("pago-alquiler").value),
        monto: parseFloat(document.getElementById("pago-monto").value),
        metodo_pago: document.getElementById("pago-metodo").value
    };

    try {
        const res = await fetch("/api/pagos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            closeModal("modal-pago");
            loadPagos();
            loadAlquileres();
        } else {
            showToast(json.error, "error");
        }
    } catch (err) {
        showToast("Error al registrar pago", "error");
    }
}

// =====================================================================
// 8. DEVOLUCIONES (RF13, RB12, RB13)
// =====================================================================
async function loadDevoluciones() {
    try {
        const res = await fetch("/api/devoluciones");
        const json = await res.json();
        if (!json.success) return;

        const tbody = document.getElementById("table-devoluciones-body");
        if (json.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-400">No hay devoluciones registradas aún.</td></tr>`;
            return;
        }

        tbody.innerHTML = json.data.map(d => `
            <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                <td class="px-5 py-3.5 font-bold text-slate-800">DEV-${d.Id_devolucion}</td>
                <td class="px-5 py-3.5 font-bold text-indigo-700">Contrato #${d.Id_alquiler}</td>
                <td class="px-5 py-3.5 font-medium text-slate-800">${d.cliente_nombre}</td>
                <td class="px-5 py-3.5 text-xs">${d.nombre_marca} ${d.nombre_modelo} (${d.matricula})</td>
                <td class="px-5 py-3.5 text-xs text-slate-600">${d.fecha_devolucion}</td>
                <td class="px-5 py-3.5 text-xs">
                    <span class="px-2.5 py-1 rounded-full font-bold ${d.estado_recepcion.includes('Daño') || d.estado_recepcion.includes('Mantenimiento') ? 'badge-mantenimiento' : 'badge-disponible'}">
                        ${d.estado_recepcion}
                    </span>
                </td>
                <td class="px-5 py-3.5 text-xs text-slate-500 max-w-xs truncate">${d.observaciones || 'Sin observaciones'}</td>
            </tr>
        `).join("");
    } catch (e) {
        showToast("Error al cargar devoluciones", "error");
    }
}

async function openModalDevolucion(idAlquilerPreseleccionado = null) {
    const sel = document.getElementById("devolucion-alquiler");
    sel.innerHTML = `<option value="">Seleccione Contrato Activo...</option>`;

    // Traer alquileres activos sin devolución previa (RB12, RB13)
    const res = await fetch("/api/alquileres");
    const json = await res.json();
    if (json.success) {
        const activos = json.data.filter(a => a.estado === "Activo" && !a.Id_devolucion);
        activos.forEach(a => {
            const isSelected = idAlquilerPreseleccionado && a.Id_alquiler === idAlquilerPreseleccionado;
            sel.innerHTML += `<option value="${a.Id_alquiler}" ${isSelected ? 'selected' : ''}>Contrato #${a.Id_alquiler} - ${a.cliente_nombre} (${a.matricula})</option>`;
        });
    }

    document.getElementById("devolucion-obs").value = "";
    openModal("modal-devolucion");
}

function registrarDevolucionParaAlquiler(idAlquiler) {
    openModalDevolucion(idAlquiler);
}

async function guardarDevolucion(e) {
    e.preventDefault();
    const payload = {
        Id_alquiler: parseInt(document.getElementById("devolucion-alquiler").value),
        estado_recepcion: document.getElementById("devolucion-estado-recepcion").value,
        observaciones: document.getElementById("devolucion-obs").value
    };

    try {
        const res = await fetch("/api/devoluciones", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            closeModal("modal-devolucion");
            loadDevoluciones();
            loadAlquileres();
            loadVehiculos();
        } else {
            showToast(json.error, "error");
        }
    } catch (err) {
        showToast("Error al registrar devolución", "error");
    }
}

// =====================================================================
// 9. MANTENIMIENTOS (RF14, RB06, RB14)
// =====================================================================
async function loadMantenimientos() {
    try {
        const res = await fetch("/api/mantenimientos");
        const json = await res.json();
        if (!json.success) return;

        const tbody = document.getElementById("table-mantenimientos-body");
        if (json.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-400">No hay órdenes de mantenimiento registradas.</td></tr>`;
            return;
        }

        tbody.innerHTML = json.data.map(m => `
            <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                <td class="px-5 py-3.5 font-bold text-amber-700">ORD-${m.Id_mantenimiento}</td>
                <td class="px-5 py-3.5">
                    <span class="font-bold text-slate-800">${m.nombre_marca} ${m.nombre_modelo}</span>
                    <span class="text-xs text-slate-500 font-mono block">${m.matricula}</span>
                </td>
                <td class="px-5 py-3.5 text-xs text-slate-600">${m.fecha}</td>
                <td class="px-5 py-3.5 text-xs">
                    <span class="px-2.5 py-1 rounded-full font-bold ${m.tipo_mantenimiento === 'Correctivo' ? 'badge-mantenimiento' : 'badge-completada'}">
                        ${m.tipo_mantenimiento}
                    </span>
                </td>
                <td class="px-5 py-3.5 text-xs text-slate-700 max-w-sm">${m.descripcion}</td>
                <td class="px-5 py-3.5 text-xs text-slate-600">${m.empleado_nombre}</td>
                <td class="px-5 py-3.5 text-right font-black text-amber-600">$${parseFloat(m.costo).toFixed(2)}</td>
            </tr>
        `).join("");
    } catch (e) {
        showToast("Error al cargar mantenimientos", "error");
    }
}

async function openModalMantenimiento() {
    await poblarSelectVehiculos("mantenimiento-vehiculo");
    document.getElementById("mantenimiento-costo").value = "0.00";
    document.getElementById("mantenimiento-descripcion").value = "";
    document.getElementById("mantenimiento-bloquear").checked = true;
    openModal("modal-mantenimiento");
}

async function guardarMantenimiento(e) {
    e.preventDefault();
    const payload = {
        Id_vehiculo: parseInt(document.getElementById("mantenimiento-vehiculo").value),
        tipo_mantenimiento: document.getElementById("mantenimiento-tipo").value,
        costo: parseFloat(document.getElementById("mantenimiento-costo").value),
        descripcion: document.getElementById("mantenimiento-descripcion").value,
        poner_en_mantenimiento: document.getElementById("mantenimiento-bloquear").checked
    };

    try {
        const res = await fetch("/api/mantenimientos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            closeModal("modal-mantenimiento");
            loadMantenimientos();
            loadVehiculos();
        } else {
            showToast(json.error, "error");
        }
    } catch (err) {
        showToast("Error al guardar mantenimiento", "error");
    }
}

// =====================================================================
// 10. EMPLEADOS Y USUARIOS (RF15)
// =====================================================================
async function loadEmpleados() {
    try {
        const res = await fetch("/api/empleados");
        const json = await res.json();
        if (!json.success) return;

        const tbody = document.getElementById("table-empleados-body");
        tbody.innerHTML = json.data.map(emp => {
            let rolColor = "bg-blue-100 text-blue-800";
            if (emp.rol === "Administrador") rolColor = "bg-purple-100 text-purple-800";
            else if (emp.rol === "Gerente") rolColor = "bg-amber-100 text-amber-800";

            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="px-5 py-3.5 font-bold text-slate-700">#${emp.Id_empleado}</td>
                    <td class="px-5 py-3.5 font-semibold text-slate-900">${emp.nombres} ${emp.apellidos}</td>
                    <td class="px-5 py-3.5 font-mono text-xs text-indigo-700 font-semibold">${emp.usuario}</td>
                    <td class="px-5 py-3.5">
                        <span class="text-xs px-2.5 py-1 rounded-full font-bold ${rolColor}">
                            ${emp.rol}
                        </span>
                    </td>
                    <td class="px-5 py-3.5 text-xs text-emerald-600 font-bold"><i class="fa-solid fa-circle text-[8px] mr-1"></i>Activo</td>
                    <td class="px-5 py-3.5 text-right">
                        <button onclick="switchRole('${emp.rol}')" class="text-xs bg-slate-100 hover:bg-indigo-600 hover:text-white px-3 py-1 rounded-lg font-medium transition">
                            Probar este rol
                        </button>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        showToast("Error al cargar empleados", "error");
    }
}

function openModalEmpleado() {
    if (currentUser.rol !== "Administrador") {
        showToast("Solo los Administradores pueden crear usuarios (RF15).", "error");
        return;
    }
    document.getElementById("emp-nombres").value = "";
    document.getElementById("emp-apellidos").value = "";
    document.getElementById("emp-usuario").value = "";
    document.getElementById("emp-clave").value = "";
    document.getElementById("emp-rol").value = "Empleado";
    openModal("modal-empleado");
}

async function guardarEmpleado(e) {
    e.preventDefault();
    const payload = {
        nombres: document.getElementById("emp-nombres").value,
        apellidos: document.getElementById("emp-apellidos").value,
        usuario: document.getElementById("emp-usuario").value,
        clave: document.getElementById("emp-clave").value,
        rol: document.getElementById("emp-rol").value
    };

    try {
        const res = await fetch("/api/empleados", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.success) {
            showToast(json.message);
            closeModal("modal-empleado");
            loadEmpleados();
        } else {
            showToast(json.error, "error");
        }
    } catch (err) {
        showToast("Error al guardar empleado", "error");
    }
}

// =====================================================================
// 11. REGLAS DE NEGOCIO (RB01 - RB17)
// =====================================================================
const REGLAS_LISTA = [
    { id: "RB01", nombre: "Unicidad de cliente", desc: "Cada cliente debe poseer un número de identificación único (cédula o pasaporte).", implementacion: "Constraint UNIQUE en BD y validación de inserción en models.py" },
    { id: "RB02", nombre: "Unicidad vehicular", desc: "Todo vehículo registrado debe contar con una matrícula/placa única que lo identifique sin ambigüedades.", implementacion: "Constraint UNIQUE en columna matricula de VEHICULO" },
    { id: "RB03", nombre: "Titularidad de reserva", desc: "Un cliente puede realizar múltiples reservas, pero cada reserva pertenece a un único cliente titular.", implementacion: "Relación 1:N entre CLIENTE y RESERVA con clave foránea obligatoria" },
    { id: "RB04", nombre: "Exclusividad temporal de reserva", desc: "Un vehículo no puede tener dos reservas confirmadas cuyos períodos de inicio y fin se superpongan.", implementacion: "Trigger en BD y validación en Python antes de Confirmar reserva" },
    { id: "RB05", nombre: "Disponibilidad para alquiler", desc: "Solo se permite formalizar contratos de alquiler sobre vehículos cuyo estado sea estrictamente 'Disponible'.", implementacion: "Trigger BEFORE INSERT ON ALQUILER y verificación en app.py" },
    { id: "RB06", nombre: "Restricción por mantenimiento", desc: "Ningún vehículo con estado 'En Mantenimiento' puede ser asignado a una reserva o contrato de alquiler.", implementacion: "Trigger en BD y filtro de selección en interfaz web" },
    { id: "RB07", nombre: "Trazabilidad del contrato", desc: "Todo alquiler debe estar vinculado obligatoriamente a un único cliente, un vehículo y un empleado responsable.", implementacion: "Foreign Keys NOT NULL en ALQUILER hacia CLIENTE, VEHICULO y EMPLEADO" },
    { id: "RB08", nombre: "Registro temporal de alquiler", desc: "Todo contrato de alquiler debe especificar una fecha y hora de inicio y una fecha prevista de devolución.", implementacion: "Columnas fecha_inicio y fecha_dev_prevista NOT NULL" },
    { id: "RB09", nombre: "Coherencia temporal", desc: "La fecha y hora prevista de devolución debe ser estrictamente posterior a la fecha y hora de inicio del alquiler.", implementacion: "CHECK (fecha_dev_prevista > fecha_inicio) en tabla ALQUILER" },
    { id: "RB10", nombre: "Asociación de pagos", desc: "Un alquiler puede registrar uno o varios pagos, pero cada registro de pago pertenece a un solo alquiler.", implementacion: "Relación 1:N entre ALQUILER y PAGO" },
    { id: "RB11", nombre: "Validación de importes", desc: "El monto registrado en cada transacción de pago debe ser un valor numérico estrictamente mayor que cero.", implementacion: "CHECK (monto > 0) en tabla PAGO y validación en API" },
    { id: "RB12", nombre: "Unicidad de devolución", desc: "Cada contrato de alquiler puede estar asociado a un único registro final de devolución del vehículo (1:0..1).", implementacion: "Constraint UNIQUE en Id_alquiler en tabla DEVOLUCION" },
    { id: "RB13", nombre: "Vinculación de devolución", desc: "Un registro de devolución sólo puede crearse si está vinculado a un contrato de alquiler activo y existente.", implementacion: "Validación de estado 'Activo' en backend previo a inserción" },
    { id: "RB14", nombre: "Historial mecánico", desc: "Un vehículo puede acumular múltiples registros de mantenimiento preventivo o correctivo a lo largo de su ciclo de vida.", implementacion: "Relación 1:N entre VEHICULO y MANTENIMIENTO" },
    { id: "RB15", nombre: "Integridad histórica de cliente", desc: "Se prohíbe eliminar físicamente clientes que tengan reservas, contratos de alquiler, pagos u otros registros históricos asociados.", implementacion: "ON DELETE RESTRICT en FKs y validación previa en delete_cliente" },
    { id: "RB16", nombre: "Origen del alquiler", desc: "El alquiler podrá originarse a partir de una reserva confirmada o realizarse directamente sin reserva previa.", implementacion: "Id_reserva NULLABLE en ALQUILER y cambio automático a Completada" },
    { id: "RB17", nombre: "Integridad histórica de vehículos", desc: "Se prohíbe eliminar físicamente vehículos que tengan reservas, alquileres o mantenimientos históricos.", implementacion: "ON DELETE RESTRICT en FKs y validación previa en delete_vehiculo" }
];

function initReglasMatriz() {
    const cont = document.getElementById("reglas-cards-container");
    if (!cont) return;
    cont.innerHTML = REGLAS_LISTA.map(r => `
        <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col justify-between">
            <div>
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-black bg-indigo-100 text-indigo-800 px-2.5 py-1 rounded-lg">${r.id}</span>
                    <span class="text-xs text-emerald-600 font-semibold"><i class="fa-solid fa-circle-check mr-1"></i>Activa</span>
                </div>
                <h4 class="font-bold text-slate-800 text-sm mb-1">${r.nombre}</h4>
                <p class="text-xs text-slate-600 mb-3">${r.desc}</p>
            </div>
            <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-[11px] text-slate-500 font-mono">
                <i class="fa-solid fa-shield-halved text-indigo-500 mr-1"></i> ${r.implementacion}
            </div>
        </div>
    `).join("");
}

// =====================================================================
// HELPERS PARA MODALES Y POBLADO DE SELECTS
// =====================================================================
function openModal(id) {
    document.getElementById(id).classList.remove("hidden");
}

function closeModal(id) {
    document.getElementById(id).classList.add("hidden");
}

async function poblarSelectModelos(selectId, selectedId = null) {
    const sel = document.getElementById(selectId);
    sel.innerHTML = `<option value="">Seleccione Modelo...</option>`;
    const res = await fetch("/api/modelos");
    const j = await res.json();
    if (j.success) {
        j.data.forEach(m => {
            const isSel = selectedId && m.Id_modelo === selectedId;
            sel.innerHTML += `<option value="${m.Id_modelo}" ${isSel ? 'selected' : ''}>${m.nombre_marca} - ${m.nombre_modelo}</option>`;
        });
    }
}

async function poblarSelectCategorias(selectId, selectedId = null) {
    const sel = document.getElementById(selectId);
    sel.innerHTML = `<option value="">Seleccione Categoría...</option>`;
    const res = await fetch("/api/categorias");
    const j = await res.json();
    if (j.success) {
        j.data.forEach(c => {
            const isSel = selectedId && c.Id_categoria === selectedId;
            sel.innerHTML += `<option value="${c.Id_categoria}" ${isSel ? 'selected' : ''}>${c.nombre_categoria}</option>`;
        });
    }
}

async function poblarSelectClientes(selectId, selectedId = null) {
    const sel = document.getElementById(selectId);
    sel.innerHTML = `<option value="">Seleccione Cliente...</option>`;
    const res = await fetch("/api/clientes");
    const j = await res.json();
    if (j.success) {
        j.data.forEach(c => {
            const isSel = selectedId && c.Id_cliente === selectedId;
            sel.innerHTML += `<option value="${c.Id_cliente}" ${isSel ? 'selected' : ''}>${c.Nombres} ${c.Apellidos} (${c.Numero_Identificacion})</option>`;
        });
    }
}

async function poblarSelectVehiculos(selectId, soloNoMantenimiento = false, selectedId = null) {
    const sel = document.getElementById(selectId);
    sel.innerHTML = `<option value="">Seleccione Vehículo...</option>`;
    const res = await fetch("/api/vehiculos");
    const j = await res.json();
    if (j.success) {
        let items = j.data;
        if (soloNoMantenimiento) items = items.filter(v => v.estado !== "En Mantenimiento");
        items.forEach(v => {
            const isSel = selectedId && v.Id_vehiculo === selectedId;
            sel.innerHTML += `<option value="${v.Id_vehiculo}" ${isSel ? 'selected' : ''}>${v.matricula} - ${v.nombre_marca} ${v.nombre_modelo} [${v.estado}] ($${v.tarifa}/d)</option>`;
        });
    }
}

async function poblarSelectVehiculosDisponibles(selectId) {
    const sel = document.getElementById(selectId);
    sel.innerHTML = `<option value="">Seleccione Vehículo Disponible...</option>`;
    const res = await fetch("/api/vehiculos?estado=Disponible");
    const j = await res.json();
    if (j.success) {
        j.data.forEach(v => {
            sel.innerHTML += `<option value="${v.Id_vehiculo}">${v.matricula} - ${v.nombre_marca} ${v.nombre_modelo} ($${v.tarifa}/día)</option>`;
        });
    }
}

