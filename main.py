# ============================================
# APP COMPLETA · CHASIDE (4 módulos con sidebar)
# ============================================

# -------- Imports --------
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from modulo3_info_individual import render_info_individual

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
# MÓDULO 3 (función) · INFORMACIÓN PARTICULAR DEL ESTUDIANTADO
# Reporte ejecutivo individual (UI formal + descargas)
# Uso: render_info_individual(df_proc)
# df_proc debe traer INTERES_*, APTITUD_*, PUNTAJE_COMBINADO_*, Area_Fuerte_Ponderada,
# Semáforo Vocacional, Score y TOTAL_* (si faltan, se calculan en caliente).
# ============================================

import streamlit as st
import pandas as pd
import numpy as np

PRIMARY = "#0F766E"; ACCENT = "#14B8A6"; SLATE = "#475569"
GREEN = "#22c55e"; AMBER = "#f59e0b"; GRAY = "#6b7280"

# Estilos (inyectados una sola vez por sesión de la página)
def _inject_styles():
    st.markdown(f"""
    <style>
    .h1-title {{ font-size: 1.8rem; font-weight: 800; color:{PRIMARY}; margin-bottom:.25rem; }}
    .badge {{
      display:inline-block; padding: 4px 10px; border-radius:999px; font-weight:700; font-size:.85rem;
      background: rgba(20,184,166,.12); color:{PRIMARY};
    }}
    .card {{ border:1px solid #e5e7eb; border-radius:16px; padding:14px 16px; background:#fff;
            box-shadow:0 2px 8px rgba(0,0,0,.03); margin-bottom:.75rem; }}
    .kpi {{ font-size:1.05rem; margin:.15rem 0; }}
    .kpi b {{ color:{SLATE}; }}
    .list-tight li {{ margin-bottom:.2rem; }}
    </style>
    """, unsafe_allow_html=True)

# Descripciones CHASIDE para el texto
DESC = {
    "C": "Organización, supervisión, orden, análisis y síntesis, colaboración, cálculo.",
    "H": "Precisión verbal, organización, relación de hechos, justicia, persuasión.",
    "A": "Estético y creativo; detallista, innovador, intuitivo; habilidades visuales, auditivas y manuales.",
    "S": "Asistir y ayudar; investigación, precisión, percepción, análisis; altruismo y paciencia.",
    "I": "Cálculo y pensamiento científico/crítico; exactitud, planificación; enfoque práctico.",
    "D": "Justicia y equidad; colaboración, liderazgo; valentía y toma de decisiones.",
    "E": "Investigación; orden, análisis y síntesis; cálculo numérico, observación; método y seguridad."
}
AREAS = ['C','H','A','S','I','D','E']

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

def _asegurar_campos(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula campos faltantes mínimos para este módulo."""
    df = df.copy()
    col_carrera = '¿A qué carrera desea ingresar?'
    col_nombre  = 'Ingrese su nombre completo'
    assert col_carrera in df.columns and col_nombre in df.columns, "Faltan columnas de nombre/carrera."

    # PUNTAJE_COMBINADO_* y Area_Fuerte_Ponderada
    faltan_pc = any(f'PUNTAJE_COMBINADO_{a}' not in df.columns for a in AREAS)
    if faltan_pc:
        # Requiere INTERES_*, APTITUD_*
        peso_i, peso_a = 0.8, 0.2
        for a in AREAS:
            if f'PUNTAJE_COMBINADO_{a}' not in df.columns:
                df[f'PUNTAJE_COMBINADO_{a}'] = df[f'INTERES_{a}']*peso_i + df[f'APTITUD_{a}']*peso_a

    if 'Area_Fuerte_Ponderada' not in df.columns:
        df['Area_Fuerte_Ponderada'] = df.apply(lambda r: max(AREAS, key=lambda a: r[f'PUNTAJE_COMBINADO_{a}']), axis=1)

    # TOTAL_* y Score
    for a in AREAS:
        tot = f'TOTAL_{a}'
        if tot not in df.columns:
            df[tot] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']
    if 'Score' not in df.columns:
        df['Score'] = df[[f'PUNTAJE_COMBINADO_{a}' for a in AREAS]].max(axis=1)

    if 'Semáforo Vocacional' not in df.columns:
        df['Semáforo Vocacional'] = 'Sin sugerencia'

    return df

def render_info_individual(df: pd.DataFrame):
    _inject_styles()
    st.markdown('<div class="h1-title">📘 Información particular del estudiantado – CHASIDE</div>', unsafe_allow_html=True)
    st.caption("Reporte ejecutivo individual con indicadores y recomendaciones por dimensiones CHASIDE.")

    df = _asegurar_campos(df)
    col_carrera = '¿A qué carrera desea ingresar?'
    col_nombre  = 'Ingrese su nombre completo'

    # ---- Selección carrera/alumno
    carreras = sorted(df[col_carrera].dropna().astype(str).unique())
    if not carreras:
        st.warning("No hay carreras disponibles.")
        return
    carrera_sel = st.selectbox("Carrera a evaluar:", carreras, index=0)
    d_carrera = df[df[col_carrera] == carrera_sel].copy()

    nombres = sorted(d_carrera[col_nombre].astype(str).unique())
    est_sel = st.selectbox("Estudiante:", nombres, index=0)

    alumno_mask = (df[col_carrera]==carrera_sel) & (df[col_nombre].astype(str)==est_sel)
    alumno = df[alumno_mask]
    if alumno.empty:
        st.warning("No se encontró el estudiante seleccionado.")
        return
    al = alumno.iloc[0]

    # ---- KPIs
    cat = al['Semáforo Vocacional']
    cat_color = {"Verde": GREEN, "Amarillo": AMBER}.get(cat, GRAY)
    total_carrera = len(d_carrera)
    n_cat = int((d_carrera['Semáforo Vocacional'] == cat).sum())
    pct_cat = (n_cat/total_carrera*100) if total_carrera else 0.0

    verde_carr = d_carrera[d_carrera['Semáforo Vocacional']=='Verde']
    amar_carr  = d_carrera[d_carrera['Semáforo Vocacional']=='Amarillo']
    indicador = "Alumno regular"
    if not verde_carr.empty and est_sel in (verde_carr.sort_values('Score', ascending=False).head(5)[col_nombre].astype(str).tolist()):
        indicador = "Joven promesa"
    if not amar_carr.empty and est_sel in (amar_carr.sort_values('Score', ascending=True).head(5)[col_nombre].astype(str).tolist()):
        indicador = "Alumno en riesgo de reprobar"

    st.markdown("## 🧾 Reporte ejecutivo individual")
    c1, c2, c3, c4 = st.columns([2.2, 2, 2.2, 2])
    with c1: st.markdown(f"<div class='card kpi'><b>Nombre del estudiante</b><br>{est_sel}</div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='card kpi'><b>Carrera</b><br>{carrera_sel}</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='card kpi'><b>Categoría identificada</b><br><span style='font-weight:700;color:{cat_color}'>{cat}</span></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='card kpi'><b>Nº en esta categoría</b><br>{n_cat} (<span style='font-weight:700'>{pct_cat:.1f}%</span>)</div>", unsafe_allow_html=True)

    badge_color = {"Joven promesa": GREEN, "Alumno en riesgo de reprobar": AMBER}.get(indicador, SLATE)
    st.markdown(f"<span class='badge' style='background:rgba(34,197,94,.12);color:{badge_color}'>Indicador: {indicador}</span>", unsafe_allow_html=True)
    st.divider()

    # ---- Comparativo (fortalezas / oportunidades)
    ref_cols = [f'TOTAL_{a}' for a in AREAS]
    mask_carrera = df[col_carrera] == carrera_sel
    mask_verde   = df['Semáforo Vocacional'] == 'Verde'
    ref_df = df.loc[mask_carrera & mask_verde, ref_cols]
    if ref_df.empty:
        ref_df = df.loc[mask_carrera, ref_cols]
    ref_vec = ref_df.mean().astype(float)
    al_vec  = df.loc[alumno_mask, ref_cols].iloc[0].astype(float)
    diff    = (al_vec - ref_vec)

    fortalezas = diff[diff > 0].sort_values(ascending=False)
    oportunidades = diff[diff < 0].abs().sort_values(ascending=False)

    st.markdown("### ✅ Fortalezas destacadas")
    if fortalezas.empty:
        st.info("No se observan dimensiones por encima del promedio de referencia del grupo.")
    else:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for letra, delta in fortalezas.items():
            k = letra.replace("TOTAL_","")
            st.markdown(f"<li><b>{k}</b> (+{delta:.2f}) — {DESC[k]}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    st.markdown("### 🛠️ Áreas de oportunidad")
    if oportunidades.empty:
        st.info("El estudiante no presenta brechas importantes respecto al grupo.")
    else:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for letra, gap in oportunidades.items():
            k = letra.replace("TOTAL_","")
            st.markdown(f"<li><b>{k}</b> (−{gap:.2f}) — {DESC[k]}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    st.divider()

    # ---- Coherencia + Carreras afines
    st.markdown("### 🎯 Coherencia vocacional (elección vs perfil CHASIDE)")
    area_fuerte = al['Area_Fuerte_Ponderada']
    perfil_sel  = PERFIL_CARRERAS.get(str(carrera_sel).strip())
    if perfil_sel:
        if area_fuerte in perfil_sel.get('Fuerte', []): coh_text = "Coherente"
        elif area_fuerte in perfil_sel.get('Baja', []): coh_text = "Requiere orientación"
        else: coh_text = "Neutral"
    else:
        coh_text = "Sin perfil definido"
    st.write(f"- **Área fuerte (CHASIDE):** {area_fuerte}")
    st.write(f"- **Evaluación de coherencia:** {coh_text}")

    st.markdown("### 📚 Carreras con mayor afinidad al perfil del estudiante (según CHASIDE)")
    sugeridas = sorted([c for c, p in PERFIL_CARRERAS.items() if area_fuerte in p.get('Fuerte', [])])
    if sugeridas:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for c in sugeridas:
            st.markdown(f"<li>{c}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
    else:
        st.info("No se identificaron carreras afines basadas en el área fuerte.")

    st.divider()

    # ---- Descargas (individual / por carrera)
    def _resumen_para(row: pd.Series) -> dict:
        a_mask = (df[col_carrera]==carrera_sel) & (df[col_nombre].astype(str)==str(row[col_nombre]))
        a_vec  = df.loc[a_mask, [f'TOTAL_{x}' for x in AREAS]].iloc[0].astype(float)
        diffs  = (a_vec - ref_vec)
        fort   = [k.replace("TOTAL_","") for k,v in diffs.items() if v>0]
        opp    = [k.replace("TOTAL_","") for k,v in diffs.items() if v<0]

        ind = "Alumno regular"
        if not verde_carr.empty and row[col_nombre] in (verde_carr.sort_values('Score', ascending=False).head(5)[col_nombre].astype(str).tolist()):
            ind = "Joven promesa"
        if not amar_carr.empty and row[col_nombre] in (amar_carr.sort_values('Score', ascending=True).head(5)[col_nombre].astype(str).tolist()):
            ind = "Alumno en riesgo de reprobar"

        cat_local = row['Semáforo Vocacional']
        n_local = int((d_carrera['Semáforo Vocacional']==cat_local).sum())
        pct_local = (n_local/total_carrera*100) if total_carrera else 0.0
        area_f = row['Area_Fuerte_Ponderada']
        suger = ", ".join(sorted([c for c,p in PERFIL_CARRERAS.items() if area_f in p.get('Fuerte', [])]))

        return {
            "Nombre": str(row[col_nombre]),
            "Carrera": carrera_sel,
            "Categoría": cat_local,
            "N en categoría (carrera)": n_local,
            "% en categoría (carrera)": round(pct_local,1),
            "Indicador": ind,
            "Área fuerte CHASIDE": area_f,
            "Carreras afines (CHASIDE)": suger,
            "Fortalezas": ", ".join(fort),
            "Áreas de oportunidad": ", ".join(opp),
        }

    col_a, col_b = st.columns([1.2, 1])
    with col_a:
        data_ind = pd.DataFrame([_resumen_para(al)])
        st.download_button(
            "⬇️ Descargar reporte individual (CSV)",
            data=data_ind.to_csv(index=False).encode("utf-8"),
            file_name=f"reporte_individual_{est_sel}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_b:
        data_all = pd.DataFrame([_resumen_para(r) for _, r in d_carrera.iterrows()])
        st.download_button(
            "⬇️ Descargar reporte de la carrera (CSV)",
            data=data_all.to_csv(index=False).encode("utf-8"),
            file_name=f"reporte_carrera_{carrera_sel}.csv",
            mime="text/csv",
            use_container_width=True
        )
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
