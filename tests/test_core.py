import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vc_evaluation import evaluate_selection
from vc_heuristics import (
    diversified_greedy_construction,
    ev_greedy_construction,
    sector_round_robin_construction,
    swap_polish,
)
from vc_reference_solver import solve_exact
from vc_scenario import generate_deals
from vc_simulation import simulate_portfolio

DEFAULT_KWARGS = dict(
    ticket_min=0.2, ticket_max=1.0, p_fail_base=0.70, p_homerun_base=0.03,
    moderate_multiple=2.5, homerun_multiple=30.0,
)


def _deals(n=30, seed=7, **overrides):
    kwargs = dict(DEFAULT_KWARGS)
    kwargs.update(overrides)
    return generate_deals(n, seed, **kwargs)


def test_deal_probabilities_sum_to_one():
    deals = _deals()
    for d in deals:
        assert math.isclose(d.p_fail + d.p_moderate + d.p_homerun, 1.0, abs_tol=1e-9)
        assert 0.0 <= d.p_fail <= 1.0
        assert 0.0 <= d.p_moderate <= 1.0
        assert 0.0 <= d.p_homerun <= 1.0


def test_diversified_greedy_respects_budget_and_sector_cap():
    deals = _deals(n=40, seed=3)
    budget = 10.0
    sector_cap = 3.0
    selected = diversified_greedy_construction(deals, budget, sector_cap)
    result = evaluate_selection(deals, selected)
    assert result["total_ticket"] <= budget + 1e-6
    for sector, invested in result["sector_invested"].items():
        assert invested <= sector_cap + 1e-6


def test_sector_round_robin_respects_constraints():
    deals = _deals(n=40, seed=3)
    budget = 10.0
    sector_cap = 3.0
    selected = sector_round_robin_construction(deals, budget, sector_cap)
    result = evaluate_selection(deals, selected)
    assert result["total_ticket"] <= budget + 1e-6
    for sector, invested in result["sector_invested"].items():
        assert invested <= sector_cap + 1e-6


def test_swap_polish_never_worse_than_start():
    deals = _deals(n=40, seed=5)
    budget = 8.0
    sector_cap = 2.5
    start = diversified_greedy_construction(deals, budget, sector_cap)
    start_value = evaluate_selection(deals, start)["expected_value"]
    polished = swap_polish(deals, start, budget, sector_cap)
    polished_result = evaluate_selection(deals, polished)
    assert polished_result["expected_value"] >= start_value - 1e-9
    assert polished_result["total_ticket"] <= budget + 1e-6
    for sector, invested in polished_result["sector_invested"].items():
        assert invested <= sector_cap + 1e-6


def test_ev_greedy_ignores_sector_cap_but_respects_budget():
    deals = _deals(n=40, seed=5)
    budget = 8.0
    selected = ev_greedy_construction(deals, budget)
    result = evaluate_selection(deals, selected)
    assert result["total_ticket"] <= budget + 1e-6


def test_exact_solver_matches_or_beats_heuristics():
    deals = _deals(n=20, seed=11)
    budget = 6.0
    sector_cap = 1.5
    heuristic_selected = diversified_greedy_construction(deals, budget, sector_cap)
    heuristic_value = evaluate_selection(deals, heuristic_selected)["expected_value"]

    solve = solve_exact(deals, budget, sector_cap, time_limit_seconds=4)
    assert solve.feasible
    exact_value = evaluate_selection(deals, solve.selected_indices)["expected_value"]
    assert exact_value >= heuristic_value - 1e-6

    result = evaluate_selection(deals, solve.selected_indices)
    assert result["total_ticket"] <= budget + 1e-6
    for sector, invested in result["sector_invested"].items():
        assert invested <= sector_cap + 1e-6


def test_simulation_p_loss_bounded_and_matches_ev_direction():
    deals = _deals(n=25, seed=9)
    budget = 8.0
    sector_cap = 2.0
    selected = diversified_greedy_construction(deals, budget, sector_cap)
    sim = simulate_portfolio(deals, selected, n_sims=4000, seed=42)
    assert 0.0 <= sim["p_loss"] <= 1.0
    assert sim["mean_multiple"] >= 0.0

    analytic_multiple = evaluate_selection(deals, selected)["expected_multiple"]
    assert abs(sim["mean_multiple"] - analytic_multiple) < 0.5  # Monte-Carlo-Rauschen bei 4000 Läufen


def test_simulation_empty_selection_is_total_loss():
    deals = _deals(n=10, seed=1)
    sim = simulate_portfolio(deals, set(), n_sims=100, seed=1)
    assert sim["p_loss"] == 1.0
    assert sim["mean_multiple"] == 0.0
