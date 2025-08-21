# ============================================
# CHASIDE • App completa con 4 módulos
# ============================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------- CONFIG ----------
st.set_page_config(page_title="CHASIDE • Diagnóstico Vocacional", layout="wide")

# ---------- CONSTANTES ----------
PRIMARY = "#0F766E"; ACCENT = "#14B8A6"; SLATE = "#475569"
GREEN = "#22c55e"; AMBER = "#f59e0b"; RED = "#ef4444"; GRAY = "#6b7280"; LIGHT = "#94a3b8"

AREAS = ['C','H','A','S','I','D','E']
DESC = {
    "C": "Administrativo/gestión: organización, análisis, cálculo, orden.",
    "H": "Humanidades/social: precisión verbal, justicia, persuasión, síntesis.",
    "A": "Artístico/creativo: detalle, innovación, intuición, habilidades manuales/visuales.",
    "S": "Salud/servicio: ayudar, análisis, precisión, paciencia, altruismo.",
    "I": "Técnico/ingenieril: cálculo, pensamiento científico/crítico, planificación.",
    "D": "Defensa/seguridad: justicia, liderazgo, decisión, trabajo colaborativo.",
    "E": "Ciencias experimentales: investigación, método, análisis numérico, observación."
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

# ---------- ESTILOS ----------
st.markdown(f"""
<style>
.block-container {{ padding-top: 1.0rem; }}
.h1-title {{ font-size: 2.0rem; font-weight: 800; color:{PRIMARY}; margin-bottom:.25rem; }}
.subtitle {{ color:#64748B; margin-bottom:1rem; }}
.section-title {{ font-weight:700; font-size:1.1rem; margin:1rem 0 .25rem 0; color:{PRIMARY}; }}
.card {{
  border: 1px solid #e5e7eb; border-radius: 16px; padding: 14px 16px;
  background: #ffffff; box-shadow: 0 2px 8px rgba(0,0,0,.04); margin-bottom:.75rem;
}}
.badge {{
  display:inline-block; padding: 4px 10px; border-radius: 999px; font-weight:700; font-size:.85rem;
  background: rgba(20,184,166,.12); color:{PRIMARY};
}}
.kpi {{ font-size:1.05rem; margin:.15rem 0; }}
.kpi b {{ color:{SLATE}; }}
.list-tight li {{ margin-bottom:.2rem; }}
</style>
""", unsafe_allow_html=True)

# ---------- HELPERS DE DATOS ----------
def _col_names():
    return '¿A qué carrera desea ingresar?', 'Ingrese su nombre completo'

def _chaside_mapeos():
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
    return intereses_items, aptitudes_items

@st.cache_data(show_spinner=False)
def load_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

def preprocess_df(df_raw: pd.DataFrame, peso_intereses: float = 0.8) -> pd.DataFrame:
    """Limpia y calcula todas las métricas necesarias para todos los módulos."""
    df = df_raw.copy()
    col_carrera, col_nombre = _col_names()

    # Validación mínima
    if col_carrera not in df.columns or col_nombre not in df.columns:
        return pd.DataFrame()

    # Ítems CHASIDE
    columnas_items = df.columns[5:103]
    # Sí/No → 1/0
    df_items = (
        df[columnas_items].astype(str).apply(lambda c: c.str.strip().str.lower())
        .replace({'sí':1,'si':1,'s':1,'1':1,'true':1,'verdadero':1,'x':1,
                  'no':0,'n':0,'0':0,'false':0,'falso':0,'':'0','nan':0})
        .apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    )
    df[columnas_items] = df_items

    # Coincidencia (sesgo Sí/No)
    suma_si = df[columnas_items].sum(axis=1)
    total_items = len(columnas_items)
    pct_si = np.where(total_items==0, 0, suma_si/total_items)
    pct_no = 1 - pct_si
    df['Coincidencia'] = np.maximum(pct_si, pct_no)

    # Mapear CHASIDE
    intereses_items, aptitudes_items = _chaside_mapeos()
    def col_item(i:int)->str: return columnas_items[i-1]
    for a in AREAS:
        df[f'INTERES_{a}']  = df[[col_item(i) for i in intereses_items[a]]].sum(axis=1)
        df[f'APTITUD_{a}'] = df[[col_item(i) for i in aptitudes_items[a]]].sum(axis=1)

    # Ponderación
    peso_aptitudes = 1 - peso_intereses
    for a in AREAS:
        df[f'PUNTAJE_COMBINADO_{a}'] = df[f'INTERES_{a}']*peso_intereses + df[f'APTITUD_{a}']*peso_aptitudes
        df[f'TOTAL_{a}'] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']
    df['Area_Fuerte_Ponderada'] = df.apply(lambda r: max(AREAS, key=lambda a: r[f'PUNTAJE_COMBINADO_{a}']), axis=1)

    # Coherencia con carrera (simple)
    def evaluar(area, carrera):
        p = PERFIL_CARRERAS.get(str(carrera).strip())
        if not p: return 'Sin perfil definido'
        if area in p.get('Fuerte',[]): return 'Coherente'
        if area in p.get('Baja',[]):   return 'Requiere Orientación'
        return 'Neutral'
    df['Coincidencia_Ponderada'] = df.apply(lambda r: evaluar(r['Area_Fuerte_Ponderada'], r[col_carrera]), axis=1)

    # Diagnóstico / Semáforo
    def carrera_mejor(r):
        if r['Coincidencia'] >= 0.75:
            return 'Información no aceptable'
        a = r['Area_Fuerte_Ponderada']
        c_actual = str(r[col_carrera]).strip()
        sugeridas = [c for c,p in PERFIL_CARRERAS.items() if a in p.get('Fuerte',[])]
        if c_actual in sugeridas: return c_actual
        return ', '.join(sugeridas) if sugeridas else 'Sin sugerencia clara'

    def diagnostico(r):
        if r['Carrera_Mejor_Perfilada']=='Información no aceptable': return 'Información no aceptable'
        if str(r[col_carrera]).strip()==str(r['Carrera_Mejor_Perfilada']).strip(): return 'Perfil adecuado'
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

    # Score general para violin/rankings
    score_cols = [f'PUNTAJE_COMBINADO_{a}' for a in AREAS]
    df['Score'] = df[score_cols].max(axis=1)

    return df

# ---------- MÓDULO 1: Presentación ----------
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
Esta herramienta orienta a estudiantes de bachillerato en el **descubrimiento de sus intereses y aptitudes**,
para apoyar una **elección de carrera informada y alineada** con sus fortalezas y aspiraciones.
Integra resultados de la escala CHASIDE y los presenta de forma clara para estudiantes, familias y docentes.
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Madurez y personalidad en el bachillerato</div>', unsafe_allow_html=True)
    st.markdown("""
La **personalidad** se encuentra en pleno desarrollo durante el bachillerato.
La **madurez** permite al joven definirse y reflexionar sobre su proyecto de vida, pero el proceso aún está en construcción.
En esta etapa es clave contar con **herramientas de orientación** que acompañen la toma de decisiones académicas.
""")

    st.markdown('<div class="section-title">¿Qué es la escala CHASIDE?</div>', unsafe_allow_html=True)
    st.markdown("""
**CHASIDE** integra **intereses** y **aptitudes** en siete áreas:
**C, H, A, S, I, D, E**. Es de aplicación rápida (ítems sí/no) y con interpretación sencilla
para vincular resultados con opciones de carrera.
""")

    st.markdown('<div class="section-title">Propuesta Única de Valor (PUV)</div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="card">
<b>Orientación vocacional personalizada</b>, basada en evidencia (CHASIDE),
con visualizaciones claras (pastel, barras apiladas, violín y radar),
y reportes descargables para que estudiantes identifiquen sus fortalezas y
las escuelas cuenten con <b>insumos objetivos</b> para el acompañamiento académico.
</div>
""", unsafe_allow_html=True)

# ---------- MÓDULO 2: Información general ----------
def render_resultados_generales(df: pd.DataFrame):
    col_carrera, col_nombre = _col_names()
    if df.empty:
        st.warning("Carga un archivo válido para visualizar resultados.")
        return

    st.header("🥧 Diagnóstico general (Pastel)")
    resumen = df['Semáforo Vocacional'].value_counts().reset_index()
    resumen.columns=['Categoría','N']
    fig = px.pie(
        resumen, names='Categoría', values='N', hole=0.35,
        color='Categoría',
        color_discrete_map={'Verde':GREEN,'Amarillo':AMBER,'Rojo':RED,'No aceptable':GRAY,'Sin sugerencia':LIGHT}
    )
    fig.update_traces(textposition='inside', texttemplate='%{label}<br>%{percent:.1%} (%{value})')
    st.plotly_chart(fig,use_container_width=True)

    st.header("📊 Distribución por carrera y categoría")
    cats_order = ['Verde', 'Amarillo', 'No aceptable', 'Sin sugerencia']
    color_map = {'Verde':GREEN,'Amarillo':AMBER,'No aceptable':RED,'Sin sugerencia':LIGHT}

    stacked = (
        df[df['Semáforo Vocacional'].isin(cats_order)]
        .groupby([col_carrera, 'Semáforo Vocacional'], dropna=False)
        .size().reset_index(name='N')
        .rename(columns={'Semáforo Vocacional':'Categoría'})
    )
    stacked['Categoría'] = pd.Categorical(stacked['Categoría'], categories=cats_order, ordered=True)

    modo = st.radio("Modo de visualización", ["Proporción (100% apilado)", "Valores absolutos"], horizontal=True, index=0)
    if modo == "Proporción (100% apilado)":
        stacked['%'] = stacked.groupby(col_carrera)['N'].transform(lambda x: 0 if x.sum()==0 else x/x.sum()*100)
        fig_stacked = px.bar(
            stacked, x=col_carrera, y='%', color='Categoría',
            category_orders={'Categoría': cats_order},
            color_discrete_map=color_map, barmode='stack',
            text=stacked['%'].round(1).astype(str) + '%',
            title="Proporción (%) de estudiantes por carrera y categoría"
        )
        fig_stacked.update_layout(yaxis_title="Proporción (%)", xaxis_title="Carrera", xaxis_tickangle=-30, height=620)
    else:
        fig_stacked = px.bar(
            stacked, x=col_carrera, y='N', color='Categoría',
            category_orders={'Categoría': cats_order},
            color_discrete_map=color_map, barmode='stack',
            text='N', title="Estudiantes por carrera y categoría (valores absolutos)"
        )
        fig_stacked.update_layout(yaxis_title="Número de estudiantes", xaxis_title="Carrera", xaxis_tickangle=-30, height=620)
        fig_stacked.update_traces(textposition='inside', cliponaxis=False)
    st.plotly_chart(fig_stacked, use_container_width=True)

    st.header("🎻 Distribución de puntajes (Violin plot) – Verde vs Amarillo")
    df_scores = df.copy()
    df_scores['Score'] = df_scores[[f'PUNTAJE_COMBINADO_{a}' for a in AREAS]].max(axis=1)
    df_violin = df_scores[df_scores['Semáforo Vocacional'].isin(['Verde','Amarillo'])].copy()

    if df_violin.empty:
        st.info("No hay estudiantes en categorías Verde o Amarillo para graficar.")
    else:
        fig_violin = px.violin(
            df_violin, x=col_carrera, y="Score", color="Semáforo Vocacional",
            box=True, points=False,
            color_discrete_map={"Verde": GREEN, "Amarillo": AMBER},
            title="Distribución de puntajes por carrera (Verde vs Amarillo)"
        )
        categorias = df_violin[col_carrera].unique()
        for i in range(len(categorias) - 1):
            fig_violin.add_vline(x=i + 0.5, line_width=1, line_dash="dot", line_color="gray")
        fig_violin.update_layout(xaxis_title="Carrera", yaxis_title="Score combinado", xaxis_tickangle=-30, height=720)
        st.plotly_chart(fig_violin, use_container_width=True)

    st.header("🕸️ Radar CHASIDE por carrera – Verde vs Amarillo (con brechas)")
    # Totales por letra = INTERES + APTITUD
    df_radar = df.copy()
    for a in AREAS:
        df_radar[a] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']
    df_radar['Categoría'] = df['Semáforo Vocacional']
    df_radar['Carrera']   = df[col_carrera]

    carreras_disp = sorted(df_radar['Carrera'].dropna().unique())
    if not carreras_disp:
        st.info("No hay carreras para el radar.")
        return

    tabs = st.tabs(carreras_disp)
    for tab, carrera_sel in zip(tabs, carreras_disp):
        with tab:
            sub = df_radar[(df_radar['Carrera']==carrera_sel) & (df_radar['Categoría'].isin(['Verde','Amarillo']))]
            if sub.empty or sub['Categoría'].nunique() < 2:
                st.warning("No hay datos suficientes de Verde y Amarillo en esta carrera.")
                continue
            prom = sub.groupby('Categoría')[AREAS].mean().reset_index()
            fig = px.line_polar(
                prom.melt(id_vars='Categoría', value_vars=AREAS, var_name='Área', value_name='Promedio'),
                r='Promedio', theta='Área', color='Categoría', line_close=True, markers=True,
                color_discrete_map={'Verde':GREEN,'Amarillo':AMBER},
                title=f"Perfil CHASIDE – {carrera_sel}"
            )
            fig.update_traces(fill='toself', opacity=0.75)
            st.plotly_chart(fig, use_container_width=True)

            prom_w = sub.groupby('Categoría')[AREAS].mean()
            diffs = (prom_w.loc['Verde'] - prom_w.loc['Amarillo']).sort_values(ascending=False)
            top3 = diffs.head(3)
            st.markdown("**Áreas a reforzar (donde Amarillo está más bajo):**")
            for letra, delta in top3.items():
                st.markdown(f"- **{letra}** (Δ = {delta:.2f}): {DESC[letra]}")

# ---------- MÓDULO 3: Información individual ----------
def render_info_individual(df: pd.DataFrame):
    col_carrera, col_nombre = _col_names()
    if df.empty:
        st.warning("Carga un archivo válido para visualizar resultados.")
        return

    st.markdown('<div class="h1-title">📘 Información particular del estudiantado – CHASIDE</div>', unsafe_allow_html=True)
    st.caption("Reporte ejecutivo individual con indicadores y recomendaciones por dimensiones CHASIDE.")
    # Selección
    carreras = sorted(df[col_carrera].dropna().astype(str).unique())
    if not carreras:
        st.warning("No hay carreras disponibles.")
        return
    carrera_sel = st.selectbox("Carrera a evaluar:", carreras, index=0)
    d_carrera = df[df[col_carrera]==carrera_sel].copy()

    nombres = sorted(d_carrera[col_nombre].astype(str).unique())
    est_sel = st.selectbox("Estudiante:", nombres, index=0)

    alumno_mask = (df[col_carrera]==carrera_sel) & (df[col_nombre].astype(str)==est_sel)
    alumno = df[alumno_mask]
    if alumno.empty:
        st.warning("No se encontró el estudiante seleccionado.")
        return
    al = alumno.iloc[0]

    # KPIs
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

    # Comparativo (fortalezas / oportunidades) — referencia: Verde de la carrera; si no hay, promedio de la carrera
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

    # Coherencia + carreras afines
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

    # Descargas (individual / carrera)
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

# ---------- MÓDULO 4: Equipo ----------
def render_equipo():
    st.header("👥 Equipo de trabajo")
    st.markdown("""
Este proyecto fue elaborado por el siguiente equipo interdisciplinario:

- **Dra. Elena Elsa Bricio Barrios** – Especialista en Psicología Educativa  
- **Dr. Santiago Arceo-Díaz** – Investigador en Ciencias Médicas y Datos  
- **Psic. Martha Cecilia Ramírez Guzmán** – Psicóloga orientada al desarrollo vocacional
""")
    st.caption("Tecnológico Nacional de México – Instituto Tecnológico de Colima")

# ---------- UI GLOBAL ----------
st.sidebar.title("CHASIDE • Navegación")
modulo = st.sidebar.radio(
    "Selecciona módulo:",
    ["Presentación", "Información general", "Información individual", "Equipo de trabajo"],
    index=0
)

# Entrada de URL (una vez para toda la app)
st.sidebar.markdown("---")
url_default = "https://docs.google.com/spreadsheets/d/1BNAeOSj2F378vcJE5-T8iJ8hvoseOleOHr-I7mVfYu4/export?format=csv"
url = st.sidebar.text_input("URL de Google Sheets (CSV export)", url_default)

# Ponderación global (afecta procesamiento)
peso_intereses = st.sidebar.slider("Peso de Intereses", 0.0, 1.0, 0.8, 0.05)
with st.sidebar.expander("Leyenda de colores"):
    st.markdown(f"- Verde: <span style='color:{GREEN}'>éxito/coherencia</span>", unsafe_allow_html=True)
    st.markdown(f"- Amarillo: <span style='color:{AMBER}'>atención</span>", unsafe_allow_html=True)
    st.markdown(f"- Rojo: <span style='color:{RED}'>requiere orientación</span>", unsafe_allow_html=True)
    st.markdown(f"- Gris: <span style='color:{GRAY}'>no aceptable/sin sugerencia</span>", unsafe_allow_html=True)

# Carga y preproceso (una sola vez)
try:
    df_raw = load_csv(url)
    df_proc = preprocess_df(df_raw, peso_intereses=peso_intereses)
except Exception as e:
    st.error(f"❌ No fue posible cargar o procesar el archivo: {e}")
    df_proc = pd.DataFrame()

# Ruteo
if modulo == "Presentación":
    render_presentacion()

elif modulo == "Información general":
    render_resultados_generales(df_proc)

elif modulo == "Información individual":
    render_info_individual(df_proc)

elif modulo == "Equipo de trabajo":
    render_equipo()
