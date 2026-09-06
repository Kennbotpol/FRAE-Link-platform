# --- 5. PANEL DE AUDITORÍA ---
elif opcion == "🔍 Panel de Auditoría":
  st.subheader("🔒 Acceso Restringido")
  clave_admin = st.text_input("Ingresa la clave de administrador:", type="password")

  if clave_admin == "frae202610": # Cambia esta clave por la que tú prefieras
    
    st.subheader("📊 Métricas de Satisfacción")
    st.caption("Datos en tiempo real sobre la experiencia de los voluntarios.")

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

    if feedback_df.empty:
      st.info("Aún no se han recolectado métricas de experiencia.")
    else:
      promedio_calif = feedback_df["calificacion"].mean()
      col1, col2 = st.columns(2)
      col1.metric("Satisfacción Promedio", f"{promedio_calif:.2f} / 5.0 ⭐")
      col2.metric("Muestras Totales (N)", len(feedback_df))

      st.dataframe(feedback_df, use_container_width=True, hide_index=True)

      enc_utf8 = "utf-8-sig"
      csv_feedback = feedback_df.to_csv(index=False, sep=";", encoding=enc_utf8)
      st.download_button(
          label="📥 Descargar Reporte de Satisfacción (Excel)",
          data=csv_feedback,
          file_name="metricas_satisfaccion.csv",
          mime="text/csv",
      )

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

    # Herramienta para eliminar registros de prueba
    st.divider()
    st.subheader("🗑️ Eliminar Registro de Prueba")
    with st.expander("Gestionar / Borrar Encuestas de Satisfacción"):
      conn = conectar_db()
      encuestas_df = pd.read_sql_query(
          """
            SELECT e.id, v.nombre, e.calificacion, e.comentario, e.fecha 
            FROM encuestas_satisfaccion e
            JOIN voluntarios v ON e.voluntario_id = v.id
            ORDER BY e.id DESC
        """,
          conn,
      )
      conn.close()

      if not encuestas_df.empty:
        opciones_encuesta = {
            f"ID: {row['id']} | {row['nombre']} | ⭐ {row['calificacion']} ({row['fecha']})": (
                row["id"]
            )
            for _, row in encuestas_df.iterrows()
        }
        encuesta_id_sel = st.selectbox(
            "Selecciona la encuesta a borrar:", list(opciones_encuesta.keys())
        )

        if st.button("❌ Eliminar esta Encuesta", type="primary"):
          id_a_borrar = opciones_encuesta[encuesta_id_sel]
          conn = conectar_db()
          cursor = conn.cursor()
          cursor.execute(
              "DELETE FROM encuestas_satisfaccion WHERE id = ?", (id_a_borrar,)
          )
          conn.commit()
          conn.close()
          st.success(
              f"Encuesta con ID {id_a_borrar} eliminada correctamente de la base de datos."
          )
          st.rerun()
      else:
        st.info("No hay encuestas registradas para eliminar.")

  elif clave_admin != "":
    st.error("⚠️ Contraseña incorrecta.")
