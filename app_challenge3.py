import streamlit as st
import pandas as pd
import plotly.express as px
import wbgapi as wb
import country_converter as coco

try:
    import janitor  # noqa: F401
    CLEAN = True
except Exception:
    CLEAN = False


# Streamlit Page Setup
st.set_page_config(page_title="Electricity, Emissions & GDP", layout="wide")
st.title("🌍 Electricity, CO₂ Emissions, and GDP (Interactive)")
st.caption("Data Source: Our World in Data, World Bank")

# Data Loading (cached)
@st.cache_data(show_spinner=True)
def load_data():
    # --- CO₂ per capita (OWID) ---
    co2 = pd.read_csv(
        "https://ourworldindata.org/grapher/co-emissions-per-capita.csv"
        "?v=1&csvType=full&useColumnShortNames=true"
    )
    if CLEAN and hasattr(co2, "clean_names"):
        co2 = co2.clean_names()
        co2 = co2.rename(columns={
            "emissions_total_per_capita": "co2_per_capita",
            "entity": "country",
            "code": "iso_code"
        })
    else:
        co2 = co2.rename(columns={
            "Entity": "country",
            "Code": "iso_code",
            "Year": "year",
            "emissions_total_per_capita": "co2_per_capita"
        })
    co2 = co2[co2["year"] >= 1990]

    # --- Energy (OWID) ---
    energy = pd.read_csv(
        "https://nyc3.digitaloceanspaces.com/owid-public/data/energy/owid-energy-data.csv"
    )
    if CLEAN and hasattr(energy, "clean_names"):
        energy = energy.clean_names()
    energy.rename(columns={
        "biofuel_electricity": "biofuel",
        "coal_electricity": "coal",
        "gas_electricity": "gas",
        "hydro_electricity": "hydro",
        "nuclear_electricity": "nuclear",
        "oil_electricity": "oil",
        "other_renewable_exc_biofuel_electricity": "other_renewable",
        "solar_electricity": "solar",
        "wind_electricity": "wind",
    }, inplace=True, errors="ignore")
    energy = energy.query("year >= 1990").dropna(subset=["iso_code"])

    # --- GDP per capita (World Bank API) ---
    indicator = "NY.GDP.PCAP.PP.KD"

    def fetch_gdp_or_fallback(energy_df_for_fallback: pd.DataFrame) -> pd.DataFrame:
        try:
            gdp = wb.data.DataFrame(
                indicator,
                time=range(1990, 2024),
                skipBlanks=True,
                columns="series",
                skipAggs=True,          # 避免 502 错误
                numericTimeKeys=True
            ).reset_index()
            gdp = gdp.rename(columns={
                "economy": "iso_code",
                "time": "year",
                indicator: "gdp_percap"
            })
            gdp = gdp.dropna(subset=["gdp_percap"])
            return gdp[["iso_code", "year", "gdp_percap"]]
        except Exception as e:
            st.warning(
                f"World Bank API unavailable ({e}). "
                "Falling back to GDP per capita computed from OWID energy data (gdp/population)."
            )
            fb = energy_df_for_fallback[["iso_code", "year", "gdp", "population"]].dropna()
            fb = fb.assign(gdp_percap=fb["gdp"] / fb["population"])
            return fb[["iso_code", "year", "gdp_percap"]]

    gdp = fetch_gdp_or_fallback(energy)

    # --- Merge datasets ---
    merged = pd.merge(
        energy[[
            "iso_code", "country", "year", "electricity_generation",
            "biofuel", "coal", "gas", "hydro", "nuclear", "oil",
            "other_renewable", "solar", "wind"
        ]],
        gdp[["iso_code", "year", "gdp_percap"]],
        on=["iso_code", "year"],
        how="inner"
    )

    combined = pd.merge(
        merged,
        co2[["iso_code", "year", "co2_per_capita"]],
        on=["iso_code", "year"],
        how="inner"
    )

    # --- Add continent info ---
    combined["continent"] = coco.convert(
        names=combined["country"], to="continent", not_found=None
    )

    # --- Create long-format version for electricity mix ---
    long_energy = (
        combined
        .melt(
            id_vars=[
                "iso_code", "country", "year", "gdp_percap",
                "co2_per_capita", "continent", "electricity_generation"
            ],
            value_vars=[
                "biofuel", "coal", "gas", "hydro",
                "nuclear", "oil", "other_renewable",
                "solar", "wind"
            ],
            var_name="source", value_name="value"
        )
        .dropna(subset=["value"])
    )

    return combined, long_energy


# Load Data
df, energy_long = load_data()


# Sidebar Filters
st.sidebar.header("Filters")
countries = sorted(df["country"].unique().tolist())
country = st.sidebar.selectbox(
    "Select a country",
    countries,
    index=countries.index("United Kingdom") if "United Kingdom" in countries else 0
)

year_min, year_max = int(df["year"].min()), int(df["year"].max())
year_range = st.sidebar.slider("Year range", year_min, year_max, (2000, 2020))


filtered = df[(df["country"] == country) & (df["year"].between(*year_range))]
energy_long_f = energy_long[
    (energy_long["country"] == country) &
    (energy_long["year"].between(*year_range))
]


# Tabs with Interactive Visualizations
tab1, tab2, tab3 = st.tabs([
    "Electricity mix",
    "CO₂ & GDP trends",
    "CO₂ vs GDP"
])

# --- Tab 1: Electricity mix ---
with tab1:
    st.subheader(f"Electricity Mix (%) — {country}")
    mix = (
        energy_long_f
        .pivot_table(index="year", columns="source", values="value", aggfunc="sum")
        .apply(lambda r: r / r.sum(), axis=1)
        .reset_index()
        .melt(id_vars="year", var_name="source", value_name="share")
        .dropna()
    )
    fig_mix = px.area(
        mix,
        x="year",
        y="share",
        color="source",
        labels={"share": "Share of electricity", "year": "Year"},
        template="plotly_white"
    )
    fig_mix.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_mix, use_container_width=True)

# --- Tab 2: CO₂ & GDP trends ---
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        fig_co2 = px.line(
            filtered,
            x="year", y="co2_per_capita",
            title="CO₂ Emissions per Capita (tonnes)",
            template="plotly_white",
            color_discrete_sequence=["#CB454A"]
        )
        st.plotly_chart(fig_co2, use_container_width=True)
    with c2:
        fig_gdp = px.line(
            filtered,
            x="year", y="gdp_percap",
            title="GDP per Capita (PPP, constant 2021 $)",
            template="plotly_white",
            color_discrete_sequence=["#2E74C0"]
        )
        st.plotly_chart(fig_gdp, use_container_width=True)

# --- Tab 3: Scatter CO₂ vs GDP ---
with tab3:
    st.subheader(f"CO₂ vs GDP — {country}")
    fig_sc = px.scatter(
        filtered,
        x="gdp_percap",
        y="co2_per_capita",
        color="year",
        template="plotly_white",
        color_continuous_scale="Viridis",
        labels={
            "gdp_percap": "GDP per capita (PPP)",
            "co2_per_capita": "CO₂ per capita (tonnes)"
        }
    )
    st.plotly_chart(fig_sc, use_container_width=True)

# --- Data Table ---
st.markdown("### 📊 Filtered Data")
st.dataframe(filtered, use_container_width=True, height=320)
st.download_button(
    "💾 Download CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name=f"{country}_{year_range[0]}_{year_range[1]}.csv",
    mime="text/csv"
)