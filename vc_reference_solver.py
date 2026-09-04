"""Exakter Referenzlöser (gemischt-ganzzahliges Programm, OR-Tools SCIP).

Multi-Constrained 0/1-Knapsack: binäre Auswahl je Deal, Budget- und je-Sektor-
Nebenbedingung. Für die hier relevanten Größenordnungen (<=60 Deals) für SCIP
trivial - dient als Cross-Check-Referenz für die Heuristiken in vc_heuristics.py.
"""

from collections import defaultdict, namedtuple

from ortools.linear_solver import pywraplp

SolveResult = namedtuple("SolveResult", ["feasible", "optimal", "selected_indices", "objective", "wall_time_ms"])


def solve_exact(deals, budget, sector_cap, time_limit_seconds=4):
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("SCIP-Solver nicht verfügbar")
    solver.SetTimeLimit(int(time_limit_seconds * 1000))

    x = {d.index: solver.BoolVar(f"x_{d.index}") for d in deals}

    solver.Add(solver.Sum(x[d.index] * d.ticket for d in deals) <= budget)

    by_sector = defaultdict(list)
    for d in deals:
        by_sector[d.sector].append(d)
    for sector, sector_deals in by_sector.items():
        solver.Add(solver.Sum(x[d.index] * d.ticket for d in sector_deals) <= sector_cap)

    solver.Maximize(solver.Sum(x[d.index] * d.expected_value for d in deals))
    status = solver.Solve()

    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return SolveResult(
            feasible=False, optimal=False, selected_indices=None, objective=None, wall_time_ms=solver.wall_time()
        )

    selected_indices = {d.index for d in deals if x[d.index].solution_value() > 0.5}

    return SolveResult(
        feasible=True,
        optimal=(status == pywraplp.Solver.OPTIMAL),
        selected_indices=selected_indices,
        objective=solver.Objective().Value(),
        wall_time_ms=solver.wall_time(),
    )
