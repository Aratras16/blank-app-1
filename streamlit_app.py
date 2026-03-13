import streamlit as st
import pandas as pd
import io
from datetime import date
import openpyxl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
# =========================
# Configuración de página
# =========================
st.set_page_config(page_title="Cotizador UX/UI Pro", page_icon="🧮", layout="wide")

st.title("🧮 Cotizador de Servicios UX/UI")
st.caption("Crea cotizaciones con rangos de precio (Mínimo vs Máximo).")

# =========================
# Catálogo Estructurado
# =========================
CATALOGO = {
    "DISEÑADOR UX/UI": {
        "Full": [127500, 124500],
        "Medio Tiempo": [76500, 74700]
    },
    "PRODUCT DESIGNER": {
        "Full": [132500, 129000],
        "Medio Tiempo": [79500, 77400]
    },
    "SERVICE DESIGNER": {
        "Full": [146500, 145000],
        "Medio Tiempo": [87900, 87000]
    },
    "CUSTOMER SUCCESS": {
        "Full": [165000, 163000],
        "Medio Tiempo": [99000, 97800],
        "Medio Tiempo 30%": [49500, 48900]
    }
}

# =========================
# Estado inicial (Session State)
# =========================
# Se unificaron los nombres de columnas para que coincidan en todo el flujo
if "items_df" not in st.session_state:
    st.session_state.items_df = pd.DataFrame(
        columns=["Rol", "Cantidad", "Meses", "Precio Mín", "Precio Máx", "Subtotal Mín", "Subtotal Máx"]
    )

if "datos" not in st.session_state:
    st.session_state.datos = {
        "fecha": date.today(),
        "cliente": "",
        "proyecto": "",
        "descripcion": "",
        "tipo_cliente": "Interno",
        "contacto": "",
        "correo":"",
        "inicio": date.today(),
        "fin": date.today(),
        "entregables": "",
        "duracion":"",
        "observaciones":""
    }

def recalcular(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # Asegurar que los tipos de datos sean correctos para operaciones matemáticas
    df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0)
    df["Meses"] = pd.to_numeric(df["Meses"], errors="coerce").fillna(0)
    df["Precio Mín"] = pd.to_numeric(df["Precio Mín"], errors="coerce").fillna(0)
    df["Precio Máx"] = pd.to_numeric(df["Precio Máx"], errors="coerce").fillna(0)
    
    df["Subtotal Mín"] = (df["Cantidad"] * df["Meses"] * df["Precio Mín"]).round(2)
    df["Subtotal Máx"] = (df["Cantidad"] * df["Meses"] * df["Precio Máx"]).round(2)
    return df

# =========================
# 1) Datos generales
# =========================
st.subheader("Datos generales")
fecha = st.date_input("Fecha de cotización", value=st.session_state.datos["fecha"])
col1, col2 = st.columns([1, 1])

with col1:
    cliente = st.text_input("Cliente", value=st.session_state.datos["cliente"], placeholder="Ej. UPAX S.A. de C.V.")
    contacto = st.text_input("Telefono de contacto", value = st.session_state.datos["contacto"],placeholder = "+00 0000 0000")
    fecha_inicio = st.date_input("Fecha de inicio del Proyecto",value = st.session_state.datos["inicio"])

with col2:
    opciones_tipo = ["Interno", "Externo"]
    idx_tipo = opciones_tipo.index(st.session_state.datos["tipo_cliente"])
    tipo_cliente = st.selectbox("Tipo de Cliente", options=opciones_tipo, index=idx_tipo)
    correo = st.text_input("Correo electrónico",value = st.session_state.datos["correo"],placeholder = "cliente@email.com")
    fecha_fin = st.date_input("Fecha de finalización del Proyecto",value = st.session_state.datos["fin"])

proyecto = st.text_input("Nombre del Proyecto", value=st.session_state.datos["proyecto"], placeholder="Ej. Rediseño app móvil")
descripcion = st.text_area("Descripción del proyecto", value=st.session_state.datos["descripcion"], placeholder="Objetivo")
entregables = st.text_area("Entregables del proyecto", value=st.session_state.datos["entregables"], placeholder="Ejemplos de entregables ")
duracion = st.text_area("Duración Máxima", value = st.session_state.datos["duracion"])
observaciones = st.text_area("Observaciones", value = st.session_state.datos["observaciones"])
# Actualizar estado de datos
st.session_state.datos.update({
    "fecha": fecha,
    "cliente": cliente,
    "proyecto": proyecto,
    "descripcion": descripcion,
    "tipo_cliente": tipo_cliente,
    "contacto" :contacto,
    "correo":correo,
    "inicio":fecha_inicio,
    "fin":fecha_fin,
    "entregables": entregables,
    "duracion":duracion,
    "observaciones":observaciones
})
st.divider()

# =========================
# 2) Agregar recursos (Rango Mín/Máx)
# =========================
st.subheader("Agregar recursos")

colA, colB, colC = st.columns([1.5, 1, 1])

with colA:
    rol_sel = st.selectbox("Selecciona el Rol", options=list(CATALOGO.keys()))
    # El radio se actualiza según el rol seleccionado
    opciones_dedicacion = list(CATALOGO[rol_sel].keys())
    tiempo_sel = st.radio("Dedicación", options=opciones_dedicacion, horizontal=True)

# Extraer precios del catálogo (Máx es el índice 0, Mín es el índice 1 según tu CATALOGO)
p_max_cat = CATALOGO[rol_sel][tiempo_sel][0]
p_min_cat = CATALOGO[rol_sel][tiempo_sel][1]

with colB:
    st.metric("Precio Ref. Mín", f"${p_min_cat:,}")
    st.metric("Precio Ref. Máx", f"${p_max_cat:,}")
    
with colC:
    cantidad = st.number_input("Cantidad de personas", min_value=1, value=1)
    meses = st.number_input("Meses de duración", min_value=0.1, value=1.0, step=0.5)

if st.button("➕ Agregar al presupuesto", type="primary"):
    nuevo = pd.DataFrame([{
        "Rol": f"{rol_sel} ({tiempo_sel})",
        "Cantidad": int(cantidad),
        "Meses": float(meses),
        "Precio Mín": float(p_min_cat),
        "Precio Máx": float(p_max_cat),
        "Subtotal Mín": round(float(p_min_cat * cantidad * meses), 2),
        "Subtotal Máx": round(float(p_max_cat * cantidad * meses), 2) # Corregido error 'p_mac_cat'
    }])
    st.session_state.items_df = pd.concat([st.session_state.items_df, nuevo], ignore_index=True)
    st.rerun()

# =========================
# 3) Detalle y Totales
# =========================
st.subheader("Cotización")

edited_df = st.data_editor(
    st.session_state.items_df,
    num_rows="dynamic",
    width="stretch",
    key="editor_tabla"
)

# Sincronizar si hay cambios y recalcular
if not edited_df.equals(st.session_state.items_df):
    st.session_state.items_df = recalcular(edited_df)
    st.rerun()

# Mostrar Totales en Rango
total_min = st.session_state.items_df["Subtotal Mín"].sum()
total_max = st.session_state.items_df["Subtotal Máx"].sum()

st.markdown(f"""
### Rango de Cotización Estimada:
## :blue[${total_min:,.2f}] — :green[${total_max:,.2f}]
""")

if st.button("🗑️ Limpiar todo"):
    st.session_state.items_df = st.session_state.items_df.iloc[0:0]
    st.rerun()

st.divider()

# =========================
# 4) Descarga
# =========================
def generar_excel(datos, df, t_min, t_max):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Resumen
        pd.DataFrame([{"Campo": k, "Valor": str(v)} for k, v in datos.items()]).to_excel(writer, sheet_name="Resumen", index=False)
        # Detalle
        df.to_excel(writer, sheet_name="Detalle_Costos", index=False)
        # Totales al final de la hoja
        ws = writer.sheets["Detalle_Costos"]
        row = ws.max_row + 2
        ws.cell(row=row, column=6, value="TOTAL MÍNIMO")
        ws.cell(row=row, column=7, value=t_min)
        ws.cell(row=row+1, column=6, value="TOTAL MÁXIMO")
        ws.cell(row=row+1, column=7, value=t_max)
    return output.getvalue()
def enviar_correo(destinatario, asunto, cuerpo, archivo_bytes, nombre_archivo):
    # --- CONFIGURACIÓN DEL SERVIDOR ---
    remitente = "calculadora.cotizacion.uix@gmail.com"
    password = "xstj flnb otsf vmfm" # No es tu clave normal
    
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    # Adjuntar el Excel
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(archivo_bytes)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {nombre_archivo}")
    msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587) # Cambiar si no es Gmail
        server.starttls()
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar: {e}")
        return False
    

st.subheader("4) Exportar Cotización")
if not st.session_state.items_df.empty and st.session_state.datos["cliente"]:
    xlsx_data = generar_excel(st.session_state.datos, st.session_state.items_df, total_min, total_max)
    file_name = f"Cotizacion_{st.session_state.datos['cliente']}.xlsx".replace(" ", "_")
    st.download_button("⬇️ Descargar Excel con Rangos", data=xlsx_data, file_name=file_name)
else:
    st.warning("Agrega recursos y el nombre del cliente para habilitar la descarga.")


st.divider()
st.subheader("5) Enviar Cotización por Email")

with st.expander("Configurar Envío"):
    email_destino = st.text_input("Correo del cliente", value=st.session_state.datos["correo"])
    asunto_email = st.text_input("Asunto", value=f"Cotización Proyecto: {st.session_state.datos['proyecto']}")
    cuerpo_email = st.text_area("Mensaje", value=f"Hola {st.session_state.datos['cliente']},\n\nAdjunto enviamos la cotización para el proyecto {st.session_state.datos['proyecto']}.\n\nSaludos.")

    if st.button("📧 Enviar Correo"):
        if email_destino:
            with st.spinner("Enviando cotización..."):
                # Generamos el archivo para enviarlo
                xlsx_data = generar_excel(st.session_state.datos, st.session_state.items_df, total_min, total_max)
                nombre_archivo = f"Cotizacion_{st.session_state.datos['cliente']}.xlsx"
                
                exito = enviar_correo(email_destino, asunto_email, cuerpo_email, xlsx_data, nombre_archivo)
                if exito:
                    st.success(f"✅ Cotización enviada con éxito a {email_destino}")
        else:
            st.warning("Por favor, ingresa un correo electrónico.")