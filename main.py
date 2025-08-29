# ============================================================
# CHASIDE • App completa con 4 módulos (Streamlit) — versión rápida
# ============================================================
# Requisitos:
#   streamlit, pandas, numpy, plotly
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -----------------------
# Estilos y constantes UI
# -----------------------
PRIMARY = "#0F766E"; ACCENT="#14B8A6"; SLATE="#475569"
GREEN="#22c55e"; AMBER="#f59e0b"; RED="#ef4444"; GRAY="#6b7280"; BLUE="#3b82f6"

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
# Config de página + CSS
# -----------------------
st.set_page_config(page_title="CHASIDE • App", layout="wide")
st.markdown(f"""
<style>
.block-container {{ padding-top: 1.0rem; }}
.h1-title {{ font-size: 1.9rem; font-weight: 800; color:{PRIMARY}; margin-bottom:.25rem; }}
.subtitle {{ color:#64748B; margin-bottom: 1.0rem; }}
.section-title {{ font-weight:700; font-size:1.1rem; margin: 1.1rem 0 .4rem 0; color:{PRIMARY}; }}
.card {{ border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px 16px; background:#fff; box-shadow:0 2px 8px rgba(0,0,0,.04); }}
.badge {{ display:inline-block; padding: 4px 10px; border-radius: 999px; font-weight:700; font-size:.85rem; background: rgba(20,184,166,0.12); color:{PRIMARY}; }}
.kpi {{ font-size:1.02rem; }}
.kpi b {{ color:{SLATE}; }}
.list-tight li {{ margin-bottom:.2rem; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# Utilidades de datos (cacheadas)
# ============================================================

@st.cache_data(show_spinner=False)  # ⚡ cachea la descarga de CSV
def load_csv(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = [str(c) for c in df.columns]
    return df

# Precompilación de mapeos (una sola vez)
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
    'C':[2,15,46,51],'H':[30,63,72,86],'A':[22,39,76,82],
    'S':[4,29,40,69],'I':[10,26,59,90],'D':[13,18,43,66],'E':[7,55,79,94]
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

# ⚡ precomputo: para cada área, cadena de sugeridas y set para membership
SUGERIDAS_POR_AREA = {a: sorted([c for c,p in PERFIL_CARRERAS.items() if a in p.get('Fuerte', [])]) for a in AREAS}
SUGERIDAS_POR_AREA_STR = {a: ", ".join(SUGERIDAS_POR_AREA[a]) if SUGERIDAS_POR_AREA[a] else "Sin sugerencia clara" for a in AREAS}
FUERTES_SETS = {c: set(p.get('Fuerte', [])) for c,p in PERFIL_CARRERAS.items()}

@st.cache_data(show_spinner=False)  # ⚡ cachea TODO el pipeline procesado
def process_chaside(df_raw: pd.DataFrame):
    df = df_raw.copy()

    col_car = '¿A qué carrera desea ingresar?'
    col_nom = 'Ingrese su nombre completo'
    if col_car not in df.columns or col_nom not in df.columns:
        raise ValueError(f"Faltan columnas: '{col_car}', '{col_nom}'")

    # a string + categoricals (⚡ menos memoria y más rápidos los groupby)
    df[col_car] = df[col_car].astype('string')
    df[col_nom] = df[col_nom].astype('string')

    cols_items = df.columns[5:103]

    # ⚡ vector: Sí/No → 1/0 (dtypes compactos)
    clean = (
        df[cols_items].astype(str).apply(lambda c: c.str.strip().str.lower())
          .replace({'sí':1,'si':1,'s':1,'1':1,'true':1,'verdadero':1,'x':1,
                    'no':0,'n':0,'0':0,'false':0,'falso':0,'':'0','nan':0})
          .apply(pd.to_numeric, errors='coerce').fillna(0).astype(np.uint8)
    )
    df[cols_items] = clean

    # Coincidencia (sesgo)
    suma_si = clean.sum(axis=1)
    total_items = clean.shape[1]
    pct_si = suma_si / total_items
    df['Coincidencia'] = np.maximum(pct_si, 1 - pct_si).astype(np.float32)

    # ⚡ construimos índices reales de columnas por número de ítem (una vez)
    def col_item(i:int)->str: return cols_items[i-1]

    # ⚡ sumas por área (uint8 → small ints)
    for a in AREAS:
        df[f'INTERES_{a}']  = df[[col_item(i) for i in INTERESES_ITEMS[a]]].sum(axis=1).astype(np.uint8)
        df[f'APTITUD_{a}'] = df[[col_item(i) for i in APTITUDES_ITEMS[a]]].sum(axis=1).astype(np.uint8)

    # Ponderación fija + ⚡ idxmax sin apply fila a fila
    peso_i, peso_a = 0.8, 0.2
    punt_cols = []
    for a in AREAS:
        col = f'PUNTAJE_COMBINADO_{a}'
        df[col] = (df[f'INTERES_{a}']*peso_i + df[f'APTITUD_{a}']*peso_a).astype(np.float32)
        punt_cols.append(col)

    # ⚡ área fuerte = idxmax más mapeo
    idx = df[punt_cols].values.argmax(axis=1)
    df['Area_Fuerte_Ponderada'] = pd.Series(idx, index=df.index).map({i:a for i,a in enumerate(AREAS)}).astype('category')

    # Score = máximo de puntajes (⚡ sin apply)
    df['Score'] = df[punt_cols].max(axis=1).astype(np.float32)

    # Totales por letra (INTERES + APTITUD)
    for a in AREAS:
        df[f'TOTAL_{a}'] = (df[f'INTERES_{a}'] + df[f'APTITUD_{a}']).astype(np.uint16)

    # ⚡ Coincidencia_Ponderada sin funciones costosas
    # (necesitamos membership: área fuerte ∈ FUERTE(carrera))
    def coh_fast(area_series: pd.Series, carrera_series: pd.Series) -> pd.Series:
        # usa comprehension vectorizado con zip (rápido y sin overhead de apply con lambdas complejas)
        out = []
        for ar, car in zip(area_series.astype(str), carrera_series.astype(str)):
            fuertes = FUERTES_SETS.get(car, set())
            if not fuertes:
                out.append('Sin perfil definido')
            elif ar in fuertes:
                out.append('Coherente')
            else:
                out.append('Neutral')  # sin 'Baja' en perfiles dados
        return pd.Series(out, index=area_series.index, dtype="string")

    df['Coincidencia_Ponderada'] = coh_fast(df['Area_Fuerte_Ponderada'], df[col_car])

    # ⚡ Carrera_Mejor_Perfilada (sin recomputar sugeridas una y otra vez)
    sug_por_area_str = pd.Series(SUGERIDAS_POR_AREA_STR)
    sug_por_area_set = {a:set(SUGERIDAS_POR_AREA[a]) for a in AREAS}

    def mejor_rapido(row):
        if row['Coincidencia'] >= 0.75:
            return 'Información no aceptable'
        a = str(row['Area_Fuerte_Ponderada'])
        c = str(row[col_car]).strip()
        if c in sug_por_area_set.get(a, set()):
            return c
        return sug_por_area_str.get(a, 'Sin sugerencia clara')

    df['Carrera_Mejor_Perfilada'] = df[['Coincidencia','Area_Fuerte_Ponderada', col_car]].apply(mejor_rapido, axis=1)

    # Diagnóstico + Semáforo (⚡ reglas compactas)
    diag = np.where(df['Carrera_Mejor_Perfilada'].eq('Información no aceptable'),
                    'Información no aceptable',
             np.where(df[col_car].astype(str).str.strip().eq(df['Carrera_Mejor_Perfilada'].astype(str).str.strip()),
                    'Perfil adecuado',
             np.where(df['Carrera_Mejor_Perfilada'].eq('Sin sugerencia clara'),
                    'Sin sugerencia clara',
                    'Sugerencia: ' + df['Carrera_Mejor_Perfilada'].astype(str))))
    df['Diagnóstico Primario Vocacional'] = pd.Series(diag, dtype='string')

    def semaforo_fast(diag_val, coh_val):
        if diag_val == 'Información no aceptable': return 'No aceptable'
        if diag_val == 'Sin sugerencia clara':     return 'Sin sugerencia'
        if coh_val == 'Coherente':                  return 'Verde'
        if coh_val == 'Neutral':                    return 'Amarillo'
        if coh_val == 'Requiere Orientación':       return 'Rojo'
        return 'Sin sugerencia'

    df['Semáforo Vocacional'] = [
        semaforo_fast(d, c) for d, c in zip(df['Diagnóstico Primario Vocacional'], df['Coincidencia_Ponderada'])
    ]

    # Etiqueta UI + categoricals (⚡)
    df['Categoría_UI'] = df['Semáforo Vocacional'].map(CAT_INT_TO_UI).fillna("Sin sugerencia")
    df['Categoría_UI'] = pd.Categorical(df['Categoría_UI'], categories=CAT_UI_ORDER, ordered=True)
    df[col_car] = df[col_car].astype('category')   # ⚡ groupby más rápido
    df[col_nom] = df[col_nom].astype('string')

    return df, col_car, col_nom

# ============================================================
# Agregados cacheados para gráficas (⚡)
# ============================================================
@st.cache_data(show_spinner=False)
def agg_pie(df: pd.DataFrame):
    return (df['Categoría_UI'].value_counts()
            .reindex(CAT_UI_ORDER, fill_value=0)
            .rename_axis('Categoría_UI')
            .reset_index(name='N'))

@st.cache_data(show_spinner=False)
def agg_stacked(df: pd.DataFrame, col_car: str):
    out = df.groupby([col_car,'Categoría_UI']).size().reset_index(name='N')
    out['Categoría_UI'] = pd.Categorical(out['Categoría_UI'], categories=CAT_UI_ORDER, ordered=True)
    return out

# ============================================================
# Módulos
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
</div>""", unsafe_allow_html=True)
        with col2:
            st.markdown("""
<div class="card">
<b>Institución</b><br>
Tecnológico Nacional de México<br>
Instituto Tecnológico de Colima
</div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-title">¿Qué pretende esta aplicación?</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="card">
Herramienta para alinear intereses y aptitudes con la elección de carrera,
usando la escala CHASIDE y visualizaciones claras para estudiantes, familias y docentes.
</div>""", unsafe_allow_html=True)

def render_info_general(df: pd.DataFrame, col_car: str):
    st.markdown('<div class="h1-title">Información general</div>', unsafe_allow_html=True)
    st.caption("Resumen global por categoría, carrera y comparativas Verde vs Amarillo.")

    # Pastel (solo %)
    st.subheader("🥧 Distribución general por categoría")
    resumen = agg_pie(df)  # ⚡
    fig_pie = px.pie(
        resumen, names='Categoría_UI', values='N', hole=0.35,
        color='Categoría_UI', color_discrete_map=CAT_UI_COLORS,
        title="Distribución general por categoría"
    )
    fig_pie.update_traces(textposition='inside', texttemplate='%{percent:.1%}')
    fig_pie.update_layout(legend_title_text="Categoría")
    st.plotly_chart(fig_pie, use_container_width=True)

    # Barras apiladas
    st.subheader("🏫 Distribución por carrera y categoría")
    stacked = agg_stacked(df, col_car)  # ⚡
    modo = st.radio("Modo de visualización", ["Proporción (100% apilado)", "Valores absolutos"], horizontal=True, index=0)

    if modo == "Proporción (100% apilado)":
        stacked = stacked.copy()
        stacked['%'] = stacked.groupby(col_car)['N'].transform(lambda x: 0 if x.sum()==0 else x/x.sum()*100)
        fig = px.bar(stacked, x=col_car, y='%', color='Categoría_UI',
                     category_orders={'Categoría_UI': CAT_UI_ORDER},
                     color_discrete_map=CAT_UI_COLORS, barmode='stack',
                     text=stacked['%'].round(1).astype(str)+'%',
                     title="Proporción (%) por carrera")
        fig.update_layout(yaxis_title="Proporción (%)", xaxis_title="Carrera", xaxis_tickangle=-30)
    else:
        fig = px.bar(stacked, x=col_car, y='N', color='Categoría_UI',
                     category_orders={'Categoría_UI': CAT_UI_ORDER},
                     color_discrete_map=CAT_UI_COLORS, barmode='stack',
                     text='N', title="Número de estudiantes por carrera")
        fig.update_layout(yaxis_title="Número de estudiantes", xaxis_title="Carrera", xaxis_tickangle=-30)
        fig.update_traces(textposition='inside')
    st.plotly_chart(fig, use_container_width=True)

    # Violín Verde vs Amarillo
    st.subheader("🎻 Distribución de puntajes (Violin) – Verde vs Amarillo por carrera")
    verde_ui = CAT_INT_TO_UI['Verde']; amarillo_ui = CAT_INT_TO_UI['Amarillo']
    df_violin = df[df['Categoría_UI'].isin([verde_ui, amarillo_ui])]
    if df_violin.empty:
        st.info("No hay estudiantes en categorías Verde o Amarillo para graficar.")
    else:
        fig_v = px.violin(df_violin, x=col_car, y="Score", color="Categoría_UI",
                          box=True, points=False, color_discrete_map=CAT_UI_COLORS,
                          category_orders={"Categoría_UI":[verde_ui,amarillo_ui]},
                          title="Distribución de Score por carrera (Verde vs Amarillo)")
        # líneas punteadas
        cats = sorted(df_violin[col_car].astype(str).unique())
        for i in range(len(cats)-1):
            fig_v.add_vline(x=i+0.5, line_width=1, line_dash="dot", line_color="gray")
        fig_v.update_layout(xaxis_title="Carrera", yaxis_title="Score (máximo ponderado CHASIDE)",
                            xaxis_tickangle=-30, legend_title_text="Categoría")
        st.plotly_chart(fig_v, use_container_width=True)

    # Radar Verde vs Amarillo
    st.subheader("🕸️ Radar CHASIDE – Comparación Verde vs Amarillo por carrera")
    carreras = sorted(df[col_car].dropna().astype(str).unique())
    if not carreras:
        st.info("No hay carreras para mostrar en el radar.")
        return
    carrera_sel = st.selectbox("Elige una carrera para comparar:", carreras)
    sub = df[(df[col_car].astype(str)==carrera_sel) & (df['Categoría_UI'].isin([verde_ui,amarillo_ui]))]

    if sub.empty or sub['Categoría_UI'].nunique() < 2:
        st.warning("No hay datos suficientes de Verde y Amarillo en esta carrera.")
    else:
        tot_cols = [f'TOTAL_{a}' for a in AREAS]
        prom = sub.groupby('Categoría_UI')[tot_cols].mean()
        prom_ren = prom.rename(columns={f'TOTAL_{a}':a for a in AREAS}).reset_index()
        fig_r = px.line_polar(prom_ren.melt(id_vars='Categoría_UI', value_vars=AREAS,
                                            var_name='Área', value_name='Promedio'),
                              r='Promedio', theta='Área', color='Categoría_UI',
                              line_close=True, markers=True, color_discrete_map=CAT_UI_COLORS,
                              category_orders={'Categoría_UI':[verde_ui,amarillo_ui]},
                              title=f"Perfil CHASIDE – {carrera_sel} (Verde vs Amarillo)")
        fig_r.update_traces(fill='toself', opacity=0.75)
        st.plotly_chart(fig_r, use_container_width=True)

        diffs = (prom.loc[verde_ui] - prom.loc[amarillo_ui])
        diffs.index = [i.replace("TOTAL_","") for i in diffs.index]
        top3 = diffs.sort_values(ascending=False).head(3)
        st.markdown("**Áreas a reforzar (donde *Amarillo* está más bajo):**")
        for letra, delta in top3.items():
            st.markdown(f"- **{letra}** (Δ = {delta:.2f}) — {DESC_CHASIDE[letra]}")

def render_info_individual(df: pd.DataFrame, col_car: str, col_nom: str):
    st.markdown('<div class="h1-title">Información particular del estudiantado</div>', unsafe_allow_html=True)
    st.caption("Reporte ejecutivo individual con indicadores y recomendaciones.")

    carreras = sorted(df[col_car].dropna().astype(str).unique())
    if not carreras:
        st.warning("No hay carreras disponibles en el archivo."); return
    carrera_sel = st.selectbox("Carrera a evaluar:", carreras, index=0)

    d_carr = df[df[col_car].astype(str)==carrera_sel]
    if d_carr.empty:
        st.warning("No hay estudiantes para esta carrera."); return

    nombres = sorted(d_carr[col_nom].astype(str).unique())
    est_sel = st.selectbox("Estudiante:", nombres, index=0)

    alumno = d_carr[d_carr[col_nom].astype(str)==est_sel]
    if alumno.empty:
        st.warning("No se encontró el estudiante seleccionado."); return
    al = alumno.iloc[0]

    cat_ui = al['Categoría_UI']
    total_carr = len(d_carr)
    n_cat = int((d_carr['Categoría_UI']==cat_ui).sum())
    pct_cat = (n_cat/total_carr*100) if total_carr else 0.0

    verde_ui = CAT_INT_TO_UI['Verde']; amarillo_ui = CAT_INT_TO_UI['Amarillo']
    verde_carr = d_carr[d_carr['Categoría_UI']==verde_ui]
    amar_carr  = d_carr[d_carr['Categoría_UI']==amarillo_ui]

    indicador = "Alumno regular"
    if not verde_carr.empty and est_sel in (verde_carr.sort_values('Score', ascending=False).head(5)[col_nom].astype(str).tolist()):
        indicador = "Joven promesa"
    if not amar_carr.empty and est_sel in (amar_carr.sort_values('Score', ascending=True).head(5)[col_nom].astype(str).tolist()):
        indicador = "Alumno en riesgo de reprobar"

    # referencia: promedio Verde de la carrera; si no hay, promedio de la carrera
    ref_cols = [f'TOTAL_{a}' for a in AREAS]
    verdes_ref = d_carr[d_carr['Categoría_UI']==verde_ui]
    ref_df = verdes_ref[ref_cols] if not verdes_ref.empty else d_carr[ref_cols]
    ref_vec = ref_df.mean().astype(float)
    al_vec  = alumno[ref_cols].iloc[0].astype(float)
    diff    = (al_vec - ref_vec)
    fortalezas   = diff[diff>0].sort_values(ascending=False)
    oportunidades= diff[diff<0].abs().sort_values(ascending=False)

    # KPIs
    st.markdown("## 🧾 Reporte ejecutivo individual")
    c1,c2,c3,c4 = st.columns([2.2,2,2.6,2])
    with c1: st.markdown(f"<div class='card kpi'><b>Nombre del estudiante</b><br>{est_sel}</div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='card kpi'><b>Carrera</b><br>{carrera_sel}</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='card kpi'><b>Categoría identificada</b><br><span style='font-weight:700;color:{BLUE}'>{cat_ui}</span></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='card kpi'><b>Nº en esta categoría</b><br>{n_cat} (<span style='font-weight:700'>{pct_cat:.1f}%</span>)</div>", unsafe_allow_html=True)
    badge_color = {"Joven promesa": GREEN, "Alumno en riesgo de reprobar": AMBER}.get(indicador, SLATE)
    st.markdown(f"<span class='badge' style='background:rgba(20,184,166,.12);color:{badge_color}'>Indicador: {indicador}</span>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### ✅ Fortalezas destacadas")
    if fortalezas.empty:
        st.info("No se observan dimensiones por encima del promedio de referencia del grupo.")
    else:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for letra_full, delta in fortalezas.items():
            k = str(letra_full).replace("TOTAL_","")
            st.markdown(f"<li><b>{k}</b> (+{delta:.2f}) — {DESC_CHASIDE[k]}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    st.markdown("### 🛠️ Áreas de oportunidad")
    if oportunidades.empty:
        st.info("El estudiante no presenta brechas importantes respecto al grupo.")
    else:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for letra_full, gap in oportunidades.items():
            k = str(letra_full).replace("TOTAL_","")
            st.markdown(f"<li><b>{k}</b> (−{gap:.2f}) — {DESC_CHASIDE[k]}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    st.divider()

    # Coherencia + afinidades
    st.markdown("### 🎯 Coherencia vocacional y afinidades")
    area_fuerte = str(al['Area_Fuerte_Ponderada'])
    perfil_sel = PERFIL_CARRERAS.get(carrera_sel, {})
    if area_fuerte in set(perfil_sel.get('Fuerte', [])): coh_text="Coherente"
    elif area_fuerte in set(perfil_sel.get('Baja', [])): coh_text="Requiere orientación"
    else: coh_text="Neutral"
    sugeridas = SUGERIDAS_POR_AREA.get(area_fuerte, [])
    st.write(f"- **Área fuerte (CHASIDE):** {area_fuerte}")
    st.write(f"- **Evaluación de coherencia con la carrera elegida:** {coh_text}")
    st.markdown("### 📚 Carreras con mayor afinidad al perfil (según CHASIDE)")
    if sugeridas:
        st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
        for c in sugeridas: st.markdown(f"<li>{c}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
    else:
        st.info("No se identificaron carreras afines basadas en el área fuerte.")

    # Descargas (CSV)
    def resumen_para(row: pd.Series) -> dict:
        a_vec = row[ref_cols].astype(float)
        diffs = (a_vec - ref_vec)
        fort = [k.replace("TOTAL_","") for k,v in diffs.items() if v>0]
        opp  = [k.replace("TOTAL_","") for k,v in diffs.items() if v<0]
        cat_local = row['Categoría_UI']
        n_local = int((d_carr['Categoría_UI']==cat_local).sum())
        pct_local = (n_local/total_carr*100) if total_carr else 0.0
        area_f = row['Area_Fuerte_Ponderada']
        sug = ", ".join(SUGERIDAS_POR_AREA.get(str(area_f), []))
        ind = "Alumno regular"
        if not verde_carr.empty and str(row[col_nom]) in (verde_carr.sort_values('Score', ascending=False).head(5)[col_nom].astype(str).tolist()):
            ind = "Joven promesa"
        if not amar_carr.empty and str(row[col_nom]) in (amar_carr.sort_values('Score', ascending=True).head(5)[col_nom].astype(str).tolist()):
            ind = "Alumno en riesgo de reprobar"
        return {
            "Nombre": str(row[col_nom]),
            "Carrera": carrera_sel,
            "Categoría": cat_local,
            "N en categoría (carrera)": n_local,
            "% en categoría (carrera)": round(pct_local,1),
            "Indicador": ind,
            "Área fuerte CHASIDE": str(area_f),
            "Carreras afines (CHASIDE)": sug,
            "Fortalezas (letras)": ", ".join(fort),
            "Áreas de oportunidad (letras)": ", ".join(opp),
        }

    col_a, col_b = st.columns([1.2, 1])
    with col_a:
        data_ind = pd.DataFrame([resumen_para(al)])
        st.download_button("⬇️ Descargar reporte individual (CSV)",
                           data=data_ind.to_csv(index=False).encode("utf-8"),
                           file_name=f"reporte_individual_{est_sel}.csv",
                           mime="text/csv", use_container_width=True)
    with col_b:
        data_all = pd.DataFrame([resumen_para(r) for _, r in d_carr.iterrows()])
        st.download_button("⬇️ Descargar reporte de la carrera (CSV)",
                           data=data_all.to_csv(index=False).encode("utf-8"),
                           file_name=f"reporte_carrera_{carrera_sel}.csv",
                           mime="text/csv", use_container_width=True)

def render_equipo():
    st.markdown('<div class="h1-title">Equipo de trabajo</div>', unsafe_allow_html=True)
    st.markdown("""
Este proyecto fue elaborado por el siguiente equipo interdisciplinario:

- **Dra. Elena Elsa Bricio Barrios** – AÑADIR SEMBLANZA  
- **Dr. Santiago Arceo-Díaz** – AÑADIR SEMBLANZA  
- **Psic. Martha Cecilia Ramírez Guzmán** – AÑADIR SEMBLANZA
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

    # Procesamiento cacheado (⚡)
    try:
        df_raw = load_csv(url)
        df, col_car, col_nom = process_chaside(df_raw)
    except Exception as e:
        st.error(f"❌ No fue posible cargar/procesar el archivo: {e}")
        return

    if modulo == "Información general":
        render_info_general(df, col_car)
    elif modulo == "Información individual":
        render_info_individual(df, col_car, col_nom)
    elif modulo == "Equipo de trabajo":
        render_equipo()

if __name__ == "__main__":
    main()
