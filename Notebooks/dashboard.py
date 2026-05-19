import streamlit as st
import pandas as pd
import plotly.express as px

# Cargar datos
df_stats = pd.read_pickle("df_stats.pkl")
df = pd.read_pickle("df.pkl")
df_significancia = pd.read_pickle("df_significancia.pkl")
st.set_page_config(page_title="Dashboard de Significancia", layout="wide")

st.title("Dashboard de Comparación de Features")

# ---------------------------------------------------
# Selección de variable
# ---------------------------------------------------
features = df_significancia["variable"].tolist()

feature = st.selectbox(
    "Selecciona una feature",
    features,
    index=0
)

# ---------------------------------------------------
# Obtener resultados estadísticos
# ---------------------------------------------------
fila = df_significancia.loc[
    df_significancia["variable"] == feature
].iloc[0]

p_value = fila["p_value"]
prueba = fila["prueba"]
significativo = fila["<0.05"]

# Columnas opcionales si existen
p_value_bh = fila["p_value_bh"] if "p_value_bh" in fila.index else None
effect_size = fila["effect_size"] if "effect_size" in fila.index else None
effect_magnitude = (
    fila["effect_magnitude"]
    if "effect_magnitude" in fila.index
    else None
)

# ---------------------------------------------------
# Mostrar métricas
# ---------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("p-value", f"{p_value:.3e}")
c2.metric("Prueba", prueba)
c3.metric("Significativo", "Sí" if significativo else "No")

if effect_size is not None and pd.notna(effect_size):
    c4.metric("Effect Size", f"{effect_size:.3f}")

if p_value_bh is not None:
    st.write(f"**p-value ajustado (Benjamini-Hochberg):** {p_value_bh:.3e}")

if effect_magnitude is not None:
    st.write(f"**Magnitud del efecto:** {effect_magnitude}")

# ---------------------------------------------------
# Preparar datos
# ---------------------------------------------------
datos = df_stats[[feature]].join(df["target"]).dropna()

# ---------------------------------------------------
# Histograma interactivo
# ---------------------------------------------------
fig = px.histogram(
    datos,
    x=feature,
    color="target",
    histnorm="probability density",
    barmode="overlay",
    opacity=0.55,
    marginal="box"
)

fig.update_layout(
    title=f"{feature}",
    legend_title="Grupo",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------
# Tabla de resultados
# ---------------------------------------------------
with st.expander("Ver resultados estadísticos"):
    st.dataframe(fila.to_frame().T, use_container_width=True)

# ---------------------------------------------------
# Ranking completo
# ---------------------------------------------------
with st.expander("Ver ranking completo"):
    st.dataframe(df_significancia, use_container_width=True)