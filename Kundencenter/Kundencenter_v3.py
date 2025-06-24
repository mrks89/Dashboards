import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .main {background-color: #222228;}
        .block-container {padding-top: 1.5rem;}
        .dashboard-section {
            border: 2px solid #ffe066;
            border-radius: 24px;
            padding: 18px 24px 24px 24px;
            margin-bottom: 24px;
            background: #18181c;
        }
        .yellow-text {color: #ffe066;}
        .white-text {color: #fff;}
        .gray-text {color: #bbb;}
        .big {font-size: 2.2rem; font-weight: 700;}
        .medium {font-size: 1.2rem;}
        .small {font-size: 0.9rem;}
        .center {text-align: center;}
        .flex-row {display: flex; flex-direction: row; align-items: center;}
        .flex-col {display: flex; flex-direction: column;}
        .gap-1 {gap: 1rem;}
        .gap-2 {gap: 2rem;}
        .box {background: #222228; border-radius: 12px; padding: 12px 18px; margin-bottom: 10px;}
        /* Removed .box-yellow, .box-red, .box-green borders */
        .box-red {background: #222228;}
        .box-green {background: #222228;}
        .box-yellow {background: #222228;}
        .box-icon {font-size: 1.5rem; margin-right: 10px;}
        .bar-label {font-size: 1.1rem; font-weight: 600;}
    </style>
""", unsafe_allow_html=True)

# --- Dummy Data ---
kc_names = ["Kundencenter 1", "Kundencenter 2", "Kundencenter 3", "Kundencenter 4", "Kundencenter 5", "Kundencenter 6"]
kc_bars = [20.2, 25.2, 30.5, 15.0, 18.0, 10.5]
kc_bars_sorted = sorted(zip(kc_names, kc_bars), key=lambda x: -x[1])
kc_bars_labels = [x[0] for x in kc_bars_sorted]
kc_bars_values = [x[1] for x in kc_bars_sorted]

# --- Main Layout ---
with st.container():
    # Remove the yellow border by removing the dashboard-section class from the container div
    # st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
    # Top: Title
    st.markdown(
        '<span class="yellow-text big">Gesamtübersicht Kundencenter Burgenland Energie</span> '
        '<span class="gray-text" style="font-size:1.2rem;">(KW12) 18.03.2024 - 15.03.2024</span>',
        unsafe_allow_html=True
    )
    st.markdown('<br>', unsafe_allow_html=True)

    # Top Row: 3 columns
    col1, col2, col3 = st.columns([2.5, 2, 2.5])

    # --- Left Column ---
    with col1:
        st.markdown('<div class="box flex-row gap-1"><span class="box-icon yellow-text">⚡</span><div><b>Gesamtverbrauch über gewählten Zeitraum</b><br><span class="yellow-text" style="font-size:1.5rem;">960</span> <span class="gray-text">kWh</span></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="box flex-row gap-1"><span class="box-icon yellow-text">📅</span><div><b>Täglicher Durchschnitt</b><br><span class="yellow-text" style="font-size:1.5rem;">10,82</span> <span class="gray-text">kWh</span></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="box box-red flex-row gap-1"><span class="box-icon yellow-text">📈</span><div><b>Höchster Verbrauch</b><br><span class="white-text">KC 3</span> <span class="yellow-text" style="font-size:1.2rem;">30,5</span> <span class="gray-text">kWh</span></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="box box-green flex-row gap-1"><span class="box-icon yellow-text">📉</span><div><b>Niedrigster Verbrauch</b><br><span class="white-text">KC 6</span> <span class="yellow-text" style="font-size:1.2rem;">10,5</span> <span class="gray-text">kWh</span></div></div>', unsafe_allow_html=True)

    # --- Middle Column (Gauge) ---
    with col2:
        st.markdown(
            '<div class="center">'
            '<span class="yellow-text medium" style="margin-right:20px;">● Live</span>'
            '<span class="white-text medium" style="font-size:1.2rem;">Gesamtverbrauch</span>'
            '</div>',
            unsafe_allow_html=True
        )
        # Plotly Gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=72,
            number={
                'font': {'color': '#ffe066', 'size': 36},
                'suffix': ' kWh',  # Add unit
            },
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': '#ffe066', 'tickwidth': 2, 'ticklen': 8, 'tickfont': {'color': '#ffe066'}},
                'bar': {'color': '#ffe066', 'thickness': 0.3},
                'bgcolor': "#222228",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 100], 'color': "#222228"}
                ],
                'threshold': {
                    'line': {'color': "#ffe066", 'width': 4},
                    'thickness': 0.75,
                    'value': 72
                }
            },
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        # Set gauge height to match the left fields (approx. 340px)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=340, paper_bgcolor="#222228")
        st.plotly_chart(fig, use_container_width=True)

    # --- Right Column ---
    with col3:
        st.markdown(
            '<div class="center">'
            '<span class="white-text medium" style="font-size:1.2rem;">Differenz Vorwoche</span>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="box box-red" style="height:340px; display:flex; flex-direction:column; justify-content:center; align-items:center;">'
            '<span class="gray-text" style="font-size:1rem; text-align:center;">(KW11) 11.03.2024 - 17.03.2024</span><br>'
            '<span class="yellow-text" style="font-size:1.5rem; text-align:center;">+24,35%</span><br>'
            '<span class="gray-text" style="text-align:center;">+120,82 kWh</span>'
            '</div>',
            unsafe_allow_html=True
        )

# --- Add space between upper and lower dashboard areas ---
st.markdown('<div style="height: 48px;"></div>', unsafe_allow_html=True)

# --- Second Row ---
with st.container():
    # Remove the yellow border by removing the dashboard-section class from the container div
    # st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 2])

    # --- Left: Bar Chart ---
    with col1:
        st.markdown(
            '<span class="yellow-text medium" style="margin-right:20px;">● Live</span>'
            '<span class="white-text medium">Kundencenter Verbrauchsübersicht</span>',
            unsafe_allow_html=True
        )
        # Bar chart
        fig = go.Figure(go.Bar(
            y=kc_bars_labels,
            x=kc_bars_values,
            orientation='h',
            marker_color=['#ffe066' if i == 1 else '#e0e0e0' for i in range(6)],
            text=[f"{v:.1f} kWh" for v in kc_bars_values],
            textposition='outside'
        ))
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#fff', size=16)),
            plot_bgcolor='#222228',
            paper_bgcolor='#222228',
            margin=dict(l=0, r=0, t=10, b=0),
            height=320  # Match the height of the indicators to the right
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Right: Detailbericht ---
    with col2:
        st.markdown(
            '<span class="white-text medium"><span class="box-icon yellow-text">🔄</span>Kundencenter 2 Detailbericht</span>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="box flex-row gap-1">'
            '<span class="box-icon yellow-text">⚡</span>'
            '<div><b>Gesamtverbrauch über gewählten Zeitraum</b><br>'
            '<span class="yellow-text" style="font-size:1.5rem;">960</span> <span class="gray-text">kWh</span></div>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="box flex-row gap-1">'
            '<span class="box-icon yellow-text">📅</span>'
            '<div><b>Täglicher Durchschnitt</b><br>'
            '<span class="yellow-text" style="font-size:1.5rem;">10,82</span> <span class="gray-text">kWh</span></div>'
            '</div>',
            unsafe_allow_html=True
        )
        # Maximalverbrauch & Minimalverbrauch side by side
        st.markdown(
            '<div style="display:flex; gap:10px; margin-bottom:10px;">'
            '<div class="box box-red flex-row gap-1" style="flex:1;">'
            '<span class="box-icon yellow-text">📈</span>'
            '<div><b>Maximalverbrauch</b><br>'
            '<span class="white-text">19. Mar 2024</span><br>'
            '<span class="yellow-text" style="font-size:1.2rem;">10,82</span> <span class="gray-text">kWh</span>'
            '</div></div>'
            '<div class="box box-green flex-row gap-1" style="flex:1;">'
            '<span class="box-icon yellow-text">📉</span>'
            '<div><b>Minimalverbrauch</b><br>'
            '<span class="white-text">23. Mar 2024</span><br>'
            '<span class="yellow-text" style="font-size:1.2rem;">1,12</span> <span class="gray-text">kWh</span>'
            '</div></div>'
            '</div>',
            unsafe_allow_html=True
        )
    # st.markdown('</div>', unsafe_allow_html=True)