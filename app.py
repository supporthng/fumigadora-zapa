import streamlit as datetime
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Fumigación - Fumigadora Zapa",
    page_icon="🐛",
    layout="wide",
)

# Archivo local simulado como base de datos
DB_FILE = "clientes_fumigacion.csv"


# Función para cargar o inicializar la base de datos
@st.cache_data
def cargar_datos():
  try:
    df = pd.read_csv(DB_FILE)
    df["Ultimo_Servicio"] = pd.to_datetime(df["Ultimo_Servicio"]).dt.date
    return df
  except FileNotFoundError:
    # Datos de ejemplo iniciales (puedes modificarlos o borrarlos)
    data = {
        "ID": ["C001", "C002", "C003"],
        "Cliente": [
            "Frituras El Primo",
            "Colmado Doña Rosa",
            "Plaza Comercial Bella Vista",
        ],
        "Sector": ["Gualey, SD", "Ensanche Luperón", "Bella Vista"],
        "Telefono": ["8095551234", "8092224321", "8098889999"],
        "Ultimo_Servicio": [
            datetime.now().date() - timedelta(days=35),
            datetime.now().date() - timedelta(days=10),
            datetime.now().date() - timedelta(days=85),
        ],
        "Frecuencia_Dias": [30, 30, 90],  # 30 días, 60 días, etc.
    }
    df = pd.DataFrame(data)
    df.to_csv(DB_FILE, index=False)
    return df


df_clientes = cargar_datos()

st.title("🐛 Fumigadora Zapa - Control de Clientes y Frecuencias")
st.sidebar.image(
    "https://img.icons8.com/color/96/pest-control.png", width=80
)  # Ícono ilustrativo
st.sidebar.header("Menú de Navegación")
opcion = st.sidebar.radio(
    "Seleccione una opción:",
    [
        "📋 Panel y Alertas",
        "➕ Registrar Cliente / Servicio",
        "💵 Módulo de Facturación (DGII)",
    ],
)

# Recalcular dinámicamente el próximo servicio y el estado
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
# SECCIÓN 1: PANEL Y ALERTAS
# ==========================================
if opcion == "📋 Panel y Alertas":
  st.subheader("Resumen de Clientes y Estado de Frecuencia")

  # Métricas rápidas
  col1, col2, col3 = st.columns(3)
  vencidos = len(df_clientes[df_clientes["Estado"].str.contains("Vencido")])
  por_vencer = len(
      df_clientes[df_clientes["Estado"].str.contains("Toca esta semana")]
  )
  total_clientes = len(df_clientes)

  col1.metric("Total Clientes", total_clientes)
  col2.metric("Servicios Vencidos", vencidos, delta_color="inverse")
  col3.metric("Próximos (Esta Semana)", por_vencer)

  st.divider()

  # Filtro por estado
  filtro_estado = st.selectbox(
      "Filtrar por estado:", ["Todos", "🔴 Vencido", "🟡 Toca esta semana", "🟢 Al día"]
  )
  if filtro_estado != "Todos":
    df_mostrar = df_clientes[df_clientes["Estado"] == filtro_estado]
  else:
    df_mostrar = df_clientes

  # Mostrar tabla interactiva
  st.dataframe(
      df_mostrar[
          [
              "ID",
              "Cliente",
              "Sector",
              "Telefono",
              "Ultimo_Servicio",
              "Frecuencia_Dias",
              "Proximo_Servicio",
              "Estado",
          ]
      ],
      use_container_width=True,
  )

  st.subheader("Acciones Rápidas (Recordatorios y Actualización)")
  cliente_seleccionado = st.selectbox(
      "Seleccione un cliente para gestionar:", df_clientes["Cliente"].tolist()
  )

  if cliente_seleccionado:
    datos_c = df_clientes[df_clientes["Cliente"] == cliente_seleccionado].iloc[
        0
    ]

    c1, c2 = st.columns(2)
    with c1:
      # Enlace directo a WhatsApp con mensaje prearmado
      mensaje_wa = (
          f"Hola {datos_c['Cliente']}, le saludamos de Fumigadora Zapa. "
          f"Le recordamos que su servicio periódico de control de plagas está programado para la fecha {datos_c['Proximo_Servicio']}. "
          "¿Coordinamos la visita?"
      )
      link_wa = (
          f"https://wa.me/1{datos_c['Telefono']}?text="
          + mensaje_wa.replace(" ", "%20")
      )
      st.markdown(
          f"📱 **WhatsApp:** [Enviar Recordatorio]({link_wa})",
          unsafe_allow_html=True,
      )

    with c2:
      # Botón para actualizar el último servicio a la fecha de hoy (renovar ciclo)
      if st.button("🔄 Marcar Servicio Realizado Hoy"):
        df_clientes.loc[
            df_clientes["Cliente"] == cliente_seleccionado, "Ultimo_Servicio"
        ] = hoy
        df_clientes.to_csv(DB_FILE, index=False)
        st.success(
            f"¡Servicio actualizado para {cliente_seleccionado}! Nuevo ciclo"
            " iniciado."
        )
        st.rerun()

# ==========================================
# SECCIÓN 2: REGISTRAR CLIENTE / SERVICIO
# ==========================================
elif opcion == "➕ Registrar Cliente / Servicio":
  st.subheader("Agregar Nuevo Cliente a la Base de Datos")

  with st.form("form_nuevo_cliente"):
    nuevo_id = f"C0{len(df_clientes) + 1}"
    nombre = st.text_input("Nombre del Cliente / Local")
    sector = st.text_input("Sector / Dirección (Ej: Gualey, SD)")
    telefono = st.text_input("Teléfono / WhatsApp (Ej: 8095551234)")
    ultimo_serv = st.date_input("Fecha del Último Servicio", value=hoy)
    frecuencia = st.selectbox(
        "Frecuencia de Fumigación",
        options=[15, 30, 60, 90, 180],
        format_func=lambda x: (
            f"Cada {x} días ({int(x/30)} meses)"
            if x >= 30
            else f"Cada {x} días"
        ),
    )

    submit = st.form_submit_button("Guardar Cliente")

    if submit:
      if nombre and telefono:
        nuevo_registro = pd.DataFrame({
            "ID": [nuevo_id],
            "Cliente": [nombre],
            "Sector": [sector],
            "Telefono": [telefono],
            "Ultimo_Servicio": [ultimo_serv],
            "Frecuencia_Dias": [frecuencia],
        })
        df_actualizado = pd.concat([df_clientes, nuevo_registro], ignore_index=True)
        df_actualizado.to_csv(DB_FILE, index=False)
        st.success(f"¡Cliente {nombre} registrado exitosamente!")
      else:
        st.error("Por favor completa al menos el nombre y el teléfono.")

# ==========================================
# SECCIÓN 3: MÓDULO DE FACTURACIÓN (DGII)
# ==========================================
elif opcion == "💵 Módulo de Facturación (DGII)":
  st.subheader("Emisión Rápida de Factura / e-CF Simulado")

  cliente_factura = st.selectbox(
      "Seleccionar Cliente para Facturar:", df_clientes["Cliente"].tolist()
  )
  datos_f = df_clientes[df_clientes["Cliente"] == cliente_factura].iloc[0]

  st.write(f"**Sector:** {datos_f['Sector']}")
  st.write(f"**Teléfono:** {datos_f['Telefono']}")

  st.divider()

  tipo_ncf = st.selectbox(
      "Tipo de Comprobante Fiscal (NCF / e-CF):",
      [
          "B01 - Factura de Crédito Fiscal",
          "B02 - Factura de Consumo",
          "E31 - e-CF Factura de Crédito Fiscal Electrónica",
          "E32 - e-CF Factura de Consumo Electrónica",
      ],
  )

  concepto = st.text_input(
      "Concepto del Servicio",
      value="Servicio periódico de control de plagas y fumigación",
  )
  monto = st.number_input(
      "Monto del Servicio (RD$)", min_value=0.0, value=2500.0, step=500.0
  )

  # Cálculo impositivo básico en RD (18% ITBIS)
  itbis = monto * 0.18
  total_pagar = monto + itbis

  st.info(
      f"**Subtotal:** RD$ {monto:,.2f} | **ITBIS (18%):** RD$ {itbis:,.2f} |"
      f" **Total a Pagar:** RD$ {total_pagar:,.2f}"
  )

  if st.button("🚀 Generar Factura y Transmitir (Simulación DGII)"):
    st.success(f"¡Factura emitida correctamente para {cliente_factura}!")
    st.markdown(
        f"**Comprobante:** {tipo_ncf}  \n**Monto Total:** RD$ {total_pagar:,.2f}"
        "  \n*Estado:* Autorizado y listo para enviar por correo o WhatsApp al"
        " cliente."
    )
