# ============================================
# APP CHASIDE – 4 MÓDULOS CON CATEGORÍAS RENOMBRADAS
# ============================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------- Estilos / Colores base ----------
PRIMARY = "#0F766E"; ACCENT = "#14B8A6"; SLATE = "#475569"
GREEN = "#22c55e"; AMBER = "#f59e0b"; RED = "#ef4444"; GRAY = "#6b7280"; BLUE = "#94a3b8"

st.set_page_config(page_title="CHASIDE • Orientación Vocacional", layout="wide")

st.markdown(f"""
<style>
.block-container {{ padding-top: 1.0rem; }}
.h1-title {{ font-size: 1.9rem; font-weight: 800; color:{PRIMARY}; margin-bottom:.25rem; }}
.subtitle {{ color: {SLATE}; margin-bottom: 1.0rem; }}
.section-title {{ font-weight: 700; font-size: 1.1rem; margin: 1.0rem 0 .5rem 0; color: {PRIMARY}; }}
.card {{
  border: 1px solid #e5e7eb; border-radius: 16px; padding: 14px 16px;
  background: #ffffff; box-shadow: 0 2px 8px rgba(0,0,0,0.03); margin-bottom: .75rem;
}}
.badge {{
  display:inline-block; padding: 4px 10px; border-radius: 999px;
  background: rgba(20,184,166,0.12); color:{PRIMARY}; font-weight: 700;
}}
.list-tight li {{ margin-bottom: .2rem; }}
hr {{ margin: 1.0rem 0; }}
</style>
""", unsafe_allow_html=True)

# ---------- Constantes CHASIDE y Perfiles ----------
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

# Renombres profesionales de categorías
CAT_UI_MAP = {
    'Verde':        '🟢 Perfil Vocacional Alineado',
    'Amarillo':     '🟡 Perfil Incongruente al seleccionado',
    'Rojo':         '🔴 Sin Perfil Definido',
    'No aceptable': '👻 Respuestas No Confiables',
    'Sin sugerencia': 'Sin sugerencia'
}
CAT_UI_COLORS = {
    '🟢 Perfil Vocacional Alineado':         GREEN,
    '🟡 Perfil Incongruente al seleccionado': AMBER,
    '🔴 Sin Perfil Definido':                RED,
    '👻 Respuestas No Confiables':           GRAY,
    'Sin sugerencia':                        BLUE
}
CAT_UI_ORDER = [
    '🟢 Perfil Vocacional Alineado',
    '🟡 Perfil Incongruente al seleccionado',
    '🔴 Sin Perfil Definido',
    '👻 Respuestas No Confiables',
    'Sin sugerencia'
]

# Descripciones CHASIDE
DESC_CHASIDE = {
    "C": "Organización, supervisión, orden, análisis y síntesis, colaboración, cálculo.",
    "H": "Precisión verbal, organización, relación de hechos, justicia, persuasión.",
    "A": "Estético y creativo; detallista, innovador, intuitivo; habilidades visuales, auditivas y manuales.",
    "S": "Asistir y ayudar; investigación, precisión, percepción, análisis; altruismo y paciencia.",
    "I": "Cálculo y pensamiento científico/crítico; exactitud, planificación; enfoque práctico.",
    "D": "Justicia y equidad; colaboración, liderazgo; valentía y toma de decisiones.",
    "E": "Investigación; orden, análisis y síntesis; cálculo numérico, observación, método y seguridad."
}

# ---------- Utilidades comunes ----------
def evaluar(area_chaside: str, carrera: str) -> str:
    perfil = PERFIL_CARRERAS.get(str(carrera).strip())
    if not perfil: return 'Sin perfil definido'
    if area_chaside in perfil.get('Fuerte', []): return 'Coherente'
    if area_chaside in perfil.get('Baja',  []): return 'Requiere Orientación'
    return 'Neutral'

def _semaforo_row(r) -> str:
    # Diagnóstico Primario Vocacional y Coincidencia_Ponderada ya calculados
    diag = r['Diagnóstico Primario Vocacional']
    if diag == 'Información no aceptable': return 'No aceptable'
    if diag == 'Sin sugerencia clara':     return 'Sin sugerencia'
    match = r['Coincidencia_Ponderada']
    if diag == 'Perfil adecuado':
        return {'Coherente':'Verde','Neutral':'Amarillo','Requiere Orientación':'Rojo'}.get(match,'Sin sugerencia')
    if isinstance(diag, str) and diag.startswith('Sugerencia:'):
        return {'Coherente':'Verde','Neutral':'Amarillo','Requiere Orientación':'Rojo'}.get(match,'Sin sugerencia')
    return 'Sin sugerencia'

@st.cache_data(show_spinner=False)
def load_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

def preprocess_chaside(df_raw: pd.DataFrame, peso_intereses=0.8) -> pd.DataFrame:
    df = df_raw.copy()
    columnas_items = df.columns[5:103]
    col_carrera = '¿A qué carrera desea ingresar?'
    col_nombre  = 'Ingrese su nombre completo'

    # Validación mínima
    if col_carrera not in df.columns or col_nombre not in df.columns:
        raise ValueError("Faltan columnas requeridas: '¿A qué carrera desea ingresar?' y/o 'Ingrese su nombre completo'.")

    # Sí/No → 1/0 robusto
    df_items = (
        df[columnas_items].astype(str).apply(lambda c: c.str.strip().str.lower())
          .replace({'sí':1,'si':1,'s':1,'1':1,'true':1,'verdadero':1,'x':1,
                    'no':0,'n':0,'0':0,'false':0,'falso':0,'':'0','nan':0})
          .apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    )
    df[columnas_items] = df_items

    # Coincidencia (sesgo Sí/No)
    suma_si = df[columnas_items].sum(axis=1)
    pct_si  = suma_si / len(columnas_items)
    df['Coincidencia'] = np.maximum(pct_si, 1 - pct_si)

    # Sumas por área
    def col_item(i:int)->str: return columnas_items[i-1]
    for a in AREAS:
        df[f'INTERES_{a}']  = df[[col_item(i) for i in INTERESES_ITEMS[a]]].sum(axis=1)
        df[f'APTITUD_{a}'] = df[[col_item(i) for i in APTITUDES_ITEMS[a]]].sum(axis=1)

    peso_aptitudes = 1.0 - peso_intereses
    for a in AREAS:
        df[f'PUNTAJE_COMBINADO_{a}'] = df[f'INTERES_{a}']*peso_intereses + df[f'APTITUD_{a}']*peso_aptitudes

    # Área fuerte ponderada y score máximo
    df['Area_Fuerte_Ponderada'] = df.apply(lambda r: max(AREAS, key=lambda a: r[f'PUNTAJE_COMBINADO_{a}']), axis=1)
    score_cols = [f'PUNTAJE_COMBINADO_{a}' for a in AREAS]
    df['Score'] = df[score_cols].max(axis=1)
    for a in AREAS:
        df[f'TOTAL_{a}'] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']

    # Coincidencia ponderada vs carrera deseada
    df['Coincidencia_Ponderada'] = df.apply(lambda r: evaluar(r['Area_Fuerte_Ponderada'], r[col_carrera]), axis=1)

    # Mejor carrera y diagnóstico
    def carrera_mejor(r):
        if r['Coincidencia'] >= 0.75:
            return 'Información no aceptable'
        a = r['Area_Fuerte_Ponderada']
        actual = str(r[col_carrera]).strip()
        sugeridas = [c for c,p in PERFIL_CARRERAS.items() if a in p.get('Fuerte', [])]
        return actual if actual in sugeridas else (', '.join(sugeridas) if sugeridas else 'Sin sugerencia clara')

    def diagnostico(r):
        if r['Carrera_Mejor_Perfilada']=='Información no aceptable': return 'Información no aceptable'
        if str(r[col_carrera]).strip()==str(r['Carrera_Mejor_Perfilada']).strip(): return 'Perfil adecuado'
        if r['Carrera_Mejor_Perfilada']=='Sin sugerencia clara': return 'Sin sugerencia clara'
        return f"Sugerencia: {r['Carrera_Mejor_Perfilada']}"

    df['Carrera_Mejor_Perfilada']         = df.apply(carrera_mejor, axis=1)
    df['Diagnóstico Primario Vocacional'] = df.apply(diagnostico, axis=1)
    df['Semáforo Vocacional']             = df.apply(_semaforo_row, axis=1)

    # Mapa UI
    df['Categoría_UI'] = df['Semáforo Vocacional'].map(CAT_UI_MAP).fillna(df['Semáforo Vocacional'])

    # Devolver junto con nombres clave de columnas
    return df

# =========================================================
# MÓDULO 1 – Presentación
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
para apoyar una <b>elección de carrera informada y alineada</b> con sus fortalezas.
Integra resultados de la escala CHASIDE y los presenta de forma clara para estudiantes, familias y docentes.
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Madurez y personalidad en el bachillerato</div>', unsafe_allow_html=True)
    st.markdown("""
La <b>personalidad</b> está en desarrollo durante el bachillerato. La <b>madurez</b> permite al joven reflexionar
sobre su proyecto de vida, pero el proceso <b>aún está en construcción</b>. En esta etapa es clave contar con
<b>herramientas de orientación</b> que acompañen la toma de decisiones académicas.
""")

    st.markdown('<div class="section-title">¿Qué es la escala CHASIDE?</div>', unsafe_allow_html=True)
    st.markdown("""
<b>CHASIDE</b> integra <b>intereses</b> y <b>aptitudes</b> en siete áreas: C, H, A, S, I, D y E.
Se caracteriza por su aplicación rápida, reactivos sí/no e interpretación práctica que vincula resultados con opciones de carrera.
""")

    st.markdown('<div class="section-title">Propuesta Única de Valor (PUV)</div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="card">
<b>Orientación vocacional personalizada</b>, basada en la escala CHASIDE, con visualizaciones claras
(pastel de categorías, barras apiladas, violines comparativos y radar por carrera) y reportes descargables
para que los estudiantes identifiquen sus fortalezas y los equipos académicos cuenten con <b>insumos objetivos</b>.
</div>
""", unsafe_allow_html=True)

# =========================================================
# MÓDULO 2 – Información general (gráficas)
# =========================================================
def render_info_general(df: pd.DataFrame):
    col_carrera = '¿A qué carrera desea ingresar?'

    st.markdown("## 🗂️ Información general")

    # ---- Pastel de categorías (UI) ----
    st.subheader("🥧 Distribución general por categoría (UI)")
    resumen = (
        df['Categoría_UI']
        .value_counts()
        .reindex(CAT_UI_ORDER, fill_value=0)
        .reset_index()
        .rename(columns={'index':'Categoría_UI', 'Categoría_UI':'N'})
    )
    fig_pie = px.pie(
        resumen, names='Categoría_UI', values='N', hole=0.35,
        color='Categoría_UI', color_discrete_map=CAT_UI_COLORS,
        title="Distribución general por categoría"
    )
    fig_pie.update_traces(textposition='inside',
                          texttemplate='%{label}<br>%{percent:.1%} (%{value})')
    st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # ---- Barras apiladas por carrera (porcentaje vs cantidad) ----
    st.subheader("📊 Distribución por carrera y categoría")
    cats = CAT_UI_ORDER[:-1] + ['Sin sugerencia']  # mantener orden
    stacked = (
        df[df['Categoría_UI'].isin(cats)]
        .groupby([col_carrera, 'Categoría_UI'], dropna=False)
        .size().reset_index(name='N')
    )
    stacked['Categoría_UI'] = pd.Categorical(stacked['Categoría_UI'], categories=cats, ordered=True)

    modo = st.radio("Modo de visualización", ["Proporción (100% apilado)", "Valores absolutos"],
                    horizontal=True, index=0)

    if modo == "Proporción (100% apilado)":
        stacked['%'] = stacked.groupby(col_carrera)['N'].transform(lambda x: 0 if x.sum()==0 else (x/x.sum()*100))
        fig_stacked = px.bar(
            stacked, x=col_carrera, y='%', color='Categoría_UI',
            category_orders={'Categoría_UI': cats},
            color_discrete_map=CAT_UI_COLORS, barmode='stack',
            text=stacked['%'].round(1).astype(str) + '%',
            title="Proporción (%) por carrera y categoría"
        )
        fig_stacked.update_layout(yaxis_title="Proporción (%)", xaxis_title="Carrera",
                                  xaxis_tickangle=-30, height=620)
    else:
        fig_stacked = px.bar(
            stacked, x=col_carrera, y='N', color='Categoría_UI',
            category_orders={'Categoría_UI': cats},
            color_discrete_map=CAT_UI_COLORS, barmode='stack',
            text='N', title="Estudiantes por carrera y categoría (valores absolutos)"
        )
        fig_stacked.update_layout(yaxis_title="Número de estudiantes", xaxis_title="Carrera",
                                  xaxis_tickangle=-30, height=620)
        fig_stacked.update_traces(textposition='inside', cliponaxis=False)

    st.plotly_chart(fig_stacked, use_container_width=True)

    st.divider()

    # ---- Violín Verde vs Amarillo (UI) ----
    st.subheader("🎻 Distribución de puntajes – Alineado vs Incongruente (por carrera)")
    # Mapear a dos categorías de interés
    verde_label = '🟢 Perfil Vocacional Alineado'
    amar_label  = '🟡 Perfil Incongruente al seleccionado'
    df_violin = df[df['Categoría_UI'].isin([verde_label, amar_label])].copy()

    if df_violin.empty:
        st.info("No hay estudiantes en categorías Alineado o Incongruente para graficar.")
    else:
        fig_violin = px.violin(
            df_violin, x=col_carrera, y="Score", color="Categoría_UI",
            box=True, points=False, color_discrete_map=CAT_UI_COLORS,
            title="Distribución de puntajes por carrera (Alineado vs Incongruente)"
        )
        # Líneas punteadas entre carreras para separar
        categorias = df_violin[col_carrera].dropna().unique()
        for i in range(len(categorias) - 1):
            fig_violin.add_vline(x=i + 0.5, line_width=1, line_dash="dot", line_color="gray")
        fig_violin.update_layout(xaxis_title="Carrera", yaxis_title="Score combinado",
                                 xaxis_tickangle=-30, height=720)
        st.plotly_chart(fig_violin, use_container_width=True)

    st.divider()

    # ---- Radar por carrera (Verde vs Amarillo) + brechas top3 ----
    st.subheader("🕸️ Radar CHASIDE por carrera – Alineado vs Incongruente")
    df_radar = df.copy()
    for a in AREAS:
        df_radar[a] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']
    df_radar['Categoría_UI'] = df['Categoría_UI']
    df_radar['Carrera'] = df[col_carrera]

    carreras_disp = sorted(df_radar['Carrera'].dropna().unique())
    if not carreras_disp:
        st.info("No hay carreras para mostrar.")
        return

    tabs = st.tabs(carreras_disp)
    for tab, carrera_sel in zip(tabs, carreras_disp):
        with tab:
            sub = df_radar[df_radar['Carrera'] == carrera_sel]
            sub = sub[sub['Categoría_UI'].isin([verde_label, amar_label])]
            if sub.empty or sub['Categoría_UI'].nunique() < 2:
                st.warning("No hay datos suficientes de ambas categorías.")
                continue

            prom = sub.groupby('Categoría_UI')[AREAS].mean().reset_index()
            fig = px.line_polar(
                prom.melt(id_vars='Categoría_UI', value_vars=AREAS, var_name='Área', value_name='Promedio'),
                r='Promedio', theta='Área', color='Categoría_UI',
                line_close=True, markers=True, color_discrete_map=CAT_UI_COLORS,
                title=f"Perfil CHASIDE – {carrera_sel}"
            )
            fig.update_traces(fill='toself', opacity=0.75)
            st.plotly_chart(fig, use_container_width=True)

            prom_w = sub.groupby('Categoría_UI')[AREAS].mean()
            diffs = (prom_w.loc[verde_label] - prom_w.loc[amar_label]).sort_values(ascending=False)
            top3 = diffs.head(3)

            st.markdown("**Áreas a reforzar (donde Incongruente está más bajo):**")
            for letra, delta in top3.items():
                st.markdown(f"- **{letra}** (Δ = {delta:.2f}): {DESC_CHASIDE[letra]}")

# =========================================================
# MÓDULO 3 – Información individual (reporte ejecutivo)
# =========================================================
def render_info_individual(df: pd.DataFrame):
    col_carrera = '¿A qué carrera desea ingresar?'
    col_nombre  = 'Ingrese su nombre completo'
    verde_label = '🟢 Perfil Vocacional Alineado'
    amar_label  = '🟡 Perfil Incongruente al seleccionado'

    st.markdown("## 📘 Información particular del estudiantado – Reporte ejecutivo")

    st.markdown("### 🧭 Selección de carrera y estudiante")
    carreras = sorted(df[col_carrera].dropna().unique())
    if not carreras:
        st.warning("No hay carreras disponibles en el archivo.")
        return

    carrera_sel = st.selectbox("Carrera a evaluar:", carreras, index=0)
    d_carrera   = df[df[col_carrera] == carrera_sel].copy()

    nombres = sorted(d_carrera[col_nombre].astype(str).unique())
    est_sel  = st.selectbox("Estudiante:", nombres, index=0)

    alumno_mask = (df[col_carrera] == carrera_sel) & (df[col_nombre].astype(str) == est_sel)
    alumno = df[alumno_mask].copy()
    if alumno.empty:
        st.warning("No se encontró el estudiante seleccionado.")
        return
    al = alumno.iloc[0]

    # KPIs
    cat_label = al['Categoría_UI']
    cat_color = CAT_UI_COLORS.get(cat_label, GRAY)
    total_carrera = len(d_carrera)
    n_cat  = int((d_carrera['Categoría_UI'] == cat_label).sum())
    pct_cat = (n_cat / total_carrera * 100) if total_carrera else 0.0

    verde_carr = d_carrera[d_carrera['Categoría_UI']==verde_label].copy()
    amar_carr  = d_carrera[d_carrera['Categoría_UI']==amar_label].copy()
    indicador = "Alumno regular"
    if not verde_carr.empty and est_sel in (verde_carr.sort_values('Score', ascending=False).head(5)[col_nombre].astype(str).tolist()):
        indicador = "Joven promesa"
    if not amar_carr.empty and est_sel in (amar_carr.sort_values('Score', ascending=True).head(5)[col_nombre].astype(str).tolist()):
        indicador = "Alumno en riesgo de reprobar"

    # Referencia para comparativos (promedio Alineado; si no hay, promedio carrera)
    ref_cols = [f'TOTAL_{a}' for a in AREAS]
    mask_carrera = df[col_carrera] == carrera_sel
    mask_verde   = df['Categoría_UI'] == verde_label
    ref_df = df.loc[mask_carrera & mask_verde, ref_cols] if not df.loc[mask_carrera & mask_verde, ref_cols].empty else df.loc[mask_carrera, ref_cols]
    ref_vec  = ref_df.mean().astype(float)
    al_vec   = df.loc[alumno_mask, ref_cols].iloc[0].astype(float)
    diff     = (al_vec - ref_vec)
    fortalezas = diff[diff > 0].sort_values(ascending=False)
    oportun    = diff[diff < 0].abs().sort_values(ascending=False)

    st.markdown("## 🧾 Reporte ejecutivo individual")
    c1, c2, c3, c4 = st.columns([2.2, 2, 2.2, 2])
    with c1: st.markdown(f"<div class='card kpi'><b>Nombre del estudiante</b><br>{est_sel}</div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='card kpi'><b>Carrera</b><br>{carrera_sel}</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='card kpi'><b>Categoría identificada</b><br><span style='font-weight:700;color:{cat_color}'>{cat_label}</span></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='card kpi'><b>Nº en esta categoría</b><br>{n_cat} (<span style='font-weight:700'>{pct_cat:.1f}%</span>)</div>", unsafe_allow_html=True)

    badge_color = {"Joven promesa": GREEN, "Alumno en riesgo de reprobar": AMBER}.get(indicador, SLATE)
    st.markdown(f"<span class='badge' style='background:rgba(2,6,23,.04);color:{badge_color}'>Indicador: {indicador}</span>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### ✅ Fortalezas destacadas")
    if fortalezas.empty:
        st.info("No se observan dimensiones por encima del promedio de referencia del grupo.")
    else:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for letra, delta in fortalezas.items():
            k = letra.replace("TOTAL_", "")
            st.markdown(f"<li><b>{k}</b> (+{delta:.2f}) — {DESC_CHASIDE[k]}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    st.markdown("### 🛠️ Áreas de oportunidad")
    if oportun.empty:
        st.info("El estudiante no presenta brechas importantes respecto al grupo.")
    else:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for letra, gap in oportun.items():
            k = letra.replace("TOTAL_", "")
            st.markdown(f"<li><b>{k}</b> (−{gap:.2f}) — {DESC_CHASIDE[k]}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    st.divider()

    # Coherencia vocacional y afinidad
    st.markdown("### 🎯 Coherencia vocacional (elección vs perfil CHASIDE)")
    area_fuerte = al['Area_Fuerte_Ponderada']
    perfil_sel  = PERFIL_CARRERAS.get(str(carrera_sel).strip())
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

    # Descargas (individual y por carrera)
    def resumen_para(alumno_row: pd.Series) -> dict:
        a_mask = (df[col_carrera]==carrera_sel) & (df[col_nombre].astype(str)==str(alumno_row[col_nombre]))
        a_vec  = df.loc[a_mask, [f'TOTAL_{x}' for x in AREAS]].iloc[0].astype(float)
        diffs  = (a_vec - ref_vec)
        fort   = [k.replace("TOTAL_","") for k,v in diffs.items() if v>0]
        opp    = [k.replace("TOTAL_","") for k,v in diffs.items() if v<0]

        ind = "Alumno regular"
        if not verde_carr.empty and alumno_row[col_nombre] in (verde_carr.sort_values('Score', ascending=False).head(5)[col_nombre].astype(str).tolist()):
            ind = "Joven promesa"
        if not amar_carr.empty and alumno_row[col_nombre] in (amar_carr.sort_values('Score', ascending=True).head(5)[col_nombre].astype(str).tolist()):
            ind = "Alumno en riesgo de reprobar"

        cat_ui_local = alumno_row['Categoría_UI']
        n_local = int((d_carrera['Categoría_UI']==cat_ui_local).sum())
        pct_local = (n_local/total_carrera*100) if total_carrera else 0.0

        area_f = alumno_row['Area_Fuerte_Ponderada']
        suger = ", ".join(sorted([c for c,p in PERFIL_CARRERAS.items() if area_f in p.get('Fuerte', [])]))

        return {
            "Nombre": str(alumno_row[col_nombre]),
            "Carrera": carrera_sel,
            "Categoría (UI)": cat_ui_local,
            "N en categoría (carrera)": n_local,
            "% en categoría (carrera)": round(pct_local,1),
            "Indicador": ind,
            "Área fuerte CHASIDE": area_f,
            "Carreras afines (CHASIDE)": suger,
            "Fortalezas (letras)": ", ".join(fort),
            "Áreas de oportunidad (letras)": ", ".join(opp),
        }

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
# MÓDULO 4 – Equipo de trabajo
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
# LAYOUT PRINCIPAL – Sidebar con módulos y URL
# =========================================================
with st.sidebar:
    st.markdown("### ⚙️ Fuente de datos")
    url_default = "https://docs.google.com/spreadsheets/d/1BNAeOSj2F378vcJE5-T8iJ8hvoseOleOHr-I7mVfYu4/export?format=csv"
    data_url = st.text_input("URL de Google Sheets (CSV export)", url_default)

    st.markdown("---")
    modulo = st.radio(
        "Módulo",
        ["Presentación", "Información general", "Información individual", "Equipo de trabajo"],
        index=0
    )

# Cargar y procesar datos (para módulos 2 y 3)
df_processed = None
if modulo in ("Información general", "Información individual"):
    try:
        df_raw = load_csv(data_url)
        df_processed = preprocess_chaside(df_raw, peso_intereses=0.8)  # ponderación por defecto
    except Exception as e:
        st.error(f"❌ No fue posible cargar/procesar los datos: {e}")
        st.stop()

# Render según módulo
if modulo == "Presentación":
    render_presentacion()
elif modulo == "Información general":
    render_info_general(df_processed)
elif modulo == "Información individual":
    render_info_individual(df_processed)
else:
    render_equipo()
