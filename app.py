from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Fumigadora Zapa | ERP System", page_icon="🐛", layout="wide"
)

DB_NAME = "fumigadora_zapa_erp.db"


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
# INICIALIZACIÓN DE LA BASE DE DATOS RELACIONAL
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
            precio REAL
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
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicios (
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

  conn.commit()

  # Insertar usuario admin por defecto
  cursor.execute(
      """
        INSERT OR IGNORE INTO usuarios (usuario, rol, pin) 
        VALUES ('admin', 'Administrador', 'admin')
    """
  )
  conn.commit()

  # Datos iniciales si está vacío
  cursor.execute("SELECT COUNT(*) FROM clientes")
  if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO clientes (cliente, sector, telefono) VALUES (?, ?, ?)",
        ("Frituras El Primo", "Gualey, SD", "8095551234"),
    )
    cliente_id = cursor.lastrowid

    cursor.execute(
        """
            INSERT INTO inmuebles (cliente_id, tipo_inmueble, detalle_ubicacion, contacto_nombre, contacto_telefono, frecuencia_dias, ultimo_servicio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cliente_id,
            "Casa",
            "Casa #14, Manzana B",
            "Ramón Pérez",
            "8095551234",
            30,
            (datetime.now().date() - timedelta(days=35)).strftime("%Y-%m-%d"),
        ),
    )
    conn.commit()

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
# CONTROL DE SESIÓN Y LOGIN MODERNO
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
  _, col_centro, _ = st.columns([1, 1.2, 1])
  with col_centro:
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.container():
      st.markdown(
          "<div style='text-align: center;'>"
          "<h2 style='color: #0f172a; margin-bottom: 0px;'>🐛 Fumigadora"
          " Zapa</h2>"
          "<p style='color: #64748b; font-size: 14px;'>Sistema Integral de"
          " Gestión y Operaciones</p>"
          "</div>",
          unsafe_allow_html=True,
      )
      st.markdown("<br>", unsafe_allow_html=True)
      with st.form("login_moderno"):
        st.markdown(
            "<p style='font-weight: 600; color: #334155; margin-bottom:"
            " 5px;'>Usuario</p>",
            unsafe_allow_html=True,
        )
        usuario_input = st.text_input(
            "Usuario", value="admin", label_visibility="collapsed"
        )
        st.markdown(
            "<p style='font-weight: 600; color: #334155; margin-bottom:"
            " 5px; margin-top: 10px;'>Contraseña o PIN</p>",
            unsafe_allow_html=True,
        )
        pin_input = st.text_input(
            "PIN", type="password", value="admin", label_visibility="collapsed"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        submit_login = st.form_submit_button(
            "Iniciar Sesión", use_container_width=True
        )

        if submit_login:
          rol_encontrado = verificar_usuario(usuario_input, pin_input)
          if rol_encontrado:
            st.session_state.autenticado = True
            st.session_state.usuario = usuario_input.strip()
            st.session_state.rol = rol_encontrado
            st.rerun()
          else:
            st.error("Credenciales incorrectas. Verifique usuario y contraseña.")

      st.markdown(
          "<div style='text-align: center; margin-top: 20px;'><p"
          " style='color: #94a3b8; font-size: 12px;'>Acceso por defecto —"
          " Usuario: <b>admin</b> | Contraseña: <b>admin</b></p></div>",
          unsafe_allow_html=True,
      )
  st.stop()


# ==========================================
# APLICACIÓN PRINCIPAL (POST-LOGIN)
# ==========================================
def cargar_datos(sql_o_tabla):
  conn = sqlite3.connect(DB_NAME)
  # Si le pasamos solo el nombre de una tabla, armamos el SELECT automáticamente
  if (
      " " not in sql_o_tabla.strip()
      and ";" not in sql_o_tabla
      and "SELECT" not in sql_o_tabla.upper()
  ):
    query = f"SELECT * FROM {sql_o_tabla}"
  else:
    query = sql_o_tabla
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
df_clientes_maestra = cargar_datos("clientes")
df_productos = cargar_datos("productos")
df_facturas = cargar_datos("facturas")
df_usuarios = cargar_datos("usuarios")

st.sidebar.markdown(
    "<h3 style='color: #0f172a; margin-bottom: 0;'>Fumigadora Zapa</h3>"
    "<p style='color: #64748b; font-size: 12px;'>Panel de Control</p>",
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
    "<p style='font-size: 12px; font-weight: bold; color: #64748b;'>NAVEGACIÓN</p>",
    unsafe_allow_html=True,
)

modulos_disponibles = [
    "📋 Panel, Alertas y Rutas",
    "➕ Registrar Localidad / Inmueble",
    "📅 Gestión de Servicios (Agenda)",
    "📄 Certificados Sanitarios",
]
if st.session_state.rol == "Administrador":
  modulos_disponibles.extend([
      "📦 Inventario de Químicos",
      "💵 Facturación y Comprobantes (DGII)",
      "👥 Gestión de Usuarios",
  ])

opcion = st.sidebar.radio(
    "Seleccione sección:", modulos_disponibles, label_visibility="collapsed"
)

hoy = datetime.now().date()
if not df_inmuebles.empty:
  df_inmuebles["ultimo_servicio"] = pd.to_datetime(
      df_inmuebles["ultimo_servicio"]
  ).dt.date
  df_inmuebles["proximo_servicio"] = df_inmuebles.apply(
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


  df_inmuebles["estado"] = df_inmuebles["proximo_servicio"].apply(
      calcular_estado
  )


# ==========================================
# 1. PANEL, ALERTAS Y RUTAS
# ==========================================
if opcion == "📋 Panel, Alertas y Rutas":
  st.title("Tablero Operativo por Localidades")
  st.write("Control de frecuencias y alertas vinculadas a cada inmueble.")

  if not df_inmuebles.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Localidades", len(df_inmuebles))
    col2.metric(
        "Servicios Vencidos",
        len(df_inmuebles[df_inmuebles["estado"].str.contains("Vencido")]),
    )
    col3.metric(
        "Por Vencer (5 días)",
        len(df_inmuebles[df_inmuebles["estado"].str.contains("Toca")]),
    )

    st.divider()
    sector_sel = st.selectbox(
        "📍 Filtrar por Sector:",
        ["Todos"] + list(df_inmuebles["sector"].dropna().unique()),
    )
    df_f = (
        df_inmuebles
        if sector_sel == "Todos"
        else df_inmuebles[df_inmuebles["sector"] == sector_sel]
    )

    st.dataframe(
        df_f[
            [
                "inmueble_id",
                "cliente",
                "sector",
                "tipo_inmueble",
                "detalle_ubicacion",
                "contacto_nombre",
                "contacto_telefono",
                "ultimo_servicio",
                "proximo_servicio",
                "estado",
            ]
        ],
        use_container_width=True,
    )

    st.subheader("Acción Directa sobre Localidad (ID Único)")
    inmueble_sel_id = st.selectbox(
        "Seleccione ID de Localidad:", df_inmuebles["inmueble_id"].tolist()
    )
    dat_i = df_inmuebles[
        df_inmuebles["inmueble_id"] == inmueble_sel_id
    ].iloc[0]

    st.info(
        f"**Cliente:** {dat_i['cliente']} | **Localidad:**"
        f" {dat_i['tipo_inmueble']} ({dat_i['detalle_ubicacion']}) |"
        f" **Contacto:** {dat_i['contacto_nombre']} ({dat_i['contacto_telefono']})"
    )

    c1, c2 = st.columns(2)
    with c1:
      msg = (
          f"Hola {dat_i['contacto_nombre']}, le saludamos de Fumigadora Zapa."
          f" Su servicio para {dat_i['tipo_inmueble']} ({dat_i['detalle_ubicacion']})"
          f" toca el {dat_i['proximo_servicio']}. ¿Confirmamos la visita?"
      )
      url_wa = (
          f"https://wa.me/1{dat_i['contacto_telefono']}?text="
          + msg.replace(" ", "%20")
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
            "UPDATE inmuebles SET ultimo_servicio = ? WHERE id = ?",
            (hoy.strftime("%Y-%m-%d"), int(dat_i["inmueble_id"])),
        )
        conn.commit()
        conn.close()
        st.success(
            f"¡Ciclo reiniciado para la localidad ID {inmueble_sel_id} con fecha"
            " de hoy!"
        )
        st.rerun()
  else:
    st.info("No hay localidades registradas en la base de datos.")


# ==========================================
# 2. REGISTRAR LOCALIDAD / INMUEBLE
# ==========================================
elif opcion == "➕ Registrar Localidad / Inmueble":
  st.title("Gestión de Clientes y Nuevas Localidades")
  st.write(
      "Asocia múltiples localidades a un cliente existente o crea uno nuevo."
  )

  with st.form("form_reg_localidad"):
    st.subheader("1. Seleccionar o Crear Cliente")
    modo_cliente = st.radio(
        "Acción:", ["Cliente Existente", "Registrar Cliente Nuevo"]
    )

    if modo_cliente == "Cliente Existente" and not df_clientes_maestra.empty:
      cliente_existente = st.selectbox(
          "Seleccione Cliente:", df_clientes_maestra["cliente"].tolist()
      )
      cliente_id = int(
          df_clientes_maestra[
              df_clientes_maestra["cliente"] == cliente_existente
          ]["id"].values[0]
      )
    else:
      nombre_nuevo = st.text_input("Nombre del Nuevo Cliente / Empresa")
      sector_nuevo = st.text_input("Sector Principal")
      telefono_nuevo = st.text_input("Teléfono Principal del Cliente")
      cliente_id = None

    st.markdown("---")
    st.subheader("2. Detalle de la Localidad a Registrar")
    tipo_inmueble = st.selectbox(
        "Tipo de Inmueble:",
        [
            "Casa",
            "Oficina / Edificio",
            "Almacén / Nave",
            "Cocina Industrial",
            "Torre / Apartamento",
        ],
    )
    detalle_ubicacion = st.text_input(
        "Detalle de Ubicación (Ej: Casa #14 / Local 402 / Apto 5B)"
    )
    contacto_nombre = st.text_input("Persona de Contacto en esta Localidad")
    contacto_telefono = st.text_input("Teléfono Directo de Contacto")
    frecuencia = st.selectbox(
        "Frecuencia Base (Días)",
        [7, 15, 30, 60, 90, 180],
        format_func=lambda x: (
            "Semanal (7 días)"
            if x == 7
            else (
                "Quincenal (15 días)"
                if x == 15
                else (
                    "Mensual (30 días)"
                    if x == 30
                    else (
                        f"Cada {int(x/30)} meses"
                        if x >= 60
                        else f"Cada {x} días"
                    )
                )
            )
        ),
    )
    ultimo_serv = st.date_input(
        "Fecha del Último Servicio (o Inicio)", value=hoy
    )

    guardar_localidad = st.form_submit_button(
        "Guardar Localidad con ID Único"
    )

    if guardar_localidad:
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()

      if modo_cliente == "Registrar Cliente Nuevo":
        if nombre_nuevo and contacto_telefono:
          cursor.execute(
              "INSERT INTO clientes (cliente, sector, telefono) VALUES (?, ?, ?)",
              (nombre_nuevo, sector_nuevo, telefono_nuevo),
          )
          cliente_id = cursor.lastrowid
        else:
          st.error("Por favor completa los datos del nuevo cliente.")
          st.stop()

      if cliente_id and detalle_ubicacion and contacto_nombre:
        cursor.execute(
            """
                INSERT INTO inmuebles (cliente_id, tipo_inmueble, detalle_ubicacion, contacto_nombre, contacto_telefono, frecuencia_dias, ultimo_servicio)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                tipo_inmueble,
                detalle_ubicacion,
                contacto_nombre,
                contacto_telefono,
                frecuencia,
                ultimo_serv.strftime("%Y-%m-%d"),
            ),
        )
        conn.commit()
        conn.close()
        st.success(
            "¡Nueva localidad registrada con éxito! (ID Único asignado)."
        )
        st.rerun()
      else:
        st.warning("Completa los campos obligatorios de la localidad.")


# ==========================================
# 3. GESTIÓN DE SERVICIOS (AGENDA Y RECURRENCIA)
# ==========================================
elif opcion == "📅 Gestión de Servicios (Agenda)":
  st.title("Gestión de Servicios y Agenda de Campo")
  st.write(
      "Agenda trabajos programando su recurrencia exacta (Semanal, Quincenal,"
      " Mensual, etc.)."
  )

  with st.form("form_nuevo_servicio"):
    st.subheader("Agendar Trabajo por Localidad (ID)")

    if not df_inmuebles.empty:
      opciones_inmuebles = df_inmuebles.apply(
          lambda row: (
              f"Localidad ID #{row['inmueble_id']} - {row['cliente']} |"
              f" {row['tipo_inmueble']}: {row['detalle_ubicacion']}"
          ),
          axis=1,
      ).tolist()
      inmueble_seleccionado_str = st.selectbox(
          "Seleccione Localidad:", opciones_inmuebles
      )
      inmueble_id_sel = int(
          inmueble_seleccionado_str.split(" - ")[0].replace(
              "Localidad ID #", ""
          )
      )
    else:
      inmueble_id_sel = None
      st.warning("Primero debes registrar al menos una localidad.")

    fecha_servicio = st.date_input("Fecha Programada del Servicio:", value=hoy)
    recurrencia_servicio = st.selectbox(
        "Recurrencia del Servicio:",
        [
            "Semanal",
            "Quincenal",
            "Mensual",
            "Cada 2 meses",
            "Cada 3 meses",
            "Cada 6 meses",
        ],
    )
    trabajo_realizar = st.selectbox(
        "Trabajo o Servicio a Realizar:",
        [
            "Fumigación General (Insectos)",
            "Control de Roedores (Ratas/Ratones)",
            "Desinfección y Saneamiento Ambiental",
            "Tratamiento Preventivo Especial",
            "Inspección y Fumigación Comercial",
        ],
    )

    lista_tecnicos = (
        df_usuarios["usuario"].tolist() if not df_usuarios.empty else ["admin"]
    )
    tecnico_asignado = st.selectbox("Técnico Asignado:", lista_tecnicos)

    guardar_servicio = st.form_submit_button("Agendar Trabajo en Agenda")

    if guardar_servicio and inmueble_id_sel:
      dias_map = {
          "Semanal": 7,
          "Quincenal": 15,
          "Mensual": 30,
          "Cada 2 meses": 60,
          "Cada 3 meses": 90,
          "Cada 6 meses": 180,
      }
      dias_frecuencia = dias_map.get(recurrencia_servicio, 30)

      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO servicios (inmueble_id, fecha_servicio, recurrencia, trabajo, tecnico_asignado, estado)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
          (
              inmueble_id_sel,
              fecha_servicio.strftime("%Y-%m-%d"),
              recurrencia_servicio,
              trabajo_realizar,
              tecnico_asignado,
              "Programado",
          ),
      )
      cursor.execute(
          "UPDATE inmuebles SET frecuencia_dias = ? WHERE id = ?",
          (dias_frecuencia, inmueble_id_sel),
      )
      conn.commit()
      conn.close()
      st.success(
          f"¡Servicio agendado con éxito para la Localidad ID #{inmueble_id_sel}"
          f" con recurrencia **{recurrencia_servicio}**!"
      )
      st.rerun()

  st.divider()
  st.subheader("Historial y Agenda de Servicios Registrados")

  df_servicios_actual = cargar_datos("""
        SELECT s.id as servicio_id, s.inmueble_id, c.cliente, i.tipo_inmueble, i.detalle_ubicacion, 
               s.fecha_servicio, s.recurrencia, s.trabajo, s.tecnico_asignado, s.estado
        FROM servicios s
        JOIN inmuebles i ON s.inmueble_id = i.id
        JOIN clientes c ON i.cliente_id = c.id
    """)

  if not df_servicios_actual.empty:
    st.dataframe(df_servicios_actual, use_container_width=True)
  else:
    st.info("No hay servicios agendados en la base de datos.")


# ==========================================
# 4. CERTIFICADOS SANITARIOS
# ==========================================
elif opcion == "📄 Certificados Sanitarios":
  st.title("Certificados Sanitarios por Localidad")
  st.write("Emisión de constancias oficiales para ubicaciones específicas.")

  if not df_inmuebles.empty:
    opciones_cert = df_inmuebles.apply(
        lambda row: (
            f"Localidad ID #{row['inmueble_id']} - {row['cliente']} |"
            f" {row['tipo_inmueble']}: {row['detalle_ubicacion']}"
        ),
        axis=1,
    ).tolist()
    cert_sel_str = st.selectbox("Seleccionar Localidad:", opciones_cert)
    inmueble_id_cert = int(
        cert_sel_str.split(" - ")[0].replace("Localidad ID #", "")
    )

    dat_c = df_inmuebles[
        df_inmuebles["inmueble_id"] == inmueble_id_cert
    ].iloc[0]

    cert_texto = f"""
    ==================================================
                 FUMIGADORA ZAPA
          Certificado Oficial de Control de Plagas
    ==================================================
    Localidad ID: #{dat_c['inmueble_id']}
    Cliente Principal: {dat_c['cliente']}
    Ubicación: {dat_c['tipo_inmueble']} - {dat_c['detalle_ubicacion']} ({dat_c['sector']})
    Contacto en Sitio: {dat_c['contacto_nombre']} ({dat_c['contacto_telefono']})
    
    DETALLES TÉCNICOS:
    - Fecha de Emisión: {hoy}
    - Próximo Servicio Programado: {dat_c['proximo_servicio']}
    
    Establecimiento verificado bajo normas de salubridad.
    --------------------------------------------------
    Firma Autorizada / Sello: Fumigadora Zapa
    """
    st.text_area("Vista Previa del Certificado:", cert_texto, height=240)
    st.download_button(
        "📥 Descargar Certificado",
        data=cert_texto,
        file_name=f"Certificado_Localidad_{dat_c['inmueble_id']}.txt",
        mime="text/plain",
    )
  else:
    st.info("No hay localidades disponibles para generar certificados.")


# ==========================================
# 5. INVENTARIO DE QUÍMICOS (Solo Admin)
# ==========================================
elif opcion == "📦 Inventario de Químicos":
  st.title("Inventario de Químicos")
  st.write("Control de stock, insumos y materiales.")
  st.dataframe(df_productos, use_container_width=True)

  with st.form("nuevo_prod"):
    st.subheader("Registrar Nuevo Insumo")
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
# 6. FACTURACIÓN Y COMPROBANTES DGII (Solo Admin)
# ==========================================
elif opcion == "💵 Facturación y Comprobantes (DGII)":
  st.title("Módulo de Facturación y Comprobantes Fiscales")
  st.write("Emisión de facturas y control de NCF / e-CF.")

  clientes_lista = (
      df_inmuebles["cliente"].unique().tolist()
      if not df_inmuebles.empty
      else ["Cliente General"]
  )

  with st.form("form_factura"):
    cli_fac = st.selectbox("Cliente a Facturar:", clientes_lista)
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
  df_facturas_actual = cargar_datos("facturas")
  if not df_facturas_actual.empty:
    st.dataframe(df_facturas_actual, use_container_width=True)
  else:
    st.info("No hay facturas registradas todavía.")


# ==========================================
# 7. GESTIÓN DE USUARIOS (Solo Admin)
# ==========================================
elif opcion == "👥 Gestión de Usuarios":
  st.title("Gestión de Usuarios y Accesos")
  st.write("Administración de roles, permisos y credenciales.")
  st.dataframe(
      cargar_datos("SELECT id, usuario, rol FROM usuarios"),
      use_container_width=True,
  )

  with st.form("nuevo_usuario"):
    st.subheader("Crear Nuevo Usuario")
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
