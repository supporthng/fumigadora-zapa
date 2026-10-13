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
# INICIALIZACIÓN DE LA BASE DE DATOS
# ==========================================
def inicializar_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  # 1. Tabla de Usuarios y Roles
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            rol TEXT NOT NULL,
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

  # Asegurar que el usuario 'admin' exista obligatoriamente (Upsert / Insert or Ignore)
  cursor.execute(
      """
        INSERT OR IGNORE INTO usuarios (usuario, rol, pin) 
        VALUES ('admin', 'Administrador', 'admin')
    """
  )
  conn.commit()

  # Datos iniciales de clientes si la tabla está vacía
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
    conn.commit()

  # Datos iniciales de productos si la tabla está vacía
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
      "SELECT rol FROM usuarios WHERE LOWER(usuario) = LOWER(?) AND pin = ?",
      (nombre_usuario.strip(), pin_ingresado.strip()),
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
  st.info("💡 **Acceso rápido:** Usuario: `admin` | Contraseña: `admin`")

  with st.form("login_form"):
    # Campo de texto libre para escribir el usuario sin depender de desplegables obsoletos
    usuario_input = st.text_input("Usuario:", value="admin")
    pin_input = st.text_input(
        "PIN / Contraseña:", type="password", value="admin"
    )
    submit_login = st.form_submit_button("Entrar al Sistema")

    if submit_login:
      rol_encontrado = verificar_usuario(usuario_input, pin_input)
      if rol_encontrado:
        st.session_state.autenticado = True
        st.session_state.usuario = usuario_input.strip()
        st.session_state.rol = rol_encontrado
        st.success(
            f"¡Bienvenido {usuario_input}! Rol asignado: {rol_encontrado}"
        )
        st.rerun()
      else:
        st.error("Usuario o contraseña incorrectos. Intente de nuevo.")
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
  st.dataframe(
      cargar_datos("usuarios")[["id", "usuario", "rol"]], use_container_width=True
  )

  with st.form("nuevo_usuario"):
    nu = st.text_input("Nombre del Usuario (Ej: Juan Pérez)")
    ro = st.selectbox("Rol del Usuario", ["Administrador", "Técnico"])
    pi = st.text_input("PIN o Contraseña", type="password")

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
        st.warning("Completa todos los campos.")
