import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="FRAE Link - Voluntariado",
    page_icon="🐾",
    layout="centered",
    initial_sidebar_state="expanded",
)

# 2. CSS PERSONALIZADO
st.markdown(
    """
<style>
    .stApp, header[data-testid="stHeader"], .block-container { background-color: #0E1117 !important; }
    .stApp, .stApp * { color: #FAFAFA !important; }
    section[data-testid="stSidebar"] { background-color: #111827 !important; border-right: 1px solid #1F2937 !important; }
    input, .stTextInput input, .stSelectbox select, .stNumberInput input, 
    [data-testid="stFileUploader"] > div, [data-testid="stFileUploader"] section, [data-testid="stFileUploadDropzone"] {
        background-color: #1F2937 !important; color: #FFFFFF !important; border-color: #374151 !important;
    }
    ::placeholder { color: #9CA3AF !important; }
    button[kind="secondary"], button[kind="primaryFormSubmit"], [data-testid="stFileUploader"] button,
    button[data-testid="stNumberInputStepUp"], button[data-testid="stNumberInputStepDown"],
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background-color: #1F2937 !important; color: #FAFAFA !important; border: 1px solid #374151 !important; border-radius: 8px !important;
    }
    button[kind="secondary"]:hover, button[kind="primaryFormSubmit"]:hover, [data-testid="stFileUploader"] button:hover,
    button[data-testid="stNumberInputStepUp"]:hover, button[data-testid="stNumberInputStepDown"]:hover,
    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        border-color: #FF7A00 !important; color: #FF7A00 !important;
    }
    footer { display: none !important; }
    .stAppDeployButton { display: none !important; }
</style>
""",
    unsafe_allow_html=True,
)


# 3. BASE DE DATOS
def conectar_db():
  return sqlite3.connect("frae_link.db")


def crear_tablas():
  conn = conectar_db()
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS voluntarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            edad INTEGER,
            foto_perfil BLOB,
            puntos INTEGER DEFAULT 0,
            fecha_registro TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas_registradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voluntario_id INTEGER,
            tarea TEXT NOT NULL,
            puntos INTEGER NOT NULL,
            evidencia BLOB,
            fecha TEXT,
            FOREIGN KEY (voluntario_id) REFERENCES voluntarios (id)
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS encuestas_satisfaccion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voluntario_id INTEGER,
            calificacion INTEGER,
            comentario TEXT,
            fecha TEXT,
            FOREIGN KEY (voluntario_id) REFERENCES voluntarios (id)
        )
    """)
  conn.commit()
  conn.close()


crear_tablas()


def obtener_nivel(puntos):
  if puntos >= 150:
    return "🥇 Embajador FRAE"
  elif puntos >= 80:
    return "🥈 Defensor Activo"
  elif puntos >= 30:
    return "🥉 Voluntario Aliado"
  return "🌱 Voluntario Semilla"


# 4. NAVEGACIÓN
st.sidebar.markdown(
    "<h2 style='text-align: center; color: #FF7A00;'>🐾 FRAE Link</h2>", unsafe_allow_html=True
)
st.sidebar.markdown("---")

opcion = st.sidebar.radio(
    "Navegación:",
    [
        "📝 Registro",
        "⚡ Reportar Tarea",
        "👤 Mi Perfil",
        "🏆 Ranking e Impacto Real",
        "🔍 Panel de Auditoría",
    ],
)

if opcion != "📝 Registro":
  st.title("🐾 FRAE Link")
  st.markdown(
      "<p style='text-align: center; color: #9CA3AF; margin-bottom: 30px;'>"
      "Sistema Inteligente de Voluntariado</p>",
      unsafe_allow_html=True,
  )

# --- 1. REGISTRO ---
if opcion == "📝 Registro":
  st.title("🐾 Únete a FRAE")
  st.markdown(
      "<p style='text-align: center; color: #9CA3AF;'>"
      "Inicia tu viaje como voluntario digital</p><br>",
      unsafe_allow_html=True,
  )

  with st.form("form_registro", clear_on_submit=True):
    st.subheader("Datos Personales")
    col1, col2 = st.columns(2)
    with col1:
      nombre = st.text_input("Nombre completo:")
    with col2:
      email = st.text_input("Correo electrónico:")

    col3, col4 = st.columns([1, 2])
    with col3:
      edad = st.number_input(
          "Edad:", min_value=12, max_value=100, value=20, step=1
      )
    with col4:
      foto_perfil = st.file_uploader(
          "Foto de perfil (Opcional):", type=["jpg", "jpeg", "png"]
      )

    st.markdown("<br>", unsafe_allow_html=True)
    submit = st.form_submit_button("🚀 Registrarme como Voluntario")

    if submit:
      if nombre and email:
        foto_bytes = foto_perfil.read() if foto_perfil is not None else None
        conn = conectar_db()
        cursor = conn.cursor()
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
          cursor.execute(
              "INSERT INTO voluntarios (nombre, email, edad, foto_perfil, fecha_registro) "
              "VALUES (?, ?, ?, ?, ?)",
              (nombre, email, int(edad), foto_bytes, fecha_actual),
          )
          conn.commit()
          st.success(
              f"¡Bienvenido/a a la familia, {nombre}! Tu registro fue exitoso."
          )
          st.balloons()
        except sqlite3.IntegrityError:
          st.error("Este correo electrónico ya está registrado.")
        finally:
          conn.close()
      else:
        st.warning("⚠️ Completa tu nombre y correo para continuar.")

# --- 2. REPORTAR TAREA ---
elif opcion == "⚡ Reportar Tarea":
  st.subheader("⚡ Reportar Nueva Acción")
  st.info(
      "🔥 **MISIÓN DE LA SEMANA:**\n\n"
      "Difundir el caso de adopción urgente de Bruno en tu estado (+30 pts)."
  )

  conn = conectar_db()
  voluntarios_df = pd.read_sql_query(
      "SELECT id, nombre FROM voluntarios", conn
  )
  conn.close()

  if voluntarios_df.empty:
    st.warning("Aún no hay voluntarios registrados en el sistema.")
  else:
    opciones = {
        f"{row['nombre']} (Voluntario #{row['id']})": row["id"]
        for _, row in voluntarios_df.iterrows()
    }

    with st.container():
      vol_sel = st.selectbox("👤 ¿Quién eres?", list(opciones.keys()))
      tareas = {
          "🔥 Misión Semanal: Difusión caso Bruno (+30 pts)": 30,
          "Difusión en redes sociales / estados (+15 pts)": 15,
          "Organización y verificación de datos (+20 pts)": 20,
          "Creación de arte / diseño gráfico (+25 pts)": 25,
          "Redacción de historias / contenido (+25 pts)": 25,
          "Inscripción de un nuevo voluntario (+30 pts)": 30,
          "Apoyo presencial en eventos o rescates (+50 pts)": 50,
      }
      cat_tarea = st.selectbox("📋 Acción completada:", list(tareas.keys()))
      evidencia = st.file_uploader(
          "📸 Sube la captura de pantalla o foto (Obligatoria):",
          type=["jpg", "jpeg", "png"],
      )

      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("✅ Enviar Evidencia y Sumar Puntos"):
        if not evidencia:
          st.error("⚠️ La captura es necesaria para validar tus puntos.")
        else:
          vol_id = opciones[vol_sel]
          pts = tareas[cat_tarea]
          fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          conn = conectar_db()
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO tareas_registradas (voluntario_id, tarea, puntos, evidencia, fecha) "
              "VALUES (?, ?, ?, ?, ?)",
              (vol_id, cat_tarea, pts, evidencia.read(), fecha_actual),
          )
          cursor.execute(
              "UPDATE voluntarios SET puntos = puntos + ? WHERE id = ?",
              (pts, vol_id),
          )
          conn.commit()
          conn.close()
          st.success(f"¡Brillante! Se han añadido +{pts} puntos a tu perfil.")
          st.session_state["ultimo_vol_id"] = vol_id

    if "ultimo_vol_id" in st.session_state:
      st.divider()
      st.subheader("💬 Encuesta de Experiencia")
      with st.form("form_feedback", clear_on_submit=True):
        calif = st.slider(
            "Facilidad de la acción realizada (1=Difícil, 5=Muy fácil)", 1, 5, 5
        )
        comentario = st.text_input("Observaciones o sugerencias de mejora:")
        sub_fb = st.form_submit_button("Enviar Evaluación")

        if sub_fb:
          conn = conectar_db()
          cursor = conn.cursor()
          fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          cursor.execute(
              "INSERT INTO encuestas_satisfaccion (voluntario_id, calificacion, comentario, fecha) "
              "VALUES (?, ?, ?, ?)",
              (st.session_state["ultimo_vol_id"], calif, comentario, fecha_actual),
          )
          conn.commit()
          conn.close()
          st.success("¡Gracias por ayudarnos a mejorar FRAE Link!")
          del st.session_state["ultimo_vol_id"]

# --- 3. MI PERFIL ---
elif opcion == "👤 Mi Perfil":
  st.subheader("👤 Credencial Digital")
  email_buscar = st.text_input("🔍 Ingresa tu correo de voluntario:")

  if st.button("Buscar Perfil") and email_buscar:
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, edad, puntos, foto_perfil FROM voluntarios WHERE email = ?",
        (email_buscar,),
    )
    user = cursor.fetchone()

    if user:
      v_id, nombre, edad, puntos, foto = user
      nivel = obtener_nivel(puntos)
      st.markdown("<br>", unsafe_allow_html=True)
      col1, col2 = st.columns([1, 2])
      with col1:
        if foto:
          st.image(foto, width=150, output_format="PNG")
        else:
          st.info("🖼️ Sin foto")
      with col2:
        st.markdown(f"### {nombre}")
        st.markdown(f"**Nivel Actual:** `{nivel}`")
        st.markdown(f"**Impacto Total:** `{puntos} pts`")
        st.markdown(f"**Edad:** {edad} años")

      st.divider()
      st.markdown("#### 📜 Tu Historial de Impacto")
      historial = pd.read_sql_query(
          f"SELECT tarea, puntos, fecha FROM tareas_registradas WHERE voluntario_id = {v_id} ORDER BY fecha DESC",
          conn,
      )
      st.dataframe(historial, use_container_width=True, hide_index=True)
    else:
      st.error("No se encontraron registros. Revisa el correo ingresado.")
    conn.close()

# --- 4. RANKING E IMPACTO ---
elif opcion == "🏆 Ranking e Impacto Real":
  conn = conectar_db()
  df = pd.read_sql_query(
      "SELECT nombre, puntos FROM voluntarios ORDER BY puntos DESC", conn
  )
  conn.close()

  if not df.empty:
    total_puntos = df["puntos"].sum()
    st.subheader("🌱 Impacto en el Refugio")
    alimento_kg = int(total_puntos / 15)
    vacunas = int(total_puntos / 50)
    adopciones = int(total_puntos / 100)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("🍲 Alimento", f"~{alimento_kg} kg")
    col_b.metric("💉 Vacunas", f"~{vacunas}")
    col_c.metric("🏡 Adopciones", f"~{adopciones}")

    st.divider()
    st.subheader("🏆 Leaderboard de Voluntarios")
    df["Rango"] = df["puntos"].apply(obtener_nivel)
    df.index = df.index + 1
    st.dataframe(df, use_container_width=True)

    df_export = df.copy()
    df_export["Rango"] = (
        df_export["Rango"]
        .str.replace("🥇 ", "")
        .str.replace("🥈 ", "")
        .str.replace("🥉 ", "")
        .str.replace("🌱 ", "")
    )
    csv_excel = df_export.to_csv(
        index=False, sep=";", encoding="utf-8-sig"
    )
    st.download_button(
        label="📥 Descargar Ranking (Excel)",
        data=csv_excel,
        file_name="tablero_de_impacto.csv",
        mime="text/csv",
    )
  else:
    st.info("Aún no hay datos suficientes para mostrar el tablero.")

# --- 5. PANEL DE AUDITORÍA ---
elif opcion == "🔍 Panel de Auditoría":
  st.subheader("🔒 Acceso Restringido")
  clave_admin = st.text_input(
      "Ingresa la clave de administrador:", type="password"
  )

  if clave_admin == "frae2026":
    # --- BOTÓN DE RESPALDO SEGURO (SOLO ADMIN) ---
    st.success("✅ Acceso concedido.")
    with st.expander("💾 Copia de Seguridad de la Base de Datos"):
      try:
        with open("frae_link.db", "rb") as f:
          st.download_button(
              label="📥 Descargar Base de Datos Real (.db)",
              data=f,
              file_name="frae_link.db",
              mime="application/octet-stream",
          )
      except FileNotFoundError:
        st.warning("No se encontró el archivo físico de la base de datos.")

    st.divider()
    st.subheader("📊 Métricas de Satisfacción")
    conn = conectar_db()
    feedback_df = pd.read_sql_query(
        """
          SELECT e.id, v.nombre, e.calificacion, e.comentario, e.fecha
          FROM encuestas_satisfaccion e
          JOIN voluntarios v ON e.voluntario_id = v.id
          ORDER BY e.fecha DESC
          """,
        conn,
    )

    if not feedback_df.empty:
      promedio_calif = feedback_df["calificacion"].mean()
      col1, col2 = st.columns(2)
      col1.metric("Satisfacción Promedio", f"{promedio_calif:.2f} / 5.0 ⭐")
      col2.metric("Muestras Totales (N)", len(feedback_df))
      st.dataframe(feedback_df, use_container_width=True, hide_index=True)

      csv_feedback = feedback_df.to_csv(
          index=False, sep=";", encoding="utf-8-sig"
      )
      st.download_button(
          label="📥 Descargar Reporte de Satisfacción (Excel)",
          data=csv_feedback,
          file_name="metricas_satisfaccion.csv",
          mime="text/csv",
      )
    else:
      st.info("Aún no hay métricas de experiencia.")

    st.divider()
    st.subheader("📸 Auditoría de Tareas")
    evidencias_df = pd.read_sql_query(
        """
          SELECT t.id, v.nombre, t.tarea, t.puntos, t.fecha, t.evidencia 
          FROM tareas_registradas t 
          JOIN voluntarios v ON t.voluntario_id = v.id 
          ORDER BY t.fecha DESC
      """,
        conn,
    )
    conn.close()

    if evidencias_df.empty:
      st.info("No hay evidencias reportadas.")
    else:
      for _, row in evidencias_df.iterrows():
        with st.expander(
            f"👤 {row['nombre']} | 🗓️ {row['fecha']} | 🏆 {row['puntos']} pts"
        ):
          st.write(f"**Actividad:** {row['tarea']}")
          if row["evidencia"]:
            st.image(row["evidencia"], use_container_width=True)
          else:
            st.write("Sin imagen adjunta.")

    st.divider()
    st.subheader("❌ Invalidar Tarea y Restar Puntos")
    with st.expander("Rechazar tarea mal registrada o falsa"):
      conn = conectar_db()
      tareas_gestion_df = pd.read_sql_query(
          """
            SELECT t.id, v.nombre, t.tarea, t.puntos, t.fecha, t.voluntario_id 
            FROM tareas_registradas t 
            JOIN voluntarios v ON t.voluntario_id = v.id 
            ORDER BY t.id DESC
        """,
          conn,
      )
      conn.close()

      if not tareas_gestion_df.empty:
        opciones_tarea = {
            f"ID: {row['id']} | {row['nombre']} | {row['tarea']} (-{row['puntos']} pts)": (
                row["id"],
                row["voluntario_id"],
                row["puntos"],
            )
            for _, row in tareas_gestion_df.iterrows()
        }
        tarea_id_sel = st.selectbox(
            "Selecciona la tarea a rechazar:", list(opciones_tarea.keys())
        )

        if st.button("🚫 Rechazar Tarea y Restar Puntos", type="primary"):
          t_id, v_id, pts_a_restar = opciones_tarea[tarea_id_sel]
          conn = conectar_db()
          cursor = conn.cursor()
          cursor.execute(
              "UPDATE voluntarios SET puntos = MAX(0, puntos - ?) WHERE id = ?",
              (pts_a_restar, v_id),
          )
          cursor.execute(
              "DELETE FROM tareas_registradas WHERE id = ?", (t_id,)
          )
          conn.commit()
          conn.close()
          st.success(
              f"Tarea ID {t_id} eliminada. Se han restado {pts_a_restar} puntos"
              " al voluntario correctamente."
          )
          st.rerun()
      else:
        st.info("No hay tareas registradas para rechazar.")

  elif clave_admin != "":
    st.error("⚠️ Contraseña incorrecta.")
