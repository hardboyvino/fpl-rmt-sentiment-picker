# utils_2025.py – minimal core + refactored dual-CSV helpers
# --------------------------------------------------------
# This keeps your original wildcard_team_11 *as-is* (clean/minimal) and
# adds a thin wrapper + helpers to support select-by-3GW & sort/report-by-1GW
# without changing the core solver.

from typing import Optional, Dict, List, Tuple
import pandas as pd
from pulp import *

# ---------------- Existing core bits (unchanged) ---------------- #

VALID_FORMATIONS = [(3,4,3), (3,5,2), (4,4,2), (4,5,1), (5,3,2), (5,4,1), (4,3,3)]
SQUAD_CAPS = {'Goalkeeper': 2, 'Defender': 5, 'Midfielder': 5, 'Forward': 3}

def _mk_uid(name, team, price):
    return f"{name}|{team}|{float(price):.1f}"

def _normalize_inputs_to_uids(df_uid, items):
    if not items:
        return set()
    uids = set()
    name_index = df_uid.groupby('Name').groups
    for s in items:
        if '|' in s:
            if s in df_uid.index:
                uids.add(s)
        else:
            if s in name_index:
                uids.update(name_index[s])
    return uids

def _solve_for_formation(
    df_merged,
    BUDGET,
    formation,                 # (DEF, MID, FWD)
    bench_budget=20.0,
    included_players=None,
    included_starting=None,
    included_teams=None,
    excluded_players=None,
    excluded_teams=None,
    max_per_team=3,
    solver_msg=False,
    use_bench=True,
):
    df = df_merged.copy()
    df['UID'] = [_mk_uid(r['Name'], r['Team'], r['Price']) for _, r in df.iterrows()]
    df = df.set_index('UID', drop=False)

    uids = list(df.index)

    name  = df['Name'].to_dict()
    team  = df['Team'].to_dict()
    pos   = df['Position'].to_dict()
    price = df['Price'].astype(float).to_dict()
    pts   = df['Points'].astype(float).to_dict()

    inc_players_u = _normalize_inputs_to_uids(df, included_players)
    inc_start_u   = _normalize_inputs_to_uids(df, included_starting)
    exc_players_u = _normalize_inputs_to_uids(df, excluded_players)

    included_teams = set(included_teams or [])
    excluded_teams = set(excluded_teams or [])

    DEF, MID, FWD = formation
    TOTAL_STARTERS = 1 + DEF + MID + FWD

    m = LpProblem("FPL_XI_with_Bench" if use_bench else "FPL_XI_only", LpMaximize)
    y = LpVariable.dicts("start", uids, 0, 1, cat="Binary")
    b = LpVariable.dicts("bench", uids, 0, 1, cat="Binary")

    start_expr      = lpSum(pts[u] * y[u] for u in uids)
    bench_expr      = lpSum(pts[u] * b[u] for u in uids)
    total_cost_expr = lpSum(price[u] * (y[u] + b[u]) for u in uids)
    bench_cost_expr = lpSum(price[u] * b[u] for u in uids)

    m += lpSum(y[u] for u in uids) == TOTAL_STARTERS
    if use_bench:
        m += lpSum(b[u] for u in uids) == 4
    else:
        m += lpSum(b[u] for u in uids) == 0

    for u in uids:
        m += y[u] + b[u] <= 1

    m += total_cost_expr <= BUDGET
    if use_bench:
        m += bench_cost_expr <= bench_budget

    m += lpSum(y[u] for u in uids if pos[u] == 'Goalkeeper') == 1
    m += lpSum(y[u] for u in uids if pos[u] == 'Defender')   == DEF
    m += lpSum(y[u] for u in uids if pos[u] == 'Midfielder') == MID
    m += lpSum(y[u] for u in uids if pos[u] == 'Forward')    == FWD

    if use_bench:
        for P, cap in SQUAD_CAPS.items():
            m += lpSum((y[u] + b[u]) for u in uids if pos[u] == P) == cap

    if use_bench:
        for c in df['Team'].unique():
            m += lpSum((y[u] + b[u]) for u in uids if team[u] == c) <= max_per_team
    else:
        for c in df['Team'].unique():
            m += lpSum(y[u] for u in uids if team[u] == c) <= max_per_team

    for u in uids:
        if u in exc_players_u or team[u] in excluded_teams:
            m += y[u] == 0
            m += b[u] == 0

    if included_teams:
        for u in uids:
            if team[u] not in included_teams:
                m += y[u] == 0
                m += b[u] == 0

    for u in inc_players_u:
        if use_bench:
            m += y[u] + b[u] == 1
        else:
            m += y[u] == 1

    for u in inc_start_u:
        m += y[u] == 1

    m.objective = start_expr
    status = m.solve(PULP_CBC_CMD(msg=solver_msg))
    if LpStatus[status] != "Optimal":
        return False, None

    start_best = sum(pts[u] * value(y[u]) for u in uids)
    EPS = 1e-6
    m += start_expr >= start_best - EPS
    m += start_expr <= start_best + EPS

    if use_bench:
        m.objective = bench_expr
        status = m.solve(PULP_CBC_CMD(msg=solver_msg))
        if LpStatus[status] != "Optimal":
            return False, None
        bench_best = sum(pts[u] * value(b[u]) for u in uids)
        m += bench_expr >= bench_best - EPS
        m += bench_expr <= bench_best + EPS

    m.objective = -total_cost_expr
    status = m.solve(PULP_CBC_CMD(msg=solver_msg))
    if LpStatus[status] != "Optimal":
        return False, None

    starters = [u for u in uids if value(y[u]) > 0.5]
    benchers = [] if not use_bench else [u for u in uids if value(b[u]) > 0.5]

    start_pts  = sum(pts[u] for u in starters)
    bench_pts  = sum(pts[u] for u in benchers)
    total_cost = sum(price[u] for u in starters + benchers)
    bench_cost = sum(price[u] for u in benchers)
    start_cost  = sum(price[u] for u in starters)

    payload = {
        "formation": formation,
        "starting_uids": starters,
        "bench_uids": benchers,
        "starting_points": start_pts,
        "bench_points": bench_pts,
        "total_budget_used": total_cost,
        "bench_budget_used": bench_cost,
        "starting_budget_used": start_cost,
        "_df_uid": df,  # for printing
        "_use_bench": use_bench,
        "_bench_budget_cap": bench_budget,
        "_budget_cap": BUDGET,
        "_max_per_team": max_per_team,
    }
    return True, payload


def wildcard_team_11(
    BUDGET,
    df_merged,
    bench_budget=20.0,
    formations=None,
    included_players=None,
    included_starting=None,
    included_teams=None,
    excluded_players=None,
    excluded_teams=None,
    max_per_team=3,
    outfile='optimized_team_with_bench.txt',
    solver_msg=False,
    use_bench=True,
):
    formations = formations or VALID_FORMATIONS

    results = []
    best_key = None
    best = None

    for f in formations:
        ok, payload = _solve_for_formation(
            df_merged, BUDGET, f, bench_budget,
            included_players=included_players,
            included_starting=included_starting,
            included_teams=included_teams,
            excluded_players=excluded_players,
            excluded_teams=excluded_teams,
            max_per_team=max_per_team,
            solver_msg=solver_msg,
            use_bench=use_bench,
        )
        if ok:
            results.append(payload)
            key = (
                payload["starting_points"],
                -payload["total_budget_used"],
                payload["bench_points"] if use_bench else 0.0
            )
            if best_key is None or key > best_key:
                best_key = key
                best = payload

    if not results:
        raise ValueError("No feasible squad found. Adjust budgets/constraints or formations.")

    # Default minimal text output (unchanged behavior)
    with open(outfile, 'w', encoding='utf-8') as f:
        f.write("Optimized Team (All Feasible Formations):\n")
        if use_bench:
            f.write(f"BUDGET: {BUDGET:.2f} | Bench budget cap: {bench_budget:.2f} | Max per team: {max_per_team}\n")
        else:
            f.write(f"BUDGET: {BUDGET:.2f} | Bench disabled (XI only) | Max per team: {max_per_team}\n")
        f.write('=' * 75 + '\n\n')

        for payload in results:
            DEF, MID, FWD = payload["formation"]
            df_uid = payload["_df_uid"]
            use_b = payload["_use_bench"]

            def _print_row(fh, u):
                r = df_uid.loc[u]
                fh.write(f"{r['Name']:<25}{r['Team']:<15}{r['Position']:<15}{float(r['Price']):<10.1f}{float(r['Points']):<10.2f}\n")

            f.write("Optimized Team:\n")
            f.write(f"{DEF} - {MID} - {FWD}\n")
            f.write(f"{'Name':<25}{'Team':<15}{'Position':<15}{'Price':<10}{'Points':<10}\n")
            f.write('-' * 75 + '\n')

            f.write("STARTING XI\n")
            pos_order = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
            for P in pos_order:
                for u in payload["starting_uids"]:
                    if df_uid.loc[u, 'Position'] == P:
                        _print_row(f, u)

            if use_b:
                f.write('-' * 75 + '\n')
                f.write("BENCH\n")
                for u in payload["bench_uids"]:
                    _print_row(f, u)

            f.write('-' * 75 + '\n')
            f.write(f"Starting XI points: {payload['starting_points']:.2f}\n")
            if use_b:
                f.write(f"Bench points:      {payload['bench_points']:.2f}\n")
                f.write(f"15-Man Team Points: {payload['starting_points'] + payload['bench_points']:.2f}\n")
                f.write(f"Starting budget used: {payload['starting_budget_used']:.2f}\n")
                f.write(f"Bench budget used:    {payload['bench_budget_used']:.2f} / {payload['_bench_budget_cap']:.2f}\n")
                f.write(f"Total budget used:    {payload['total_budget_used']:.2f} / {payload['_budget_cap']:.2f}\n")
                f.write('=' * 75 + '\n\n')
            else:
                f.write(f"Total budget used (XI): {payload['_budget_cap']:.2f}\n")
                f.write('=' * 75 + '\n\n')
            if payload is best:
                f.write("[BEST BY XI POINTS]\n")
                f.write('=' * 75 + '\n\n')
            f.write('\n')

    def _shape_public_payload(p):
        base = {
            "formation": p["formation"],
            "starting_points": p["starting_points"],
            "starting_budget_used": p["starting_budget_used"],
            "total_budget_used": p["total_budget_used"],
            "starting_uids": p["starting_uids"],
            "bench_uids": p["bench_uids"] if use_bench else [],
        }
        if use_bench:
            base.update({
                "bench_points": p["bench_points"],
                "bench_budget_used": p["bench_budget_used"],
            })
        else:
            base.update({
                "bench_points": 0.0,
                "bench_budget_used": 0.0,
            })
        return base

    return {
        "best": _shape_public_payload(best),
        "all_results": [_shape_public_payload(p) for p in results],
    }

# -------------- New helpers for dual-CSV reporting -------------- #

def _build_uid_index(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d['UID'] = [_mk_uid(r['Name'], r['Team'], r['Price']) for _, r in d.iterrows()]
    return d.set_index('UID', drop=False)


def _rows_for_uids(uids: List[str], df_sel_uid: pd.DataFrame, sort_pts: Dict[str, float]) -> List[Dict]:
    rows = []
    for u in uids:
        r = df_sel_uid.loc[u]
        sel = float(r['Points'])
        so = float(sort_pts.get(u, sel))
        rows.append({
            'UID': u,
            'Name': r['Name'], 'Team': r['Team'], 'Position': r['Position'],
            'Price': float(r['Price']), 'SelPts': sel, 'SortPts': so,
        })
    return rows


def _write_dual_report(outfile: str, formation: Tuple[int,int,int], use_bench: bool,
                       xi_rows: List[Dict], bench_rows: List[Dict], sort_by: str):
    key = 'SortPts' if sort_by == 'sort' else 'SelPts'
    xi_sorted = sorted(xi_rows, key=lambda r: r[key], reverse=True)
    bench_sorted = sorted(bench_rows, key=lambda r: r[key], reverse=True) if use_bench else []

    def _totals(rows):
        return sum(r['SelPts'] for r in rows), sum(r['SortPts'] for r in rows), sum(r['Price'] for r in rows)

    xi_ps, xi_po, xi_cost = _totals(xi_rows)
    b_ps, b_po, b_cost = _totals(bench_rows) if use_bench else (0.0,0.0,0.0)

    with open(outfile, 'w', encoding='utf-8') as f:
        d,m,fw = formation
        f.write("Optimized Wildcard Team — Dual CSV Report\n")
        f.write(f"Formation: {d}-{m}-{fw}\n")
        f.write(f"Sorted by: {'df_sort Points' if sort_by=='sort' else 'selection Points'}\n")
        f.write('='*96 + "\n\n")
        f.write("STARTING XI\n")
        f.write(f"{'Name':<25}{'Team':<15}{'Position':<12}{'Price':>8}  {'SelPts':>8}  {'SortPts':>8}\n")
        f.write('-'*96 + "\n")
        for r in xi_sorted:
            f.write(f"{r['Name']:<25}{r['Team']:<15}{r['Position']:<12}{r['Price']:>8.1f}  {r['SelPts']:>8.2f}  {r['SortPts']:>8.2f}\n")
        f.write('\n')
        if use_bench:
            f.write("BENCH\n")
            f.write(f"{'Name':<25}{'Team':<15}{'Position':<12}{'Price':>8}  {'SelPts':>8}  {'SortPts':>8}\n")
            f.write('-'*96 + "\n")
            for r in bench_sorted:
                f.write(f"{r['Name']:<25}{r['Team']:<15}{r['Position']:<12}{r['Price']:>8.1f}  {r['SelPts']:>8.2f}  {r['SortPts']:>8.2f}\n")
            f.write('\n')

        f.write('Totals\n')
        f.write('-'*96 + "\n")
        f.write(f"XI:    SelectPts={xi_ps:.2f}  SortPts={xi_po:.2f}  Cost={xi_cost:.2f}\n")
        if use_bench:
            f.write(f"Bench: SelectPts={b_ps:.2f}  SortPts={b_po:.2f}  Cost={b_cost:.2f}\n")
            f.write(f"ALL15: SelectPts={xi_ps+b_ps:.2f}  SortPts={xi_po+b_po:.2f}  Cost={xi_cost+b_cost:.2f}\n")
        else:
            f.write(f"XI-only: SelectPts={xi_ps:.2f}  SortPts={xi_po:.2f}  Cost={xi_cost:.2f}\n")


# -------------- Thin wrapper that keeps core clean -------------- #

def wildcard_team_11_dual(
    BUDGET: float,
    df_select: pd.DataFrame,
    df_sort: Optional[pd.DataFrame] = None,
    sort_by: str = 'select',
    bench_budget: float = 20.0,
    formations: Optional[List[Tuple[int,int,int]]] = None,
    included_players=None,
    included_starting=None,
    included_teams=None,
    excluded_players=None,
    excluded_teams=None,
    max_per_team: int = 3,
    use_bench: bool = True,
    outfile: str = 'optimized_dual_wildcard.txt',
    solver_msg: bool = False,
):
    """Selects by df_select['Points'] using the *core* wildcard_team_11, then
    writes a dual-CSV report that also shows df_sort['Points'] (if provided)
    and orders sections per `sort_by` ('select' or 'sort').

    Returns the same dict structure as wildcard_team_11.
    """
    formations = formations or VALID_FORMATIONS

    # Run the core solver with selection CSV only; suppress its file output
    core = wildcard_team_11(
        BUDGET=BUDGET,
        df_merged=df_select[["Name","Team","Position","Price","Points"]].copy(),
        bench_budget=bench_budget,
        formations=formations,
        included_players=included_players,
        included_starting=included_starting,
        included_teams=included_teams,
        excluded_players=excluded_players,
        excluded_teams=excluded_teams,
        max_per_team=max_per_team,
        outfile=outfile,
        solver_msg=solver_msg,
        use_bench=use_bench,
    )

    best = core['best']
    xi_uids = best['starting_uids']
    bench_uids = best.get('bench_uids', []) if use_bench else []

    # Build UID indices from selection CSV and optional sort CSV
    df_sel_uid = _build_uid_index(df_select)

    if df_sort is not None:
        df_sort_uid = _build_uid_index(df_sort)
        sort_pts = df_sort_uid['Points'].astype(float).to_dict()
    else:
        sort_pts = df_sel_uid['Points'].astype(float).to_dict()

    # Prepare rows
    xi_rows = _rows_for_uids(xi_uids, df_sel_uid, sort_pts)
    bench_rows = _rows_for_uids(bench_uids, df_sel_uid, sort_pts) if use_bench else []

    # Use formation from best result for the header
    formation = best['formation']

    # Write the dual report
    _write_dual_report(outfile, formation, use_bench, xi_rows, bench_rows, sort_by)

    return core

# -----------------------------
# Usage from wildcard.py (example)
# -----------------------------
# from utils_2025 import wildcard_team_11_dual
# import pandas as pd
# df3 = pd.read_csv('gw3.csv')   # 3GW
# df1 = pd.read_csv('gw1.csv')   # 1GW
# res = wildcard_team_11_dual(
#     BUDGET=1000.0,
#     df_select=df3,          # select by 3GW
#     df_sort=df1,            # sort/report by 1GW (optional)
#     sort_by='sort',         # 'select' or 'sort'
#     bench_budget=20,
#     formations=[(3,4,3),(3,5,2),(4,4,2)],
#     excluded_players=['Wan-Bissaka','Cunha'],
#     max_per_team=3,
#     use_bench=False,
#     outfile='optimized_challenge_team.txt',
# )

# -------------- XI re-arrangement helpers (fixed squad) -------------- #

def _arrange_best_xi_for_fixed_squad_uids(
    selected_uids: List[str],
    pos_by_uid: Dict[str, str],
    pts_by_uid: Dict[str, float],
    formation: Tuple[int,int,int],
):
    """Given a fixed squad (UIDs), choose the best XI for a *specific* formation.
    Returns (xi_uids, bench_uids, xi_points).
    """
    DEF, MID, FWD = formation
    m = LpProblem("Arrange_Best_XI_UID", LpMaximize)
    y = LpVariable.dicts("start", selected_uids, 0, 1, cat="Binary")

    # XI size
    m += lpSum(y[u] for u in selected_uids) == 11

    # Formation constraints
    m += lpSum(y[u] for u in selected_uids if pos_by_uid[u] == 'Goalkeeper') == 1
    m += lpSum(y[u] for u in selected_uids if pos_by_uid[u] == 'Defender')   == DEF
    m += lpSum(y[u] for u in selected_uids if pos_by_uid[u] == 'Midfielder') == MID
    m += lpSum(y[u] for u in selected_uids if pos_by_uid[u] == 'Forward')    == FWD

    # Objective: maximize points (under provided pts_by_uid basis)
    m.objective = lpSum(float(pts_by_uid.get(u, 0.0)) * y[u] for u in selected_uids)
    m.solve(PULP_CBC_CMD(msg=False))

    xi = [u for u in selected_uids if value(y[u]) > 0.5]
    bench = [u for u in selected_uids if u not in xi]
    xi_points = sum(float(pts_by_uid.get(u, 0.0)) for u in xi)
    return xi, bench, xi_points


def _best_xi_over_formations(
    selected_uids: List[str],
    pos_by_uid: Dict[str, str],
    pts_by_uid: Dict[str, float],
    formations: List[Tuple[int,int,int]],
):
    """Try all formations and return the best-arranged XI/bench under pts_by_uid.
    Returns dict with keys: formation, xi_uids, bench_uids, xi_points.
    """
    best = None
    best_key = None
    for f in formations:
        xi, bench, points = _arrange_best_xi_for_fixed_squad_uids(selected_uids, pos_by_uid, pts_by_uid, f)
        key = (points,)
        if best_key is None or key > best_key:
            best_key = key
            best = {"formation": f, "xi_uids": xi, "bench_uids": bench, "xi_points": points}
    return best


# -------------- Mode 1: Wildcard (3GW select) + 1GW re-arrangement -------------- #

def wildcard_compare_3gw_1gw(
    BUDGET: float,
    df_3gw: pd.DataFrame,
    df_1gw: pd.DataFrame,
    bench_budget: float = 20.0,
    formations: Optional[List[Tuple[int,int,int]]] = None,
    included_players=None,
    included_starting=None,
    included_teams=None,
    excluded_players=None,
    excluded_teams=None,
    max_per_team: int = 3,
    use_bench: bool = True,
    outfile: str = 'optimized_wildcard_vs_1gw.txt',
    solver_msg: bool = False,
):
    """
    For each *3GW selection* (wildcard) produced by the core solver across the
    provided formations, re-arrange that fixed 15 for the coming GW using the
    1GW points and allowing ANY valid formation from `formations`.

    Output resembles `wildcard_team_11`: grouped by position order
    (Goalkeeper, Defender, Midfielder, Forward) and shows both 3GW and 1GW
    points for each player, plus totals for XI (and Bench if enabled).
    """
    formations = formations or VALID_FORMATIONS

    # 1) Select squads by 3GW (like a wildcard); gather *all feasible* selections
    core = wildcard_team_11(
        BUDGET=BUDGET,
        df_merged=df_3gw[["Name","Team","Position","Price","Points"]].copy(),
        bench_budget=bench_budget,
        formations=formations,
        included_players=included_players,
        included_starting=included_starting,
        included_teams=included_teams,
        excluded_players=excluded_players,
        excluded_teams=excluded_teams,
        max_per_team=max_per_team,
        outfile=outfile,  # we'll write a custom report below
        solver_msg=solver_msg,
        use_bench=use_bench,
    )

    # Lookups (UID keyed)
    df3_uid = _build_uid_index(df_3gw)
    df1_uid = _build_uid_index(df_1gw)
    pos_by_uid = df3_uid['Position'].to_dict()
    pts3_by_uid = df3_uid['Points'].astype(float).to_dict()
    pts1_by_uid = df1_uid['Points'].astype(float).to_dict()

    def _print_row(fh, uid: str):
        # Pick metadata from 3GW if present; else 1GW
        r = df3_uid.loc[uid] if uid in df3_uid.index else df1_uid.loc[uid]
        name, team, pos = r['Name'], r['Team'], r['Position']
        price = float(r['Price'])
        p3 = float(pts3_by_uid.get(uid, 0.0))
        p1 = float(pts1_by_uid.get(uid, 0.0))
        fh.write(f"{name:<25}{team:<15}{pos:<15}{price:<10.1f}{p3:<10.2f}{p1:<10.2f}\n")
        return p3, p1, price

    # --- Precompute best 1GW metrics across all 3GW selections (for annotations) ---
    pre = []
    for sel in core['all_results']:
        squad_uids = sel['starting_uids'] + sel['bench_uids'] if use_bench else sel['starting_uids']
        best_1gw_tmp = _best_xi_over_formations(squad_uids, pos_by_uid, pts1_by_uid, formations)
        xi_1gw = sum(float(pts1_by_uid.get(u, 0.0)) for u in best_1gw_tmp['xi_uids'])
        bench_1gw = sum(float(pts1_by_uid.get(u, 0.0)) for u in best_1gw_tmp['bench_uids']) if use_bench else 0.0
        pre.append({'xi_1gw': xi_1gw, 'all15_1gw': xi_1gw + bench_1gw})

    best_xi_idx = max(range(len(pre)), key=lambda i: pre[i]['xi_1gw']) if pre else -1
    best_all15_idx = max(range(len(pre)), key=lambda i: pre[i]['all15_1gw']) if pre else -1

    with open(outfile, 'w', encoding='utf-8') as f:
        f.write("Optimized Team (3GW selections re-arranged for 1GW)\n")
        if use_bench:
            f.write(f"BUDGET: {BUDGET:.2f} | Bench budget cap: {bench_budget:.2f} | Max per team: {max_per_team}\n")
        else:
            f.write(f"BUDGET: {BUDGET:.2f} | Bench disabled (XI only) | Max per team: {max_per_team}\n")
        f.write('=' * 80 + '\n\n')

        pos_order = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']

        for idx, sel in enumerate(core['all_results']):
            # The fixed squad chosen by this 3GW selection
            if use_bench:
                squad_uids = sel['starting_uids'] + sel['bench_uids']
            else:
                squad_uids = sel['starting_uids']

            # 2) Re-arrange this fixed squad for the coming GW (1GW) allowing ANY valid formation
            best_1gw = _best_xi_over_formations(squad_uids, pos_by_uid, pts1_by_uid, formations)

            # Optional: also compute the best XI formation under the 3GW basis for comparison
            best_3gw = _best_xi_over_formations(squad_uids, pos_by_uid, pts3_by_uid, formations)

            # Header for this selection
            d0, m0, f0 = sel['formation']
            d1, m1, f1 = best_1gw['formation']
            f.write("Optimized Team:\n")
            f.write(f"3GW selection formation: {d0}-{m0}-{f0}  |  1GW best formation: {d1}-{m1}-{f1}\n")
            f.write(f"{'Name':<25}{'Team':<15}{'Position':<15}{'Price':<10}{'3GW':<10}{'1GW':<10}\n")
            f.write('-' * 80 + '\n')

            # STARTING XI for the coming GW (grouped by position order)
            f.write("STARTING XI (arranged for 1GW)\n")
            xi_tot_3 = xi_tot_1 = xi_cost = 0.0
            for P in pos_order:
                for uid in best_1gw['xi_uids']:
                    if pos_by_uid[uid] == P:
                        p3, p1, pr = _print_row(f, uid)
                        xi_tot_3 += p3; xi_tot_1 += p1; xi_cost += pr

            # BENCH (remaining from the fixed 15)
            if use_bench:
                f.write('-' * 80 + '\n')
                f.write("BENCH\n")
                b_tot_3 = b_tot_1 = b_cost = 0.0
                for uid in best_1gw['bench_uids']:
                    p3, p1, pr = _print_row(f, uid)
                    b_tot_3 += p3; b_tot_1 += p1; b_cost += pr

            f.write('-' * 80 + '\n')
            f.write(f"Starting XI points (1GW): {xi_tot_1:.2f}\n")
            f.write(f"Starting XI points (3GW): {xi_tot_3:.2f}\n")
            if use_bench:
                f.write(f"Bench points (1GW):      {b_tot_1:.2f}\n")
                f.write(f"Bench points (3GW):      {b_tot_3:.2f}\n")
                f.write(f"15-Man Team Points (1GW): {xi_tot_1 + b_tot_1:.2f}\n")
                f.write(f"15-Man Team Points (3GW): {xi_tot_3 + b_tot_3:.2f}\n")
                f.write(f"Starting budget used: {xi_cost:.2f}\n")
                f.write(f"Bench budget used:    {b_cost:.2f} / {bench_budget:.2f}\n")
                f.write(f"Total budget used:    {xi_cost + b_cost:.2f} / {BUDGET:.2f}\n")
            else:
                f.write(f"Total budget used (XI): {xi_cost:.2f} / {BUDGET:.2f}\n")
                

            # --- Best 1GW annotations across selections ---
            if idx == best_xi_idx:
                f.write("[BEST 1GW XI]\n")
            if use_bench and idx == best_all15_idx:
                f.write("[BEST 1GW XI+Bench]\n")
            f.write('=' * 80 + '\n\n')
            # Mark which selection was best by 3GW XI points (optional tag)
            if sel is core['best']:
                f.write("[BEST 3GW SELECTION BY XI POINTS]\n")

            # # Also show the best XI (by 3GW) summary line to make differences clear
            # f.write(f"(For reference) Best 3GW XI formation: {best_3gw['formation'][0]}-{best_3gw['formation'][1]}-{best_3gw['formation'][2]}  | XI 3GW pts: {best_3gw['xi_points']:.2f}\n")
            f.write('\n\n')

    return core


# -------------- Mode 2: Free Hit for coming GW (1GW only) -------------- #

def free_hit_1gw(
    BUDGET: float,
    df_1gw: pd.DataFrame,
    bench_budget: float = 20.0,
    formations: Optional[List[Tuple[int,int,int]]] = None,
    included_players=None,
    included_starting=None,
    included_teams=None,
    excluded_players=None,
    excluded_teams=None,
    max_per_team: int = 3,
    use_bench: bool = True,
    outfile: str = 'optimized_free_hit_1gw.txt',
    solver_msg: bool = False,
):
    """Best possible team for *this* gameweek only (uses 1GW CSV for both select & arrangement)."""
    formations = formations or VALID_FORMATIONS
    return wildcard_team_11(
        BUDGET=BUDGET,
        df_merged=df_1gw[["Name","Team","Position","Price","Points"]].copy(),
        bench_budget=bench_budget,
        formations=formations,
        included_players=included_players,
        included_starting=included_starting,
        included_teams=included_teams,
        excluded_players=excluded_players,
        excluded_teams=excluded_teams,
        max_per_team=max_per_team,
        outfile=outfile,
        solver_msg=solver_msg,
        use_bench=use_bench,
    )


# -------------- Mode 3: Wildcard by 3GW only (default) -------------- #

def wildcard_3gw_only(
    BUDGET: float,
    df_3gw: pd.DataFrame,
    bench_budget: float = 20.0,
    formations: Optional[List[Tuple[int,int,int]]] = None,
    included_players=None,
    included_starting=None,
    included_teams=None,
    excluded_players=None,
    excluded_teams=None,
    max_per_team: int = 3,
    use_bench: bool = True,
    outfile: str = 'optimized_wildcard_3gw.txt',
    solver_msg: bool = False,
):
    """Classic wildcard: select & arrange by 3GW only (identical to calling core)."""
    formations = formations or VALID_FORMATIONS
    return wildcard_team_11(
        BUDGET=BUDGET,
        df_merged=df_3gw[["Name","Team","Position","Price","Points"]].copy(),
        bench_budget=bench_budget,
        formations=formations,
        included_players=included_players,
        included_starting=included_starting,
        included_teams=included_teams,
        excluded_players=excluded_players,
        excluded_teams=excluded_teams,
        max_per_team=max_per_team,
        outfile=outfile,
        solver_msg=solver_msg,
        use_bench=use_bench,
    )

def sort_dataframe(df):
    # ensure numeric + categorical ordering
    pos_order = ['Forward', 'Midfielder', 'Defender', 'Goalkeeper']
    df = df.copy()
    df['Points'] = pd.to_numeric(df['Points'], errors='coerce')
    df['Price']  = pd.to_numeric(df['Price'],  errors='coerce')
    df['Position'] = pd.Categorical(df['Position'], categories=pos_order, ordered=True)

    # sort: Points desc, Price desc, Position (given order)
    df_sorted = df.sort_values(
        by=['Points', 'Price', 'Position'],
        ascending=[False, False, True],
        kind='mergesort'  # stable
    )

    return df_sorted