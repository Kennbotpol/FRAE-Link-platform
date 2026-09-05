import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="FRAE Link - Gestión de Voluntarios",
    page_icon="🐾",
    layout="centered",
)


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


st.title("🐾 FRAE Link: Sistema de Voluntariado")
st.caption("Plataforma de registro y control de voluntariado")

opcion = st.sidebar.radio(
    "Selecciona una opción:",
    [
        "📝 Registro",
        "⚡ Reportar Tarea",
        "👤 Mi Perfil",
        "🏆 Ranking y Métricas",
        "🔍 Audit de Evidencias",
    ],
)

# 1. REGISTRO DE VOLUNTARIOS
if opcion == "📝 Registro":
    st.header("Formulario de Inscripción")
    with st.form("form_registro", clear_on_submit=True):
        nombre = st.text_input("Nombre completo:")
        email = st.text_input("Correo electrónico:")
        edad = st.number_input(
            "Edad:", min_value=12, max_value=100, value=20, step=1
        )
        foto_perfil = st.file_uploader(
            "Foto de perfil (Opcional):", type=["jpg", "jpeg", "png"]
        )
        submit = st.form_submit_button("Registrarme como Voluntario")

        if submit:
            if nombre and email:
                foto_bytes = (
                    foto_perfil.read() if foto_perfil is not None else None
                )
                conn = conectar_db()
                cursor = conn.cursor()
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    cursor.execute(
                        "INSERT INTO voluntarios (nombre, email, edad, foto_perfil, fecha_registro) VALUES (?, ?, ?, ?, ?)",
                        (nombre, email, int(edad), foto_bytes, fecha_actual),
                    )
                    conn.commit()
                    st.success(
                        f"¡Bienvenido/a a FRAE Link, {nombre}! Registro exitoso."
                    )
                except sqlite3.IntegrityError:
                    st.error("Este correo electrónico ya está registrado.")
                finally:
                    conn.close()
            else:
                st.warning("Completa los campos obligatorios.")

# 2. REPORTAR TAREA
elif opcion == "⚡ Reportar Tarea":
    st.header("Registrar Tarea Completada")
    conn = conectar_db()
    voluntarios_df = pd.read_sql_query(
        "SELECT id, nombre, email FROM voluntarios", conn
    )
    conn.close()

    if voluntarios_df.empty:
        st.info("Aún no hay voluntarios registrados.")
    else:
        opciones = {
            f"{row['nombre']} ({row['email']})": row["id"]
            for _, row in voluntarios_df.iterrows()
        }
        vol_sel = st.selectbox("Selecciona tu usuario:", list(opciones.keys()))

        tareas = {
            "Difusión en redes sociales / estados (+15 pts)": 15,
            "Organización y verificación de datos (+20 pts)": 20,
            "Creación de arte / diseño gráfico (+25 pts)": 25,
            "Redacción de historias / contenido (+25 pts)": 25,
            "Inscripción de un nuevo voluntario (+30 pts)": 30,
            "Apoyo en eventos o rescates (+50 pts)": 50,
        }
        cat_tarea = st.selectbox("Tipo de tarea realizada:", list(tareas.keys()))
        evidencia = st.file_uploader(
            "Sube una foto o captura como comprobante:",
            type=["jpg", "jpeg", "png"],
        )

        if st.button("Guardar y Sumar Puntos"):
            if not evidencia:
                st.error("⚠️ Sube una captura como evidencia obligatoria.")
            else:
                vol_id = opciones[vol_sel]
                pts = tareas[cat_tarea]
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tareas_registradas (voluntario_id, tarea, puntos, evidencia, fecha) VALUES (?, ?, ?, ?, ?)",
                    (
                        vol_id,
                        cat_tarea,
                        pts,
                        evidencia.read(),
                        fecha_actual,
                    ),
                )
                cursor.execute(
                    "UPDATE voluntarios SET puntos = puntos + ? WHERE id = ?",
                    (pts, vol_id),
                )
                conn.commit()
                conn.close()
                st.balloons()
                st.success(f"¡Gran trabajo! +{pts} puntos asignados.")

# 3. MI PERFIL Y CARNET DIGITAL
elif opcion == "👤 Mi Perfil":
    st.header("Consulta tu Perfil y Rango")
    email_buscar = st.text_input("Ingresa tu correo registrado:")
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

            col1, col2 = st.columns([1, 2])
            with col1:
                if foto:
                    st.image(foto, width=130)
                else:
                    st.write("🖼️ *Sin foto de perfil*")
            with col2:
                st.subheader(nombre)
                st.write(f"**Rango:** {nivel}")
                st.write(f"**Puntos acumulados:** {puntos} pts")
                st.write(f"**Edad:** {edad} años")

            st.divider()
            st.write("**Historial de tareas completadas:**")
            historial = pd.read_sql_query(
                f"SELECT tarea, puntos, fecha FROM tareas_registradas WHERE voluntario_id = {v_id} ORDER BY fecha DESC",
                conn,
            )
            st.dataframe(historial, use_container_width=True)
        else:
            st.error("No se encontró ningún voluntario con ese correo.")
        conn.close()

# 4. RANKING Y MÉTRICAS
elif opcion == "🏆 Ranking y Métricas":
    st.header("🏆 Tablero de Impacto")
    conn = conectar_db()
    df = pd.read_sql_query(
        "SELECT nombre, puntos, edad FROM voluntarios ORDER BY puntos DESC",
        conn,
    )
    conn.close()

    if not df.empty:
        df["Nivel / Rango"] = df["puntos"].apply(obtener_nivel)
        df.index = df.index + 1
        st.dataframe(df, use_container_width=True)

        # Copia para exportar a Excel sin emojis corruptos
        df_export = df.copy()
        df_export["Nivel / Rango"] = (
            df_export["Nivel / Rango"]
            .str.replace("🥇 ", "")
            .str.replace("🥈 ", "")
            .str.replace("🥉 ", "")
            .str.replace("🌱 ", "")
        )

        csv_excel = df_export.to_csv(index=False, sep=";", encoding="utf-8-sig")
        st.download_button(
            label="📥 Descargar Tablero (Formato Excel)",
            data=csv_excel,
            file_name="tablero_de_impacto.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("📊 Resumen de Impacto Comunitario")
        total_puntos = df["puntos"].sum()
        total_voluntarios = len(df)

        col1, col2, col3 = st.columns(3)
        col1.metric("Voluntarios Activos", total_voluntarios)
        col2.metric("Puntos Acumulados", f"{total_puntos} pts")
        col3.metric("Nivel Promedio", "Defensores Activos 🐾")

# 5. AUDITORÍA DE EVIDENCIAS
elif opcion == "🔍 Audit de Evidencias":
    st.header("Visualización de Evidencias Subidas")
    conn = conectar_db()
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
        st.info("No hay evidencias registradas aún.")
    else:
        for _, row in evidencias_df.iterrows():
            with st.expander(f"{row['nombre']} - {row['tarea']} ({row['fecha']})"):
                st.write(f"**Puntos otorgados:** {row['puntos']}")
                if row["evidencia"]:
                    st.image(row["evidencia"], use_container_width=True)
                else:
                    st.write("Sin imagen adjunta.")