"""Wiederverwendbares Panel zur Darstellung einer Methode im Methodenvergleich."""

import pandas as pd
import streamlit as st

from vc_pdf_export import generate_portfolio_pdf
from vc_visualization import build_sector_allocation_chart


def render_vc_panel(prefix, label, result, sector_cap):
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Erwarteter Portfolio-Wert", f"{result['expected_value']:.2f} Mio. €")
    m2.metric("Investiertes Kapital", f"{result['total_ticket']:.2f} Mio. €")
    m3.metric("Anzahl Deals", result["n_selected"])
    m4.metric("Ø Multiple", f"{result['expected_multiple']:.2f}x")

    fig = build_sector_allocation_chart(result, sector_cap, title=label)
    st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_sector_chart")

    deals_df = pd.DataFrame(
        [
            {
                "Deal": d.name,
                "Sektor": d.sector,
                "Phase": d.stage,
                "Ticket (Mio. €)": round(d.ticket, 2),
                "Erw. Multiple": round(d.expected_multiple, 2),
            }
            for d in sorted(result["selected_deals"], key=lambda d: d.expected_value, reverse=True)
        ]
    )
    st.dataframe(deals_df, use_container_width=True, hide_index=True)

    pdf_bytes = generate_portfolio_pdf(label, result)
    st.download_button(
        "📄 Portfolio als PDF herunterladen",
        data=pdf_bytes,
        file_name=f"startup_portfolio_{prefix}.pdf",
        mime="application/pdf",
        key=f"{prefix}_pdf_download",
    )

    return result
