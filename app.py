from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Fumigadora Zapa - Sistema ERP", page_icon="🐛", layout="wide"
)

DB_NAME = "fumigadora_zapa_erp.db"


# ==========================================
# INICIALIZACIÓN DE LA BASE DE DATOS (4 TABLAS)
# ==========================================
def inicializar_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  # 1. Tabla de Usuarios y Roles
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            rol TEXT NOT NULL, -- 'Administrador' o 'Técnico'
            pin TEXT NOT NULL
        )
    """)

  # 2. Tabla de Clientes
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            sector TEXT,
            telefono TEXT,
            ultimo_servicio TEXT,
            frecuencia_dias INTEGER,
            plaga_tratada TEXT,
            monto_sugerido REAL
        )
    """)

  # 3. Tabla de Productos y Químicos
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_producto TEXT NOT NULL,
            categoria TEXT,
            stock INTEGER,
            unidad TEXT,
            precio REAL
        )
    """)

  # 4. Tabla de Facturación e Historial Fiscal (DGII)
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

  # Datos iniciales por defecto si las tablas están vacías
  cursor.execute("SELECT COUNT(*) FROM usuarios")
  if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO usuarios (usuario, rol, pin) VALUES (?, ?, ?)",
        [
            ("César Castillo", "Administrador", "1234"),
            ("Técnico Zona Norte", "Técnico", "0000"),
        ],
    )

  cursor.execute("SELECT COUNT(*) FROM clientes")
  if cursor.fetchone()[0] == 0:
    cursor.executemany(
        """
            INSERT INTO clientes (cliente, sector, telefono, ultimo_servicio, frecuencia_dias, plaga_tratada, monto_sugerido)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "Frituras El Primo",
                "Gualey, SD",
                "8095551234",
                (datetime.now().date() - timedelta(days=35)).strftime(
                    "%Y-%m-%d"
                ),
                30,
                "Cucarachas y Hormigas",
                2500.0,
            ),
            (
                "Colmado Doña Rosa",
                "Ensanche Luperón",
                "8092224321",
                (datetime.now().date() - timedelta(days=10)).strftime(
                    "%Y-%m-%d"
                ),
                60,
                "Rodedores (Ratas)",
                3500.0,
            ),
        ],
    )

  cursor.execute("SELECT COUNT(*) FROM productos")
  if cursor.fetchone()[0] == 0:
    cursor.executemany(
        """
            INSERT INTO productos (nombre_producto, categoria, stock, unidad, precio)
            VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("Cyperkill", "Insecticida", 15, "Litros", 850.0),
            ("K-Othrine SC", "Insecticida", 10, "Litros", 1200.0),
            ("Brodifacoum", "Rodenticida", 25, "Kilos", 450.0),
        ],
    )

  conn.commit()
  conn.close()


inicializar_db()


# ==========================================
# CONTROL DE SESIÓN Y ACCESO (LOGIN)
# ==========================================
def verificar_usuario(nombre_usuario, pin_ingresado):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT rol FROM usuarios WHERE usuario = ? AND pin = ?",
      (nombre_usuario, pin_ingresado),
  )
  res = cursor.fetchone()
  conn.close()
  return res[0] if res else None


if "autenticado" not in st.session_state:
  st.session_state.autenticado = False
  st.session_state.usuario = ""
  st.session_state.rol = ""

if not st.session_state.autenticado:
  st.title("🔐 Acceso - Fumigadora Zapa")
  with st.form("login_form"):
    conn = sqlite3.connect(DB_NAME)
    df_u = pd.read_sql_query("SELECT usuario FROM usuarios", conn)
    conn.close()

    usuario_sel = st.selectbox("Seleccione Usuario:", df_u["usuario"].tolist())
    pin_input = st.text_input("PIN de Acceso:", type="password")
    submit_login = st.form_submit_button("Entrar al Sistema")

    if submit_login:
      rol_encontrado = verificar_usuario(usuario_sel, pin_input)
      if rol_encontrado:
        st.session_state.autenticado = True
        st.session_state.usuario = usuario_sel
        st.session_state.rol = rol_encontrado
        st.success(
            f"¡Bienvenido {usuario_sel}! Rol asignado: {rol_encontrado}"
        )
        st.rerun()
      else:
        st.error("PIN incorrecto. Intente de nuevo.")
  st.stop()


# ==========================================
# APLICACIÓN PRINCIPAL (POST-LOGIN)
# ==========================================
def cargar_datos(tabla):
  conn = sqlite3.connect(DB_NAME)
  df = pd.read_sql_query(f"SELECT * FROM {tabla}", conn)
  conn.close()
  return df


df_clientes = cargar_datos("clientes")
df_clientes["ultimo_servicio"] = pd.to_datetime(
    df_clientes["ultimo_servicio"]
).dt.date
df_productos = cargar_datos("productos")
df_facturas = cargar_datos("facturas")

st.sidebar.image("https://img.icons8.com/color/96/pest-control.png", width=70)
st.sidebar.write(
    f"👤 **Usuario:** {st.session_state.usuario}  \n🛡️ **Rol:**"
    f" {st.session_state.rol}"
)
if st.sidebar.button("Cerrar Sesión"):
  st.session_state.autenticado = False
  st.rerun()

st.sidebar.header("Módulos del Sistema")
modulos_disponibles = ["📋 Panel, Alertas y Rutas", "📄 Certificados Sanitarios"]

# Si es Administrador, tiene acceso total a inventario, facturación y usuarios
if st.session_state.rol == "Administrador":
  modulos_disponibles.extend([
      "📦 Inventario de Químicos",
      "💵 Facturación y Comprobantes (DGII)",
      "👥 Gestión de Usuarios",
  ])

opcion = st.sidebar.radio("Seleccione sección:", modulos_disponibles)

hoy = datetime.now().date()
df_clientes["proximo_servicio"] = df_clientes.apply(
    lambda row: row["ultimo_servicio"]
    + timedelta(days=int(row["frecuencia_dias"])),
    axis=1,
)


def calcular_estado(prox):
  dias_restantes = (prox - hoy).days
  if dias_restantes < 0:
    return "🔴 Vencido"
  elif dias_restantes <= 5:
    return "🟡 Toca esta semana"
  else:
    return "🟢 Al día"


df_clientes["estado"] = df_clientes["proximo_servicio"].apply(calcular_estado)


# ==========================================
# 1. PANEL, ALERTAS Y RUTAS
# ==========================================
if opcion == "📋 Panel, Alertas y Rutas":
  st.subheader("Tablero Operativo y Planificación de Servicios")

  col1, col2, col3 = st.columns(3)
  col1.metric("Total Clientes", len(df_clientes))
  col2.metric(
      "Servicios Vencidos",
      len(df_clientes[df_clientes["estado"].str.contains("Vencido")]),
  )
  col3.metric(
      "Por Vencer (5 días)",
      len(df_clientes[df_clientes["estado"].str.contains("Toca")]),
  )

  st.divider()
  sector_sel = st.selectbox(
      "📍 Filtrar por Sector:", ["Todos"] + list(df_clientes["sector"].unique())
  )
  df_f = (
      df_clientes
      if sector_sel == "Todos"
      else df_clientes[df_clientes["sector"] == sector_sel]
  )

  st.dataframe(
      df_f[
          [
              "id",
              "cliente",
              "sector",
              "telefono",
              "ultimo_servicio",
              "proximo_servicio",
              "plaga_tratada",
              "estado",
          ]
      ],
      use_container_width=True,
  )

  if not df_clientes.empty:
    st.subheader("Acción Directa sobre Cliente")
    cli_sel = st.selectbox(
        "Seleccione cliente:", df_clientes["cliente"].tolist()
    )
    dat_c = df_clientes[df_clientes["cliente"] == cli_sel].iloc[0]

    c1, c2 = st.columns(2)
    with c1:
      msg = (
          f"Hola {dat_c['cliente']}, le saludamos de Fumigadora Zapa. Su"
          f" servicio de control de plagas toca el"
          f" {dat_c['proximo_servicio']}. ¿Confirmamos la visita?"
      )
      url_wa = (
          f"https://wa.me/1{dat_c['telefono']}?text=" + msg.replace(" ", "%20")
      )
      st.markdown(
          f"📱 **WhatsApp:** [Enviar Recordatorio]({url_wa})",
          unsafe_allow_html=True,
      )
    with c2:
      if st.button("🔄 Marcar Servicio Realizado Hoy"):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE clientes SET ultimo_servicio = ? WHERE id = ?",
            (hoy.strftime("%Y-%m-%d"), int(dat_c["id"])),
        )
        conn.commit()
        conn.close()
        st.success(
            f"¡Ciclo reiniciado para {cli_sel}! Fecha actualizada a hoy."
        )
        st.rerun()


# ==========================================
# 2. CERTIFICADOS SANITARIOS
# ==========================================
elif opcion == "📄 Certificados Sanitarios":
  st.subheader("Generación de Certificado de Fumigación")
  if not df_clientes.empty:
    cli_cert = st.selectbox(
        "Seleccionar Cliente:", df_clientes["cliente"].tolist()
    )
    dat_c = df_clientes[df_clientes["cliente"] == cli_cert].iloc[0]

    cert_texto = f"""
    ==================================================
                 FUMIGADORA ZAPA
          Certificado Oficial de Control de Plagas
    ==================================================
    Fecha: {hoy}
    Cliente: {dat_c['cliente']}
    Ubicación: {dat_c['sector']}
    
    DETALLES TÉCNICOS:
    - Plaga Controlada: {dat_c['plaga_tratada']}
    - Próximo Servicio: {dat_c['proximo_servicio']}
    
    Establecimiento verificado bajo normas de salubridad.
    --------------------------------------------------
    Firma Autorizada / Sello: Fumigadora Zapa
    """
    st.text_area("Vista Previa:", cert_texto, height=220)
    st.download_button(
        "📥 Descargar Certificado",
        data=cert_texto,
        file_name=f"Certificado_{dat_c['cliente']}.txt",
        mime="text/plain",
    )


# ==========================================
# 3. INVENTARIO DE QUÍMICOS (Solo Admin)
# ==========================================
elif opcion == "📦 Inventario de Químicos":
  st.subheader("Control de Stock e Insumos")
  st.dataframe(df_productos, use_container_width=True)

  with st.form("nuevo_prod"):
    n_prod = st.text_input("Nombre del Químico / Producto")
    cat_prod = st.selectbox(
        "Categoría", ["Insecticida", "Rodenticida", "Cebo", "Equipo"]
    )
    stk = st.number_input("Stock", min_value=0, value=10)
    uni = st.selectbox("Unidad", ["Litros", "Kilos", "Tubos", "Galones"])
    prc = st.number_input("Precio Unitario (RD$)", min_value=0.0, value=500.0)

    if st.form_submit_button("Agregar al Inventario"):
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO productos (nombre_producto, categoria, stock, unidad,"
          " precio) VALUES (?, ?, ?, ?, ?)",
          (n_prod, cat_prod, stk, uni, prc),
      )
      conn.commit()
      conn.close()
      st.success("¡Producto registrado con éxito!")
      st.rerun()


# ==========================================
# 4. FACTURACIÓN Y COMPROBANTES DGII (Solo Admin)
# ==========================================
elif opcion == "💵 Facturación y Comprobantes (DGII)":
  st.subheader("Módulo de Facturación y Emisión e-CF")

  with st.form("form_factura"):
    cli_fac = st.selectbox(
        "Cliente a Facturar:", df_clientes["cliente"].tolist()
    )
    ncf = st.selectbox(
        "Tipo de Comprobante Fiscal:",
        [
            "B01 - Crédito Fiscal",
            "B02 - Factura de Consumo",
            "E31 - e-CF Crédito Fiscal",
            "E32 - e-CF Factura de Consumo",
        ],
    )
    sub = st.number_input(
        "Monto Subtotal (RD$)", min_value=0.0, value=3000.0, step=500.0
    )

    itb = sub * 0.18
    tot = sub + itb

    st.write(
        f"**Subtotal:** RD$ {sub:,.2f} | **ITBIS (18%):** RD$ {itb:,.2f} |"
        f" **Total a Pagar:** RD$ {tot:,.2f}"
    )

    emitir = st.form_submit_button("Generar y Registrar Factura Fiscal")
    if emitir:
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO facturas (fecha_factura, cliente, tipo_ncf, subtotal, itbis, total, estado_pago)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
          (
              hoy.strftime("%Y-%m-%d"),
              cli_fac,
              ncf,
              sub,
              itb,
              tot,
              "Emitida / Pagada",
          ),
      )
      conn.commit()
      conn.close()
      st.success(
          f"¡Factura emitida correctamente bajo el comprobante {ncf} por un"
          f" total de RD$ {tot:,.2f}!"
      )
      st.rerun()

  st.divider()
  st.subheader("Historial de Facturas Emitidas")
  if not df_facturas.empty:
    st.dataframe(df_facturas, use_container_width=True)
  else:
    st.info("No hay facturas registradas todavía.")


# ==========================================
# 5. GESTIÓN DE USUARIOS (Solo Admin)
# ==========================================
elif opcion == "👥 Gestión de Usuarios":
  st.subheader("Control de Accesos y Permisos del Sistema")
  st.dataframe(cargar_datos("usuarios")[["id", "usuario", "rol"]], use_container_width=True)

  with st.form("nuevo_usuario"):
    nu = st.text_input("Nombre del Usuario (Ej: Juan Pérez)")
    ro = st.selectbox("Rol del Usuario", ["Administrador", "Técnico"])
    pi = st.text_input("PIN de 4 dígitos", type="password", max_chars=4)

    if st.form_submit_button("Crear Nuevo Usuario"):
      if nu and pi:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
          cursor.execute(
              "INSERT INTO usuarios (usuario, rol, pin) VALUES (?, ?, ?)",
              (nu, ro, pi),
          )
          conn.commit()
          st.success(f"¡Usuario {nu} creado con éxito!")
          st.rerun()
        except sqlite3.IntegrityError:
          st.error("Ese nombre de usuario ya existe.")
        finally:
          conn.close()
      else:
        st.warning("Completa todos los campos.")from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Fumigadora Zapa - Sistema SQLite", page_icon="🐛", layout="wide"
)

DB_NAME = "fumigadora_zapa.db"


# ==========================================
# GESTIÓN DE BASE DE DATOS (SQLITE)
# ==========================================
def inicializar_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            sector TEXT,
            telefono TEXT,
            ultimo_servicio TEXT,
            frecuencia_dias INTEGER,
            plaga_tratada TEXT,
            productos_usados TEXT,
            estatus_pago TEXT,
            monto REAL
        )
    """)
  conn.commit()

  # Insertar datos de ejemplo si la tabla está vacía
  cursor.execute("SELECT COUNT(*) FROM clientes")
  if cursor.fetchone()[0] == 0:
    ejemplos = [
        (
            "Frituras El Primo",
            "Gualey, SD",
            "8095551234",
            (datetime.now().date() - timedelta(days=35)).strftime("%Y-%m-%d"),
            30,
            "Cucarachas y Hormigas",
            "Cyperkill / K-Othrine",
            "Pendiente",
            2500.0,
        ),
        (
            "Colmado Doña Rosa",
            "Ensanche Luperón",
            "8092224321",
            (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d"),
            60,
            "Rodedores (Ratas)",
            "Cebo Rodenticida Brodifacoum",
            "Pagado",
            3500.0,
        ),
    ]
    cursor.executemany(
        """
            INSERT INTO clientes (cliente, sector, telefono, ultimo_servicio, frecuencia_dias, plaga_tratada, productos_usados, estatus_pago, monto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ejemplos,
    )
    conn.commit()
  conn.close()


inicializar_db()


def cargar_datos_sql():
  conn = sqlite3.connect(DB_NAME)
  df = pd.read_sql_query("SELECT * FROM clientes", conn)
  conn.close()
  df["ultimo_servicio"] = pd.to_datetime(df["ultimo_servicio"]).dt.date
  return df


df_clientes = cargar_datos_sql()

st.title("🐛 Fumigadora Zapa - Sistema de Gestión (SQLite)")
st.sidebar.image("https://img.icons8.com/color/96/pest-control.png", width=70)
st.sidebar.header("Navegación")
opcion = st.sidebar.radio(
    "Seleccione módulo:",
    [
        "📋 Panel, Alertas y Rutas",
        "⚡ Registro Rápido (Texto Libre)",
        "➕ Nuevo Cliente Detallado",
        "📄 Generar Certificado PDF",
        "💵 Facturación y Cobros",
    ],
)

# Cálculos dinámicos de fecha y estado
hoy = datetime.now().date()
df_clientes["proximo_servicio"] = df_clientes.apply(
    lambda row: row["ultimo_servicio"]
    + timedelta(days=int(row["frecuencia_dias"])),
    axis=1,
)


def calcular_estado(prox):
  dias_restantes = (prox - hoy).days
  if dias_restantes < 0:
    return "🔴 Vencido"
  elif dias_restantes <= 5:
    return "🟡 Toca esta semana"
  else:
    return "🟢 Al día"


df_clientes["estado"] = df_clientes["proximo_servicio"].apply(calcular_estado)


# ==========================================
# 1. PANEL, ALERTAS Y RUTAS POR SECTOR
# ==========================================
if opcion == "📋 Panel, Alertas y Rutas":
  st.subheader("Tablero Operativo y Planificación de Rutas")

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("Total Clientes", len(df_clientes))
  col2.metric(
      "Vencidos", len(df_clientes[df_clientes["estado"].str.contains("Vencido")])
  )
  col3.metric(
      "Por Vencer (5 días)",
      len(df_clientes[df_clientes["estado"].str.contains("Toca")]),
  )
  col4.metric(
      "Pendientes de Cobro",
      len(df_clientes[df_clientes["estatus_pago"] == "Pendiente"]),
  )

  st.divider()

  sectores_disponibles = ["Todos"] + list(
      df_clientes["sector"].dropna().unique()
  )
  filtro_sector = st.selectbox("📍 Filtrar Ruta por Sector/Zona:", sectores_disponibles)

  if filtro_sector != "Todos":
    df_filtrado = df_clientes[df_clientes["sector"] == filtro_sector]
  else:
    df_filtrado = df_clientes

  st.dataframe(
      df_filtrado[
          [
              "id",
              "cliente",
              "sector",
              "telefono",
              "ultimo_servicio",
              "proximo_servicio",
              "plaga_tratada",
              "estatus_pago",
              "estado",
          ]
      ],
      use_container_width=True,
  )

  st.subheader("Acción Directa sobre Cliente")
  if not df_clientes.empty:
    cliente_sel = st.selectbox(
        "Seleccione cliente a gestionar:", df_clientes["cliente"].tolist()
    )
    datos_c = df_clientes[df_clientes["cliente"] == cliente_sel].iloc[0]

    c1, c2 = st.columns(2)
    with c1:
      msg = (
          f"Hola {datos_c['cliente']}, le saludamos de Fumigadora Zapa. Su"
          f" servicio de control de plagas toca el"
          f" {datos_c['proximo_servicio']}. ¿Confirmamos la visita?"
      )
      url_wa = (
          f"https://wa.me/1{datos_c['telefono']}?text=" + msg.replace(" ", "%20")
      )
      st.markdown(
          f"📱 **WhatsApp:** [Enviar Recordatorio]({url_wa})",
          unsafe_allow_html=True,
      )

    with c2:
      if st.button("🔄 Marcar Servicio Realizado Hoy"):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE clientes SET ultimo_servicio = ? WHERE id = ?",
            (hoy.strftime("%Y-%m-%d"), int(datos_c["id"])),
        )
        conn.commit()
        conn.close()
        st.success(f"¡Ciclo reiniciado para {cliente_sel} con fecha de hoy!")
        st.rerun()


# ==========================================
# 2. REGISTRO RÁPIDO (TEXTO LIBRE)
# ==========================================
elif opcion == "⚡ Registro Rápido (Texto Libre)":
  st.subheader("Asistente de Registro Rápido en Ruta")
  texto_rapido = st.text_area(
      "Detalles del servicio (Ej: Fumigé local en Gualey, cucarachas, cobré"
      " 2500):"
  )

  if st.button("Procesar y Guardar en SQLite"):
    if texto_rapido:
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO clientes (cliente, sector, telefono, ultimo_servicio, frecuencia_dias, plaga_tratada, productos_usados, estatus_pago, monto)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
          (
              "Cliente Rápido",
              "Santo Domingo",
              "8090000000",
              hoy.strftime("%Y-%m-%d"),
              30,
              texto_rapido[:40],
              "Estándar Zapa",
              "Pendiente",
              2500.0,
          ),
      )
      conn.commit()
      conn.close()
      st.success("¡Guardado exitosamente en la base de datos SQLite!")
      st.rerun()
    else:
      st.warning("Por favor escribe los detalles.")


# ==========================================
# 3. NUEVO CLIENTE DETALLADO
# ==========================================
elif opcion == "➕ Nuevo Cliente Detallado":
  st.subheader("Ficha Completa de Cliente y Tratamiento Técnico")

  with st.form("form_detallado"):
    nom = st.text_input("Nombre del Local / Cliente")
    sec = st.text_input("Sector (Ej: Gualey, Bella Vista, Luperón)")
    tel = st.text_input("Teléfono / Celular")
    ult = st.date_input("Fecha del Servicio", value=hoy)
    freq = st.selectbox("Frecuencia", [15, 30, 60, 90, 180])
    plaga = st.text_input("Plaga Tratada (Ej: Cucarachas, Mosquitos, Roedores)")
    prod = st.text_input("Productos / Químicos Aplicados y Dosis")
    monto_s = st.number_input("Monto Acordado (RD$)", value=3000.0)
    pago_s = st.selectbox("Estatus de Pago", ["Pendiente", "Pagado"])

    enviar = st.form_submit_button("Guardar Ficha en Base de Datos")
    if enviar:
      if nom and tel:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
                    INSERT INTO clientes (cliente, sector, telefono, ultimo_servicio, frecuencia_dias, plaga_tratada, productos_usados, estatus_pago, monto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                nom,
                sec,
                tel,
                ult.strftime("%Y-%m-%d"),
                freq,
                plaga,
                prod,
                pago_s,
                monto_s,
            ),
        )
        conn.commit()
        conn.close()
        st.success(f"¡Cliente {nom} registrado correctamente en SQLite!")
        st.rerun()
      else:
        st.error("Completa al menos el nombre y el teléfono.")


# ==========================================
# 4. GENERADOR DE CERTIFICADO PDF
# ==========================================
elif opcion == "📄 Generar Certificado PDF":
  st.subheader("Generación de Certificado Sanitario de Fumigación")
  if not df_clientes.empty:
    cli_cert = st.selectbox(
        "Seleccionar Cliente:", df_clientes["cliente"].tolist()
    )
    dat_c = df_clientes[df_clientes["cliente"] == cli_cert].iloc[0]

    contenido_cert = f"""
    ==================================================
                 FUMIGADORA ZAPA
          Certificado Oficial de Control de Plagas
    ==================================================
    Fecha de Emisión: {hoy}
    Cliente: {dat_c['cliente']}
    Ubicación: {dat_c['sector']}
    
    DETALLES TÉCNICOS:
    - Plaga Controlada: {dat_c['plaga_tratada']}
    - Productos Utilizados: {dat_c['productos_usados']}
    - Próximo Servicio Sugerido: {dat_c['proximo_servicio']}
    
    Este establecimiento cumple con los controles sanitarios
    requeridos para la prevención y saneamiento ambiental.
    --------------------------------------------------
    Firma Autorizada / Sello: Fumigadora Zapa
    """
    st.text_area("Certificado Generado:", contenido_cert, height=250)
    st.download_button(
        "📥 Descargar Certificado",
        data=contenido_cert,
        file_name=f"Certificado_{dat_c['cliente']}.txt",
        mime="text/plain",
    )


# ==========================================
# 5. FACTURACIÓN Y CUENTAS POR COBRAR
# ==========================================
elif opcion == "💵 Facturación y Cobros":
  st.subheader("Control Financiero y Emisión e-CF (DGII)")

  if not df_clientes.empty:
    st.dataframe(
        df_clientes[["id", "cliente", "monto", "estatus_pago"]],
        use_container_width=True,
    )

    cli_fac = st.selectbox(
        "Facturar a cliente:", df_clientes["cliente"].tolist(), key="fac"
    )
    d_fac = df_clientes[df_clientes["cliente"] == cli_fac].iloc[0]

    ncf_tipo = st.selectbox(
        "Tipo de Comprobante:",
        [
            "B01 - Crédito Fiscal",
            "B02 - Consumo",
            "E31 - e-CF Crédito Fiscal",
            "E32 - e-CF Consumo",
        ],
    )
    val_monto = st.number_input("Monto (RD$)", value=float(d_fac["monto"]))

    itbis = val_monto * 0.18
    total = val_monto + itbis

    st.write(
        f"Subtotal: RD$ {val_monto:,.2f} | ITBIS (18%): RD$ {itbis:,.2f} |"
        f" **Total: RD$ {total:,.2f}**"
    )

    if st.button("🚀 Emitir Factura Fiscal y Actualizar Cobro"):
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          "UPDATE clientes SET estatus_pago = 'Pagado' WHERE id = ?",
          (int(d_fac["id"]),),
      )
      conn.commit()
      conn.close()
      st.success(
          f"¡Factura emitida bajo {ncf_tipo}! Estatus de cobro actualizado a:"
          " Pagado en SQLite."
      )
      st.rerun()
