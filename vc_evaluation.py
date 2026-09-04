"""Auswertung einer Deal-Auswahl (Menge ausgewählter Deal-Indizes)."""

from collections import defaultdict


def evaluate_selection(deals, selected_indices, label=""):
    selected_indices = set(selected_indices)
    selected = [d for d in deals if d.index in selected_indices]

    total_ticket = sum(d.ticket for d in selected)
    expected_value = sum(d.expected_value for d in selected)
    expected_multiple = (expected_value / total_ticket) if total_ticket > 0 else 0.0

    sector_invested = defaultdict(float)
    for d in selected:
        sector_invested[d.sector] += d.ticket

    return {
        "label": label,
        "selected_indices": selected_indices,
        "selected_deals": selected,
        "total_ticket": total_ticket,
        "expected_value": expected_value,
        "expected_multiple": expected_multiple,
        "n_selected": len(selected),
        "sector_invested": dict(sector_invested),
    }


def comparison_table(results):
    import pandas as pd

    rows = []
    for r in results:
        rows.append(
            {
                "Methode": r["label"],
                "Erwarteter Wert (Mio. €)": round(r["expected_value"], 2),
                "Investiert (Mio. €)": round(r["total_ticket"], 2),
                "Anzahl Deals": r["n_selected"],
                "Ø Multiple": round(r["expected_multiple"], 2),
                "Sektoren belegt": len(r["sector_invested"]),
            }
        )
    return pd.DataFrame(rows)
