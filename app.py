import streamlit as st

import vc_constants as C
from vc_evaluation import comparison_table, evaluate_selection
from vc_heuristics import (
    diversified_greedy_construction,
    ev_greedy_construction,
    sector_round_robin_construction,
    swap_polish,
)
from vc_pdf_export import generate_portfolio_pdf
from vc_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from vc_reference_solver import solve_exact
from vc_scenario import generate_deals
from vc_simulation import simulate_portfolio
from vc_ui_panel import render_vc_panel
from vc_visualization import build_sector_allocation_chart, build_simulation_histogram, build_value_comparison_chart

st.set_page_config(page_title="Startup-Portfolio – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _compute_heuristics(
    n_deals,
    budget,
    ticket_min,
    ticket_max,
    sector_cap_pct,
    p_fail_base,
    p_homerun_base,
    moderate_multiple,
    homerun_multiple,
    seed,
):
    deals = generate_deals(
        n_deals, seed, ticket_min, ticket_max, p_fail_base, p_homerun_base, moderate_multiple, homerun_multiple
    )
    sector_cap = budget * sector_cap_pct / 100.0

    sel_greedy = diversified_greedy_construction(deals, budget, sector_cap)
    sel_rotation = sector_round_robin_construction(deals, budget, sector_cap)

    eval_greedy = evaluate_selection(deals, sel_greedy, label="EV-Greedy (diversifiziert)")
    eval_rotation = evaluate_selection(deals, sel_rotation, label="Sektor-Rotation")

    polish_start = sel_greedy if eval_greedy["expected_value"] >= eval_rotation["expected_value"] else sel_rotation
    sel_polished = swap_polish(deals, polish_start, budget, sector_cap)
    eval_polished = evaluate_selection(deals, sel_polished, label="Greedy + Politur")

    results = [eval_greedy, eval_rotation, eval_polished]

    sel_ev_only = ev_greedy_construction(deals, budget)
    eval_ev_only = evaluate_selection(deals, sel_ev_only, label="Nur Erwartungswert (ohne Streuung)")

    return deals, results, eval_ev_only, sector_cap


@st.cache_data(show_spinner=False)
def _compute_exact(
    n_deals,
    budget,
    ticket_min,
    ticket_max,
    sector_cap_pct,
    p_fail_base,
    p_homerun_base,
    moderate_multiple,
    homerun_multiple,
    seed,
):
    """Getrennt von `_compute_heuristics`, damit der exakte Löser NICHT automatisch bei jeder
    Regler-Änderung mitläuft - läuft nur, wenn der Nutzer explizit den Button klickt (siehe
    unten)."""
    deals = generate_deals(
        n_deals, seed, ticket_min, ticket_max, p_fail_base, p_homerun_base, moderate_multiple, homerun_multiple
    )
    sector_cap = budget * sector_cap_pct / 100.0
    solve = solve_exact(deals, budget, sector_cap, time_limit_seconds=C.EXACT_SOLVE_TIME_LIMIT_SECONDS)
    if not solve.feasible:
        return None
    exact_label = "Exakt (OR-Tools)" if solve.optimal else "Exakt (OR-Tools, Zeitlimit)"
    exact_eval = evaluate_selection(deals, solve.selected_indices, label=exact_label)
    return {"eval": exact_eval, "optimal": solve.optimal, "wall_time_ms": solve.wall_time_ms}


st.title("🚀 Startup-Portfolio-Optimierung")
st.markdown(
    """
Ein VC-Fonds hat ein festes Budget und einen Dealflow aus Startups mit sehr unterschiedlichen
**Ausfall-, Erfolgs- und Homerun-Wahrscheinlichkeiten**. Welche Deals passen bei welcher
**Sektor-Diversifizierung** am besten ins Portfolio - und warum reicht reine
**Erwartungswert-Maximierung** bei so schiefen Power-Law-Renditen nicht aus? Wie das
deterministische Auswahlmodell und die ergänzende **Monte-Carlo-Simulation** im Detail
funktionieren, steht im Expander "Wie funktioniert diese Demo?" weiter unten, die formale
Herleitung im Expander "📐 Mathematische Formulierung".
"""
)

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = {
    "Ausgewogener Fonds": "Normale Ticketgrößen relativ zum Fondsvolumen - Diversifizierung hilft spürbar, "
    "aber nicht dramatisch.",
    "Wenige, große Wetten": "Große Tickets, kleiner Dealflow - ohne Sektor-Obergrenze konzentriert sich das "
    "Budget schnell in 1-2 Sektoren. Größter Unterschied zwischen EV-Greedy und diversifiziertem Portfolio.",
    "Breiter Streuungsfonds": "Viele kleine Tickets - selbst ohne Diversifizierungs-Grenze verteilt sich das "
    "Budget von selbst über viele Deals und Sektoren.",
    "Später-Phase-Fonds": "Series-A-lastig: geringere Ausfallwahrscheinlichkeit, kleinere Homeruns - deutlich "
    "weniger Power-Law-Charakter als ein Frühphasen-Fonds.",
}
preset_cols = st.columns(len(C.PRESETS))
for i, name in enumerate(C.PRESETS.keys()):
    with preset_cols[i]:
        st.button(name, use_container_width=True, on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_deals = st.slider("Anzahl Deals im Dealflow", *bounds("n_deals_slider"), key="n_deals_slider")
    budget = st.slider("Fondsvolumen (Mio. €)", *bounds("budget_slider"), key="budget_slider")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)

    st.markdown("**Ticketgröße & Diversifizierung**")
    ticket_min = st.slider("Ticketgröße, Minimum (Mio. €)", *bounds("ticket_min_slider"), key="ticket_min_slider")
    ticket_max = st.slider("Ticketgröße, Maximum (Mio. €)", *bounds("ticket_max_slider"), key="ticket_max_slider")
    sector_cap_pct = st.slider(
        "Sektor-Obergrenze (% des Fondsvolumens)", *bounds("sector_cap_pct_slider"), key="sector_cap_pct_slider"
    )

    st.markdown("**Return-Profil**")
    p_fail_base = st.slider(
        "Basis-Ausfallwahrscheinlichkeit", *bounds("p_fail_base_slider"), key="p_fail_base_slider"
    )
    p_homerun_base = st.slider(
        "Basis-Homerun-Wahrscheinlichkeit", *bounds("p_homerun_base_slider"), key="p_homerun_base_slider"
    )
    moderate_multiple = st.slider(
        "Multiple bei moderatem Erfolg", *bounds("moderate_multiple_slider"), key="moderate_multiple_slider"
    )
    homerun_multiple = st.slider(
        "Multiple bei Homerun", *bounds("homerun_multiple_slider"), key="homerun_multiple_slider"
    )

    st.button(
        "🎲 Neuen Dealflow generieren",
        use_container_width=True,
        on_click=randomize_seed,
        help="Würfelt einen neuen Zufalls-Seed für den Dealflow.",
    )

sync_query_params(
    n_deals, budget, ticket_min, ticket_max, sector_cap_pct, p_fail_base, p_homerun_base,
    moderate_multiple, homerun_multiple, seed,
)

scenario_key = (
    int(n_deals), budget, ticket_min, ticket_max, sector_cap_pct, p_fail_base, p_homerun_base,
    moderate_multiple, homerun_multiple, int(seed),
)

with st.spinner("Berechne Portfolio..."):
    deals, results, eval_ev_only, sector_cap = _compute_heuristics(*scenario_key)

best = max(results, key=lambda r: r["expected_value"])
baseline = min(results, key=lambda r: r["expected_value"])

if best["total_ticket"] <= 0:
    st.warning(
        "Bei dieser Budget-/Ticketgrößen-Kombination passt kein einziger Deal ins Budget. "
        "Budget erhöhen oder Ticketgröße reduzieren."
    )
    st.stop()

value_gain = best["expected_value"] - baseline["expected_value"]
pct_gain = (value_gain / baseline["expected_value"] * 100) if baseline["expected_value"] > 0 else 0.0

st.markdown("## 🎯 Ihr erwartungswert-optimiertes Startup-Portfolio")
st.caption(f"Methode: **{best['label']}** - wird bei jedem Lauf neu anhand des erwarteten Portfolio-Werts bestimmt.")

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Erwarteter Portfolio-Wert",
    f"{best['expected_value']:.2f} Mio. €",
    delta=f"+{value_gain:.2f} Mio. € ggü. {baseline['label']}",
    delta_color="normal",
)
m2.metric("Investiertes Kapital", f"{best['total_ticket']:.2f} / {budget:.1f} Mio. €")
m3.metric("Anzahl Deals", best["n_selected"])
m4.metric("Ø Multiple", f"{best['expected_multiple']:.2f}x")

if value_gain > 0.01:
    st.success(
        f"💰 **{best['label']}** erzielt hier einen um ca. **{value_gain:.2f} Mio. €** ({pct_gain:.1f}%) "
        f"höheren erwarteten Portfolio-Wert als '{baseline['label']}'."
    )

fig_best = build_sector_allocation_chart(best, sector_cap, title=best["label"])
st.plotly_chart(fig_best, use_container_width=True, key="primary_sector_chart")

pdf_bytes_best = generate_portfolio_pdf(best["label"], best)
st.download_button(
    "📄 Portfolio als PDF herunterladen",
    data=pdf_bytes_best,
    file_name="startup_portfolio_optimiert.pdf",
    mime="application/pdf",
    key="primary_pdf_download",
)

st.caption(
    "Ermittelt mit der besten von drei eigenen Optimierungsmethoden für dieses Szenario. "
    "Details zu allen Methoden und dem Vergleich mit Google OR-Tools unten."
)

st.markdown("---")

st.subheader("📐 Warum reicht Erwartungswert-Maximierung bei Startups nicht?")
st.markdown(
    """
Kernfrage dieser Demo: Startup-Renditen sind extrem **schief verteilt** (Power Law) - die meisten
Deals scheitern total, wenige liefern das 10- bis 100-fache. Ein Portfolio, das NUR den
Erwartungswert maximiert und Sektor-Konzentration ignoriert, kann trotzdem ein sehr ähnliches
erwartetes Ergebnis wie ein diversifiziertes Portfolio erzielen - aber mit einer ganz anderen
**Verlustwahrscheinlichkeit**. Das lässt sich nicht am Erwartungswert allein ablesen, sondern nur
über eine **Monte-Carlo-Simulation** der tatsächlichen Ausgänge - hier live für Ihre aktuelle
Konfiguration geprüft, nicht nur behauptet.
"""
)

sim_best = simulate_portfolio(deals, best["selected_indices"], C.N_SIMULATIONS, seed=int(seed) + 9973)
sim_ev_only = simulate_portfolio(deals, eval_ev_only["selected_indices"], C.N_SIMULATIONS, seed=int(seed) + 9973)

core_col1, core_col2, core_col3 = st.columns(3)
core_col1.metric(
    f"Ø Multiple (Simulation) – {best['label']}",
    f"{sim_best['mean_multiple']:.2f}x",
    delta=f"{sim_best['mean_multiple'] - sim_ev_only['mean_multiple']:.2f}x ggü. nur Erwartungswert",
    delta_color="off",
)
loss_delta = sim_best["p_loss"] - sim_ev_only["p_loss"]
core_col2.metric(
    f"Verlustwahrscheinlichkeit (Fonds < 1x) – {best['label']}",
    f"{sim_best['p_loss'] * 100:.1f}%",
    delta=f"{loss_delta * 100:.1f} Prozentpunkte ggü. nur Erwartungswert",
    delta_color="inverse",
)
core_col3.metric(
    f"5%-Schlechtfall-Multiple – {best['label']}",
    f"{sim_best['var5_multiple']:.2f}x",
    delta=f"{sim_best['var5_multiple'] - sim_ev_only['var5_multiple']:.2f}x ggü. nur Erwartungswert",
    delta_color="off",
)

st.caption(
    f"Vergleichsportfolio 'Nur Erwartungswert (ohne Streuung)': {eval_ev_only['expected_value']:.2f} Mio. € "
    f"erwarteter Wert, {sim_ev_only['p_loss'] * 100:.1f}% Verlustwahrscheinlichkeit, "
    f"{sim_ev_only['var5_multiple']:.2f}x 5%-Schlechtfall-Multiple ({C.N_SIMULATIONS:,} Simulationsläufe)."
)

ev_gap = eval_ev_only["expected_value"] - best["expected_value"]
if loss_delta < -0.01 and ev_gap < 0.25:
    st.success(
        f"✅ Bei ähnlichem erwarteten Wert (Differenz nur {ev_gap:.2f} Mio. €) senkt die Sektor-"
        f"Diversifizierung die Verlustwahrscheinlichkeit um **{-loss_delta * 100:.1f} Prozentpunkte** "
        f"({sim_ev_only['p_loss'] * 100:.1f}% → {sim_best['p_loss'] * 100:.1f}%) - Power-Law-Risiko wird "
        f"eingedämmt, ohne im Erwartungswert nennenswert zu verlieren."
    )
elif loss_delta < -0.01:
    st.info(
        f"📉 Diversifizierung senkt die Verlustwahrscheinlichkeit um **{-loss_delta * 100:.1f} Prozentpunkte**, "
        f"kostet dafür {ev_gap:.2f} Mio. € erwarteten Wert gegenüber der reinen EV-Maximierung."
    )
else:
    st.info(
        "Bei dieser Konfiguration unterscheiden sich Verlustwahrscheinlichkeit und Erwartungswert beider "
        "Portfolios kaum - die Sektor-Obergrenze greift hier faktisch kaum ein (z.B. weil die Tickets ohnehin "
        "klein gegenüber dem Fondsvolumen sind)."
    )

st.plotly_chart(
    build_simulation_histogram(sim_best["samples"], best["label"], sim_ev_only["samples"], eval_ev_only["label"]),
    use_container_width=True,
    key="core_theme_histogram",
)

st.markdown("---")

with st.expander("🔧 Wie wir das erreichen – vollständiger Methodenvergleich"):
    prefixes = ["greedy", "rotation", "polished"]
    tab_labels = [r["label"] for r in results] + ["🧮 Exakt (OR-Tools)", "📊 Vergleich"]
    tabs = st.tabs(tab_labels)

    for tab, r, prefix in zip(tabs[: len(results)], results, prefixes):
        with tab:
            render_vc_panel(prefix, r["label"], r, sector_cap)

    tab_exact, tab_compare = tabs[len(results)], tabs[len(results) + 1]

    exact_eval = None
    with tab_exact:
        st.caption(
            "Löst dasselbe gemischt-ganzzahlige Modell exakt statt mit unseren eigenen Verfahren - "
            f"dient als Cross-Check. Auf {C.EXACT_SOLVE_TIME_LIMIT_SECONDS}s begrenzt (bei dieser "
            "Problemgröße praktisch immer sofort bewiesen optimal)."
        )
        solve_clicked = st.button("🧮 Mit OR-Tools lösen", key="exact_solve_btn")
        if solve_clicked:
            st.session_state["exact_scenario_key"] = scenario_key

        if st.session_state.get("exact_scenario_key") == scenario_key:
            with st.spinner(f"Berechne exakte Lösung (OR-Tools, bis zu {C.EXACT_SOLVE_TIME_LIMIT_SECONDS}s)..."):
                exact_result = _compute_exact(*scenario_key)

            if exact_result is None:
                st.error(
                    "🚫 OR-Tools hat innerhalb des Zeitlimits keine gültige Lösung gefunden."
                )
            else:
                exact_eval = exact_result["eval"]
                gap = exact_eval["expected_value"] - best["expected_value"]
                gap_pct = (gap / exact_eval["expected_value"] * 100) if exact_eval["expected_value"] > 0 else 0.0

                if exact_result["optimal"]:
                    if gap < 0.01:
                        st.info(
                            f"✅ Optimal gelöst ({exact_result['wall_time_ms']:.0f} ms): "
                            f"**{best['label']}** erreicht bereits das Optimum "
                            f"({exact_eval['expected_value']:.2f} Mio. €)."
                        )
                    else:
                        st.info(
                            f"📐 Optimal gelöst ({exact_result['wall_time_ms']:.0f} ms): Optimum "
                            f"liegt bei {exact_eval['expected_value']:.2f} Mio. € - Lücke zur besten "
                            f"Heuristik: {gap:.2f} Mio. € ({gap_pct:.1f}%)."
                        )
                else:
                    if gap <= 0.01:
                        st.warning(
                            f"⏱️ Zeitlimit erreicht, kein Optimalitätsbeweis "
                            f"({exact_result['wall_time_ms']:.0f} ms): **{best['label']}** "
                            f"({best['expected_value']:.2f} Mio. €) erreicht oder übertrifft sogar "
                            f"die beste vom Solver gefundene Lösung "
                            f"({exact_eval['expected_value']:.2f} Mio. €)."
                        )
                    else:
                        st.warning(
                            f"⏱️ Zeitlimit erreicht, kein Optimalitätsbeweis "
                            f"({exact_result['wall_time_ms']:.0f} ms): beste bislang gefundene "
                            f"Lösung liegt bei {exact_eval['expected_value']:.2f} Mio. € - "
                            f"{gap:.2f} Mio. € ({gap_pct:.1f}%) über der besten Heuristik, aber "
                            "ohne Optimalitätsgarantie."
                        )
                render_vc_panel("exact", exact_eval["label"], exact_eval, sector_cap)
        elif "exact_scenario_key" in st.session_state:
            st.info(
                "ℹ️ Die zuletzt berechnete exakte Lösung bezog sich auf ein anderes Szenario - "
                "Einstellungen geändert? Erneut auf '🧮 Mit OR-Tools lösen' klicken."
            )
        else:
            st.info("Noch keine Lösung berechnet – auf den Button oben klicken.")

    with tab_compare:
        all_results = list(results) + ([exact_eval] if exact_eval is not None else [])
        st.dataframe(comparison_table(all_results), use_container_width=True, hide_index=True)
        st.plotly_chart(build_value_comparison_chart(all_results), use_container_width=True, key="value_comparison")

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        """
Ein VC-Fonds sieht in einer Runde $n$ Startup-Deals. Jeder Deal verlangt ein festes **Ticket**
(alles-oder-nichts, keine Teilinvestition) und gehört zu einem **Sektor** sowie einer **Phase**
(Pre-Seed / Seed / Series A). Frühere Phasen scheitern häufiger, liefern im Erfolgsfall aber
größere Multiples - genau der Effekt, der Startup-Renditen zu einer **Power-Law-Verteilung**
macht: die meisten Ausgänge sind Totalausfälle, wenige sind Homeruns mit dem 10- bis 100-fachen
Einsatz.

Das Fondsbudget ist begrenzt, zusätzlich gilt eine **Sektor-Obergrenze** (maximal X% des
Fondsvolumens je Sektor) - eine klassische Diversifizierungsregel. Gesucht ist die Deal-Auswahl,
die den **erwarteten Portfolio-Wert** maximiert, ohne diese Grenze zu verletzen.

Drei selbst gebaute Verfahren stehen zur Auswahl (im Expander "Wie wir das erreichen" alle
nebeneinander), zusätzlich eine **exakte Referenzlösung** (Google OR-Tools, gemischt-
ganzzahliges Programm):

- **EV-Greedy (diversifiziert)**: sortiert Deals nach erwartetem Multiple, nimmt jeden Deal, der
  noch ins Budget UND die Sektor-Obergrenze passt.
- **Sektor-Rotation**: rotiert über die Sektoren und nimmt je Runde den besten noch passenden
  Deal des jeweils aussichtsreichsten Sektors - streut von sich aus, unabhängig vom Greedy-Ranking.
- **Greedy + Politur**: startet bei der besseren der beiden obigen Lösungen, füllt freie
  Restkapazität auf und sucht anschließend paarweise Tauschzüge (ein Deal raus, ein besserer
  rein) - nachweislich nie schlechter als sein Startpunkt.

Zusätzlich wird **ohne** Sektor-Obergrenze ein rein erwartungswert-maximierendes Portfolio
("Nur Erwartungswert") berechnet - der Kontrastfall für den Abschnitt oben. Eine
**Monte-Carlo-Simulation** (viele zufällige Ausgänge je Deal, gemäß seiner eigenen Ausfall-/
Erfolgs-/Homerun-Wahrscheinlichkeiten) zeigt, wie sich die tatsächliche Ergebnisverteilung -
nicht nur ihr Mittelwert - zwischen diversifiziertem und undiversifiziertem Portfolio
unterscheidet.
        """
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        """
**Multi-Constrained 0/1-Knapsack** (mehrfach nebenbedingter Rucksack), NP-schwer (Kellerer,
Pferschy, Pisinger, *Knapsack Problems*, 2004).

Gegeben Deals $i \\in \\{1,\\dots,n\\}$ mit Ticketgröße $t_i$, erwartetem Multiple
$\\mu_i = p_i^{mod}\\, m_i^{mod} + p_i^{hr}\\, m_i^{hr}$ (Ausfallwahrscheinlichkeit $p_i^{fail}$
trägt mit Multiple 0 nichts bei), Sektor $s(i) \\in S$, Fondsvolumen $B$ und
Sektor-Obergrenzenanteil $\\kappa \\in (0,1]$.

Binäre Variable $x_i \\in \\{0,1\\}$: Deal $i$ wird ins Portfolio aufgenommen.

$$
\\max \\sum_{i=1}^n t_i\\, \\mu_i\\, x_i
$$

unter

$$
\\sum_{i=1}^n t_i\\, x_i \\;\\le\\; B, \\qquad
\\sum_{i:\\, s(i)=s} t_i\\, x_i \\;\\le\\; \\kappa B \\quad \\forall s \\in S.
$$

Gelöst mit Google OR-Tools (`pywraplp`, SCIP-Backend) in
[vc_reference_solver.py](vc_reference_solver.py), auf 4 Sekunden Rechenzeit begrenzt - bei
den hier relevanten Größenordnungen (<=60 Binärvariablen, wenige Sektor-Nebenbedingungen)
praktisch immer sofort bewiesen optimal.

**Stochastische Ergänzung** (Monte Carlo, [vc_simulation.py](vc_simulation.py)): je Deal $i$
und Simulationslauf $r$ wird ein Ausgang $o_{i,r} \\in \\{0,\\, m_i^{mod},\\, m_i^{hr}\\}$ gemäß
$(p_i^{fail}, p_i^{mod}, p_i^{hr})$ gezogen - unabhängig über Deals und Läufe. Das simulierte
Portfolio-Multiple je Lauf ist

$$
M_r = \\frac{\\sum_i t_i\\, x_i\\, o_{i,r}}{\\sum_i t_i\\, x_i}.
$$

Für viele Läufe konvergiert $\\mathbb{E}[M_r]$ gegen den analytischen Erwartungswert des
deterministischen Modells (Gesetz der großen Zahlen) - die Simulation liefert zusätzlich die
gesamte Verteilung, insbesondere die Verlustwahrscheinlichkeit $P(M_r < 1)$ und untere
Perzentile, die das deterministische Modell allein nicht sichtbar macht.
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
