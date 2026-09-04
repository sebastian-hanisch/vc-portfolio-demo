"""Plotly-Visualisierungen: Sektor-Allokation, Methodenvergleich, Simulationsverteilung."""

import plotly.graph_objects as go

import vc_constants as C

BAR_COLOR = "#4C78A8"
CAP_COLOR = "#E45756"


def build_sector_allocation_chart(result, sector_cap, title=""):
    invested = result["sector_invested"]
    sectors = C.SECTORS
    values = [invested.get(s, 0.0) for s in sectors]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=sectors, y=values, marker_color=BAR_COLOR, name="Investiert"))
    fig.add_trace(
        go.Scatter(
            x=sectors,
            y=[sector_cap] * len(sectors),
            mode="lines",
            line=dict(color=CAP_COLOR, dash="dash", width=2),
            name="Sektor-Obergrenze",
        )
    )
    fig.update_layout(
        title=title,
        yaxis_title="Investiert (Mio. €)",
        margin=dict(l=10, r=10, t=40, b=10),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    # fixedrange auf beiden Achsen: verhindert Pinch-Zoom/Drag-Pan im Chart,
    # damit auf Touch-Geräten stattdessen die Seite normal gescrollt wird
    # (Hover-Tooltips bleiben davon unberührt).
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def build_value_comparison_chart(results):
    labels = [r["label"] for r in results]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[r["expected_value"] for r in results], marker_color=BAR_COLOR))
    fig.update_layout(
        yaxis_title="Erwarteter Portfolio-Wert (Mio. €)",
        margin=dict(l=10, r=10, t=30, b=10),
        height=360,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def build_simulation_histogram(samples_best, label_best, samples_ev_only, label_ev_only):
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(x=samples_best, name=label_best, opacity=0.65, marker_color="#54A24B", nbinsx=60)
    )
    fig.add_trace(
        go.Histogram(x=samples_ev_only, name=label_ev_only, opacity=0.55, marker_color="#E45756", nbinsx=60)
    )
    fig.add_vline(x=1.0, line_dash="dash", line_color="gray", annotation_text="Kapitalerhalt (1x)")
    fig.update_layout(
        barmode="overlay",
        xaxis_title="Simuliertes Portfolio-Multiple",
        yaxis_title="Anzahl Simulationsläufe",
        margin=dict(l=10, r=10, t=30, b=10),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig
