import pandas as pd
import io


def cargar_datos(ruta):
    df = pd.read_excel(
        ruta,
        dtype={"DOCUMENTO": str}  # mantiene ceros a la izquierda
    )

    df.columns = df.columns.str.upper().str.strip()

    df["MONTO"] = pd.to_numeric(df["MONTO"], errors="coerce").fillna(0)

    return df


def resumen_kam_tipo(df):
    tabla = pd.pivot_table(
        df,
        index="KAM",
        columns="TIPO",
        values="MONTO",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    hc = (
        df.groupby("KAM")["DOCUMENTO"]
        .nunique()
        .reset_index(name="HC Afectados")
    )

    return tabla.merge(hc, on="KAM", how="left")


def resumen_documento(df):
    return (
        df.groupby(
            ["DOCUMENTO", "DETALLE", "ERRORES CARGA"],
            as_index=False
        )
        .agg(
            MONTO_TOTAL=("MONTO", "sum"),
            CANTIDAD_DETALLES=("DETALLE", "count")
        )
    )

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Detalle Rebotes")
    return output.getvalue()