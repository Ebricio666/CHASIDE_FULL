# app.py
# =========================================================
# CHASIDE • App completa con 4 módulos y barra lateral
# =========================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ------------------------
# Estilos / Colores
# ------------------------
PRIMARY = "#0F766E"      # teal-700
ACCENT  = "#14B8A6"      # teal-400
SLATE   = "#475569"
GREEN   = "#22c55e"
AMBER   = "#f59e0b"
GRAY    = "#6b7280"
GRAY_LT = "#94a3b8"

st.set_page_config(page_title="CHASIDE • App", layout="wide")

st.markdown(f"""
<style>
.block-container {{ padding-top: 0.75rem; padding-bottom: 1.25rem; }}
.h1-title {{
  font-size: 2.0rem; font-weight: 800; color: {PRIMARY}; margin-bottom: .25rem;
}}
.subtitle {{ color: #64748B; margin-bottom: 1.0rem; }}
.section-title {{
  font-weight: 700; font-size: 1.1rem; margin: 1.0rem 0 .2rem 0; color: {PRIMARY};
}}
.card {{
  border: 1px solid #e5e7eb; border-radius: 16px; padding: 14px 16px;
  background: #ffffff; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}}
.badge {{
  display:inline-block; padding: 4px 10px; border-radius: 999px;
  background: rgba(20,184,166,0.12); color:{PRIMARY}; font-weight: 700;
}}
.puv {{
  border-left: 6px solid {ACCENT}; padding: 12px 14px; background: #f8fffd;
  border-radius: 10px; font-size: 1.02rem;
}}
.kpi {{ font-size:1.05rem; margin:.15rem 0; }}
.kpi b {{ color:{SLATE}; }}
.list-tight li {{ margin-bottom:.2rem; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# Utilidades de datos
# =========================================================
DEFAULT_SHEET = "https://docs.google.com/spreadsheets/d/1BNAeOSj2F378vcJE5-T8iJ8hvoseOleOHr-I7mVfYu4/export?format=csv"
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
    'C':[2,15,46,51], 'H':[30,63,72,86], 'A':[22,39,76,82],
    'S':[4,29,40,69], 'I':[10,26,59,90], 'D':[13,18,43,66], 'E':[7,55,79,94]
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

# Nombres 'pro' (renombrado profesional de categorías)
CAT_MAP_TO_UI = {
    'Verde': 'Perfil congruente a la carrera seleccionada',
    'Amarillo': 'Perfil incongruente a la carrera seleccionada',
    'Rojo': 'Sin perfil definido',
    'Sin sugerencia': 'Sin perfil definido',
    'No aceptable': 'Respuestas inconsistentes (≥75% iguales)',
}
CAT_UI_ORDER = [
    'Perfil congruente a la carrera seleccionada',
    'Perfil incongruente al seleccionado',
    'Sin perfil definido',
    'Respuestas inconsistentes (≥75% iguales)',
]
CAT_UI_COLORS = {
    'Perfil congruente a la carrera seleccionada': GREEN,
    'Perfil incongruente a la carrera seleccionada': AMBER,
    'Sin perfil definido': GRAY,
    'Respuestas inconsistentes (≥75% iguales)': GRAY_LT,
}

DESC_CHASIDE = {
    "C": "Organización, supervisión, orden, análisis y síntesis, colaboración, cálculo.",
    "H": "Precisión verbal, organización, relación de hechos, justicia, persuasión.",
    "A": "Estético/creativo; detalle, innovación; habilidades visuales, auditivas y manuales.",
    "S": "Asistir y ayudar; investigación, precisión, análisis; altruismo y paciencia.",
    "I": "Cálculo y pensamiento científico/crítico; exactitud; planificación; enfoque práctico.",
    "D": "Justicia y equidad; colaboración, liderazgo; toma de decisiones.",
    "E": "Investigación; orden; análisis/síntesis; cálculo numérico; observación; método."
}

@st.cache_data(show_spinner=False)
def load_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

def preprocess_chaside(df: pd.DataFrame) -> pd.DataFrame:
    """ Realiza todo el pipeline CHASIDE y añade columnas necesarias. """
    df = df.copy()
    # Detectar columnas clave
    columnas_items = df.columns[5:103]
    columna_carrera = '¿A qué carrera desea ingresar?'
    columna_nombre  = 'Ingrese su nombre completo'

    # Sanitizar Sí/No → 1/0  (FIX: usar .str.strip().str.lower())
    df_items = (
        df[columnas_items]
          .astype(str)
          .apply(lambda s: s.str.strip().str.lower())
          .replace({'sí':1,'si':1,'s':1,'1':1,'true':1,'verdadero':1,'x':1,
                    'no':0,'n':0,'0':0,'false':0,'falso':0,'':'0','nan':0})
          .apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    )
    df[columnas_items] = df_items

    # Coincidencia (sesgo)
    suma_si = df[columnas_items].sum(axis=1)
    total_items = len(columnas_items)
    pct_si = np.where(total_items==0, 0, suma_si/total_items)
    df['Coincidencia'] = np.maximum(pct_si, 1 - pct_si)

    # Mapear items a áreas
    def col_item(i:int)->str: return columnas_items[i-1]
    for a in AREAS:
        df[f'INTERES_{a}']  = df[[col_item(i) for i in INTERESES_ITEMS[a]]].sum(axis=1)
        df[f'APTITUD_{a}'] = df[[col_item(i) for i in APTITUDES_ITEMS[a]]].sum(axis=1)

    # Ponderación fija 80/20
    peso_intereses, peso_aptitudes = 0.8, 0.2
    for a in AREAS:
        df[f'PUNTAJE_COMBINADO_{a}'] = df[f'INTERES_{a}']*peso_intereses + df[f'APTITUD_{a}']*peso_aptitudes
        df[f'TOTAL_{a}'] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']

    # Área fuerte ponderada
    df['Area_Fuerte_Ponderada'] = df.apply(lambda r: max(AREAS, key=lambda a: r[f'PUNTAJE_COMBINADO_{a}']), axis=1)

    # Coincidencia con carrera (Coherente/Neutral/Requiere)
    def evaluar(area_chaside, carrera):
        p = PERFIL_CARRERAS.get(str(carrera).strip())
        if not p: return 'Sin perfil definido'
        if area_chaside in p.get('Fuerte',[]): return 'Coherente'
        if area_chaside in p.get('Baja',[]):   return 'Requiere Orientación'
        return 'Neutral'
    df['Coincidencia_Ponderada'] = df.apply(lambda r: evaluar(r['Area_Fuerte_Ponderada'], r[columna_carrera]), axis=1)

    # Diagnóstico y semáforo
    def carrera_mejor(r):
        if r['Coincidencia'] >= 0.75: return 'Información no aceptable'
        a = r['Area_Fuerte_Ponderada']
        c_act = str(r[columna_carrera]).strip()
        sugeridas = [c for c,p in PERFIL_CARRERAS.items() if a in p.get('Fuerte',[])]
        return c_act if c_act in sugeridas else (', '.join(sugeridas) if sugeridas else 'Sin sugerencia clara')

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

    # Score máximo
    score_cols = [f'PUNTAJE_COMBINADO_{a}' for a in AREAS]
    df['Score'] = df[score_cols].max(axis=1)

    # Etiqueta UI profesional
    df['Categoría_UI'] = (
        df['Semáforo Vocacional'].map(CAT_MAP_TO_UI).fillna('Sin perfil definido')
    )
    df['Categoría_UI'] = pd.Categorical(df['Categoría_UI'], categories=CAT_UI_ORDER, ordered=True)

    # Exponer nombres de columnas clave
    df.attrs['columna_carrera'] = columna_carrera
    df.attrs['columna_nombre']  = columna_nombre
    return df

# =========================================================
# Módulo 1: Presentación
# =========================================================
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
            st.markdown(f"""
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
""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Intereses y aptitudes: base de la formación académica</div>', unsafe_allow_html=True)
    st.markdown("""
Reconocer <b>lo que me interesa</b> y <b>para lo que tengo aptitud</b> ayuda a dirigir el esfuerzo,
sostener la motivación y <b>reducir el riesgo de abandono</b>. Factores determinantes para persistir en la universidad.
""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">¿Qué es la escala CHASIDE?</div>', unsafe_allow_html=True)
    st.markdown("""
<b>CHASIDE</b> integra <b>intereses</b> y <b>aptitudes</b> en siete áreas: C, H, A, S, I, D, E. Es de aplicación rápida (sí/no),
con interpretación sencilla y enfoque práctico para vincular resultados con opciones de carrera.
""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Propuesta Única de Valor (PUV)</div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="puv">
<b>Orientación vocacional personalizada</b>, basada en evidencia (CHASIDE),
con visualizaciones claras (pastel, barras, violines) y reportes descargables
para que los estudiantes identifiquen sus fortalezas y las escuelas cuenten con <b>insumos objetivos</b>.
</div>
""", unsafe_allow_html=True)

# =========================================================
# Módulo 2: Información general
# =========================================================
def render_info_general(df: pd.DataFrame):
    if df is None or df.empty:
        st.warning("Carga un archivo válido en la barra lateral.")
        return

    columna_carrera = df.attrs.get('columna_carrera','¿A qué carrera desea ingresar?')

    st.header("📊 Información general")

  # ============================================
# 📊 Información general
# ============================================

# ---- Pastel (corregido) ----
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
# ✅ Solo mostrar % en el gráfico y usar descripción en la leyenda
fig_pie.update_traces(textposition='inside', texttemplate='%{percent:.1%}')
fig_pie.update_layout(legend_title_text="Categoría")
st.plotly_chart(fig_pie, use_container_width=True)

# ---- Barras apiladas ----
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
                          .transform(lambda x: x / x.sum() * 100)
    fig_stacked = px.bar(
        stacked, x=columna_carrera, y='%',
        color='Categoría_UI',
        category_orders={'Categoría_UI': CAT_UI_ORDER},
        color_discrete_map=CAT_UI_COLORS,
        barmode='stack',
        text=stacked['%'].round(1).astype(str) + '%',
        title="Proporción (%) de estudiantes por carrera"
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

# ---- Violines (Congruente vs Incongruente) ----
    st.subheader("🎻 Distribución de puntajes por carrera (Congruente vs Incongruente)")
    score_cols = [f'PUNTAJE_COMBINADO_{a}' for a in AREAS]
    if not all(c in df.columns for c in score_cols):
        st.info("No se encontraron columnas PUNTAJE_COMBINADO_* para generar los violines.")
        return
    df_v = df[df['Categoría_UI'].isin([
        'Perfil congruente a la carrera seleccionada',
        'Perfil incongruente al seleccionado'
    ])].copy()
    if df_v.empty:
        st.info("No hay estudiantes congruentes/incongruentes para graficar.")
        return
    df_v['Score'] = df_v[score_cols].max(axis=1)
    fig_violin = px.violin(
        df_v, x=columna_carrera, y="Score", color="Categoría_UI",
        box=True, points=False, color_discrete_map=CAT_UI_COLORS,
        category_orders={'Categoría_UI': CAT_UI_ORDER},
        title="Distribución de puntajes por carrera"
    )
    cats_sorted = sorted(list(df_v[columna_carrera].dropna().unique()), key=lambda x: str(x))
    for i in range(len(cats_sorted)-1):
        fig_violin.add_vline(x=i+0.5, line_width=1, line_dash="dot", line_color="gray")
    fig_violin.update_layout(xaxis_title="Carrera", yaxis_title="Score combinado", xaxis_tickangle=-30, height=720)
    st.plotly_chart(fig_violin, use_container_width=True)

# =========================================================
# Módulo 3: Información particular (reporte ejecutivo)
# =========================================================
def render_info_individual(df: pd.DataFrame):
    if df is None or df.empty:
        st.warning("Carga un archivo válido en la barra lateral.")
        return
    columna_carrera = df.attrs.get('columna_carrera','¿A qué carrera desea ingresar?')
    columna_nombre  = df.attrs.get('columna_nombre','Ingrese su nombre completo')

    st.header("📘 Información particular del estudiantado – Reporte ejecutivo")

    # Selección Carrera / Estudiante
    carreras = sorted(df[columna_carrera].dropna().unique())
    if not carreras:
        st.warning("No hay carreras disponibles.")
        return
    carrera_sel = st.selectbox("Carrera a evaluar:", carreras, index=0)
    d_carrera = df[df[columna_carrera]==carrera_sel].copy()

    nombres = sorted(d_carrera[columna_nombre].astype(str).unique())
    if not nombres:
        st.warning("No hay estudiantes en esta carrera.")
        return
    est_sel = st.selectbox("Estudiante:", nombres, index=0)

    mask_al = (df[columna_carrera]==carrera_sel) & (df[columna_nombre].astype(str)==est_sel)
    alumno = df[mask_al].copy()
    if alumno.empty:
        st.warning("No se encontró el estudiante seleccionado.")
        return
    al = alumno.iloc[0]

    # KPIs
    cat = al['Categoría_UI']
    cat_color = CAT_UI_COLORS.get(cat, GRAY)
    total_carrera = len(d_carrera)
    n_cat = int((d_carrera['Categoría_UI'] == cat).sum())
    pct_cat = (n_cat/total_carrera*100) if total_carrera else 0.0

    # Indicadores (promesa / riesgo) sobre la misma carrera
    score_cols = [f'PUNTAJE_COMBINADO_{a}' for a in AREAS]
    d_carrera = d_carrera.copy()
    d_carrera['Score'] = d_carrera[score_cols].max(axis=1)
    verde_carr = d_carrera[d_carrera['Categoría_UI']=='Perfil congruente a la carrera seleccionada']
    amar_carr  = d_carrera[d_carrera['Categoría_UI']=='Perfil incongruente al seleccionado']

    indicador = "Alumno regular"
    if not verde_carr.empty and est_sel in (verde_carr.sort_values('Score', ascending=False).head(5)[columna_nombre].astype(str).tolist()):
        indicador = "Joven promesa"
    if not amar_carr.empty and est_sel in (amar_carr.sort_values('Score', ascending=True).head(5)[columna_nombre].astype(str).tolist()):
        indicador = "Alumno en riesgo de reprobar"

    # Referencia (grupo congruente si hay; si no, promedio de la carrera)
    ref_cols = [f'TOTAL_{a}' for a in AREAS]
    mask_verde = df['Categoría_UI']=='Perfil congruente a la carrera seleccionada'
    ref_df = df.loc[(df[columna_carrera]==carrera_sel) & mask_verde, ref_cols]
    if ref_df.empty:
        ref_df = df.loc[(df[columna_carrera]==carrera_sel), ref_cols]
        referencia = "Promedio general de la carrera (sin grupo congruente)."
    else:
        referencia = "Promedio del grupo congruente de la carrera."

    ref_vec = ref_df.mean().astype(float)
    al_vec  = df.loc[mask_al, ref_cols].iloc[0].astype(float)
    diff    = al_vec - ref_vec
    fortalezas = diff[diff > 0].sort_values(ascending=False)
    oportun    = diff[diff < 0].abs().sort_values(ascending=False)

    # Encabezado
    st.markdown("## 🧾 Reporte ejecutivo individual")
    c1, c2, c3, c4 = st.columns([2.2, 2, 2.2, 2])
    with c1: st.markdown(f"<div class='card kpi'><b>Nombre del estudiante</b><br>{est_sel}</div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='card kpi'><b>Carrera</b><br>{carrera_sel}</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='card kpi'><b>Categoría</b><br><span style='font-weight:700;color:{cat_color}'>{cat}</span></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='card kpi'><b>Nº en esta categoría</b><br>{n_cat} (<span style='font-weight:700'>{pct_cat:.1f}%</span>)</div>", unsafe_allow_html=True)

    badge_color = {"Joven promesa": GREEN, "Alumno en riesgo de reprobar": AMBER}.get(indicador, SLATE)
    st.markdown(f"<span class='badge' style='background:rgba(20,184,166,.12);color:{badge_color}'>Indicador: {indicador}</span>", unsafe_allow_html=True)
    st.divider()

    st.markdown(f"**Referencia utilizada:** _{referencia}_")

    st.markdown("### ✅ Fortalezas destacadas")
    if fortalezas.empty:
        st.info("No se observan dimensiones por encima de la referencia.")
    else:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for letra, delta in fortalezas.items():
            k = str(letra).replace("TOTAL_","")
            st.markdown(f"<li><b>{k}</b> (+{float(delta):.2f}) — {DESC_CHASIDE[k]}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    st.markdown("### 🛠️ Áreas de oportunidad")
    if oportun.empty:
        st.info("Sin brechas relevantes respecto a la referencia.")
    else:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for letra, gap in oportun.items():
            k = str(letra).replace("TOTAL_","")
            st.markdown(f"<li><b>{k}</b> (−{float(gap):.2f}) — {DESC_CHASIDE[k]}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    st.divider()

    # Coherencia y afinidad de carreras
    st.markdown("### 🎯 Coherencia vocacional (elección vs perfil CHASIDE)")
    area_fuerte = al['Area_Fuerte_Ponderada']
    perfil_sel = PERFIL_CARRERAS.get(str(carrera_sel).strip())
    if perfil_sel:
        if area_fuerte in perfil_sel.get('Fuerte', []): coh_text = "Coherente"
        elif area_fuerte in perfil_sel.get('Baja', []): coh_text = "Requiere orientación"
        else: coh_text = "Neutral"
    else:
        coh_text = "Sin perfil definido"
    sugeridas = sorted([c for c,p in PERFIL_CARRERAS.items() if area_fuerte in p.get('Fuerte', [])])

    st.write(f"- **Área fuerte (CHASIDE):** {area_fuerte}")
    st.write(f"- **Evaluación de coherencia:** {coh_text}")
    st.markdown("### 📚 Carreras con mayor afinidad al perfil del estudiante (según CHASIDE)")
    if sugeridas:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for c in sugeridas:
            st.markdown(f"<li>{c}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
    else:
        st.info("No se identificaron carreras afines basadas en el área fuerte.")

    st.divider()

    # Descargas (individual / carrera)
    def resumen_para(alumno_row: pd.Series) -> dict:
        mask = (df[columna_carrera]==carrera_sel) & (df[columna_nombre].astype(str)==str(alumno_row[columna_nombre]))
        a_vec  = df.loc[mask, [f'TOTAL_{x}' for x in AREAS]].iloc[0].astype(float)
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
        suger = ", ".join(sorted([c for c,p in PERFIL_CARRERAS.items() if area_f in p.get('Fuerte', [])]))
        return {
            "Nombre": str(alumno_row[columna_nombre]),
            "Carrera": carrera_sel,
            "Categoría (UI)": cat_local,
            "N en categoría (carrera)": n_local,
            "% en categoría (carrera)": round(pct_local,1),
            "Indicador": ind,
            "Área fuerte CHASIDE": area_f,
            "Carreras afines (CHASIDE)": suger,
            "Fortalezas": ", ".join(fort),
            "Áreas de oportunidad": ", ".join(opp),
        }

    ref_vec = ref_vec  # ya definido arriba
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

# =========================================================
# Módulo 4: Equipo de trabajo
# =========================================================
def render_equipo():
    st.header("👥 Equipo de trabajo")
    st.markdown("""
Este proyecto fue elaborado por el siguiente equipo interdisciplinario:

- **Dra. Elena Elsa Bricio Barrios** – Especialista en Psicología Educativa  
- **Dr. Santiago Arceo-Díaz** – Investigador en Ciencias Médicas y Datos  
- **Psic. Martha Cecilia Ramírez Guzmán** – Psicóloga orientada al desarrollo vocacional
""")
    st.caption("Tecnológico Nacional de México – Instituto Tecnológico de Colima")

# =========================================================
# App principal con barra lateral
# =========================================================
def main():
    st.sidebar.title("CHASIDE • Navegación")
    modulo = st.sidebar.radio(
        "Ir a…",
        options=["Presentación", "Información general", "Información individual", "Equipo de trabajo"],
        index=0
    )

    # Entrada de datos (URL)
    st.sidebar.markdown("---")
    url = st.sidebar.text_input("URL de Google Sheets (CSV export)", DEFAULT_SHEET)

    df = None
    if modulo in ("Información general", "Información individual"):
        if not url:
            st.warning("Indica la URL del CSV de Google Sheets en la barra lateral.")
            return
        try:
            raw = load_csv(url)
            df = preprocess_chaside(raw)
        except Exception as e:
            st.error(f"❌ No fue posible cargar/procesar el archivo: {e}")
            return

    if modulo == "Presentación":
        render_presentacion()
    elif modulo == "Información general":
        render_info_general(df)
    elif modulo == "Información individual":
        render_info_individual(df)
    elif modulo == "Equipo de trabajo":
        render_equipo()

if __name__ == "__main__":
    main()
