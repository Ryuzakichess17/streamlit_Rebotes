import streamlit as st
import plotly.express as px
from pathlib import Path
from utils import cargar_datos, resumen_kam_tipo, resumen_documento, to_excel
import io

# =============================
# CONFIGURACIÓN GENERAL
# =============================
st.set_page_config(
    page_title="Dashboard de Rebotes",
    layout="wide"
)

# =============================
# ESTILOS (CSS)
# =============================
st.markdown("""
<style>
[data-testid="metric-container"] {
    background-color: #F8F9FA;
    border-radius: 12px;
    padding: 15px;
    border-left: 6px solid #0D6EFD;
}

thead tr th {
    background-color: #0D6EFD;
    color: white;
}

h1, h2, h3 {
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# =============================
# RUTA BASE
# =============================
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "rebotes.xlsx"

# =============================
# CARGA DE DATOS
# =============================
df = cargar_datos(DATA_PATH)

# =============================
# TÍTULO
# =============================
st.title("📉 Rebotes – Montos no Pagados")

# =============================
# FILTROS (LIMPIOS)
# =============================
with st.sidebar.expander("🎛️ Filtros", expanded=True):

    kam_sel = st.selectbox(
        "KAM",
        options=["Todos"] + sorted(df["KAM"].dropna().unique().tolist())
    )

    condicion_sel = st.segmented_control(
        "Condición",
        options=df["CONDICION"].unique(),
        selection_mode="multi",
        default=df["CONDICION"].unique()
    )

    canal_sel = st.segmented_control(
        "Canal",
        options=df["CANAL"].unique(),
        selection_mode="multi",
        default=df["CANAL"].unique()
    )

df_f = df.copy()

if kam_sel != "Todos":
    df_f = df_f[df_f["KAM"] == kam_sel]

df_f = df_f[
    (df_f["CONDICION"].isin(condicion_sel)) &
    (df_f["CANAL"].isin(canal_sel))
]

# =============================
# KPIs
# =============================
c1, c2, c3 = st.columns(3)

c1.metric(
    "💰 Rebotes Totales",
    f"S/ {df_f['MONTO'].sum():,.2f}",
    help="Monto total retenido pendiente de pago"
)

c2.metric(
    "👥 HC Afectados",
    df_f["DOCUMENTO"].nunique(),
    help="Documentos únicos con rebotes"
)

c3.metric(
    "📄 Registros",
    len(df_f)
)

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
    use_container_width=True
)

st.markdown("### 📥 Exportar a Excel")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        "⬇️ Descargar TODO (Excel)",
        to_excel(df),
        file_name="rebotes_completo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with col2:
    st.download_button(
        "⬇️ Descargar FILTRADO (Excel)",
        to_excel(df_f),
        file_name="rebotes_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =============================
# GRÁFICA KAM x CONDICIÓN
# =============================
st.subheader("📉 Rebotes por KAM y Condición")

df_cond = (
    df_f.groupby(["KAM", "CONDICION"], as_index=False)
    .agg(MONTO=("MONTO", "sum"))
)

fig = px.bar(
    df_cond,
    x="KAM",
    y="MONTO",
    color="CONDICION",
    text_auto=".2s"
)

fig.update_layout(
    yaxis_title="Monto (S/)",
    legend_title="Condición"
)

st.plotly_chart(fig, use_container_width=True)

# =============================
# BUSCADOR POR DOCUMENTO
# =============================
st.subheader("🔍 Consulta por DOCUMENTO")

doc = st.text_input("Ingrese DOCUMENTO")

if doc:
    df_doc = df_f[df_f["DOCUMENTO"] == doc]

    if df_doc.empty:
        st.warning("Documento no encontrado")
    else:
        resumen_doc = resumen_documento(df_doc)

        c1, c2 = st.columns(2)
        c1.metric(
            "💰 Total Adeudado",
            f"S/ {resumen_doc['MONTO_TOTAL'].sum():,.2f}"
        )
        c2.metric(
            "📄 Cantidad de Detalles",
            len(resumen_doc)
        )

        st.dataframe(
            resumen_doc.style.format(
                {"MONTO_TOTAL": "S/ {:,.2f}"}
            ),
            use_container_width=True
        )

        st.download_button(
            "⬇️ Descargar detalle",
            data=resumen_doc.to_csv(index=False),
            file_name=f"detalle_{doc}.csv"
        )

# =============================
# DETALLE GENERAL
# =============================
with st.expander("📄 Ver detalle completo"):
    st.dataframe(df_f, use_container_width=True)