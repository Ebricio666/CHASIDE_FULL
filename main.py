# ============================================================
# CHASIDE • App completa con 4 módulos (Streamlit)
# ============================================================
# Requisitos mínimos:
#   streamlit
#   pandas
#   numpy
#   plotly
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -----------------------
# Estilos y constantes UI
# -----------------------
PRIMARY = "#0F766E"    # teal-700
ACCENT  = "#14B8A6"    # teal-400
SLATE   = "#475569"    # slate-600
GREEN   = "#22c55e"
AMBER   = "#f59e0b"
RED     = "#ef4444"
GRAY    = "#6b7280"
BLUE    = "#3b82f6"

# Mapeo de categorías internas → etiquetas UI profesionales
CAT_INT_ORDER = ["Verde", "Amarillo", "Rojo", "No aceptable"]
CAT_INT_TO_UI = {
    "Verde":        "Perfil congruente con la carrera seleccionada",
    "Amarillo":     "Perfil incongruente al seleccionado",
    "Rojo":         "Perfil no definido",
    "No aceptable": "Respuestas no válidas (sesgo de respuesta)"
}
CAT_UI_ORDER = [
    "Perfil congruente con la carrera seleccionada",
    "Perfil incongruente al seleccionado",
    "Perfil no definido",
    "Respuestas no válidas (sesgo de respuesta)"
]
CAT_UI_COLORS = {
    "Perfil congruente con la carrera seleccionada": GREEN,
    "Perfil incongruente al seleccionado": AMBER,
    "Perfil no definido": RED,
    "Respuestas no válidas (sesgo de respuesta)": GRAY,
}

# Descripciones CHASIDE (para reporte individual)
DESC_CHASIDE = {
    "C": "Organización, supervisión, orden, análisis y síntesis, colaboración, cálculo.",
    "H": "Precisión verbal, organización, relación de hechos, justicia, persuasión.",
    "A": "Estético y creativo; detallista, innovador, intuitivo; habilidades visuales, auditivas y manuales.",
    "S": "Asistir y ayudar; investigación, precisión, percepción, análisis; altruismo y paciencia.",
    "I": "Cálculo y pensamiento científico/crítico; exactitud, planificación; enfoque práctico.",
    "D": "Justicia y equidad; colaboración, liderazgo; valentía y toma de decisiones.",
    "E": "Investigación; orden, análisis y síntesis; cálculo numérico, observación; método y seguridad."
}

# -----------------------
# Config general de página
# -----------------------
st.set_page_config(page_title="CHASIDE • App", layout="wide")

st.markdown(f"""
<style>
.block-container {{ padding-top: 1.0rem; }}
.h1-title {{ font-size: 1.9rem; font-weight: 800; color:{PRIMARY}; margin-bottom:.25rem; }}
.subtitle {{ color:#64748B; margin-bottom: 1.0rem; }}
.section-title {{ font-weight:700; font-size:1.1rem; margin: 1.1rem 0 .4rem 0; color:{PRIMARY}; }}
.card {{
  border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px 16px; background:#fff;
  box-shadow:0 2px 8px rgba(0,0,0,.04);
}}
.badge {{
  display:inline-block; padding: 4px 10px; border-radius: 999px; font-weight:700; font-size:.85rem;
  background: rgba(20,184,166,0.12); color:{PRIMARY};
}}
.kpi {{ font-size:1.02rem; }}
.kpi b {{ color:{SLATE}; }}
.list-tight li {{ margin-bottom:.2rem; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# Utilidades de datos
# ============================================================

def load_csv(url: str) -> pd.DataFrame:
    """Carga CSV remoto. Maneja errores y limpia columnas básicas."""
    df = pd.read_csv(url)
    df.columns = [str(c) for c in df.columns]
    return df

def process_chaside(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Aplica todo el pipeline CHASIDE y genera columnas auxiliares y etiquetas UI."""
    df = df_raw.copy()

    # --- columnas base
    columna_carrera = '¿A qué carrera desea ingresar?'
    columna_nombre  = 'Ingrese su nombre completo'

    if columna_carrera not in df.columns or columna_nombre not in df.columns:
        raise ValueError(
            f"Columnas faltantes. Se requieren: '{columna_carrera}' y '{columna_nombre}'. "
            f"Columnas disponibles: {list(df.columns)}"
        )

    # normalizar a string
    df[columna_carrera] = df[columna_carrera].astype(str)
    df[columna_nombre]  = df[columna_nombre].astype(str)

    # --- ítems F:CV (98)
    columnas_items = df.columns[5:103]

    # Sí/No → 1/0
    df_items = (
        df[columnas_items].astype(str).apply(lambda c: c.str.strip().str.lower())
          .replace({'sí':1,'si':1,'s':1,'1':1,'true':1,'verdadero':1,'x':1,
                    'no':0,'n':0,'0':0,'false':0,'falso':0,'':'0','nan':0})
          .apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    )
    df[columnas_items] = df_items

    # Coincidencia (sesgo)
    suma_si = df[columnas_items].sum(axis=1)
    total_items = len(columnas_items)
    pct_si = np.where(total_items==0, 0, suma_si/total_items)
    pct_no = 1 - pct_si
    df['Coincidencia'] = np.maximum(pct_si, pct_no)

    # Mapeo CHASIDE
    areas = ['C','H','A','S','I','D','E']
    intereses_items = {
        'C':[1,12,20,53,64,71,78,85,91,98],
        'H':[9,25,34,41,56,67,74,80,89,95],
        'A':[3,11,21,28,36,45,50,57,81,96],
        'S':[8,16,23,33,44,52,62,70,87,92],
        'I':[6,19,27,38,47,54,60,75,83,97],
        'D':[5,14,24,31,37,48,58,65,73,84],
        'E':[17,32,35,42,49,61,68,77,88,93]
    }
    aptitudes_items = {
        'C':[2,15,46,51],
        'H':[30,63,72,86],
        'A':[22,39,76,82],
        'S':[4,29,40,69],
        'I':[10,26,59,90],
        'D':[13,18,43,66],
        'E':[7,55,79,94]
    }
    def col_item(i:int)->str: return columnas_items[i-1]

    for a in areas:
        df[f'INTERES_{a}']  = df[[col_item(i) for i in intereses_items[a]]].sum(axis=1)
        df[f'APTITUD_{a}'] = df[[col_item(i) for i in aptitudes_items[a]]].sum(axis=1)

    # Ponderación fija
    peso_intereses, peso_aptitudes = 0.8, 0.2
    for a in areas:
        df[f'PUNTAJE_COMBINADO_{a}'] = df[f'INTERES_{a}']*peso_intereses + df[f'APTITUD_{a}']*peso_aptitudes

    # Área fuerte ponderada
    df['Area_Fuerte_Ponderada'] = df.apply(lambda r: max(areas, key=lambda a: r[f'PUNTAJE_COMBINADO_{a}']), axis=1)

    # Score combinado (para rankings/violín)
    score_cols = [f'PUNTAJE_COMBINADO_{a}' for a in areas]
    df['Score'] = df[score_cols].max(axis=1)

    # Totales por letra (INTERES + APTITUD) para radar/individual
    for a in areas:
        df[f'TOTAL_{a}'] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']

    # Perfiles por carrera (coherencia)
    perfil_carreras = {
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
    def evaluar(area_chaside, carrera):
        p = perfil_carreras.get(str(carrera).strip())
        if not p: return 'Sin perfil definido'
        if area_chaside in p.get('Fuerte',[]): return 'Coherente'
        if area_chaside in p.get('Baja',[]):   return 'Requiere Orientación'
        return 'Neutral'

    df['Coincidencia_Ponderada'] = df.apply(lambda r: evaluar(r['Area_Fuerte_Ponderada'], r[columna_carrera]), axis=1)

    def carrera_mejor(r):
        if r['Coincidencia'] >= 0.75:
            return 'Información no aceptable'
        a = r['Area_Fuerte_Ponderada']
        c_actual = str(r[columna_carrera]).strip()
        sugeridas = [c for c,p in perfil_carreras.items() if a in p.get('Fuerte',[])]
        return c_actual if c_actual in sugeridas else (', '.join(sugeridas) if sugeridas else 'Sin sugerencia clara')

    def diagnostico(r):
        if r['Carrera_Mejor_Perfilada']=='Información no aceptable': return 'Información no aceptable'
        if str(r[columna_carrera]).strip()==str(r['Carrera_Mejor_Perfilada']).strip(): return 'Perfil adecuado'
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

    # Etiqueta UI profesional
    df['Categoría_UI'] = df['Semáforo Vocacional'].map(CAT_INT_TO_UI).fillna("Sin sugerencia")
    df['Categoría_UI'] = pd.Categorical(df['Categoría_UI'], categories=CAT_UI_ORDER, ordered=True)

    return df, columna_carrera, columna_nombre

# ============================================================
# Módulo 1 · Presentación
# ============================================================
def render_presentacion():
    st.markdown('<div class="h1-title">Diagnóstico Vocacional – Escala CHASIDE</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Aplicación de apoyo a la elección de carrera universitaria</div>', unsafe_allow_html=True)

    with st.container():
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
sostener la motivación y <b>reducir el riesgo de abandono o frustración</b>. Estos factores son
determinantes para <b>persistir y desempeñarse</b> durante la vida universitaria.
""")

    st.markdown('<div class="section-title">¿Qué es la escala CHASIDE?</div>', unsafe_allow_html=True)
    st.markdown("""
<b>CHASIDE</b> integra <b>intereses</b> y <b>aptitudes</b> en siete áreas:
<b>C</b> Administrativa, <b>H</b> Humanidades y Sociales, <b>A</b> Artística, <b>S</b> Salud,
<b>I</b> Técnicas, <b>D</b> Defensa y Seguridad, <b>E</b> Experimentales.
""")

    st.markdown('<div class="section-title">Propuesta Única de Valor (PUV)</div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="card">
<b>Orientación vocacional personalizada</b>, basada en evidencia (CHASIDE),
con visualizaciones claras y reportes descargables para acompañamiento académico.
</div>
""", unsafe_allow_html=True)

# ============================================================
# Módulo 2 · Información general
# (Incluye Pastel, Barras apiladas, Violín, y Radar Verde vs Amarillo)
# ============================================================
def render_info_general(df: pd.DataFrame, columna_carrera: str):
    st.markdown('<div class="h1-title">Información general</div>', unsafe_allow_html=True)
    st.caption("Resumen global por categoría, carrera y comparativas Verde vs Amarillo.")

    # ---- Pastel (solo %)
    st.subheader("🥧 Distribución general por categoría")
    resumen = (
        df['Categoría_UI']
          .value_counts()
          .reindex(CAT_UI_ORDER, fill_value=0)
          .rename_axis('Categoría_UI')
          .reset_index(name='N')
    )
    fig_pie = px.pie(
        resumen,
        names='Categoría_UI',
        values='N',
        hole=0.35,
        color='Categoría_UI',
        color_discrete_map=CAT_UI_COLORS,
        title="Distribución general por categoría"
    )
    fig_pie.update_traces(textposition='inside', texttemplate='%{percent:.1%}')
    fig_pie.update_layout(legend_title_text="Categoría")
    st.plotly_chart(fig_pie, use_container_width=True)

    # ---- Barras apiladas por carrera
    st.subheader("🏫 Distribución por carrera y categoría")
    stacked = (
        df.groupby([columna_carrera, 'Categoría_UI'])
          .size()
          .reset_index(name='N')
    )
    stacked['Categoría_UI'] = pd.Categorical(stacked['Categoría_UI'],
                                             categories=CAT_UI_ORDER,
                                             ordered=True)

    modo = st.radio(
        "Modo de visualización",
        ["Proporción (100% apilado)", "Valores absolutos"],
        horizontal=True, index=0
    )

    if modo == "Proporción (100% apilado)":
        stacked['%'] = stacked.groupby(columna_carrera)['N'] \
                              .transform(lambda x: 0 if x.sum()==0 else x/x.sum()*100)
        fig_stacked = px.bar(
            stacked, x=columna_carrera, y='%',
            color='Categoría_UI',
            category_orders={'Categoría_UI': CAT_UI_ORDER},
            color_discrete_map=CAT_UI_COLORS,
            barmode='stack',
            text=stacked['%'].round(1).astype(str) + '%',
            title="Proporción (%) por carrera"
        )
        fig_stacked.update_layout(
            yaxis_title="Proporción (%)",
            xaxis_title="Carrera",
            xaxis_tickangle=-30
        )
    else:
        fig_stacked = px.bar(
            stacked, x=columna_carrera, y='N',
            color='Categoría_UI',
            category_orders={'Categoría_UI': CAT_UI_ORDER},
            color_discrete_map=CAT_UI_COLORS,
            barmode='stack',
            text='N',
            title="Número de estudiantes por carrera"
        )
        fig_stacked.update_layout(
            yaxis_title="Número de estudiantes",
            xaxis_title="Carrera",
            xaxis_tickangle=-30
        )
        fig_stacked.update_traces(textposition='inside')

    st.plotly_chart(fig_stacked, use_container_width=True)

    # ---- Violín: Verde vs Amarillo (Score) por carrera
    st.subheader("🎻 Distribución de puntajes (Violin) – Verde vs Amarillo por carrera")
    verde_ui = CAT_INT_TO_UI['Verde']
    amarillo_ui = CAT_INT_TO_UI['Amarillo']
    df_violin = df[df['Categoría_UI'].isin([verde_ui, amarillo_ui])].copy()

    if df_violin.empty:
        st.info("No hay estudiantes en categorías Verde o Amarillo para graficar.")
    else:
        fig_violin = px.violin(
            df_violin,
            x=columna_carrera,
            y="Score",
            color="Categoría_UI",
            box=True,
            points=False,  # sin puntos (densidad indica cantidad)
            color_discrete_map=CAT_UI_COLORS,
            category_orders={"Categoría_UI":[verde_ui, amarillo_ui]},
            title="Distribución de Score por carrera (Verde vs Amarillo)"
        )

        # líneas punteadas entre carreras
        categorias = list(df_violin[columna_carrera].unique())
        categorias.sort()
        for i in range(len(categorias) - 1):
            fig_violin.add_vline(
                x=i + 0.5,
                line_width=1,
                line_dash="dot",
                line_color="gray"
            )

        fig_violin.update_layout(
            xaxis_title="Carrera",
            yaxis_title="Score (máximo ponderado CHASIDE)",
            xaxis_tickangle=-30,
            legend_title_text="Categoría"
        )
        st.plotly_chart(fig_violin, use_container_width=True)

    # ---- Radar Verde vs Amarillo por carrera (promedio TOTAL_* por letra)
    st.subheader("🕸️ Radar CHASIDE – Comparación Verde vs Amarillo por carrera")

    carreras_disp = sorted(df[columna_carrera].dropna().unique())
    if not carreras_disp:
        st.info("No hay carreras para mostrar en el radar.")
        return

    carrera_sel = st.selectbox("Elige una carrera para comparar:", carreras_disp)
    sub = df[df[columna_carrera] == carrera_sel]
    sub = sub[sub['Categoría_UI'].isin([verde_ui, amarillo_ui])]

    areas = ['C','H','A','S','I','D','E']
    if sub.empty or sub['Categoría_UI'].nunique() < 2:
        st.warning("No hay datos suficientes de Verde y Amarillo en esta carrera.")
    else:
        # promedios por letra (INTERES + APTITUD)
        for a in areas:
            if f'TOTAL_{a}' not in sub.columns:
                sub[f'TOTAL_{a}'] = sub[f'INTERES_{a}'] + sub[f'APTITUD_{a}']

        prom = sub.groupby('Categoría_UI')[[f'TOTAL_{a}' for a in areas]].mean()
        prom_ren = prom.rename(columns={f'TOTAL_{a}':a for a in areas}).reset_index()

        fig_radar = px.line_polar(
            prom_ren.melt(id_vars='Categoría_UI', value_vars=areas, var_name='Área', value_name='Promedio'),
            r='Promedio',
            theta='Área',
            color='Categoría_UI',
            line_close=True,
            markers=True,
            color_discrete_map=CAT_UI_COLORS,
            category_orders={'Categoría_UI':[verde_ui, amarillo_ui]},
            title=f"Perfil CHASIDE – {carrera_sel} (Verde vs Amarillo)"
        )
        fig_radar.update_traces(fill='toself', opacity=0.75)
        st.plotly_chart(fig_radar, use_container_width=True)

        # Top 3 brechas (Verde - Amarillo)
        diffs = (prom.loc[verde_ui] - prom.loc[amarillo_ui]).rename(index=lambda x: x.replace("TOTAL_",""))
        diffs = diffs.sort_values(ascending=False)
        top3 = diffs.head(3)

        st.markdown("**Áreas a reforzar (donde *Amarillo* está más bajo):**")
        for letra, delta in top3.items():
            st.markdown(f"- **{letra}** (Δ = {delta:.2f}) — {DESC_CHASIDE[letra]}")

# ============================================================
# Módulo 3 · Información particular del estudiantado
# (Reporte ejecutivo individual + descargas)
# ============================================================
def render_info_individual(df: pd.DataFrame, columna_carrera: str, columna_nombre: str):
    st.markdown('<div class="h1-title">Información particular del estudiantado</div>', unsafe_allow_html=True)
    st.caption("Reporte ejecutivo individual con indicadores y recomendaciones.")

    # Selector carrera / alumno
    carreras = sorted(df[columna_carrera].dropna().unique())
    if not carreras:
        st.warning("No hay carreras disponibles en el archivo.")
        return
    carrera_sel = st.selectbox("Carrera a evaluar:", carreras, index=0)

    d_carrera = df[df[columna_carrera] == carrera_sel].copy()
    if d_carrera.empty:
        st.warning("No hay estudiantes para esta carrera.")
        return

    nombres = sorted(d_carrera[columna_nombre].astype(str).unique())
    est_sel = st.selectbox("Estudiante:", nombres, index=0)

    alumno_mask = (df[columna_carrera] == carrera_sel) & (df[columna_nombre].astype(str) == est_sel)
    alumno = df[alumno_mask].copy()
    if alumno.empty:
        st.warning("No se encontró el estudiante seleccionado.")
        return
    al = alumno.iloc[0]

    # KPIs
    cat_ui = al['Categoría_UI']
    total_carrera = len(d_carrera)
    n_cat = int((d_carrera['Categoría_UI'] == cat_ui).sum())
    pct_cat = (n_cat / total_carrera * 100) if total_carrera else 0.0

    # Indicador de riesgo
    verde_ui = CAT_INT_TO_UI['Verde']
    amarillo_ui = CAT_INT_TO_UI['Amarillo']
    verde_carr = d_carrera[d_carrera['Categoría_UI'] == verde_ui].copy()
    amar_carr  = d_carrera[d_carrera['Categoría_UI'] == amarillo_ui].copy()

    indicador = "Alumno regular"
    if not verde_carr.empty and est_sel in (verde_carr.sort_values('Score', ascending=False).head(5)[columna_nombre].astype(str).tolist()):
        indicador = "Joven promesa"
    if not amar_carr.empty and est_sel in (amar_carr.sort_values('Score', ascending=True).head(5)[columna_nombre].astype(str).tolist()):
        indicador = "Alumno en riesgo de reprobar"

    # Referencia para comparativos
    areas = ['C','H','A','S','I','D','E']
    ref_cols = [f'TOTAL_{a}' for a in areas]
    mask_carr = df[columna_carrera] == carrera_sel
    mask_verde = df['Categoría_UI'] == verde_ui
    ref_df = df.loc[mask_carr & mask_verde, ref_cols] if not df.loc[mask_carr & mask_verde, ref_cols].empty else df.loc[mask_carr, ref_cols]
    ref_vec = ref_df.mean().astype(float)
    al_vec  = df.loc[alumno_mask, ref_cols].iloc[0].astype(float)
    diff    = (al_vec - ref_vec)

    fortalezas = diff[diff > 0].sort_values(ascending=False)
    oportunidades = diff[diff < 0].abs().sort_values(ascending=False)

    # UI KPIs
    st.markdown("## 🧾 Reporte ejecutivo individual")
    c1, c2, c3, c4 = st.columns([2.2, 2, 2.6, 2])
    with c1: st.markdown(f"<div class='card kpi'><b>Nombre del estudiante</b><br>{est_sel}</div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='card kpi'><b>Carrera</b><br>{carrera_sel}</div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card kpi'><b>Categoría identificada</b><br><span style='font-weight:700;color:{BLUE}'>{cat_ui}</span></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='card kpi'><b>Nº en esta categoría</b><br>{n_cat} (<span style='font-weight:700'>{pct_cat:.1f}%</span>)</div>", unsafe_allow_html=True)

    badge_color = {"Joven promesa": GREEN, "Alumno en riesgo de reprobar": AMBER}.get(indicador, SLATE)
    st.markdown(
        f"<span class='badge' style='background:rgba(20,184,166,.12);color:{badge_color}'>Indicador: {indicador}</span>",
        unsafe_allow_html=True
    )
    st.divider()

    st.markdown("### ✅ Fortalezas destacadas")
    if fortalezas.empty:
        st.info("No se observan dimensiones por encima del promedio de referencia del grupo.")
    else:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for letra_full, delta in fortalezas.items():
            k = str(letra_full).replace("TOTAL_", "")
            st.markdown(f"<li><b>{k}</b> (+{delta:.2f}) — {DESC_CHASIDE[k]}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    st.markdown("### 🛠️ Áreas de oportunidad")
    if oportunidades.empty:
        st.info("El estudiante no presenta brechas importantes respecto al grupo.")
    else:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for letra_full, gap in oportunidades.items():
            k = str(letra_full).replace("TOTAL_", "")
            st.markdown(f"<li><b>{k}</b> (−{gap:.2f}) — {DESC_CHASIDE[k]}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    st.divider()

    st.markdown("### 🎯 Coherencia vocacional y afinidades")
    area_fuerte = al['Area_Fuerte_Ponderada']
    perfil_carreras = {
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
    perfil_sel = perfil_carreras.get(str(carrera_sel).strip())
    if perfil_sel:
        if area_fuerte in perfil_sel.get('Fuerte', []): coh_text = "Coherente"
        elif area_fuerte in perfil_sel.get('Baja', []): coh_text = "Requiere orientación"
        else: coh_text = "Neutral"
    else:
        coh_text = "Sin perfil definido"

    sugeridas = sorted([c for c,p in perfil_carreras.items() if area_fuerte in p.get('Fuerte', [])])

    st.write(f"- **Área fuerte (CHASIDE):** {area_fuerte}")
    st.write(f"- **Evaluación de coherencia con la carrera elegida:** {coh_text}")

    st.markdown("### 📚 Carreras con mayor afinidad al perfil (según CHASIDE)")
    if sugeridas:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for c in sugeridas:
            st.markdown(f"<li>{c}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
    else:
        st.info("No se identificaron carreras afines basadas en el área fuerte.")

    st.divider()

    # Descargas
    def resumen_para(alumno_row: pd.Series) -> dict:
        a_mask = (df[columna_carrera]==carrera_sel) & (df[columna_nombre].astype(str)==str(alumno_row[columna_nombre]))
        a_vec  = df.loc[a_mask, [f'TOTAL_{x}' for x in areas]].iloc[0].astype(float)
        diffs  = (a_vec - ref_vec)
        fort   = [k.replace("TOTAL_","") for k,v in diffs.items() if v>0]
        opp    = [k.replace("TOTAL_","") for k,v in diffs.items() if v<0]
        ind = "Alumno regular"
        if not verde_carr.empty and alumno_row[columna_nombre] in (verde_carr.sort_values('Score', ascending=False).head(5)[columna_nombre].astype(str).tolist()):
            ind = "Joven promesa"
        if not amar_carr.empty and alumno_row[columna_nombre] in (amar_carr.sort_values('Score', ascending=True).head(5)[columna_nombre].astype(str).tolist()):
            ind = "Alumno en riesgo de reprobar"
        cat_local = alumno_row['Categoría_UI']
        n_local = int((d_carrera['Categoría_UI']==cat_local).sum())
        pct_local = (n_local/total_carrera*100) if total_carrera else 0.0
        area_f = alumno_row['Area_Fuerte_Ponderada']
        suger = ", ".join(sorted([c for c,p in perfil_carreras.items() if area_f in p.get('Fuerte', [])]))
        return {
            "Nombre": str(alumno_row[columna_nombre]),
            "Carrera": carrera_sel,
            "Categoría": cat_local,
            "N en categoría (carrera)": n_local,
            "% en categoría (carrera)": round(pct_local,1),
            "Indicador": ind,
            "Área fuerte CHASIDE": area_f,
            "Carreras afines (CHASIDE)": suger,
            "Fortalezas (letras)": ", ".join(fort),
            "Áreas de oportunidad (letras)": ", ".join(opp),
        }

    # Para descargas necesitamos ref_vec (ya calculada arriba)
    ref_cols = [f'TOTAL_{a}' for a in areas]
    mask_carr = df[columna_carrera] == carrera_sel
    mask_verde = df['Categoría_UI'] == CAT_INT_TO_UI['Verde']
    ref_df = df.loc[mask_carr & mask_verde, ref_cols] if not df.loc[mask_carr & mask_verde, ref_cols].empty else df.loc[mask_carr, ref_cols]
    ref_vec = ref_df.mean().astype(float)

    col_a, col_b = st.columns([1.2, 1])
    with col_a:
        data_ind = pd.DataFrame([resumen_para(al)])
        st.download_button(
            "⬇️ Descargar reporte individual (CSV)",
            data=data_ind.to_csv(index=False).encode("utf-8"),
            file_name=f"reporte_individual_{est_sel}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_b:
        data_all = pd.DataFrame([resumen_para(r) for _, r in d_carrera.iterrows()])
        st.download_button(
            "⬇️ Descargar reporte de la carrera (CSV)",
            data=data_all.to_csv(index=False).encode("utf-8"),
            file_name=f"reporte_carrera_{carrera_sel}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ============================================================
# Módulo 4 · Equipo de trabajo
# ============================================================
def render_equipo():
    st.markdown('<div class="h1-title">Equipo de trabajo</div>', unsafe_allow_html=True)
    st.markdown("""
Este proyecto fue elaborado por el siguiente equipo interdisciplinario:

- **Dra. Elena Elsa Bricio Barrios** – Especialista en Psicología Educativa  
- **Dr. Santiago Arceo-Díaz** – Investigador en Ciencias Médicas y Datos  
- **Psic. Martha Cecilia Ramírez Guzmán** – Psicóloga orientada al desarrollo vocacional
""")
    st.caption("Tecnológico Nacional de México – Instituto Tecnológico de Colima")

# ============================================================
# App: barra lateral y ruteo
# ============================================================
def main():
    st.sidebar.title("CHASIDE • Navegación")
    modulo = st.sidebar.radio(
        "Selecciona un módulo",
        ["Presentación", "Información general", "Información individual", "Equipo de trabajo"],
        index=0
    )

    st.sidebar.markdown("---")
    url = st.sidebar.text_input(
        "URL de Google Sheets (CSV export)",
        "https://docs.google.com/spreadsheets/d/1BNAeOSj2F378vcJE5-T8iJ8hvoseOleOHr-I7mVfYu4/export?format=csv"
    )

    if modulo == "Presentación":
        render_presentacion()
        return

    try:
        df_raw = load_csv(url)
        df_proc, columna_carrera, columna_nombre = process_chaside(df_raw)
    except Exception as e:
        st.error(f"❌ No fue posible cargar/procesar el archivo: {e}")
        return

    if modulo == "Información general":
        render_info_general(df_proc, columna_carrera)

    elif modulo == "Información individual":
        render_info_individual(df_proc, columna_carrera, columna_nombre)

    elif modulo == "Equipo de trabajo":
        render_equipo()

if __name__ == "__main__":
    main()
