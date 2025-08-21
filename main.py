# ============================================
# MÓDULO 3 · INFORMACIÓN PARTICULAR DEL ESTUDIANTADO
# Reporte ejecutivo individual (UI formal + descargas)
# ============================================
import streamlit as st
import pandas as pd
import numpy as np

# ---------- estilos rápidos ----------
PRIMARY = "#0F766E"     # teal-700
ACCENT  = "#14B8A6"     # teal-400
SLATE   = "#475569"     # slate-600
GREEN   = "#22c55e"
AMBER   = "#f59e0b"
GRAY    = "#6b7280"

st.set_page_config(page_title="Información particular • CHASIDE", layout="wide")
st.markdown(f"""
<style>
.block-container {{ padding-top: 1.0rem; }}
.h1-title {{ font-size: 1.8rem; font-weight: 800; color:{PRIMARY}; margin-bottom:.25rem; }}
.badge {{
  display:inline-block; padding: 4px 10px; border-radius:999px; font-weight:700; font-size:.85rem;
  background: rgba(20,184,166,.12); color:{PRIMARY};
}}
.card {{
  border: 1px solid #e5e7eb; border-radius: 16px; padding: 14px 16px; background:#fff;
  box-shadow: 0 2px 8px rgba(0,0,0,.03); margin-bottom:.75rem;
}}
.kpi {{ font-size:1.05rem; margin:.15rem 0; }}
.kpi b {{ color:{SLATE}; }}
.list-tight li {{ margin-bottom:.2rem; }}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="h1-title">📘 Información particular del estudiantado – CHASIDE</div>', unsafe_allow_html=True)
st.caption("Reporte ejecutivo individual con indicadores y recomendaciones por dimensiones CHASIDE.")

# ---------- entrada de datos ----------
url = st.text_input(
    "URL de Google Sheets (CSV export)",
    "https://docs.google.com/spreadsheets/d/1BNAeOSj2F378vcJE5-T8iJ8hvoseOleOHr-I7mVfYu4/export?format=csv"
)

@st.cache_data(show_spinner=False)
def load_data(u: str) -> pd.DataFrame:
    return pd.read_csv(u)

try:
    df = load_data(url)
except Exception as e:
    st.error(f"❌ No fue posible cargar el archivo: {e}")
    st.stop()

# ---------- preprocesamiento CHASIDE ----------
columnas_items = df.columns[5:103]
columna_carrera = '¿A qué carrera desea ingresar?'
columna_nombre  = 'Ingrese su nombre completo'

faltantes = [c for c in [columna_carrera, columna_nombre] if c not in df.columns]
if faltantes:
    st.error(f"❌ Faltan columnas requeridas: {faltantes}")
    st.stop()

# Sí/No → 1/0
df_items = (
    df[columnas_items].astype(str).apply(lambda c: c.str.strip().str.lower())
      .replace({
          'sí':1,'si':1,'s':1,'1':1,'true':1,'verdadero':1,'x':1,
          'no':0,'n':0,'0':0,'false':0,'falso':0,'':'0','nan':0
      })
      .apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
)
df[columnas_items] = df_items

# Coincidencia (sesgo Sí/No)
suma_si = df[columnas_items].sum(axis=1)
porcentaje_si = suma_si / len(columnas_items)
df['Coincidencia'] = np.maximum(porcentaje_si, 1 - porcentaje_si)

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
    'C':[2,15,46,51], 'H':[30,63,72,86], 'A':[22,39,76,82],
    'S':[4,29,40,69], 'I':[10,26,59,90], 'D':[13,18,43,66], 'E':[7,55,79,94]
}
def col_item(i:int)->str: return columnas_items[i-1]

for a in areas:
    df[f'INTERES_{a}']  = df[[col_item(i) for i in intereses_items[a]]].sum(axis=1)
    df[f'APTITUD_{a}'] = df[[col_item(i) for i in aptitudes_items[a]]].sum(axis=1)

peso_intereses, peso_aptitudes = 0.8, 0.2
for a in areas:
    df[f'PUNTAJE_COMBINADO_{a}'] = df[f'INTERES_{a}']*peso_intereses + df[f'APTITUD_{a}']*peso_aptitudes

df['Area_Fuerte_Ponderada'] = df.apply(lambda r: max(areas, key=lambda a: r[f'PUNTAJE_COMBINADO_{a}']), axis=1)
score_cols = [f'PUNTAJE_COMBINADO_{a}' for a in areas]
df['Score'] = df[score_cols].max(axis=1)
for a in areas:
    df[f'TOTAL_{a}'] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']

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

# Diagnóstico de alto nivel (mantenemos tu lógica base)
df['Coincidencia_Ponderada'] = df.apply(lambda r: evaluar(r['Area_Fuerte_Ponderada'], r[columna_carrera]), axis=1)

def carrera_mejor(r):
    if r['Coincidencia'] >= 0.75: return 'Información no aceptable'
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

# ---------- diccionario CHASIDE (para textos en fortalezas / oportunidades) ----------
desc_chaside = {
    "C": "Organización, supervisión, orden, análisis y síntesis, colaboración, cálculo.",
    "H": "Precisión verbal, organización, relación de hechos, justicia, persuasión.",
    "A": "Estético y creativo; detallista, innovador, intuitivo; habilidades visuales, auditivas y manuales.",
    "S": "Asistir y ayudar; investigación, precisión, percepción, análisis; altruismo y paciencia.",
    "I": "Cálculo y pensamiento científico/crítico; exactitud, planificación; enfoque práctico.",
    "D": "Justicia y equidad; colaboración, liderazgo; valentía y toma de decisiones.",
    "E": "Investigación; orden, análisis y síntesis; cálculo numérico, observación; método y seguridad."
}

# ---------- selección de carrera / estudiante ----------
st.markdown("### 🧭 Selección de carrera y estudiante")
carreras = sorted(df[columna_carrera].dropna().unique())
if not carreras:
    st.warning("No hay carreras disponibles en el archivo.")
    st.stop()

carrera_sel = st.selectbox("Carrera a evaluar:", carreras, index=0)
d_carrera   = df[df[columna_carrera] == carrera_sel].copy()

nombres = sorted(d_carrera[columna_nombre].astype(str).unique())
est_sel  = st.selectbox("Estudiante:", nombres, index=0)

alumno_mask = (df[columna_carrera] == carrera_sel) & (df[columna_nombre].astype(str) == est_sel)
alumno = df[alumno_mask].copy()
if alumno.empty:
    st.warning("No se encontró el estudiante seleccionado.")
    st.stop()
al = alumno.iloc[0]

# ---------- KPIs del encabezado ----------
cat = al['Semáforo Vocacional']
cat_color = { "Verde": GREEN, "Amarillo": AMBER }.get(cat, GRAY)
total_carrera = len(d_carrera)
n_cat = int((d_carrera['Semáforo Vocacional'] == cat).sum())
pct_cat = (n_cat / total_carrera * 100) if total_carrera else 0.0

# Indicador de riesgo (top 5 verde o bottom 5 amarillo dentro de la carrera)
verde_carr = d_carrera[d_carrera['Semáforo Vocacional']=='Verde'].copy()
amar_carr  = d_carrera[d_carrera['Semáforo Vocacional']=='Amarillo'].copy()

indicador = "Alumno regular"
if not verde_carr.empty:
    if est_sel in (verde_carr.sort_values('Score', ascending=False).head(5)[columna_nombre].astype(str).tolist()):
        indicador = "Joven promesa"
if not amar_carr.empty:
    if est_sel in (amar_carr.sort_values('Score', ascending=True).head(5)[columna_nombre].astype(str).tolist()):
        indicador = "Alumno en riesgo de reprobar"

# ---------- comparativo por letra (referencia = promedio grupo VERDE de la carrera; si no hay, promedio carrera) ----------
ref_cols = [f'TOTAL_{a}' for a in areas]
mask_carrera = df[columna_carrera] == carrera_sel
mask_verde   = df['Semáforo Vocacional'] == 'Verde'

if df.loc[mask_carrera & mask_verde, ref_cols].empty:
    ref_df = df.loc[mask_carrera, ref_cols]
else:
    ref_df = df.loc[mask_carrera & mask_verde, ref_cols]

ref_vec  = ref_df.mean().astype(float)
al_vec   = df.loc[alumno_mask, ref_cols].iloc[0].astype(float)
diff     = (al_vec - ref_vec)  # positivo = por encima del grupo

# Fortalezas (Δ>0) y Oportunidades (Δ<0) → ordenadas por magnitud
fortalezas = diff[diff > 0].sort_values(ascending=False)
oportun    = diff[diff < 0].abs().sort_values(ascending=False)

# ---------- ENCABEZADO BONITO ----------
st.markdown("## 🧾 Reporte ejecutivo individual")

c1, c2, c3, c4 = st.columns([2.2, 2, 2.2, 2])
with c1:
    st.markdown(f"<div class='card kpi'><b>Nombre del estudiante</b><br>{est_sel}</div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='card kpi'><b>Carrera</b><br>{carrera_sel}</div>", unsafe_allow_html=True)
with c3:
    st.markdown(
        f"<div class='card kpi'><b>Categoría identificada</b><br>"
        f"<span style='font-weight:700;color:{cat_color}'>{cat}</span></div>",
        unsafe_allow_html=True
    )
with c4:
    st.markdown(
        f"<div class='card kpi'><b>Nº en esta categoría</b><br>{n_cat} "
        f"(<span style='font-weight:700'>{pct_cat:.1f}%</span>)</div>",
        unsafe_allow_html=True
    )

# Indicador de riesgo (badge de color)
badge_color = {"Joven promesa": GREEN, "Alumno en riesgo de reprobar": AMBER}.get(indicador, SLATE)
st.markdown(
    f"<span class='badge' style='background:rgba(34,197,94,.12);color:{badge_color}'>"
    f"Indicador: {indicador}</span>", unsafe_allow_html=True
)

st.divider()

# ---------- FORTALEZAS / OPORTUNIDADES (con descripciones) ----------
st.markdown("### ✅ Fortalezas destacadas")
if fortalezas.empty:
    st.info("No se observan dimensiones por encima del promedio de referencia del grupo.")
else:
    st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
    for letra, delta in fortalezas.items():
        k = letra.replace("TOTAL_", "") if str(letra).startswith("TOTAL_") else letra
        st.markdown(f"<li><b>{k}</b> (+{delta:.2f}) — {desc_chaside[k]}</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)

st.markdown("### 🛠️ Áreas de oportunidad")
if oportun.empty:
    st.info("El estudiante no presenta brechas importantes respecto al grupo.")
else:
    st.markdown("<ul class='list-tight'>", unsafe_allow_html=True)
    for letra, gap in oportun.items():
        k = letra.replace("TOTAL_", "") if str(letra).startswith("TOTAL_") else letra
        st.markdown(f"<li><b>{k}</b> (−{gap:.2f}) — {desc_chaside[k]}</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)

st.divider()

# ---------- Coherencia vocacional (elección vs perfil CHASIDE) ----------
st.markdown("### 🎯 Coherencia vocacional (elección vs perfil CHASIDE)")
area_fuerte = al['Area_Fuerte_Ponderada']
perfil_sel  = perfil_carreras.get(str(carrera_sel).strip())
if perfil_sel:
    if area_fuerte in perfil_sel.get('Fuerte', []):
        coh_text = "Coherente"
    elif area_fuerte in perfil_sel.get('Baja', []):
        coh_text = "Requiere orientación"
    else:
        coh_text = "Neutral"
else:
    coh_text = "Sin perfil definido"

sugeridas = [c for c,p in perfil_carreras.items() if area_fuerte in p.get('Fuerte', [])]
st.write(f"- **Área fuerte (CHASIDE):** {area_fuerte}")
st.write(f"- **Evaluación de coherencia:** {coh_text}")
if coh_text != "Coherente":
    st.write("- **Carreras con mayor afinidad:** " + (", ".join(sugeridas) if sugeridas else "—"))

st.divider()

# ==========================================================
# DESCARGAS:  reporte individual y reporte de toda la carrera
# ==========================================================
def resumen_para(alumno_row: pd.Series) -> dict:
    # recomputa diffs para cada alumno contra la misma referencia usada (grupo Verde o carrera)
    a_mask = (df[columna_carrera]==carrera_sel) & (df[columna_nombre].astype(str)==str(alumno_row[columna_nombre]))
    a_vec  = df.loc[a_mask, [f'TOTAL_{x}' for x in areas]].iloc[0].astype(float)
    diffs  = (a_vec - ref_vec)
    fort   = [k for k,v in diffs.items() if v>0]
    opp    = [k for k,v in diffs.items() if v<0]
    # indicador
    ind = "Alumno regular"
    if not verde_carr.empty:
        if alumno_row[columna_nombre] in (verde_carr.sort_values('Score', ascending=False).head(5)[columna_nombre].astype(str).tolist()):
            ind = "Joven promesa"
    if not amar_carr.empty:
        if alumno_row[columna_nombre] in (amar_carr.sort_values('Score', ascending=True).head(5)[columna_nombre].astype(str).tolist()):
            ind = "Alumno en riesgo de reprobar"

    cat_local = alumno_row['Semáforo Vocacional']
    n_local = int((d_carrera['Semáforo Vocacional']==cat_local).sum())
    pct_local = (n_local/total_carrera*100) if total_carrera else 0.0

    return {
        "Nombre": str(alumno_row[columna_nombre]),
        "Carrera": carrera_sel,
        "Categoría": cat_local,
        "N en categoría (carrera)": n_local,
        "% en categoría (carrera)": round(pct_local,1),
        "Indicador": ind,
        "Área fuerte CHASIDE": alumno_row['Area_Fuerte_Ponderada'],
        "Fortalezas (letras)": ", ".join(fort),
        "Áreas de oportunidad (letras)": ", ".join(opp),
    }

# Botones
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
