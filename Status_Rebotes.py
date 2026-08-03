import io
from pathlib import Path

import plotly.express as px
import streamlit as st
from utils import cargar_datos, resumen_documento, resumen_kam_tipo, to_excel

# =============================
# CONFIGURACIÓN GENERAL
# =============================
st.set_page_config(page_title="Dashboard de Rebotes", layout="wide")

# =============================
# ESTILOS (CSS PERSONALIZADO)
# =============================
st.markdown(
    """
<style>
/* Estilo base para tarjetas */
[data-testid="metric-container"] {
    background-color: #F8F9FA;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

thead tr th {
    background-color: #0D6EFD;
    color: white;
}

h1, h2, h3 {
    font-weight: 600;
}
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# RUTA BASE Y CARGA
# =============================
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "rebotes.xlsx"

df = cargar_datos(DATA_PATH)

# =============================
# TÍTULO
# =============================
st.title("📉 Dashboard de Rebotes y Status de Pagos")

# =============================
# FILTROS
# =============================
with st.sidebar.expander("🎛️ Filtros de Búsqueda", expanded=True):

    kam_sel = st.selectbox(
        "KAM", options=["Todos"] + sorted(df["KAM"].dropna().unique().tolist())
    )

    condicion_sel = st.segmented_control(
        "Condición",
        options=df["CONDICION"].unique(),
        selection_mode="multi",
        default=df["CONDICION"].unique(),
    )

    canal_sel = st.segmented_control(
        "Canal",
        options=df["CANAL"].unique(),
        selection_mode="multi",
        default=df["CANAL"].unique(),
    )

    estado_opciones = df["ESTADO FINAL"].dropna().unique()
    estado_sel = st.segmented_control(
        "Estado Final",
        options=estado_opciones,
        selection_mode="multi",
        default=estado_opciones,
    )

# Aplicar filtros
df_f = df.copy()

if kam_sel != "Todos":
    df_f = df_f[df_f["KAM"] == kam_sel]

df_f = df_f[
    (df_f["CONDICION"].isin(condicion_sel))
    & (df_f["CANAL"].isin(canal_sel))
    & (df_f["ESTADO FINAL"].isin(estado_sel))
]

# =============================
# CÁLCULO DE MÉTRICAS (KPIs)
# =============================
# PENDIENTES (REBOTARON)
df_pendiente = df_f[df_f["ESTADO FINAL"] == "Pendiente"]
monto_pendiente = df_pendiente["MONTO"].sum()
hc_pendiente = df_pendiente["DOCUMENTO"].nunique()

# OK (PROCESADOS CON ÉXITO)
df_ok = df_f[df_f["ESTADO FINAL"] == "Ok"]
monto_ok = df_ok["MONTO"].sum()
hc_ok = df_ok["DOCUMENTO"].nunique()

# TOTALES Y EFECTIVIDAD
monto_total = df_f["MONTO"].sum()
pct_efectividad = (monto_ok / monto_total * 100) if monto_total > 0 else 0

# =============================
# TARJETAS DE KPIs DIFERENCIADAS
# =============================
st.subheader("📌 Resumen del Estado de Pagos")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        label="🚨 Rebotes Pendientes",
        value=f"S/ {monto_pendiente:,.2f}",
        delta=f"{hc_pendiente} HC Afectados",
        delta_color="inverse",
        help="Monto de pagos que rebotaron y siguen sin procesarse",
    )

with c2:
    st.metric(
        label="✅ Procesados con Éxito (Ok)",
        value=f"S/ {monto_ok:,.2f}",
        delta=f"{hc_ok} HC Resueltos",
        delta_color="normal",
        help="Monto de pagos rebotados que ya fueron solucionados correctamente",
    )

with c3:
    st.metric(
        label="💼 Monto Total Gestionado",
        value=f"S/ {monto_total:,.2f}",
        delta=f"{len(df_f)} Registros",
        delta_color="off",
        help="Suma total (Pendientes + Procesados)",
    )

with c4:
    st.metric(
        label="📈 Efectividad de Pago",
        value=f"{pct_efectividad:.1f}%",
        help="Porcentaje del monto rebotado que ya fue solucionado",
    )

st.divider()

# =============================
# TABLA DINÁMICA KAM x TIPO
# =============================
st.subheader("📊 Resumen por KAM y TIPO")

tabla_kam = resumen_kam_tipo(df_f)

st.dataframe(
    tabla_kam.style.format(
        {
            col: "S/ {:,.2f}"
            for col in tabla_kam.columns
            if col not in ["KAM", "HC Afectados"]
        }
    ),
    use_container_width=True,
)

# Exportación
col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "⬇️ Descargar TODO (Excel)",
        to_excel(df),
        file_name="rebotes_completo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with col2:
    st.download_button(
        "⬇️ Descargar FILTRADO (Excel)",
        to_excel(df_f),
        file_name="rebotes_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.divider()

# =============================
# GRÁFICOS VISUALES
# =============================
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("📉 Monto por KAM y Condición")
    df_cond = df_f.groupby(["KAM", "CONDICION"], as_index=False).agg(
        MONTO=("MONTO", "sum")
    )
    fig_cond = px.bar(
        df_cond, x="KAM", y="MONTO", color="CONDICION", text_auto=".2s"
    )
    fig_cond.update_layout(
        yaxis_title="Monto (S/)", legend_title="Condición", height=380
    )
    st.plotly_chart(fig_cond, use_container_width=True)

with col_g2:
    st.subheader("🎯 Estado Final por KAM (Pendiente vs Ok)")
    df_est = df_f.groupby(["KAM", "ESTADO FINAL"], as_index=False).agg(
        MONTO=("MONTO", "sum")
    )
    # Colores semánticos: Rojo = Pendiente, Verde = Ok
    color_map = {"Pendiente": "#DC3545", "Ok": "#198754"}

    fig_est = px.bar(
        df_est,
        x="KAM",
        y="MONTO",
        color="ESTADO FINAL",
        color_discrete_map=color_map,
        text_auto=".2s",
        barmode="group",
    )
    fig_est.update_layout(
        yaxis_title="Monto (S/)", legend_title="Estado Final", height=380
    )
    st.plotly_chart(fig_est, use_container_width=True)

# =============================
# BUSCADOR POR DOCUMENTO
# =============================
st.divider()
st.subheader("🔍 Consulta por DOCUMENTO")

doc = st.text_input("Ingrese número de DOCUMENTO")

if doc:
    df_doc = df_f[df_f["DOCUMENTO"] == doc]

    if df_doc.empty:
        st.warning("⚠️ Documento no encontrado con los filtros actuales.")
    else:
        resumen_doc = resumen_documento(df_doc)

        c_doc1, c_doc2 = st.columns(2)
        c_doc1.metric(
            "💰 Total Adeudado/Procesado",
            f"S/ {resumen_doc['MONTO_TOTAL'].sum():,.2f}",
        )
        c_doc2.metric("📄 Registros Encontrados", len(resumen_doc))

        st.dataframe(
            resumen_doc.style.format({"MONTO_TOTAL": "S/ {:,.2f}"}),
            use_container_width=True,
        )

        st.download_button(
            "⬇️ Descargar detalle (CSV)",
            data=resumen_doc.to_csv(index=False),
            file_name=f"detalle_{doc}.csv",
        )

# =============================
# DETALLE GENERAL
# =============================
with st.expander("📄 Ver detalle completo de registros"):
    st.dataframe(df_f, use_container_width=True)