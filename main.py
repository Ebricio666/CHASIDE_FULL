# ============================================
# APP COMPLETA · CHASIDE (4 módulos con sidebar)
# ============================================

# -------- Imports --------
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -------- Config global --------
st.set_page_config(page_title="CHASIDE – Diagnóstico Vocacional", layout="wide")

# -------- Constantes --------
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1BNAeOSj2F378vcJE5-T8iJ8hvoseOleOHr-I7mVfYu4/export?format=csv"
COL_CARRERA = '¿A qué carrera desea ingresar?'
COL_NOMBRE  = 'Ingrese su nombre completo'
AREAS = ['C','H','A','S','I','D','E']

INTERESES_ITEMS = {
    'C':[1,12,20,53,64,71,78,85,91,98],
    'H':[9,25,34,41,56,67,74,80,89,95],
    'A':[3,11,21,28,36,45,50,57,81,96],
    'S':[8,16,23,33,44,52,62,70,87,92],
    'I':[6,19,27,38,47,54,60,75,83,97],
    'D':[5,14,24,31,37,48,58,65,73,84],
    'E':[17,32,35,42,49,61,68,77,88,93]
}
APTITUDES_ITEMS = {
    'C':[2,15,46,51],
    'H':[30,63,72,86],
    'A':[22,39,76,82],
    'S':[4,29,40,69],
    'I':[10,26,59,90],
    'D':[13,18,43,66],
    'E':[7,55,79,94]
}
PERFIL_CARRERAS = {
    'Arquitectura': {'Fuerte': ['A','I','C']},
    'Contador Público': {'Fuerte': ['C','D']},
    'Licenciatura en Administración': {'Fuerte': ['C','D']},
    'Ingeniería Ambiental': {'Fuerte': ['I','C','E']},
    'Ingeniería Bioquímica': {'Fuerte': ['I','C','E']},
    'Ingeniería en Gestión Empresarial': {'Fuerte': ['C','D','H']},
    'Ingeniería Industrial': {'Fuerte': ['C','D','H']},
    'Ingeniería en Inteligencia Artificial': {'Fuerte': ['I','E']},
    'Ingeniería Mecatrónica': {'Fuerte': ['I','E']},
    'Ingeniería en Sistemas Computacionales': {'Fuerte': ['I','E']}
}
COLOR_CATEG = {
    'Verde':'#22c55e',
    'Amarillo':'#f59e0b',
    'Rojo':'#ef4444',
    'No aceptable':'#6b7280',
    'Sin sugerencia':'#94a3b8'
}

# ============================================
# Helpers: carga y procesamiento único
# ============================================
@st.cache_data(show_spinner=False)
def load_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

def evaluar(area_chaside, carrera):
    perfil = PERFIL_CARRERAS.get(str(carrera).strip())
    if not perfil: return 'Sin perfil definido'
    if area_chaside in perfil.get('Fuerte',[]): return 'Coherente'
    if area_chaside in perfil.get('Baja',[]):   return 'Requiere Orientación'
    return 'Neutral'

def procesar_chaside(df_raw: pd.DataFrame, peso_intereses=0.8) -> pd.DataFrame:
    df = df_raw.copy()

    # Validación columnas base
    if COL_CARRERA not in df.columns or COL_NOMBRE not in df.columns:
        raise ValueError(f"Faltan columnas requeridas: '{COL_CARRERA}' o '{COL_NOMBRE}'.")

    # Ítems (F..CV) → 98 preguntas
    columnas_items = df.columns[5:103]

    # Sí/No → 1/0 robusto
    df_items = (
        df[columnas_items].astype(str).apply(lambda c: c.str.strip().str.lower())
        .replace({
            'sí':1,'si':1,'s':1,'1':1,'true':1,'verdadero':1,'x':1,
            'no':0,'n':0,'0':0,'false':0,'falso':0,'':'0','nan':0
        }).apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    )
    df[columnas_items] = df_items

    # Coincidencia (sesgo Sí/No)
    suma_si = df[columnas_items].sum(axis=1)
    total_items = len(columnas_items)
    pct_si = np.where(total_items==0, 0, suma_si/total_items)
    pct_no = 1 - pct_si
    df['Coincidencia'] = np.maximum(pct_si, pct_no)

    # Sumas por área
    def col_item(i:int)->str: return columnas_items[i-1]
    for a in AREAS:
        df[f'INTERES_{a}']  = df[[col_item(i) for i in INTERESES_ITEMS[a]]].sum(axis=1)
        df[f'APTITUD_{a}'] = df[[col_item(i) for i in APTITUDES_ITEMS[a]]].sum(axis=1)

    # Ponderación
    peso_aptitudes = 1 - peso_intereses
    for a in AREAS:
        df[f'PUNTAJE_COMBINADO_{a}'] = df[f'INTERES_{a}']*peso_intereses + df[f'APTITUD_{a}']*peso_aptitudes
        df[f'TOTAL_{a}'] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']

    # Área fuerte
    df['Area_Fuerte_Ponderada'] = df.apply(lambda r: max(AREAS, key=lambda a: r[f'PUNTAJE_COMBINADO_{a}']), axis=1)

    # Coincidencia con carrera
    df['Coincidencia_Ponderada'] = df.apply(lambda r: evaluar(r['Area_Fuerte_Ponderada'], r[COL_CARRERA]), axis=1)

    # Diagnóstico / semáforo
    def carrera_mejor(r):
        if r['Coincidencia'] >= 0.75: return 'Información no aceptable'
        a = r['Area_Fuerte_Ponderada']
        c_actual = str(r[COL_CARRERA]).strip()
        sugeridas = [c for c,p in PERFIL_CARRERAS.items() if a in p.get('Fuerte',[])]
        return c_actual if c_actual in sugeridas else (', '.join(sugeridas) if sugeridas else 'Sin sugerencia clara')

    def diagnostico(r):
        if r['Carrera_Mejor_Perfilada']=='Información no aceptable': return 'Información no aceptable'
        if str(r[COL_CARRERA]).strip()==str(r['Carrera_Mejor_Perfilada']).strip(): return 'Perfil adecuado'
        if r['Carrera_Mejor_Perfilada']=='Sin sugerencia clara': return 'Sin sugerencia clara'
        return f"Sugerencia: {r['Carrera_Mejor_Perfilada']}"

    def semaforo(r):
        diag=r['Diagnóstico Primario Vocacional']
        if diag=='Información no aceptable': return 'No aceptable'
        if diag=='Sin sugerencia clara': return 'Sin sugerencia'
        match=r['Coincidencia_Ponderada']
        if diag=='Perfil adecuado':
            return {'Coherente':'Verde','Neutral':'Amarillo','Requiere Orientación':'Rojo'}.get(match,'Sin sugerencia')
        if diag.startswith('Sugerencia:'):
            return {'Coherente':'Verde','Neutral':'Amarillo','Requiere Orientación':'Rojo'}.get(match,'Sin sugerencia')
        return 'Sin sugerencia'

    df['Carrera_Mejor_Perfilada']         = df.apply(carrera_mejor, axis=1)
    df['Diagnóstico Primario Vocacional'] = df.apply(diagnostico, axis=1)
    df['Semáforo Vocacional']             = df.apply(semaforo, axis=1)

    # Score global (para rankings/violín)
    score_cols = [f'PUNTAJE_COMBINADO_{a}' for a in AREAS]
    df['Score'] = df[score_cols].max(axis=1)

    return df

# ============================================
# MÓDULO 1 · Presentación
# ============================================
PRIMARY = "#0F766E"      # teal-700
ACCENT  = "#14B8A6"      # teal-400
MUTED   = "#64748B"      # slate-500

def render_presentacion():
    st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1.5rem; padding-bottom: 2.5rem; }}
    .h1-title {{ font-size: 2.0rem; font-weight: 800; color: {PRIMARY}; margin-bottom: .25rem; }}
    .subtitle {{ color: {MUTED}; margin-bottom: 1.25rem; }}
    .section-title {{ font-weight: 700; font-size: 1.1rem; margin: 1.2rem 0 .2rem 0; color: {PRIMARY}; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px 18px; background: #ffffff; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
    .puv {{ border-left: 6px solid {ACCENT}; padding: 12px 14px; background: #f8fffd; border-radius: 10px; font-size: 1.02rem; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="h1-title">Diagnóstico Vocacional – Escala CHASIDE</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Aplicación de apoyo a la elección de carrera universitaria</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Autores e institución</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1.2])
    with col1:
        st.markdown("""
        <div class="card">
        <b>Autores</b><br>
        • Dra. Elena Elsa Bricio Barrios<br>
        • Dr. Santiago Arceo-Díaz<br>
        • Psic. Martha Cecilia Ramírez Guzmán
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card">
        <b>Institución</b><br>
        Tecnológico Nacional de México<br>
        Instituto Tecnológico de Colima
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">¿Qué pretende esta aplicación?</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
    Esta herramienta orienta a estudiantes de bachillerato en el <b>descubrimiento de sus intereses y aptitudes</b>,
    para apoyar una <b>elección de carrera informada y alineada</b> con sus fortalezas y aspiraciones.
    Integra resultados de la escala CHASIDE y los presenta de forma clara para estudiantes, familias y docentes.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Madurez y personalidad en el bachillerato</div>', unsafe_allow_html=True)
    st.markdown("""
    La <b>personalidad</b> se encuentra en pleno desarrollo durante el bachillerato. La <b>madurez</b> permite al joven
    empezar a definirse y reflexionar sobre su proyecto de vida, pero el proceso <b>aún está en construcción</b>.
    En esta etapa es clave contar con <b>herramientas de orientación</b> que acompañen la toma de decisiones académicas.
    """)

    st.markdown('<div class="section-title">Intereses y aptitudes: base de la formación académica</div>', unsafe_allow_html=True)
    st.markdown("""
    Reconocer <b>lo que me interesa</b> y <b>para lo que tengo aptitud</b> ayuda a dirigir el esfuerzo,
    sostener la motivación y <b>reducir el riesgo de abandono</b>. Estos factores son determinantes para
    <b>persistir y desempeñarse</b> durante la vida universitaria.
    """)

    st.markdown('<div class="section-title">¿Qué es la escala CHASIDE?</div>', unsafe_allow_html=True)
    st.markdown("""
    <b>CHASIDE</b> integra <b>intereses</b> y <b>aptitudes</b> en siete áreas: C, H, A, S, I, D, E.
    Aplicación rápida (sí/no), interpretación práctica y vínculo directo con opciones de carrera.
    """)

    st.markdown('<div class="section-title">Propuesta Única de Valor (PUV)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="puv">
    <b>Orientación vocacional personalizada</b>, basada en evidencia (CHASIDE), con visualizaciones claras
    y reportes ejecutivos para apoyar decisiones académicas informadas.
    </div>
    """, unsafe_allow_html=True)

# ============================================
# MÓDULO 2 · Información general (gráficas)
# ============================================
def render_info_general(df_proc: pd.DataFrame):
    st.subheader("🥧 Diagnóstico general (Pastel)")

    resumen = df_proc['Semáforo Vocacional'].value_counts().reindex(
        ['Verde','Amarillo','Rojo','No aceptable','Sin sugerencia'], fill_value=0
    ).reset_index()
    resumen.columns = ['Categoría','N']
    fig = px.pie(
        resumen, names='Categoría', values='N', hole=0.35,
        color='Categoría', color_discrete_map=COLOR_CATEG,
        title="Distribución global por categoría"
    )
    fig.update_traces(textposition='inside', texttemplate='%{label}<br>%{percent:.1%} (%{value})')
    st.plotly_chart(fig, use_container_width=True)

    st.header("📊 Distribución por carrera y categoría")
    cats_order = ['Verde', 'Amarillo', 'No aceptable', 'Sin sugerencia']
    stacked = (
        df_proc[df_proc['Semáforo Vocacional'].isin(cats_order)]
        .groupby([COL_CARRERA, 'Semáforo Vocacional'], dropna=False).size()
        .reset_index(name='N').rename(columns={'Semáforo Vocacional':'Categoría'})
    )
    stacked['Categoría'] = pd.Categorical(stacked['Categoría'], categories=cats_order, ordered=True)

    modo = st.radio("Modo de visualización", ["Proporción (100% apilado)", "Valores absolutos"],
                    horizontal=True, index=0)

    if modo == "Proporción (100% apilado)":
        stacked['%'] = stacked.groupby(COL_CARRERA)['N'].transform(lambda x: 0 if x.sum()==0 else x/x.sum()*100)
        fig_stacked = px.bar(
            stacked, x=COL_CARRERA, y='%', color='Categoría',
            category_orders={'Categoría': cats_order}, color_discrete_map=COLOR_CATEG,
            barmode='stack', text=stacked['%'].round(1).astype(str)+'%',
            title="Proporción (%) por carrera y categoría"
        )
        fig_stacked.update_layout(yaxis_title="Proporción (%)", xaxis_title="Carrera", xaxis_tickangle=-30, height=620)
    else:
        fig_stacked = px.bar(
            stacked, x=COL_CARRERA, y='N', color='Categoría',
            category_orders={'Categoría': cats_order}, color_discrete_map=COLOR_CATEG,
            barmode='stack', text='N', title="Estudiantes por carrera y categoría (valores absolutos)"
        )
        fig_stacked.update_layout(yaxis_title="Número de estudiantes", xaxis_title="Carrera", xaxis_tickangle=-30, height=620)
        fig_stacked.update_traces(textposition='inside', cliponaxis=False)
    st.plotly_chart(fig_stacked, use_container_width=True)

    st.header("🎻 Distribución de puntajes (Violin) – Verde vs Amarillo")
    df_scores = df_proc.copy()
    df_scores['Score'] = df_scores[[f'PUNTAJE_COMBINADO_{a}' for a in AREAS]].max(axis=1)
    df_violin = df_scores[df_scores['Semáforo Vocacional'].isin(['Verde','Amarillo'])].copy()

    if df_violin.empty:
        st.info("No hay estudiantes en categorías Verde o Amarillo para graficar.")
    else:
        fig_violin = px.violin(
            df_violin, x=COL_CARRERA, y="Score", color="Semáforo Vocacional",
            box=True, points=False, color_discrete_map={"Verde": COLOR_CATEG['Verde'], "Amarillo": COLOR_CATEG['Amarillo']},
            title="Distribución de puntajes por carrera (Verde vs Amarillo)"
        )
        # separadores verticales punteados
        categorias = df_violin[COL_CARRERA].unique()
        for i in range(len(categorias)-1):
            fig_violin.add_vline(x=i+0.5, line_width=1, line_dash="dot", line_color="gray")
        fig_violin.update_layout(xaxis_title="Carrera", yaxis_title="Score combinado", xaxis_tickangle=-30, height=720)
        st.plotly_chart(fig_violin, use_container_width=True)

    st.header("🕸️ Radar CHASIDE por carrera – Verde vs Amarillo")
    # Totales por letra ya existen (TOTAL_*)
    df_radar = df_proc.copy()
    for a in AREAS:
        if f'TOTAL_{a}' not in df_radar.columns:
            df_radar[f'TOTAL_{a}'] = df_radar[f'INTERES_{a}'] + df_radar[f'APTITUD_{a}']
    df_radar['Categoría'] = df_radar['Semáforo Vocacional']
    df_radar['Carrera']   = df_radar[COL_CARRERA]

    carreras_disp = sorted(df_radar['Carrera'].dropna().unique())
    if not carreras_disp:
        st.info("No hay carreras para mostrar en el radar.")
        return

    tabs = st.tabs(carreras_disp)
    for tab, carrera_sel in zip(tabs, carreras_disp):
        with tab:
            sub = df_radar[(df_radar['Carrera']==carrera_sel) & (df_radar['Categoría'].isin(['Verde','Amarillo']))]
            if sub.empty or sub['Categoría'].nunique() < 2:
                st.warning("No hay datos suficientes de Verde y Amarillo en esta carrera.")
                continue
            prom = sub.groupby('Categoría')[[f'TOTAL_{a}' for a in AREAS]].mean()
            prom = prom.rename(columns={f'TOTAL_{a}':a for a in AREAS}).reset_index()

            fig = px.line_polar(
                prom.melt(id_vars='Categoría', value_vars=AREAS, var_name='Área', value_name='Promedio'),
                r='Promedio', theta='Área', color='Categoría', line_close=True, markers=True,
                color_discrete_map={'Verde':COLOR_CATEG['Verde'],'Amarillo':COLOR_CATEG['Amarillo']},
                title=f"Perfil CHASIDE – {carrera_sel}"
            )
            fig.update_traces(fill='toself', opacity=0.75)
            st.plotly_chart(fig, use_container_width=True)

# ============================================
# MÓDULO 3 · Información individual (reporte ejecutivo)
# ============================================
def render_info_individual(df_proc: pd.DataFrame):
    st.header("📘 Información particular del estudiantado – Reporte ejecutivo")

    carreras = sorted(df_proc[COL_CARRERA].dropna().unique())
    if not carreras:
        st.warning("No hay carreras disponibles en el archivo.")
        return
    carrera_sel = st.selectbox("Carrera a evaluar:", carreras, index=0)

    d_carrera = df_proc[df_proc[COL_CARRERA] == carrera_sel].copy()
    if d_carrera.empty:
        st.warning("No hay estudiantes para esta carrera.")
        return

    nombres = sorted(d_carrera[COL_NOMBRE].astype(str).unique())
    est_sel = st.selectbox("Estudiante:", nombres, index=0)

    alumno_mask = (df_proc[COL_CARRERA] == carrera_sel) & (df_proc[COL_NOMBRE].astype(str) == est_sel)
    alumno = df_proc[alumno_mask].copy()
    if alumno.empty:
        st.warning("No se encontró el estudiante seleccionado.")
        return
    al = alumno.iloc[0]

    # Encabezado formal
    categoria = al['Semáforo Vocacional']
    cat_color = {"Verde":COLOR_CATEG['Verde'], "Amarillo":COLOR_CATEG['Amarillo']}.get(categoria, COLOR_CATEG['No aceptable'])
    cat_count_carrera = int((d_carrera['Semáforo Vocacional']==categoria).sum())

    st.markdown(
        f"""
**Nombre del estudiante:** {est_sel}  
**Carrera:** {carrera_sel}  
**Categoría diagnóstica:** <span style='color:{cat_color}; font-weight:bold'>{categoria}</span>  
**Número de estudiantes en esta categoría (en la carrera):** {cat_count_carrera}
""", unsafe_allow_html=True
    )
    st.divider()

    # Banderas (dentro de la MISMA carrera)
    verde_carrera    = d_carrera[d_carrera['Semáforo Vocacional']=='Verde'].copy()
    amarillo_carrera = d_carrera[d_carrera['Semáforo Vocacional']=='Amarillo'].copy()

    banderas = []
    if not verde_carrera.empty:
        top5_verde = verde_carrera.sort_values('Score', ascending=False).head(5)[COL_NOMBRE].astype(str).tolist()
        if est_sel in top5_verde:
            banderas.append("🟢 **Joven promesa** (Top 5 de la categoría Verde en su carrera).")
    if not amarillo_carrera.empty:
        bottom5_amar = amarillo_carrera.sort_values('Score', ascending=True).head(5)[COL_NOMBRE].astype(str).tolist()
        if est_sel in bottom5_amar:
            banderas.append("🟠 **Joven en riesgo** (Bottom 5 de la categoría Amarillo en su carrera).")

    st.markdown("### Indicadores particulares")
    if banderas:
        for msg in banderas:
            if "promesa" in msg.lower():
                st.success(msg, icon="✅")
            else:
                st.warning(msg, icon="⚠️")
    else:
        st.info("Sin indicadores particulares para este estudiante.", icon="ℹ️")
    st.divider()

    # Fortalezas y brechas vs referencia (preferencia: Verde de la carrera)
    ref_cols = [f'TOTAL_{a}' for a in AREAS]
    mask_carrera = df_proc[COL_CARRERA] == carrera_sel
    mask_verde   = df_proc['Semáforo Vocacional'] == 'Verde'
    if df_proc.loc[mask_carrera & mask_verde, ref_cols].empty:
        ref_df = df_proc.loc[mask_carrera, ref_cols]
        referencia = "Promedio general de la carrera (no hay estudiantes *Verde*)."
    else:
        ref_df = df_proc.loc[mask_carrera & mask_verde, ref_cols]
        referencia = "Promedio del grupo *Verde* de la carrera."

    grupo_vec  = ref_df.mean().astype(float)
    alumno_vec = df_proc.loc[alumno_mask, ref_cols].iloc[0].astype(float)

    df_comp = pd.DataFrame({
        "Letra": AREAS,
        "Alumno": [alumno_vec[f"TOTAL_{a}"] for a in AREAS],
        "Referencia": [grupo_vec[f"TOTAL_{a}"] for a in AREAS],
    })
    df_comp["Δ (Alumno - Referencia)"] = df_comp["Alumno"] - df_comp["Referencia"]

    fortalezas = (
        df_comp[df_comp["Δ (Alumno - Referencia)"] > 0]
        .sort_values("Δ (Alumno - Referencia)", ascending=False)[["Letra","Δ (Alumno - Referencia)"]]
    )
    brechas_serie = (df_comp["Referencia"] - df_comp["Alumno"]).rename("Brecha")
    top3_reforzar = brechas_serie.sort_values(ascending=False).head(3)
    top3_reforzar = top3_reforzar[top3_reforzar > 0]

    st.markdown(f"### Referencia utilizada\n_{referencia}_")

    st.markdown("### ✅ Fortalezas destacadas")
    if fortalezas.empty:
        st.info("No se observan letras por encima de la referencia en este momento.")
    else:
        for _, r in fortalezas.iterrows():
            st.markdown(f"- **{r['Letra']}**: {r['Δ (Alumno - Referencia)']:.2f} puntos por arriba de la referencia.")

    st.markdown("### 🛠️ Áreas por reforzar (principales brechas)")
    if top3_reforzar.empty:
        st.info("El estudiante se encuentra a la par o por encima de la referencia en todas las letras.")
    else:
        for letra, gap in top3_reforzar.items():
            st.markdown(f"- **{letra}**: {gap:.2f} puntos por debajo de la referencia.")

    st.divider()

    # Coherencia vocacional
    st.markdown("## 🎯 Coherencia vocacional (elección vs perfil CHASIDE)")
    area_fuerte = al['Area_Fuerte_Ponderada']
    perfil_sel = PERFIL_CARRERAS.get(str(carrera_sel).strip())
    if perfil_sel:
        if area_fuerte in perfil_sel.get('Fuerte', []):
            coincidencia = "Coherente"
        elif area_fuerte in perfil_sel.get('Baja', []):
            coincidencia = "Requiere orientación"
        else:
            coincidencia = "Neutral"
    else:
        coincidencia = "Sin perfil definido"
    sugeridas = [c for c,p in PERFIL_CARRERAS.items() if area_fuerte in p.get('Fuerte',[])]

    st.markdown(
        f"""
**Área fuerte (CHASIDE):** **{area_fuerte}**  
**Evaluación de coherencia con la carrera elegida:** **{coincidencia}**
"""
    )
    if coincidencia != "Coherente":
        if sugeridas:
            st.markdown("**Carreras con mayor afinidad al perfil del estudiante:** " + ", ".join(sugeridas))
        else:
            st.markdown("_No se encontraron sugerencias basadas en el área fuerte._")

# ============================================
# MÓDULO 4 · Equipo de trabajo
# ============================================
def render_equipo():
    st.header("👥 Equipo de trabajo")
    st.markdown("""
    Este proyecto fue elaborado por el siguiente equipo interdisciplinario:

    - **Dra. Elena Elsa Bricio Barrios** – Especialista en Psicología Educativa  
    - **Dr. Santiago Arceo-Díaz** – Investigador en Ciencias Médicas y Datos  
    - **Psic. Martha Cecilia Ramírez Guzmán** – Psicóloga orientada al desarrollo vocacional
    """)
    st.caption("Tecnológico Nacional de México – Instituto Tecnológico de Colima")

# ============================================
# UI principal con barra lateral (sidebar)
# ============================================
st.title("📊 CHASIDE – Diagnóstico Vocacional")

# Entrada URL (una vez, para toda la app)
with st.sidebar:
    st.header("⚙️ Configuración")
    sheet_url = st.text_input("URL de Google Sheets (CSV export)", DEFAULT_SHEET_URL)
    peso_intereses = st.slider("Ponderación de Intereses", 0.0, 1.0, 0.8, 0.05)
    st.caption(f"Intereses: **{peso_intereses:.2f}** · Aptitudes: **{1-peso_intereses:.2f}**")

    st.header("🧭 Navegación")
    modulo = st.radio("Selecciona un módulo", [
        "📘 Presentación",
        "📈 Información general",
        "🧾 Información individual",
        "👥 Equipo de trabajo"
    ])

# Carga + procesamiento único
try:
    df_raw = load_csv(sheet_url)
    df_proc = procesar_chaside(df_raw, peso_intereses=peso_intereses)
except Exception as e:
    if modulo == "📘 Presentación":
        render_presentacion()
        st.error(f"No fue posible cargar/procesar datos: {e}")
        st.stop()
    else:
        st.error(f"No fue posible cargar/procesar datos: {e}")
        st.stop()

# Router de módulos
if modulo == "📘 Presentación":
    render_presentacion()
elif modulo == "📈 Información general":
    render_info_general(df_proc)
elif modulo == "🧾 Información individual":
    render_info_individual(df_proc)
elif modulo == "👥 Equipo de trabajo":
    render_equipo()
