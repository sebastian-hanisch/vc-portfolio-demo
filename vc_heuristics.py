"""Heuristiken für das diversifizierte Portfolio-Auswahlproblem (0/1-Knapsack mit
Sektor-Nebenbedingungen).

- ev_greedy_construction: reines Erwartungswert-Greedy, NUR budgetbeschränkt - ignoriert
  Sektor-Konzentration bewusst (dient als Kontrastfall im Core-Theme-Abschnitt, "was, wenn
  wir Diversifizierung ignorieren?").
- diversified_greedy_construction: dieselbe Greedy-Reihenfolge, respektiert zusätzlich die
  Sektor-Obergrenze - überspringt Deals, die die Grenze verletzen würden, statt abzubrechen.
- sector_round_robin_construction: rotiert über die Sektoren (bester verbleibender Deal je
  Sektor und Runde) - eine strukturell andere Konstruktion, die von sich aus streut.
- swap_polish: lokale Verbesserungssuche (freie Restkapazität auffüllen + paarweise Tausch-
  züge) auf einer gegebenen Auswahl - kann eine Lösung nur verbessern, nie verschlechtern.
"""


def _fits(ticket, sector, remaining_budget, sector_invested, sector_cap):
    if ticket > remaining_budget + 1e-9:
        return False
    if sector_invested.get(sector, 0.0) + ticket > sector_cap + 1e-9:
        return False
    return True


def ev_greedy_construction(deals, budget):
    order = sorted(deals, key=lambda d: d.expected_multiple, reverse=True)
    selected = set()
    remaining = budget
    for d in order:
        if d.ticket <= remaining + 1e-9:
            selected.add(d.index)
            remaining -= d.ticket
    return selected


def diversified_greedy_construction(deals, budget, sector_cap):
    order = sorted(deals, key=lambda d: d.expected_multiple, reverse=True)
    selected = set()
    remaining = budget
    sector_invested = {}
    for d in order:
        if _fits(d.ticket, d.sector, remaining, sector_invested, sector_cap):
            selected.add(d.index)
            remaining -= d.ticket
            sector_invested[d.sector] = sector_invested.get(d.sector, 0.0) + d.ticket
    return selected


def sector_round_robin_construction(deals, budget, sector_cap):
    by_sector = {}
    for d in deals:
        by_sector.setdefault(d.sector, []).append(d)
    for sector in by_sector:
        by_sector[sector].sort(key=lambda d: d.expected_multiple, reverse=True)
    cursor = {sector: 0 for sector in by_sector}

    selected = set()
    remaining = budget
    sector_invested = {}

    progressed = True
    while progressed:
        progressed = False
        sector_order = sorted(
            by_sector.keys(),
            key=lambda s: (by_sector[s][cursor[s]].expected_multiple if cursor[s] < len(by_sector[s]) else -1),
            reverse=True,
        )
        for sector in sector_order:
            deals_in_sector = by_sector[sector]
            while cursor[sector] < len(deals_in_sector):
                candidate = deals_in_sector[cursor[sector]]
                cursor[sector] += 1
                if _fits(candidate.ticket, sector, remaining, sector_invested, sector_cap):
                    selected.add(candidate.index)
                    remaining -= candidate.ticket
                    sector_invested[sector] = sector_invested.get(sector, 0.0) + candidate.ticket
                    progressed = True
                    break
    return selected


def _selection_state(deals_by_index, selected):
    remaining_ticket = sum(deals_by_index[i].ticket for i in selected)
    sector_invested = {}
    for i in selected:
        d = deals_by_index[i]
        sector_invested[d.sector] = sector_invested.get(d.sector, 0.0) + d.ticket
    return remaining_ticket, sector_invested


def swap_polish(deals, selected, budget, sector_cap, max_rounds=5):
    deals_by_index = {d.index: d for d in deals}
    selected = set(selected)
    invested, sector_invested = _selection_state(deals_by_index, selected)
    remaining = budget - invested

    # Freie Restkapazität zunächst gierig mit noch nicht ausgewählten Deals auffüllen.
    excluded = sorted(
        (d for d in deals if d.index not in selected), key=lambda d: d.expected_multiple, reverse=True
    )
    changed = True
    while changed:
        changed = False
        for d in excluded:
            if d.index in selected:
                continue
            if _fits(d.ticket, d.sector, remaining, sector_invested, sector_cap):
                selected.add(d.index)
                remaining -= d.ticket
                sector_invested[d.sector] = sector_invested.get(d.sector, 0.0) + d.ticket
                changed = True

    # Paarweise Tauschzüge: ein ausgewählter Deal raus, ein nicht ausgewählter rein.
    for _ in range(max_rounds):
        improved = False
        for out_idx in list(selected):
            out_deal = deals_by_index[out_idx]
            for in_deal in deals:
                if in_deal.index in selected:
                    continue
                if in_deal.expected_value <= out_deal.expected_value + 1e-9:
                    continue
                trial_remaining = remaining + out_deal.ticket - in_deal.ticket
                trial_sector_invested = dict(sector_invested)
                trial_sector_invested[out_deal.sector] = trial_sector_invested.get(out_deal.sector, 0.0) - out_deal.ticket
                if not _fits(in_deal.ticket, in_deal.sector, trial_remaining, trial_sector_invested, sector_cap):
                    continue
                selected.discard(out_idx)
                selected.add(in_deal.index)
                remaining = trial_remaining
                sector_invested = trial_sector_invested
                sector_invested[in_deal.sector] = sector_invested.get(in_deal.sector, 0.0) + in_deal.ticket
                improved = True
                break
        if not improved:
            break
    return selected
