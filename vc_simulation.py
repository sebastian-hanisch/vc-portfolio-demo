"""Monte-Carlo-Simulation des realisierten Portfolio-Multiples.

Jeder Deal zieht unabhängig einen von drei Ausgängen (Ausfall / moderater Erfolg /
Homerun) gemäß seiner eigenen Wahrscheinlichkeiten - genau die Verteilung, die das
deterministische Modell nur über ihren Erwartungswert kennt. Für viele Wiederholungen
konvergiert der simulierte Mittelwert gegen genau diesen Erwartungswert (Gesetz der
großen Zahlen) - guter Cross-Check zwischen den beiden Modellsichten.
"""

import numpy as np


def simulate_portfolio(deals, selected_indices, n_sims, seed):
    selected = [d for d in deals if d.index in selected_indices]
    total_ticket = sum(d.ticket for d in selected)

    if not selected or total_ticket <= 0:
        zeros = np.zeros(n_sims)
        return {
            "samples": zeros,
            "mean_multiple": 0.0,
            "median_multiple": 0.0,
            "p_loss": 1.0,
            "var5_multiple": 0.0,
            "total_ticket": 0.0,
        }

    rng = np.random.default_rng(seed)
    total_value = np.zeros(n_sims)
    for d in selected:
        outcomes = np.array([0.0, d.moderate_multiple, d.homerun_multiple])
        probs = np.array([d.p_fail, d.p_moderate, d.p_homerun])
        probs = probs / probs.sum()  # Rundungsfehler aus der Szenario-Erzeugung abfangen
        draws = rng.choice(outcomes, size=n_sims, p=probs)
        total_value += draws * d.ticket

    samples = total_value / total_ticket

    return {
        "samples": samples,
        "mean_multiple": float(samples.mean()),
        "median_multiple": float(np.median(samples)),
        "p_loss": float((samples < 1.0).mean()),
        "var5_multiple": float(np.percentile(samples, 5)),
        "total_ticket": total_ticket,
    }
