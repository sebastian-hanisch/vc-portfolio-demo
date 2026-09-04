"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (nach dem in
network-flow-demo/freight_demo/linehaul-demo etablierten Muster)."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import vc_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


SETTING_SPECS = {
    "n_deals_slider": SettingSpec("nd", int, C.N_DEALS_DEFAULT, *C.N_DEALS_RANGE),
    "budget_slider": SettingSpec("b", float, C.BUDGET_DEFAULT, *C.BUDGET_RANGE),
    "ticket_min_slider": SettingSpec("tmin", float, C.TICKET_MIN_DEFAULT, *C.TICKET_MIN_RANGE),
    "ticket_max_slider": SettingSpec("tmax", float, C.TICKET_MAX_DEFAULT, *C.TICKET_MAX_RANGE),
    "sector_cap_pct_slider": SettingSpec("cap", float, C.SECTOR_CAP_PCT_DEFAULT, *C.SECTOR_CAP_PCT_RANGE),
    "p_fail_base_slider": SettingSpec("pf", float, C.P_FAIL_BASE_DEFAULT, *C.P_FAIL_BASE_RANGE),
    "p_homerun_base_slider": SettingSpec("ph", float, C.P_HOMERUN_BASE_DEFAULT, *C.P_HOMERUN_BASE_RANGE),
    "moderate_multiple_slider": SettingSpec("mm", float, C.MODERATE_MULTIPLE_DEFAULT, *C.MODERATE_MULTIPLE_RANGE),
    "homerun_multiple_slider": SettingSpec("hm", float, C.HOMERUN_MULTIPLE_DEFAULT, *C.HOMERUN_MULTIPLE_RANGE),
    "seed_input": SettingSpec("seed", int, C.RANDOM_SEED_DEFAULT, *C.RANDOM_SEED_RANGE),
}


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if isinstance(value, float) and not math.isfinite(value):
                    continue
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def sync_query_params(n_deals, budget, ticket_min, ticket_max, sector_cap_pct, p_fail_base,
                       p_homerun_base, moderate_multiple, homerun_multiple, seed):
    try:
        st.query_params["nd"] = str(int(n_deals))
        st.query_params["b"] = str(budget)
        st.query_params["tmin"] = str(ticket_min)
        st.query_params["tmax"] = str(ticket_max)
        st.query_params["cap"] = str(sector_cap_pct)
        st.query_params["pf"] = str(p_fail_base)
        st.query_params["ph"] = str(p_homerun_base)
        st.query_params["mm"] = str(moderate_multiple)
        st.query_params["hm"] = str(homerun_multiple)
        st.query_params["seed"] = str(int(seed))
    except Exception:
        pass


def apply_preset(name):
    p = C.PRESETS[name]
    st.session_state["n_deals_slider"] = p["n_deals"]
    st.session_state["budget_slider"] = p["budget"]
    st.session_state["ticket_min_slider"] = p["ticket_min"]
    st.session_state["ticket_max_slider"] = p["ticket_max"]
    st.session_state["sector_cap_pct_slider"] = p["sector_cap_pct"]
    st.session_state["p_fail_base_slider"] = p["p_fail_base"]
    st.session_state["p_homerun_base_slider"] = p["p_homerun_base"]
    st.session_state["moderate_multiple_slider"] = p["moderate_multiple"]
    st.session_state["homerun_multiple_slider"] = p["homerun_multiple"]
    st.session_state["seed_input"] = p["seed"]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, 2_000_000_000)
