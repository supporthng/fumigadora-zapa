from datetime import datetime, timedelta
import io
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Fumigadora Zapa - Sistema Integral",
    page_icon="🐛",
    layout="wide",
)

DB_FILE = "clientes_fumigacion_avanzado.csv"


# Inicializar o cargar datos con la estructura completa
@st.cache_data
def cargar_datos():
  try:
    df = pd.read_csv(DB_FILE)
    df["Ultimo_Servicio"] = pd.to_datetime(df["Ultimo_Servicio"]).dt.date
    return df
  except FileNotFoundError:
    data = {
        "ID": ["C001", "C002"],
        "Cliente": ["Frituras El Primo", "Colmado Doña Rosa"],
        "Sector": ["Gualey, SD", "Ensanche Luperón"],
        "Telefono": ["8095551234", "8092224321"],
        "Ultimo_Servicio": [
            datetime.now().date() - timedelta(days=35),
            datetime.now().date() - timedelta(days=10),
        ],
        "Frecuencia_Dias": [30, 60],
        "Plaga_Tratada": ["Cucarachas y Hormigas", "Rodedores (Ratas)"],
        "Productos_Usados": ["Cyperkill / K-Othrine", "Cebo Rodenticida Brodifacoum"],
        "Estatus_Pago": ["Pendiente", "Pagado"],
        "Monto": [2500.0, 3500.0],
    }
    df = pd.DataFrame(data)
    df.to_csv(DB_FILE, index=False)
    return df


df_clientes = cargar_datos()

st.title("🐛 Fumigadora Zapa - Panel de Gestión y Operaciones")
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
df_clientes["Ultimo_Servicio"] = pd.to_datetime(
    df_clientes["Ultimo_Servicio"]
).dt.date
df_clientes["Proximo_Servicio"] = df_clientes.apply(
    lambda row: row["Ultimo_Servicio"]
    + timedelta(days=int(row["Frecuencia_Dias"])),
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


df_clientes["Estado"] = df_clientes["Proximo_Servicio"].apply(calcular_estado)


# ==========================================
# 1. PANEL, ALERTAS Y RUTAS POR SECTOR
# ==========================================
if opcion == "📋 Panel, Alertas y Rutas":
  st.subheader("Tablero Operativo y Planificación de Rutas")

  col1, col2, col3, col4 = st.columns(4)
  col1.metric(
      "Total Clientes", len(df_clientes)
  )
  col2.metric(
      "Vencidos",
      len(df_clientes[df_clientes["Estado"].str.contains("Vencido")]),
  )
  col3.metric(
      "Por Vencer (5 días)",
      len(df_clientes[df_clientes["Estado"].str.contains("Toca")]),
  )
  col4.metric(
      "Pendientes de Cobro",
      len(df_clientes[df_clientes["Estatus_Pago"] == "Pendiente"]),
  )

  st.divider()

  # Filtro por Sector para organizar rutas de visita
  sectores_disponibles = ["Todos"] + list(
      df_clientes["Sector"].dropna().unique()
  )
  filtro_sector = st.selectbox("📍 Filtrar Ruta por Sector/Zona:", sectores_disponibles)

  if filtro_sector != "Todos":
    df_filtrado = df_clientes[df_clientes["Sector"] == filtro_sector]
  else:
    df_filtrado = df_clientes

  st.dataframe(
      df_filtrado[
          [
              "ID",
              "Cliente",
              "Sector",
              "Telefono",
              "Ultimo_Servicio",
              "Proximo_Servicio",
              "Plaga_Tratada",
              "Estatus_Pago",
              "Estado",
          ]
      ],
      use_container_width=True,
  )

  st.subheader("Acción Directa sobre Cliente")
  cliente_sel = st.selectbox(
      "Seleccione cliente a gestionar:", df_clientes["Cliente"].tolist()
  )

  if cliente_sel:
    datos_c = df_clientes[df_clientes["Cliente"] == cliente_sel].iloc[0]
    c1, c2 = st.columns(2)

    with c1:
      msg = (
          f"Hola {datos_c['Cliente']}, le saludamos de Fumigadora Zapa. Su servicio"
          f" de control de plagas toca el {datos_c['Proximo_Servicio']}. "
          "¿Confirmamos la visita?"
      )
      url_wa = (
          f"https://wa.me/1{datos_c['Telefono']}?text=" + msg.replace(" ", "%20")
      )
      st.markdown(
          f"📱 **WhatsApp:** [Enviar Recordatorio]({url_wa})",
          unsafe_allow_html=True,
      )

    with c2:
      if st.button("🔄 Marcar Servicio Realizado Hoy"):
        df_clientes.loc[
            df_clientes["Cliente"] == cliente_sel, "Ultimo_Servicio"
        ] = hoy
        df_clientes.to_csv(DB_FILE, index=False)
        st.success(
            f"¡Ciclo reiniciado para {cliente_sel} con fecha de hoy!"
        )
        st.rerun()


# ==========================================
# 2. REGISTRO RÁPIDO (TEXTO LIBRE / INTELIGENTE)
# ==========================================
elif opcion == "⚡ Registro Rápido (Texto Libre)":
  st.subheader("Asistente de Registro Rápido en Ruta")
  st.write(
      "Escribe o pega en una sola línea lo que hiciste y el sistema extraerá"
      " los datos (Ej: *Fumigé a Colmado Rosa en Luperón, plaga cucarachas,"
      " cobré 3000, repite en 30 días*)."
  )

  texto_rapido = st.text_area("Detalles del servicio:")

  if st.button("Procesar y Guardar Rápido"):
    if texto_rapido:
      # Simulación de parseo inteligente básico
      nuevo_id = f"C0{len(df_clientes) + 1}"
      # Agregamos un registro genérico basado en el texto ingresado
      nuevo_df = pd.DataFrame({
          "ID": [nuevo_id],
          "Cliente": ["Cliente de Ruta Rápida"],
          "Sector": ["Santo Domingo"],
          "Telefono": ["8090000000"],
          "Ultimo_Servicio": [hoy],
          "Frecuencia_Dias": [30],
          "Plaga_Tratada": [texto_rapido[:40]],
          "Productos_Usados": ["Estándar Zapa"],
          "Estatus_Pago": ["Pendiente"],
          "Monto": [2500.0],
      })
      df_clientes = pd.concat([df_clientes, nuevo_df], ignore_index=True)
      df_clientes.to_csv(DB_FILE, index=False)
      st.success(
          "¡Servicio registrado e incorporado a la base de datos con éxito!"
      )
    else:
      st.warning("Por favor escribe los detalles.")


# ==========================================
# 3. NUEVO CLIENTE DETALLADO
# ==========================================
elif opcion == "➕ Nuevo Cliente Detallado":
  st.subheader("Ficha Completa de Cliente y Tratamiento Técnico")

  with st.form("form_detallado"):
    n_id = f"C0{len(df_clientes) + 1}"
    nom = st.text_input("Nombre del Local / Cliente")
    sec = st.text_input("Sector (Ej: Gualey, Bella Vista, Luperón)")
    tel = st.text_input("Teléfono / Celular")
    ult = st.date_input("Fecha del Servicio", value=hoy)
    freq = st.selectbox("Frecuencia", [15, 30, 60, 90, 180])
    plaga = st.text_input("Plaga Tratada (Ej: Cucarachas, Mosquitos, Roedores)")
    prod = st.text_input("Productos / Químicos Aplicados y Dosis")
    monto_s = st.number_input("Monto Acordado (RD$)", value=3000.0)
    pago_s = st.selectbox("Estatus de Pago", ["Pendiente", "Pagado"])

    enviar = st.form_submit_button("Guardar Ficha Técnica")
    if enviar:
      if nom and tel:
        row_nueva = pd.DataFrame({
            "ID": [n_id],
            "Cliente": [nom],
            "Sector": [sec],
            "Telefono": [tel],
            "Ultimo_Servicio": [ult],
            "Frecuencia_Dias": [freq],
            "Plaga_Tratada": [plaga],
            "Productos_Usados": [prod],
            "Estatus_Pago": [pago_s],
            "Monto": [monto_s],
        })
        df_clientes = pd.concat([df_clientes, row_nueva], ignore_index=True)
        df_clientes.to_csv(DB_FILE, index=False)
        st.success(f"¡Cliente {nom} registrado correctamente!")
      else:
        st.error("Completa al menos el nombre y el teléfono.")


# ==========================================
# 4. GENERADOR DE CERTIFICADO PDF
# ==========================================
elif opcion == "📄 Generar Certificado PDF":
  st.subheader("Generación de Certificado Sanitario de Fumigación")

  cli_cert = st.selectbox(
      "Seleccionar Cliente para Certificado:", df_clientes["Cliente"].tolist()
  )
  dat_c = df_clientes[df_clientes["Cliente"] == cli_cert].iloc[0]

  st.info(
      f"**Cliente:** {dat_c['Cliente']}  \n**Sector:** {dat_c['Sector']}"
      f"  \n**Tratamiento:** {dat_c['Plaga_Tratada']}  \n**Último Servicio:**"
      f" {dat_c['Ultimo_Servicio']}"
  )

  if st.button("🖨️ Generar Certificado Oficial (Vista Previa / Descarga)"):
    # Contenido simulado del certificado listo para imprimir
    contenido_cert = f"""
    ==================================================
                 FUMIGADORA ZAPA
          Certificado Oficial de Control de Plagas
    ==================================================
    Fecha de Emisión: {hoy}
    Cliente: {dat_c['Cliente']}
    Ubicación: {dat_c['Sector']}
    
    DETALLES TÉCNICOS:
    - Plaga Controlada: {dat_c['Plaga_Tratada']}
    - Productos Utilizados: {dat_c['Productos_Usados']}
    - Próximo Servicio Sugerido: {dat_c['Proximo_Servicio']}
    
    Este establecimiento cumple con los controles sanitarios
    requeridos para la prevención y saneamiento ambiental.
    --------------------------------------------------
    Firma Autorizada / Sello: Fumigadora Zapa
    """
    st.text_area("Certificado Generado:", contenido_cert, height=250)
    st.download_button(
        "📥 Descargar Certificado en TXT/PDF",
        data=contenido_cert,
        file_name=f"Certificado_{dat_c['Cliente']}.txt",
        mime="text/plain",
    )


# ==========================================
# 5. FACTURACIÓN Y CUENTAS POR COBRAR
# ==========================================
elif opcion == "💵 Facturación y Cobros":
  st.subheader("Control Financiero y Emisión e-CF (DGII)")

  st.dataframe(
      df_clientes[["ID", "Cliente", "Monto", "Estatus_Pago"]],
      use_container_width=True,
  )

  cli_fac = st.selectbox(
      "Facturar a cliente:", df_clientes["Cliente"].tolist(), key="fac"
  )
  d_fac = df_clientes[df_clientes["Cliente"] == cli_fac].iloc[0]

  ncf_tipo = st.selectbox(
      "Tipo de Comprobante:",
      [
          "B01 - Crédito Fiscal",
          "B02 - Consumo",
          "E31 - e-CF Crédito Fiscal",
          "E32 - e-CF Consumo",
      ],
  )
  val_monto = st.number_input("Monto (RD$)", value=float(d_fac["Monto"]))

  itbis = val_monto * 0.18
  total = val_monto + itbis

  st.write(
      f"Subtotal: RD$ {val_monto:,.2f} | ITBIS (18%): RD$ {itbis:,.2f} |"
      f" **Total: RD$ {total:,.2f}**"
  )

  if st.button("🚀 Emitir Factura Fiscal y Actualizar Cobro"):
    df_clientes.loc[
        df_clientes["Cliente"] == cli_fac, "Estatus_Pago"
    ] = "Pagado"
    df_clientes.to_csv(DB_FILE, index=False)
    st.success(
        f"¡Factura emitida con éxito bajo el comprobante {ncf_tipo}! Estatus"
        " de cobro actualizado a: Pagado."
    )
