"""Zufällige Erzeugung des Dealflows: N Startup-Deals mit Sektor, Phase, Ticketgröße
und einer dreistufigen Return-Verteilung (Ausfall / moderater Erfolg / Homerun)."""

from dataclasses import dataclass

import numpy as np

import vc_constants as C


@dataclass(frozen=True)
class Deal:
    index: int
    name: str
    sector: str
    stage: str
    ticket: float  # Mio. EUR, benötigte Investitionssumme (alles-oder-nichts)
    p_fail: float
    p_moderate: float
    p_homerun: float
    moderate_multiple: float
    homerun_multiple: float

    @property
    def expected_multiple(self) -> float:
        return self.p_moderate * self.moderate_multiple + self.p_homerun * self.homerun_multiple

    @property
    def expected_value(self) -> float:
        return self.ticket * self.expected_multiple


def generate_deals(
    n_deals,
    seed,
    ticket_min,
    ticket_max,
    p_fail_base,
    p_homerun_base,
    moderate_multiple,
    homerun_multiple,
):
    rng = np.random.default_rng(seed)
    ticket_lo, ticket_hi = min(ticket_min, ticket_max), max(ticket_min, ticket_max)

    deals = []
    for i in range(n_deals):
        sector = C.SECTORS[rng.integers(0, len(C.SECTORS))]
        stage = rng.choice(C.STAGES, p=C.STAGE_WEIGHTS)
        mod = C.STAGE_MODIFIERS[stage]

        ticket = float(rng.uniform(ticket_lo, ticket_hi))

        fail_jitter = rng.normal(0.0, 0.04)
        homerun_jitter = rng.normal(0.0, 0.006)
        p_fail = float(np.clip(p_fail_base + mod["fail_delta"] + fail_jitter, 0.05, 0.95))
        p_homerun = float(np.clip(p_homerun_base + mod["homerun_delta"] + homerun_jitter, 0.001, 0.30))
        if p_fail + p_homerun > 0.97:
            scale = 0.97 / (p_fail + p_homerun)
            p_fail *= scale
            p_homerun *= scale
        p_moderate = 1.0 - p_fail - p_homerun

        moderate_mult = float(moderate_multiple * rng.uniform(0.85, 1.15))
        homerun_mult = float(homerun_multiple * mod["homerun_mult_factor"] * rng.uniform(0.7, 1.4))

        deals.append(
            Deal(
                index=i,
                name=f"Startup {i + 1:02d}",
                sector=sector,
                stage=stage,
                ticket=ticket,
                p_fail=p_fail,
                p_moderate=p_moderate,
                p_homerun=p_homerun,
                moderate_multiple=moderate_mult,
                homerun_multiple=homerun_mult,
            )
        )
    return deals
