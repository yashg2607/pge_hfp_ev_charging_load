import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="PG&E EV Charging Load Dashboard", layout="wide")
st.title("PG&E EV Charging Load Dashboard")

HOURS_IN_YEAR = 8760
N_PROFILES = 2500
CHARGING_POWER_KW = 10
PROFILE_DIR = "data/ev_charging_profile_database"

final_data = pd.read_csv("data/final_data.csv", dtype={"FeederID": str})
zipcodes = sorted(final_data["ZIP_CODE"].astype(str).unique())
adoption_options = [f"{i}%" for i in range(0, 101, 10)]

col1, col2, col3 = st.columns(3)
with col1:
    selected_zip = st.selectbox("Zipcode", zipcodes)
with col2:
    selected_adoption = st.selectbox("Managed Charging Adoption", adoption_options, index=6)
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    run_clicked = st.button("Run", use_container_width=True)

if run_clicked:
    smart_adoption = int(selected_adoption.replace("%", "")) / 100
    rows = final_data[final_data["ZIP_CODE"].astype(str) == selected_zip]
    total_ev = int(rows["ev_count"].sum())

    baseline_load = np.zeros(HOURS_IN_YEAR)
    hfp_load = np.zeros(HOURS_IN_YEAR)
    profile_cache = {}

    with st.spinner(f"Processing {total_ev} EVs across {len(rows)} feeder(s)..."):
        for _, row in rows.iterrows():
            fid = row["FeederID"]
            ev_count = int(row["ev_count"])
            ch_key = f"ch_{fid}"

            n_optimized = int(smart_adoption * ev_count)
            n_baseline_only = ev_count - n_optimized

            rng = np.random.default_rng(42)
            opt_indices = rng.choice(N_PROFILES, size=n_optimized, replace=True) if n_optimized > 0 else np.array([], dtype=int)
            base_indices = rng.choice(N_PROFILES, size=n_baseline_only, replace=True) if n_baseline_only > 0 else np.array([], dtype=int)

            all_indices = np.unique(np.concatenate([opt_indices, base_indices]))
            for idx in all_indices:
                if idx not in profile_cache:
                    with open(f"{PROFILE_DIR}/sample_{idx + 1}.json") as f:
                        profile_cache[idx] = json.load(f)

            for idx in opt_indices:
                for s in profile_cache[idx]:
                    baseline_load[s["ps"]:s["pe"] + 1] += np.array(s["ch_baseline"]) * CHARGING_POWER_KW
                    hfp_load[s["ps"]:s["pe"] + 1] += np.array(s[ch_key]) * CHARGING_POWER_KW

            for idx in base_indices:
                for s in profile_cache[idx]:
                    baseline_load[s["ps"]:s["pe"] + 1] += np.array(s["ch_baseline"]) * CHARGING_POWER_KW
                    hfp_load[s["ps"]:s["pe"] + 1] += np.array(s["ch_baseline"]) * CHARGING_POWER_KW

    timestamps = pd.date_range("2025-01-01", periods=HOURS_IN_YEAR, freq="h")
    adoption_label = f"{int(smart_adoption * 100)}% Managed Charging Adoption under HFP"
    hour_labels = ["12 AM"] + [f"{h} AM" for h in range(1, 12)] + ["12 PM"] + [f"{h} PM" for h in range(1, 12)]

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=timestamps, y=baseline_load, mode="lines", name="Baseline", line=dict(width=0.5, color="#A0AEC0")))
    fig1.add_trace(go.Scatter(x=timestamps, y=hfp_load, mode="lines", name=adoption_label, line=dict(width=0.5, color="#FF9F1C")))
    fig1.update_layout(
        title=dict(text=f"EV Charging Load Profile — ZIP {selected_zip}", font=dict(size=28)),
        xaxis=dict(title="Time", title_font_size=24, tickfont_size=20),
        yaxis=dict(title="Power (kW)", title_font_size=24, tickfont_size=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=20)),
        height=500
    )
    st.plotly_chart(fig1, use_container_width=True)

    baseline_by_hour = baseline_load.reshape(365, 24)
    hfp_by_hour = hfp_load.reshape(365, 24)
    baseline_peak = baseline_by_hour.max(axis=0)
    hfp_peak = hfp_by_hour.max(axis=0)
    pct_change = np.where(baseline_peak > 0, (hfp_peak - baseline_peak) / baseline_peak * 100, 0)
    colors = ["#2ecc71" if p <= 0 else "#e74c3c" for p in pct_change]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=hour_labels, y=pct_change, marker_color=colors, text=[f"{p:+.1f}%" for p in pct_change], textposition="outside", textfont_size=18))
    fig2.update_layout(
        title=dict(text=f"Change in Annual Peak Demand (HFP vs Baseline) — ZIP {selected_zip}", font=dict(size=28)),
        xaxis=dict(title="Hour of Day", title_font_size=24, tickfont_size=20, tickangle=0),
        yaxis=dict(title="% Change", title_font_size=24, tickfont_size=20, zeroline=True, zerolinewidth=2, zerolinecolor="black"),
        height=500
    )
    st.plotly_chart(fig2, use_container_width=True)

    baseline_daily = baseline_load.reshape(365, 24).mean(axis=0)
    hfp_daily = hfp_load.reshape(365, 24).mean(axis=0)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=hour_labels, y=baseline_daily, mode="lines", name="Baseline", line=dict(width=2, color="#A0AEC0"), line_shape="spline"))
    fig3.add_trace(go.Scatter(x=hour_labels, y=hfp_daily, mode="lines", name=adoption_label, line=dict(width=2, color="#FF9F1C"), line_shape="spline"))
    fig3.update_layout(
        title=dict(text=f"Annual Average Daily Load Profile — ZIP {selected_zip}", font=dict(size=28)),
        xaxis=dict(title="Hour of Day", title_font_size=24, tickfont_size=20, tickangle=0),
        yaxis=dict(title="Power (kW)", title_font_size=24, tickfont_size=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=20)),
        height=500
    )
    st.plotly_chart(fig3, use_container_width=True)
