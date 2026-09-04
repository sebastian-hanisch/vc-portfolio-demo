"""Defaults, Regler-Grenzen, Sektoren/Stages und Beispielszenarien."""

SECTORS = ["SaaS", "Fintech", "Biotech", "DeepTech", "Consumer", "Climate-Tech"]

STAGES = ["Pre-Seed", "Seed", "Series A"]
STAGE_WEIGHTS = [0.40, 0.35, 0.25]

# Stufenabhängige Verschiebung gegenüber den Basiswerten der Regler: frühere Phasen
# scheitern häufiger, dafür mit größerem Homerun-Multiple; spätere Phasen sind
# vorhersehbarer (siehe README/Expander "Wie funktioniert diese Demo?").
STAGE_MODIFIERS = {
    "Pre-Seed": dict(fail_delta=0.10, homerun_delta=0.015, homerun_mult_factor=1.5),
    "Seed": dict(fail_delta=0.0, homerun_delta=0.0, homerun_mult_factor=1.0),
    "Series A": dict(fail_delta=-0.15, homerun_delta=-0.015, homerun_mult_factor=0.6),
}

N_DEALS_DEFAULT = 30
N_DEALS_RANGE = (10, 60)

BUDGET_DEFAULT = 10.0  # Fondsvolumen, Mio. EUR
BUDGET_RANGE = (2.0, 50.0)

TICKET_MIN_DEFAULT = 0.2  # Mio. EUR
TICKET_MIN_RANGE = (0.05, 3.0)

TICKET_MAX_DEFAULT = 1.0  # Mio. EUR
TICKET_MAX_RANGE = (0.1, 5.0)

SECTOR_CAP_PCT_DEFAULT = 30.0  # % des Fondsvolumens je Sektor
SECTOR_CAP_PCT_RANGE = (10.0, 100.0)  # 100% = Diversifizierungs-Grenze wirkt faktisch nicht

P_FAIL_BASE_DEFAULT = 0.70
P_FAIL_BASE_RANGE = (0.40, 0.90)

P_HOMERUN_BASE_DEFAULT = 0.03
P_HOMERUN_BASE_RANGE = (0.005, 0.10)

MODERATE_MULTIPLE_DEFAULT = 2.5
MODERATE_MULTIPLE_RANGE = (1.2, 5.0)

HOMERUN_MULTIPLE_DEFAULT = 30.0
HOMERUN_MULTIPLE_RANGE = (5.0, 100.0)

RANDOM_SEED_DEFAULT = 7
RANDOM_SEED_RANGE = (0, 2_000_000_000)

EXACT_SOLVE_TIME_LIMIT_SECONDS = 4  # Multi-Constrained-Knapsack mit <=60 Binärvariablen
# ist für SCIP trivial - Zeitlimit greift praktisch nie, bleibt aber als Sicherheitsnetz
# und fuer die "Zeitlimit erreicht"-Meldungslogik konsistent mit den anderen Demos.

N_SIMULATIONS = 8000  # Monte-Carlo-Läufe für den Core-Theme-Risikovergleich

PRESETS = {
    "Ausgewogener Fonds": dict(
        n_deals=30, budget=10.0, ticket_min=0.2, ticket_max=1.0, sector_cap_pct=30.0,
        p_fail_base=0.70, p_homerun_base=0.03, moderate_multiple=2.5, homerun_multiple=30.0, seed=7,
    ),
    "Wenige, große Wetten": dict(
        n_deals=14, budget=10.0, ticket_min=1.0, ticket_max=2.5, sector_cap_pct=25.0,
        p_fail_base=0.70, p_homerun_base=0.03, moderate_multiple=2.5, homerun_multiple=30.0, seed=11,
    ),
    "Breiter Streuungsfonds": dict(
        n_deals=50, budget=10.0, ticket_min=0.1, ticket_max=0.3, sector_cap_pct=30.0,
        p_fail_base=0.70, p_homerun_base=0.03, moderate_multiple=2.5, homerun_multiple=30.0, seed=3,
    ),
    "Später-Phase-Fonds": dict(
        n_deals=25, budget=15.0, ticket_min=0.5, ticket_max=1.5, sector_cap_pct=35.0,
        p_fail_base=0.45, p_homerun_base=0.01, moderate_multiple=2.0, homerun_multiple=12.0, seed=21,
    ),
}
