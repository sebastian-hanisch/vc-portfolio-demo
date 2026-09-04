# Startup-Portfolio-Optimierung

Interaktive Demo zur Portfoliokonstruktion für einen VC-Fonds: aus einem Dealflow von
Startups mit stark schief verteilten (Power-Law) Renditen wird die Deal-Auswahl gesucht,
die den erwarteten Portfolio-Wert maximiert, ohne sich in einzelnen Sektoren zu
konzentrieren. Kombiniert ein **deterministisches** Auswahlmodell (0/1-Knapsack mit
Sektor-Nebenbedingungen) mit einer **stochastischen** Monte-Carlo-Simulation der
tatsächlich realisierten Ausgänge, um zu zeigen, warum reine
Erwartungswert-Maximierung bei Power-Law-Renditen zu unterschätztem Verlustrisiko führt.

## Das Modell

Jeder Deal $i$ verlangt ein festes Ticket $t_i$ (alles-oder-nichts) und gehört zu einem
Sektor und einer Finanzierungsphase (Pre-Seed / Seed / Series A). Er zieht einen von drei
Ausgängen: Totalausfall (Multiple 0), moderater Erfolg oder Homerun (10-100x) - mit
phasenabhängigen Wahrscheinlichkeiten. Gesucht ist die Auswahl $x_i \in \{0,1\}$, die

$$\max \sum_i t_i \mu_i x_i \quad \text{unter} \quad \sum_i t_i x_i \le B, \quad \sum_{i: s(i)=s} t_i x_i \le \kappa B \ \forall s$$

maximiert ($\mu_i$ = erwartetes Multiple je Deal, $B$ = Fondsvolumen, $\kappa$ =
Sektor-Obergrenzenanteil). Details und Herleitung im Expander "📐 Mathematische
Formulierung" der App.

Vier Verfahren stehen nebeneinander:

- **EV-Greedy (diversifiziert)** - Greedy nach erwartetem Multiple, respektiert Budget
  und Sektor-Obergrenze.
- **Sektor-Rotation** - rotiert über Sektoren, streut strukturell anders als Greedy.
- **Greedy + Politur** - startet bei der besseren der beiden obigen Lösungen, füllt
  Restkapazität auf und sucht paarweise Tauschzüge.
- **Exakt (OR-Tools)** - gemischt-ganzzahliges Referenzmodell (SCIP), beweist die
  Optimalität für kleine bis mittlere Dealflows praktisch immer innerhalb des
  4-Sekunden-Zeitlimits. Läuft bewusst nur auf Klick (Button "🎯 Exakte Lösung berechnen" in
  der Seitenleiste), nicht automatisch bei jeder Regler-Änderung - dient nur als Cross-Check,
  nicht für das primäre (immer schnelle) Heuristik-Ergebnis.

Zusätzlich wird ein **undiversifiziertes** Vergleichsportfolio (reine
EV-Maximierung, keine Sektor-Obergrenze) berechnet und beiden Portfolios eine
Monte-Carlo-Simulation (8.000 Läufe) der tatsächlichen Ergebnisverteilung gegenübergestellt
- der Kernvergleich der Demo (Abschnitt "📐 Warum reicht Erwartungswert-Maximierung bei
Startups nicht?").

## Setup & Ausführung

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements-dev.txt
streamlit run app.py
```

Die App läuft in diesem Portfolio üblicherweise unter `--server.port 8516`, siehe
`../.claude/launch.json`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Deckt die zentralen Invarianten ab: Wahrscheinlichkeiten je Deal summieren sich zu 1,
alle Heuristiken respektieren Budget- und Sektor-Nebenbedingung, `swap_polish` wird nie
schlechter als sein Startpunkt, der exakte Solver erreicht mindestens den Wert der besten
Heuristik, und die Monte-Carlo-Verlustwahrscheinlichkeit liegt in [0, 1] und ihr
Mittelwert konvergiert (im Rahmen des Simulationsrauschens) gegen den analytischen
Erwartungswert.

## Projektstruktur

- `app.py` - Streamlit-Oberfläche.
- `vc_scenario.py` - Zufällige Erzeugung des Dealflows.
- `vc_heuristics.py` - Die drei Konstruktionsheuristiken + Politur.
- `vc_reference_solver.py` - Exakter MILP-Löser (OR-Tools).
- `vc_simulation.py` - Monte-Carlo-Simulation der Ergebnisverteilung.
- `vc_evaluation.py`, `vc_visualization.py`, `vc_pdf_export.py`, `vc_ui_panel.py`,
  `vc_presets.py`, `vc_constants.py` - Auswertung, Charts, PDF-Export, UI-Bausteine,
  Presets/Permalink, Konstanten.
- `tests/` - pytest-Suite.
