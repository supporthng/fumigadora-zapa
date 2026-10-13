from datetime import datetime, timedelta
import os
import sqlite3
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Fumigadora Zapa | ERP Modular", page_icon="🐛", layout="wide"
)

DB_NAME = "fumigadora_zapa_modular.db"
CARPETA_FICHAS = "fichas_tecnicas"

if not os.path.exists(CARPETA_FICHAS):
  os.makedirs(CARPETA_FICHAS)


# ==========================================
# ESTILOS CSS MODERNOS (UI / UX)
# ==========================================
st.markdown("""
    <style>
    .stApp {
        background-color: #f8fafc;
    }
    .login-card {
        background: #ffffff;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    h1, h2, h3 {
        color: #1e293b;
        font-family: 'Inter', sans-serif;
    }
    .stButton>button {
        background-color: #0f172a;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.1);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #334155;
        border: none;
        color: white;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# INICIALIZACIÓN Y MIGRACIÓN DE LA BASE DE DATOS
# ==========================================
def inicializar_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            rol TEXT NOT NULL,
            pin TEXT NOT NULL
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS tecnicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_tecnico TEXT NOT NULL,
            telefono TEXT,
            especialidad TEXT,
            zona TEXT,
            estado TEXT DEFAULT 'Activo'
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_proveedor TEXT NOT NULL,
            contacto TEXT,
            telefono TEXT,
            email TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            sector TEXT,
            telefono TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS inmuebles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            tipo_inmueble TEXT NOT NULL,
            detalle_ubicacion TEXT NOT NULL,
            contacto_nombre TEXT NOT NULL,
            contacto_telefono TEXT NOT NULL,
            frecuencia_dias INTEGER DEFAULT 30,
            ultimo_servicio TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_producto TEXT NOT NULL,
            categoria TEXT,
            stock INTEGER,
            unidad TEXT,
            precio REAL,
            proveedor_id INTEGER,
            ficha_tecnica TEXT,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
        )
    """)

  cursor.execute("PRAGMA table_info(productos)")
  columnas_productos = [col[1] for col in cursor.fetchall()]
  if "proveedor_id" not in columnas_productos:
    cursor.execute("ALTER TABLE productos ADD COLUMN proveedor_id INTEGER")
  if "ficha_tecnica" not in columnas_productos:
    cursor.execute("ALTER TABLE productos ADD COLUMN ficha_tecnica TEXT")

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalogo_servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_servicio TEXT NOT NULL,
            descripcion TEXT,
            precio_base REAL
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_cotizacion TEXT,
            cliente TEXT,
            detalle TEXT,
            monto_total REAL,
            estado TEXT DEFAULT 'Pendiente'
        )
    """)
  
  # Tabla de Agenda (Programación)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicios_agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inmueble_id INTEGER,
            fecha_servicio TEXT NOT NULL,
            recurrencia TEXT NOT NULL,
            trabajo TEXT NOT NULL,
            tecnico_asignado TEXT NOT NULL,
            estado TEXT DEFAULT 'Programado',
            FOREIGN KEY (inmueble_id) REFERENCES inmuebles (id)
        )
    """)

  # Tabla de Confirmación de Servicios (Conduce y Próxima fecha)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicios_confirmados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agenda_id INTEGER,
            conduce TEXT NOT NULL,
            fecha_ejecucion TEXT NOT NULL,
            proxima_fumigacion TEXT NOT NULL,
            observaciones TEXT,
            FOREIGN KEY (agenda_id) REFERENCES servicios_agenda (id)
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_factura TEXT,
            cliente TEXT,
            tipo_ncf TEXT,
            subtotal REAL,
            itbis REAL,
            total REAL,
            estado_pago TEXT
        )
    """)

  conn.commit()

  cursor.execute(
      "INSERT OR IGNORE INTO usuarios (usuario, rol, pin) VALUES ('admin',"
      " 'Administrador', 'admin')"
  )

  cursor.execute("SELECT COUNT(*) FROM proveedores")
  if cursor.fetchone()[0] == 0:
    cursor.executemany(
        """
            INSERT INTO proveedores (nombre_proveedor, contacto, telefono, email)
            VALUES (?, ?, ?, ?)
        """,
        [
            (
                "Químicos del Caribe S.R.L.",
                "Lic. Alberto Sosa",
                "8096881122",
                "ventas@quimicoscaribe.do",
            ),
            (
                "Distribuidora Agroindustrial",
                "Mariana Ruiz",
                "8095334455",
                "mruiz@agroindustrial.do",
            ),
        ],
    )
    conn.commit()

  cursor.execute("SELECT COUNT(*) FROM tecnicos")
  if cursor.fetchone()[0] == 0:
    cursor.executemany(
        """
            INSERT INTO tecnicos (nombre_tecnico, telefono, especialidad, zona, estado)
            VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                "Juan Pérez",
                "8091112233",
                "Fumigación General",
                "Santo Domingo Este",
                "Activo",
            ),
            (
                "Carlos Gómez",
                "8094445566",
                "Control de Roedores",
                "Distrito Nacional",
                "Activo",
            ),
        ],
    )

  cursor.execute("SELECT COUNT(*) FROM clientes")
  if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO clientes (cliente, sector, telefono) VALUES (?, ?, ?)",
        ("Frituras El Primo", "Gualey, SD", "8095551234"),
    )
    cid = cursor.lastrowid
    cursor.execute(
        """
            INSERT INTO inmuebles (cliente_id, tipo_inmueble, detalle_ubicacion, contacto_nombre, contacto_telefono, frecuencia_dias, ultimo_servicio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cid,
            "Casa",
            "Casa #14, Manzana B",
            "Ramón Pérez",
            "8095551234",
            30,
            (datetime.now().date() - timedelta(days=35)).strftime("%Y-%m-%d"),
        ),
    )

  cursor.execute("SELECT COUNT(*) FROM catalogo_servicios")
  if cursor.fetchone()[0] == 0:
    cursor.executemany(
        """
            INSERT INTO catalogo_servicios (nombre_servicio, descripcion, precio_base)
            VALUES (?, ?, ?)
        """,
        [
            (
                "Fumigación General",
                "Control de insectos rastreros y voladores",
                2500.0,
            ),
            (
                "Control de Roedores",
                "Colocación de cebos y trampas para ratas/ratones",
                3500.0,
            ),
            (
                "Desinfección Ambiental",
                "Saneamiento bacteriológico de espacios",
                3000.0,
            ),
        ],
    )

  cursor.execute("SELECT COUNT(*) FROM productos")
  if cursor.fetchone()[0] == 0:
    cursor.executemany(
        """
            INSERT INTO productos (nombre_producto, categoria, stock, unidad, precio, proveedor_id, ficha_tecnica)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "Cyperkill",
                "Insecticida",
                15,
                "Litros",
                850.0,
                1,
                "cyperkill_ficha.pdf",
            ),
            ("Brodifacoum", "Rodenticida", 25, "Kilos", 450.0, 2, "brodifacoum.pdf"),
        ],
    )

  conn.commit()
  conn.close()


inicializar_db()


# ==========================================
# CONTROL DE SESIÓN Y LOGIN
# ==========================================
def verificar_usuario(usuario, pin):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT rol FROM usuarios WHERE LOWER(usuario) = LOWER(?) AND pin = ?",
      (usuario.strip(), pin.strip()),
  )
  res = cursor.fetchone()
  conn.close()
  return res[0] if res else None


if "autenticado" not in st.session_state:
  st.session_state.autenticado = False
  st.session_state.usuario = ""
  st.session_state.rol = ""

if not st.session_state.autenticado:
  _, col_centro, _ = st.columns([1, 1.2, 1])
  with col_centro:
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.container():
      st.markdown(
          "<div style='text-align: center;'>"
          "<h2 style='color: #0f172a; margin-bottom: 0px;'>🐛 Fumigadora"
          " Zapa</h2>"
          "<p style='color: #64748b; font-size: 14px;'>Sistema ERP Modular</p>"
          "</div>",
          unsafe_allow_html=True,
      )
      st.markdown("<br>", unsafe_allow_html=True)
      with st.form("login"):
        u_in = st.text_input("Usuario", value="admin")
        p_in = st.text_input("PIN / Contraseña", type="password", value="admin")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Iniciar Sesión", use_container_width=True):
          rol = verificar_usuario(u_in, p_in)
          if rol:
            st.session_state.autenticado = True
            st.session_state.usuario = u_in.strip()
            st.session_state.rol = rol
            st.rerun()
          else:
            st.error("Credenciales incorrectas.")
      st.markdown(
          "<div style='text-align: center; margin-top: 20px;'><p"
          " style='color: #94a3b8; font-size: 12px;'>Por defecto — Usuario:"
          " <b>admin</b> | Contraseña: <b>admin</b></p></div>",
          unsafe_allow_html=True,
      )
  st.stop()


# ==========================================
# CARGA DE DATOS CENTRALIZADA
# ==========================================
def cargar_datos(sql):
  conn = sqlite3.connect(DB_NAME)
  if (
      " " not in sql.strip()
      and ";" not in sql
      and "SELECT" not in sql.upper()
  ):
    query = f"SELECT * FROM {sql}"
  else:
    query = sql
  df = pd.read_sql_query(query, conn)
  conn.close()
  return df


df_inmuebles = cargar_datos("""
    SELECT i.id as inmueble_id, c.id as cliente_id, c.cliente, c.sector, c.telefono as cliente_telefono,
           i.tipo_inmueble, i.detalle_ubicacion, i.contacto_nombre, i.contacto_telefono, 
           i.frecuencia_dias, i.ultimo_servicio
    FROM inmuebles i
    JOIN clientes c ON i.cliente_id = c.id
""")
df_clientes = cargar_datos("clientes")
df_tecnicos = cargar_datos("tecnicos")
df_proveedores = cargar_datos("proveedores")
df_productos = cargar_datos("""
    SELECT p.id, p.nombre_producto, p.categoria, p.stock, p.unidad, p.precio, 
           COALESCE(pr.nombre_proveedor, 'Sin Proveedor') as proveedor, p.ficha_tecnica
    FROM productos p
    LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
""")
df_servicios_cat = cargar_datos("catalogo_servicios")
df_cotizaciones = cargar_datos("cotizaciones")
df_facturas = cargar_datos("facturas")
df_usuarios = cargar_datos("usuarios")

# ==========================================
# NAVEGACIÓN MODULAR (SIDEBAR)
# ==========================================
st.sidebar.markdown(
    "<h3 style='color: #0f172a; margin-bottom: 0;'>Fumigadora Zapa</h3>"
    "<p style='color: #64748b; font-size: 12px;'>Módulos del Sistema</p>",
    unsafe_allow_html=True,
)
st.sidebar.divider()
st.sidebar.write(
    f"👤 **{st.session_state.usuario}**  \n🛡️ Rol: *{st.session_state.rol}*"
)
if st.sidebar.button("Cerrar Sesión", use_container_width=True):
  st.session_state.autenticado = False
  st.rerun()

st.sidebar.divider()
st.sidebar.markdown(
    "<p style='font-size: 11px; font-weight: bold; color:"
    " #64748b;'>SELECCIONE MÓDULO</p>",
    unsafe_allow_html=True,
)

modulo = st.sidebar.radio(
    "Módulos",
    [
        "📋 Panel Operativo y Alertas",
        "👥 Módulo de Clientes",
        "👷 Módulo de Técnicos",
        "🏭 Módulo de Proveedores",
        "📦 Módulo de Inventario (Productos & Servicios)",
        "📄 Módulo de Cotización",
        "📅 1. Agenda de Servicios",
        "✅ 2. Confirmación y Cierre de Servicios",
        "💵 Módulo de Facturación (DGII)",
        "⚙️ Módulo de Configuración (Usuarios & Datos)",
    ],
    label_visibility="collapsed",
)

hoy = datetime.now().date()
if not df_inmuebles.empty:
  df_inmuebles["ultimo_servicio"] = pd.to_datetime(
      df_inmuebles["ultimo_servicio"]
  ).dt.date
  df_inmuebles["proximo_servicio"] = df_inmuebles.apply(
      lambda r: r["ultimo_servicio"] + timedelta(days=int(r["frecuencia_dias"])),
      axis=1,
  )


  def est(p):
    d = (p - hoy).days
    return (
        "🔴 Vencido"
        if d < 0
        else "🟡 Toca esta semana"
        if d <= 5
        else "🟢 Al día"
    )


  df_inmuebles["estado"] = df_inmuebles["proximo_servicio"].apply(est)


# ==========================================
# 1. PANEL OPERATIVO Y ALERTAS
# ==========================================
if modulo == "📋 Panel Operativo y Alertas":
  st.title("📋 Panel Operativo y Alertas")
  st.write(
      "Resumen general de frecuencias, vencimientos y estado de localidades."
  )

  if not df_inmuebles.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Localidades", len(df_inmuebles))
    c2.metric(
        "Vencidos",
        len(df_inmuebles[df_inmuebles["estado"].str.contains("Vencido")]),
    )
    c3.metric(
        "Por Vencer",
        len(df_inmuebles[df_inmuebles["estado"].str.contains("Toca")]),
    )

    st.divider()
    st.dataframe(
        df_inmuebles[
            [
                "inmueble_id",
                "cliente",
                "sector",
                "tipo_inmueble",
                "detalle_ubicacion",
                "contacto_nombre",
                "contacto_telefono",
                "proximo_servicio",
                "estado",
            ]
        ],
        use_container_width=True,
    )


# ==========================================
# 2. MÓDULO DE CLIENTES
# ==========================================
elif modulo == "👥 Módulo de Clientes":
  st.title("👥 Módulo de Clientes e Inmuebles")
  st.write(
      "Registra un nuevo cliente y su localidad simultáneamente o consulta el"
      " directorio."
  )

  tab1, tab2 = st.tabs(["Registrar Cliente y Localidad", "Directorio General"])

  with tab1:
    with st.form("form_cliente_inmueble_unificado"):
      st.subheader("1. Información del Cliente / Empresa")
      nuevo_cliente = st.text_input(
          "Nombre del Cliente o Empresa (Ej: Supermercado Zapa)"
      )
      sector_cliente = st.text_input("Sector Principal (Ej: Gualey, SD)")
      telefono_cliente = st.text_input("Teléfono Principal del Cliente")

      st.markdown("---")
      st.subheader("2. Detalle de la Primera Localidad / Inmueble")
      tipo_inm = st.selectbox(
          "Tipo de Inmueble:",
          [
              "Casa",
              "Oficina / Edificio",
              "Almacén / Nave",
              "Cocina Industrial",
              "Torre / Apartamento",
          ],
      )
      ubicacion = st.text_input(
          "Detalle de Ubicación (Ej: Local 402, Manzana B)"
      )
      cnom = st.text_input("Persona de Contacto en Sitio")
      ctel = st.text_input("Teléfono Directo de Contacto")
      freq = st.selectbox("Frecuencia Base (Días)", [7, 15, 30, 60, 90, 180])
      ult_s = st.date_input("Fecha Último Servicio", value=hoy)

      guardar_todo = st.form_submit_button(
          "Guardar Cliente y Localidad en el Momento"
      )

      if guardar_todo:
        if nuevo_cliente and telefono_cliente and ubicacion and cnom:
          conn = sqlite3.connect(DB_NAME)
          cur = conn.cursor()

          cur.execute(
              "INSERT INTO clientes (cliente, sector, telefono) VALUES (?, ?, ?)",
              (nuevo_cliente, sector_cliente, telefono_cliente),
          )
          cliente_id_generado = cur.lastrowid

          cur.execute(
              """
                    INSERT INTO inmuebles (cliente_id, tipo_inmueble, detalle_ubicacion, contacto_nombre, contacto_telefono, frecuencia_dias, ultimo_servicio)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
              (
                  cliente_id_generado,
                  tipo_inm,
                  ubicacion,
                  cnom,
                  ctel,
                  freq,
                  ult_s.strftime("%Y-%m-%d"),
              ),
          )
          conn.commit()
          conn.close()
          st.success(
              f"¡Cliente '{nuevo_cliente}' y su localidad registrados con"
              " éxito!"
          )
          st.rerun()
        else:
          st.warning(
              "Por favor completa los campos obligatorios del cliente y la"
              " localidad."
          )

  with tab2:
    st.subheader("Directorio General de Clientes e Inmuebles")
    st.dataframe(df_inmuebles, use_container_width=True)


# ==========================================
# 3. MÓDULO DE TÉCNICOS
# ==========================================
elif modulo == "👷 Módulo de Técnicos":
  st.title("👷 Módulo de Técnicos de Campo")
  st.write(
      "Administración del personal técnico encargado de ejecutar los servicios."
  )

  tab_tec1, tab_tec2 = st.tabs(["Registrar Técnico", "Listado de Técnicos"])

  with tab_tec1:
    with st.form("form_reg_tecnico"):
      st.subheader("Nuevo Personal Técnico")
      nombre_tec = st.text_input("Nombre Completo del Técnico")
      tel_tec = st.text_input("Teléfono / Celular")
      esp_tec = st.text_input(
          "Especialidad (Ej: Control de Plagas, Roedores, Termitas)"
      )
      zona_tec = st.text_input(
          "Zona o Sector Asignado (Ej: Distrito Nacional, Santo Domingo Este)"
      )
      estado_tec = st.selectbox("Estado", ["Activo", "Inactivo"])

      if st.form_submit_button("Guardar Técnico"):
        if nombre_tec:
          conn = sqlite3.connect(DB_NAME)
          cur = conn.cursor()
          cur.execute(
              """
                    INSERT INTO tecnicos (nombre_tecnico, telefono, especialidad, zona, estado)
                    VALUES (?, ?, ?, ?, ?)
                """,
              (nombre_tec, tel_tec, esp_tec, zona_tec, estado_tec),
          )
          conn.commit()
          conn.close()
          st.success(f"¡Técnico {nombre_tec} registrado con éxito!")
          st.rerun()
        else:
          st.warning("Por favor ingresa el nombre del técnico.")

  with tab_tec2:
    st.subheader("Personal Técnico Registrado")
    st.dataframe(df_tecnicos, use_container_width=True)


# ==========================================
# 4. MÓDULO DE PROVEEDORES
# ==========================================
elif modulo == "🏭 Módulo de Proveedores":
  st.title("🏭 Módulo de Proveedores")
  st.write(
      "Gestión de proveedores de químicos, cebos, equipos y materiales."
  )

  tab_prov1, tab_prov2 = st.tabs(
      ["Registrar Proveedor", "Directorio de Proveedores"]
  )

  with tab_prov1:
    with st.form("form_reg_prov"):
      st.subheader("Datos del Proveedor")
      nom_prov = st.text_input("Nombre de la Empresa Proveedora")
      cont_prov = st.text_input("Persona de Contacto")
      tel_prov = st.text_input("Teléfono de Contacto")
      email_prov = st.text_input("Correo Electrónico")

      if st.form_submit_button("Guardar Proveedor"):
        if nom_prov:
          conn = sqlite3.connect(DB_NAME)
          cur = conn.cursor()
          cur.execute(
              """
                    INSERT INTO proveedores (nombre_proveedor, contacto, telefono, email)
                    VALUES (?, ?, ?, ?)
                """,
              (nom_prov, cont_prov, tel_prov, email_prov),
          )
          conn.commit()
          conn.close()
          st.success(f"¡Proveedor {nom_prov} registrado con éxito!")
          st.rerun()
        else:
          st.warning("Por favor ingresa el nombre del proveedor.")

  with tab_prov2:
    st.subheader("Listado de Proveedores Registrados")
    st.dataframe(df_proveedores, use_container_width=True)


# ==========================================
# 5. MÓDULO DE INVENTARIO (PRODUCTOS & SERVICIOS)
# ==========================================
elif modulo == "📦 Módulo de Inventario (Productos & Servicios)":
  st.title("📦 Módulo de Inventario")
  st.write(
      "Control de químicos, carga directa de fichas técnicas y catálogo de"
      " servicios."
  )

  tab_prod, tab_serv = st.tabs(
      ["Químicos / Productos", "Catálogo de Servicios"]
  )

  with tab_prod:
    st.subheader("Inventario de Químicos y Materiales")
    st.dataframe(
        df_productos[
            [
                "id",
                "nombre_producto",
                "categoria",
                "stock",
                "unidad",
                "precio",
                "proveedor",
                "ficha_tecnica",
            ]
        ],
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("Registrar Químico / Producto con su Ficha Técnica")

    with st.form("form_prod_unificado"):
      np = st.text_input("Nombre del Químico (Ej: Deltametrina)")
      cat = st.selectbox(
          "Categoría", ["Insecticida", "Rodenticida", "Cebo", "Equipo"]
      )
      stk = st.number_input("Stock", min_value=0, value=10)
      uni = st.selectbox("Unidad", ["Litros", "Kilos", "Tubos", "Galones"])
      prc = st.number_input("Precio Estimado (RD$)", min_value=0.0, value=500.0)

      prov_dict = (
          dict(
              zip(
                  df_proveedores["nombre_proveedor"],
                  df_proveedores["id"],
              )
          )
          if not df_proveedores.empty
          else {}
      )
      if prov_dict:
        prov_sel = st.selectbox(
            "Proveedor Asociado:", list(prov_dict.keys())
        )
        prov_id_sel = prov_dict[prov_sel]
      else:
        prov_id_sel = None
        st.warning("No hay proveedores registrados.")

      submit_prod = st.form_submit_button("Guardar Químico en Inventario")

    st.write(
        "📎 **Adjuntar Ficha Técnica (PDF o Documento):** Selecciona un producto"
        " existente para subir su archivo:"
    )
    if not df_productos.empty:
      prod_dict_inv = dict(
          zip(df_productos["nombre_producto"], df_productos["id"])
      )
      prod_sel_archivo = st.selectbox(
          "Seleccionar Producto:", list(prod_dict_inv.keys())
      )
      prod_id_archivo = prod_dict_inv[prod_sel_archivo]

      archivo_ficha = st.file_uploader(
          "Sube el archivo PDF de la Ficha Técnica", type=["pdf", "doc", "docx"]
      )

      if st.button("📤 Guardar Ficha Técnica en el Producto"):
        if archivo_ficha is not None:
          nombre_archivo = f"ficha_{prod_id_archivo}_{archivo_ficha.name}"
          ruta_destino = os.path.join(CARPETA_FICHAS, nombre_archivo)

          with open(ruta_destino, "wb") as f:
            f.write(archivo_ficha.getbuffer())

          conn = sqlite3.connect(DB_NAME)
          cur = conn.cursor()
          cur.execute(
              "UPDATE productos SET ficha_tecnica = ? WHERE id = ?",
              (nombre_archivo, prod_id_archivo),
          )
          conn.commit()
          conn.close()
          st.success(
              f"¡Ficha técnica '{archivo_ficha.name}' enlazada con éxito a"
              f" {prod_sel_archivo}!"
          )
          st.rerun()
        else:
          st.warning("Por favor selecciona un archivo.")

    if submit_prod:
      if np:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            """
                INSERT INTO productos (nombre_producto, categoria, stock, unidad, precio, proveedor_id, ficha_tecnica)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (np, cat, stk, uni, prc, prov_id_sel, "Pendiente"),
        )
        conn.commit()
        conn.close()
        st.success(
            "¡Químico registrado con éxito! Ahora puedes subir su archivo PDF en"
            " la sección de arriba."
        )
        st.rerun()
      else:
        st.warning("Por favor ingresa el nombre del producto.")

  with tab_serv:
    st.subheader("Catálogo de Servicios de Fumigación")
    st.dataframe(df_servicios_cat, use_container_width=True)

    with st.form("form_cat_serv"):
      ns = st.text_input("Nombre del Servicio (Ej: Termitas y Carcoma)")
      desc = st.text_area("Descripción del Servicio")
      pbase = st.number_input("Precio Base (RD$)", min_value=0.0, value=4000.0)

      if st.form_submit_button("Agregar al Catálogo"):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO catalogo_servicios (nombre_servicio, descripcion,"
            " precio_base) VALUES (?, ?, ?)",
            (ns, desc, pbase),
        )
        conn.commit()
        conn.close()
        st.success("¡Servicio agregado al catálogo!")
        st.rerun()


# ==========================================
# 6. MÓDULO DE COTIZACIÓN
# ==========================================
elif modulo == "📄 Módulo de Cotización":
  st.title("📄 Módulo de Cotización")
  st.write("Genera presupuestos formales para clientes.")

  with st.form("form_cot"):
    cli_c = st.selectbox(
        "Cliente:",
        df_inmuebles["cliente"].unique().tolist()
        if not df_inmuebles.empty
        else ["General"],
    )
    serv_c = st.selectbox(
        "Servicio a Cotizar:", df_servicios_cat["nombre_servicio"].tolist()
    )
    monto_c = st.number_input("Monto Total (RD$)", min_value=0.0, value=3500.0)
    obs_c = st.text_area(
        "Observaciones / Términos de la Cotización",
        value=(
            "Incluye garantía de 30 días y certificado para fines de Salud"
            " Pública."
        ),
    )

    if st.form_submit_button("Generar y Guardar Cotización"):
      conn = sqlite3.connect(DB_NAME)
      cur = conn.cursor()
      cur.execute(
          """
                INSERT INTO cotizaciones (fecha_cotizacion, cliente, detalle, monto_total, estado)
                VALUES (?, ?, ?, ?, ?)
            """,
          (
              hoy.strftime("%Y-%m-%d"),
              cli_c,
              f"{serv_c} - {obs_c}",
              monto_c,
              "Emitida",
          ),
      )
      conn.commit()
      conn.close()
      st.success(
          f"¡Cotización generada exitosamente para {cli_c} por RD$ {monto_c:,.2f}!"
      )
      st.rerun()

  st.divider()
  st.subheader("Historial de Cotizaciones")
  st.dataframe(df_cotizaciones, use_container_width=True)


# ==========================================
# 7. AGENDA DE SERVICIOS (PROGRAMACIÓN)
# ==========================================
elif modulo == "📅 1. Agenda de Servicios":
  st.title("📅 Agenda de Servicios (Programación)")
  st.write(
      "Programa las visitas futuras seleccionando la localidad, recurrencia y"
      " técnico asignado."
  )

  with st.form("form_agenda"):
    if not df_inmuebles.empty:
      op_inm = df_inmuebles.apply(
          lambda r: (
              f"ID #{r['inmueble_id']} - {r['cliente']} | {r['tipo_inmueble']}:"
              f" {r['detalle_ubicacion']}"
          ),
          axis=1,
      ).tolist()
      inm_sel = st.selectbox("Seleccione Localidad:", op_inm)
      inm_id = int(inm_sel.split(" - ")[0].replace("ID #", ""))
    else:
      inm_id = None
      st.warning("Registra una localidad primero.")

    f_serv = st.date_input("Fecha Programada del Servicio:", value=hoy)
    rec = st.selectbox(
        "Recurrencia:",
        [
            "Semanal",
            "Quincenal",
            "Mensual",
            "Cada 2 meses",
            "Cada 3 meses",
            "Cada 6 meses",
        ],
    )
    trab = st.selectbox(
        "Trabajo:", df_servicios_cat["nombre_servicio"].tolist()
    )
    lista_tecnicos_reg = (
        df_tecnicos["nombre_tecnico"].tolist()
        if not df_tecnicos.empty
        else ["Sin técnicos"]
    )
    tec = st.selectbox("Técnico Asignado:", lista_tecnicos_reg)

    if st.form_submit_button("Agendar Trabajo"):
      if inm_id:
        d_map = {
            "Semanal": 7,
            "Quincenal": 15,
            "Mensual": 30,
            "Cada 2 meses": 60,
            "Cada 3 meses": 90,
            "Cada 6 meses": 180,
        }
        dias = d_map.get(rec, 30)

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            """
                INSERT INTO servicios_agenda (inmueble_id, fecha_servicio, recurrencia, trabajo, tecnico_asignado, estado)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                inm_id,
                f_serv.strftime("%Y-%m-%d"),
                rec,
                trab,
                tec,
                "Programado",
            ),
        )
        cur.execute(
            "UPDATE inmuebles SET frecuencia_dias = ? WHERE id = ?", (dias, inm_id)
        )
        conn.commit()
        conn.close()
        st.success(
            f"¡Servicio agendado para la Localidad ID #{inm_id} con recurrencia"
            f" {rec}!"
        )
        st.rerun()

  st.divider()
  st.subheader("Trabajos Programados en Agenda")
  df_ag = cargar_datos("""
        SELECT s.id as agenda_id, s.inmueble_id, c.cliente, i.tipo_inmueble, i.detalle_ubicacion, 
               s.fecha_servicio, s.recurrencia, s.trabajo, s.tecnico_asignado, s.estado
        FROM servicios_agenda s
        JOIN inmuebles i ON s.inmueble_id = i.id
        JOIN clientes c ON i.cliente_id = c.id
        WHERE s.estado = 'Programado'
    """)
  st.dataframe(df_ag, use_container_width=True)


# ==========================================
# 8. CONFIRMACIÓN Y CIERRE DE SERVICIOS
# ==========================================
elif modulo == "✅ 2. Confirmación y Cierre de Servicios":
  st.title("✅ Confirmación y Cierre de Servicios")
  st.write(
      "Confirma los servicios realizados ingresando el número de conduce y la"
      " fecha de la próxima fumigación."
  )

  df_pendientes = cargar_datos("""
        SELECT s.id as agenda_id, c.cliente, i.tipo_inmueble, i.detalle_ubicacion, 
               s.fecha_servicio, s.trabajo, s.tecnico_asignado, s.recurrencia
        FROM servicios_agenda s
        JOIN inmuebles i ON s.inmueble_id = i.id
        JOIN clientes c ON i.cliente_id = c.id
        WHERE s.estado = 'Programado'
    """)

  if not df_pendientes.empty:
    with st.form("form_confirmar_servicio"):
      op_pend = df_pendientes.apply(
          lambda r: (
              f"Agenda ID #{r['agenda_id']} - {r['cliente']} |"
              f" {r['tipo_inmueble']} ({r['detalle_ubicacion']}) - Programado"
              f" para {r['fecha_servicio']}"
          ),
          axis=1,
      ).tolist()

      sel_agenda_str = st.selectbox("Seleccione Servicio Programado:", op_pend)
      agenda_id_sel = int(
          sel_agenda_str.split(" - ")[0].replace("Agenda ID #", "")
      )

      # Obtener datos de recurrencia del servicio seleccionado
      row_sel = df_pendientes[
          df_pendientes["agenda_id"] == agenda_id_sel
      ].iloc[0]
      recurrencia_act = row_sel["recurrencia"]

      d_map = {
          "Semanal": 7,
          "Quincenal": 15,
          "Mensual": 30,
          "Cada 2 meses": 60,
          "Cada 3 meses": 90,
          "Cada 6 meses": 180,
      }
      dias_rec = d_map.get(recurrencia_act, 30)

      st.markdown("---")
      col1, col2 = st.columns(2)
      with col1:
        num_conduce = st.text_input("Número de Conduce (Confirmación)")
        fecha_ejec = st.date_input("Fecha Real de Ejecución", value=hoy)
      with col2:
        # Calcular fecha sugerida de próxima fumigación
        sugerencia_prox = fecha_ejec + timedelta(days=dias_rec)
        fecha_prox = st.date_input(
            "Fecha de Próxima Fumigación", value=sugerencia_prox
        )

      obs_cierre = st.text_area("Observaciones del Servicio Realizado")

      confirmar_btn = st.form_submit_button(
          "Confirmar Servicio, Guardar Conduce y Actualizar Próxima Fecha"
      )

      if confirmar_btn:
        if num_conduce:
          conn = sqlite3.connect(DB_NAME)
          cur = conn.cursor()

          # Registrar en servicios confirmados
          cur.execute(
              """
                    INSERT INTO servicios_confirmados (agenda_id, conduce, fecha_ejecucion, proxima_fumigacion, observaciones)
                    VALUES (?, ?, ?, ?, ?)
                """,
              (
                  agenda_id_sel,
                  num_conduce,
                  fecha_ejec.strftime("%Y-%m-%d"),
                  fecha_prox.strftime("%Y-%m-%d"),
                  obs_cierre,
              ),
          )

          # Actualizar estado en agenda a 'Completado'
          cur.execute(
              "UPDATE servicios_agenda SET estado = 'Completado' WHERE id = ?",
              (agenda_id_sel,),
          )

          # Actualizar último servicio en la tabla inmuebles para reflejar el ciclo nuevo
          cur.execute(
              """
                    UPDATE inmuebles 
                    SET ultimo_s = ? 
                    WHERE id = (SELECT inmueble_id FROM servicios_agenda WHERE id = ?)
                """,
              (fecha_ejec.strftime("%Y-%m-%d"), agenda_id_sel),
          )
          # Nota: actualizamos la columna ultimo_servicio según corresponda en la base de datos
          cur.execute(
              """
                    UPDATE inmuebles 
                    SET ultimo_servicio = ? 
                    WHERE id = (SELECT inmueble_id FROM servicios_agenda WHERE id = ?)
                """,
              (fecha_ejec.strftime("%Y-%m-%d"), agenda_id_sel),
          )

          conn.commit()
          conn.close()
          st.success(
              f"¡Servicio confirmado con Conduce #{num_conduce}! Próxima"
              f" fumigación programada para el {fecha_prox}."
          )
          st.rerun()
        else:
          st.warning("Por favor ingresa el número de conduce.")
  else:
    st.info("No hay servicios programados pendientes de confirmación.")

  st.divider()
  st.subheader("Historial de Servicios Confirmados (Conduces Emitidos)")
  df_confirmados = cargar_datos("""
        SELECT sc.id as confirmacion_id, sc.agenda_id, c.cliente, i.tipo_inmueble, i.detalle_ubicacion,
               sc.conduce, sc.fecha_ejecucion, sc.proxima_fumigacion, s.tecnico_asignado, sc.observaciones
        FROM servicios_confirmados sc
        JOIN servicios_agenda s ON sc.agenda_id = s.id
        JOIN inmuebles i ON s.inmueble_id = i.id
        JOIN clientes c ON i.cliente_id = c.id
    """)
  if not df_confirmados.empty:
    st.dataframe(df_confirmados, use_container_width=True)
  else:
    st.info("Aún no hay servicios confirmados en el historial.")


# ==========================================
# 9. MÓDULO DE FACTURACIÓN (DGII)
# ==========================================
elif modulo == "💵 Módulo de Facturación (DGII)":
  st.title("💵 Módulo de Facturación y Comprobantes Fiscales")
  st.write("Emisión de facturas con cálculo de ITBIS (18%) y NCF / e-CF.")

  with st.form("form_fact"):
    cli_f = st.selectbox(
        "Cliente:",
        df_inmuebles["cliente"].unique().tolist()
        if not df_inmuebles.empty
        else ["General"],
    )
    tipo_n = st.selectbox(
        "Tipo de Comprobante:",
        [
            "B01 - Crédito Fiscal",
            "B02 - Factura de Consumo",
            "E31 - e-CF Crédito Fiscal",
            "E32 - e-CF Factura de Consumo",
        ],
    )
    sub = st.number_input("Subtotal (RD$)", min_value=0.0, value=3000.0)

    itb = sub * 0.18
    tot = sub + itb
    st.write(
        f"Subtotal: RD$ {sub:,.2f} | ITBIS (18%): RD$ {itb:,.2f} | **Total:"
        f" RD$ {tot:,.2f}**"
    )

    if st.form_submit_button("Emitir Factura Fiscal"):
      conn = sqlite3.connect(DB_NAME)
      cur = conn.cursor()
      cur.execute(
          """
                INSERT INTO facturas (fecha_factura, cliente, tipo_ncf, subtotal, itbis, total, estado_pago)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
          (
              hoy.strftime("%Y-%m-%d"),
              cli_f,
              tipo_n,
              sub,
              itb,
              tot,
              "Emitida / Pagada",
          ),
      )
      conn.commit()
      conn.close()
      st.success(
          f"¡Factura emitida bajo el comprobante {tipo_n} por RD$ {tot:,.2f}!"
      )
      st.rerun()

  st.divider()
  st.subheader("Historial de Facturación")
  st.dataframe(df_facturas, use_container_width=True)


# ==========================================
# 10. MÓDULO DE CONFIGURACIÓN (USUARIOS & DATOS)
# ==========================================
elif modulo == "⚙️ Módulo de Configuración (Usuarios & Datos)":
  st.title("⚙️ Configuración, Gestión de Usuarios y Datos Masivos")
  st.write(
      "Administración de accesos y carga masiva de datos mediante Excel."
  )

  tab_cfg1, tab_cfg2 = st.tabs(
      ["Gestión de Datos (Excel)", "Usuarios del Sistema"]
  )

  with tab_cfg1:
    st.subheader("📥 Importación Masiva de Datos (Excel / CSV)")
    st.write(
        "Sube un archivo Excel para alimentar automáticamente las tablas del"
        " sistema."
    )

    tipo_destino = st.selectbox(
        "Seleccione la tabla de destino:",
        [
            "Clientes",
            "Proveedores",
            "Productos / Inventario",
            "Catálogo de Servicios",
            "Técnicos",
        ],
    )

    archivo_subido = st.file_uploader(
        "Sube tu archivo Excel (.xlsx o .csv)", type=["xlsx", "csv"]
    )

    if archivo_subido is not None:
      try:
        if archivo_subido.name.endswith(".csv"):
          df_subido = pd.read_csv(archivo_subido)
        else:
          df_subido = pd.read_excel(archivo_subido)

        st.markdown("---")
        st.write("🔍 **Vista previa de los datos detectados:**")
        st.dataframe(df_subido.head(), use_container_width=True)

        if st.button("🚀 Procesar e Insertar Datos en la Base de Datos"):
          conn = sqlite3.connect(DB_NAME)

          if tipo_destino == "Clientes":
            df_subido.to_sql("clientes", conn, if_exists="append", index=False)
          elif tipo_destino == "Proveedores":
            df_subido.to_sql(
                "proveedores", conn, if_exists="append", index=False
            )
          elif tipo_destino == "Productos / Inventario":
            df_subido.to_sql("productos", conn, if_exists="append", index=False)
          elif tipo_destino == "Catálogo de Servicios":
            df_subido.to_sql(
                "catalogo_servicios", conn, if_exists="append", index=False
            )
          elif tipo_destino == "Técnicos":
            df_subido.to_sql("tecnicos", conn, if_exists="append", index=False)

          conn.close()
          st.success(
              "¡Datos importados y guardados en la base de datos con éxito!"
          )
          st.rerun()

      except Exception as e:
        st.error(
            f"Ocurrió un error al procesar el archivo. Verifica que las"
            f" columnas coincidan. Detalle: {e}"
        )

  with tab_cfg2:
    st.subheader("Control de Accesos y Permisos")
    st.dataframe(
        df_usuarios[["id", "usuario", "rol"]], use_container_width=True
    )

    if st.session_state.rol == "Administrador":
      with st.form("form_usr"):
        st.subheader("Crear Nuevo Usuario de Sistema")
        nu = st.text_input("Nombre de Usuario")
        ro = st.selectbox("Rol", ["Administrador", "Técnico"])
        pi = st.text_input("PIN o Contraseña", type="password")

        if st.form_submit_button("Crear Usuario"):
          if nu and pi:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            try:
              cur.execute(
                  "INSERT INTO usuarios (usuario, rol, pin) VALUES (?, ?, ?)",
                  (nu, ro, pi),
              )
              conn.commit()
              st.success(f"¡Usuario {nu} creado con éxito!")
              st.rerun()
            except sqlite3.IntegrityError:
              st.error("Ese usuario ya existe.")
            finally:
              conn.close()
          else:
            st.warning("Completa todos los campos.")
    else:
      st.info(
          "Se requieren permisos de Administrador para crear nuevos usuarios."
      )
