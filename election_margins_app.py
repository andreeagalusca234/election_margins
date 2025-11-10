import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="US Election Margins 2020 vs 2024", layout="wide")

# Generate Sample Data - NO SWING COUNTIES
@st.cache_data
def generate_sample_data():
    """Generate sample election data - only Republican and Democrat counties"""
    np.random.seed(42)
    
    states = ["Texas", "California", "Florida", "Pennsylvania", "Ohio", "Georgia", "Michigan", "Arizona"]
    
    data = []
    
    # Generate Republican counties (positive margins in both years)
    for i in range(120):
        state = np.random.choice(states)
        base_margin = np.random.uniform(5, 85)  # Positive only
        margin_2020 = base_margin + np.random.normal(0, 3)
        margin_2024 = base_margin + np.random.normal(0, 4)
        
        # Keep positive
        margin_2020 = np.clip(margin_2020, 1, 95)
        margin_2024 = np.clip(margin_2024, 1, 95)
        
        data.append({
            "county": f"County {i+1}",
            "state": state,
            "margin_2020": round(margin_2020, 1),
            "margin_2024": round(margin_2024, 1),
            "total_votes": np.random.randint(100, 80000),
            "party": "Republican"
        })
    
    # Generate Democrat counties (negative margins in both years)
    for i in range(120, 240):
        state = np.random.choice(states)
        base_margin = np.random.uniform(-85, -5)  # Negative only
        margin_2020 = base_margin + np.random.normal(0, 3)
        margin_2024 = base_margin + np.random.normal(0, 4)
        
        # Keep negative
        margin_2020 = np.clip(margin_2020, -95, -1)
        margin_2024 = np.clip(margin_2024, -95, -1)
        
        data.append({
            "county": f"County {i+1}",
            "state": state,
            "margin_2020": round(margin_2020, 1),
            "margin_2024": round(margin_2024, 1),
            "total_votes": np.random.randint(100, 80000),
            "party": "Democrat"
        })
    
    return pd.DataFrame(data)

# Load data
df = generate_sample_data()

# Sidebar Filters
with st.sidebar:
    st.header("🎛️ Filters")
    
    selected_state = st.selectbox(
        "State", 
        ["All"] + sorted(df["state"].unique().tolist())
    )
    
    min_votes = st.slider(
        "Min Total Votes", 
        0, 80000, 0, 5000
    )
    
    show_republican = st.checkbox("Show Republican Counties", value=True)
    show_democrat = st.checkbox("Show Democrat Counties", value=True)

# Apply filters
filtered_df = df.copy()
if selected_state != "All":
    filtered_df = filtered_df[filtered_df["state"] == selected_state]
filtered_df = filtered_df[filtered_df["total_votes"] >= min_votes]
filtered_df = filtered_df[filtered_df["party"].isin(party_filter)]

# Title
st.title("US Presidential Election Margins: 2020 vs. 2024")

# Create scatter plot - EXACTLY like reference
fig = go.Figure()

# Separate data by party
rep_data = filtered_df[filtered_df["party"] == "Republican"]
dem_data = filtered_df[filtered_df["party"] == "Democrat"]

# Add Republican counties (red/coral color like reference)
if len(rep_data) > 0:
    fig.add_trace(go.Scatter(
        x=rep_data["margin_2020"],
        y=rep_data["margin_2024"],
        mode="markers",
        name="Republican Counties",
        marker=dict(
            color="rgba(205, 92, 92, 0.65)",  # Indian red / coral
            size=7,
            line=dict(width=0)
        ),
        customdata=rep_data[["county", "state", "total_votes"]],
        hovertemplate="<b>%{customdata[0]}</b><br>" +
                     "2020 Margin=%{x:.0f}%<br>" +
                     "2024 Margin=%{y:.0f}%<br>" +
                     "state_name=%{customdata[1]}<br>" +
                     "total_votes=%{customdata[2]:,}<extra></extra>"
    ))

# Add Democrat counties (blue like reference)
if len(dem_data) > 0:
    fig.add_trace(go.Scatter(
        x=dem_data["margin_2020"],
        y=dem_data["margin_2024"],
        mode="markers",
        name="Democrat Counties",
        marker=dict(
            color="rgba(65, 105, 225, 0.65)",  # Royal blue
            size=7,
            line=dict(width=0)
        ),
        customdata=dem_data[["county", "state", "total_votes"]],
        hovertemplate="<b>%{customdata[0]}</b><br>" +
                     "2020 Margin=%{x:.0f}%<br>" +
                     "2024 Margin=%{y:.0f}%<br>" +
                     "state_name=%{customdata[1]}<br>" +
                     "total_votes=%{customdata[2]:,}<extra></extra>"
    ))

# Add diagonal reference line (black dashed)
fig.add_shape(
    type="line",
    x0=-100, y0=-100, x1=100, y1=100,
    line=dict(color="black", width=2, dash="dash")
)

# Add vertical line at x=0 (dashed)
fig.add_shape(
    type="line",
    x0=0, y0=-100, x1=0, y1=100,
    line=dict(color="gray", width=2, dash="dash")
)

# Add horizontal line at y=0 (dashed)
fig.add_shape(
    type="line",
    x0=-100, y0=0, x1=100, y1=0,
    line=dict(color="gray", width=2, dash="dash")
)

# Update layout to match reference exactly
fig.update_layout(
    xaxis_title="2020 Margin",
    yaxis_title="2024 Margin",
    font=dict(size=13),
    template="plotly_white",
    height=650,
    xaxis=dict(
        range=[-100, 105],
        tickmode="linear",
        tick0=-100,
        dtick=50,
        ticksuffix="%",
        zeroline=False,
        showgrid=True,
        gridcolor="rgba(211, 211, 211, 0.5)",
        gridwidth=0.8
    ),
    yaxis=dict(
        range=[-100, 105],
        tickmode="linear",
        tick0=-100,
        dtick=50,
        ticksuffix="%",
        zeroline=False,
        showgrid=True,
        gridcolor="rgba(211, 211, 211, 0.5)",
        gridwidth=0.8
    ),
    legend=dict(
        x=0.02, 
        y=0.98,
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="lightgray",
        borderwidth=1
    ),
    plot_bgcolor="white",
    paper_bgcolor="white"
)

st.plotly_chart(fig, use_container_width=True)

# Stats section
col1, col2, col3 = st.columns(3)
col1.metric("Total Counties", len(filtered_df))
col2.metric("Republican Counties", len(filtered_df[filtered_df["party"] == "Republican"]))
col3.metric("Democrat Counties", len(filtered_df[filtered_df["party"] == "Democrat"]))

# Analysis tables
filtered_df["change"] = filtered_df["margin_2024"] - filtered_df["margin_2020"]

col1, col2 = st.columns(2)
with col1:
    st.subheader("🔴 Most Republican Shift")
    top_r = filtered_df.nlargest(5, "change")[["county", "state", "margin_2020", "margin_2024", "change"]]
    st.dataframe(top_r, hide_index=True, use_container_width=True)

with col2:
    st.subheader("🔵 Most Democrat Shift")
    top_d = filtered_df.nsmallest(5, "change")[["county", "state", "margin_2020", "margin_2024", "change"]]
    st.dataframe(top_d, hide_index=True, use_container_width=True)

# About
with st.expander("ℹ️ How to Read This Chart"):
    st.markdown("""
    **This visualization shows county-level election margins:**
    
    - **X-axis (2020 Margin)**: How each county voted in 2020
    - **Y-axis (2024 Margin)**: How each county voted in 2024
    - **Red dots**: Republican counties (positive margins both years)
    - **Blue dots**: Democrat counties (negative margins both years)
    
    **Key insights:**
    - Points **above** the diagonal line → County shifted MORE Republican in 2024
    - Points **below** the diagonal line → County shifted MORE Democrat in 2024
    - Points **on** the diagonal line → No change between elections
    
    *Using sample data for demonstration.*
    """)