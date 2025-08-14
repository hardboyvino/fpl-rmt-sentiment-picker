from pulp import *
import pandas as pd

VALID_FORMATIONS = [(3,4,3), (3,5,2), (4,4,2), (4,5,1), (5,3,2), (5,4,1), (4,3,3)]
SQUAD_CAPS = {'Goalkeeper': 2, 'Defender': 5, 'Midfielder': 5, 'Forward': 3}

def _mk_uid(name, team, price):
    # normalize to one decimal place to match typical FPL price precision
    return f"{name}|{team}|{float(price):.1f}"

def _normalize_inputs_to_uids(df_uid, items):
    """
    items: iterable of strings that are either:
       - exact UID "Name|Team|Price"
       - plain player name "Name"
    Returns a set of UIDs.
    """
    if not items:
        return set()
    uids = set()
    name_index = df_uid.groupby('Name').groups  # map name -> list of index labels (UIDs)
    for s in items:
        if '|' in s:
            # assume UID
            if s in df_uid.index:
                uids.add(s)
        else:
            # treat as Name; include all rows with that name
            if s in name_index:
                uids.update(name_index[s])
    return uids

def _solve_for_formation(
    df_merged,
    BUDGET,
    formation,                 # (DEF, MID, FWD)
    bench_budget=20.0,
    included_players=None,     # list of Names or UIDs -> must be in 15
    included_starting=None,    # list of Names or UIDs -> must start
    included_teams=None,       # if given, only choose from these teams
    excluded_players=None,     # list of Names or UIDs -> forbid entirely
    excluded_teams=None,       # forbid teams
    max_per_team=3,
    solver_msg=False,
):
    # Build UID index to disambiguate duplicates
    df = df_merged.copy()
    df['UID'] = [_mk_uid(r['Name'], r['Team'], r['Price']) for _, r in df.iterrows()]
    df = df.set_index('UID', drop=False)

    uids = list(df.index)

    name  = df['Name'].to_dict()
    team  = df['Team'].to_dict()
    pos   = df['Position'].to_dict()
    price = df['Price'].astype(float).to_dict()
    pts   = df['Points'].astype(float).to_dict()

    # Normalize include/exclude lists to UIDs
    inc_players_u = _normalize_inputs_to_uids(df, included_players)
    inc_start_u   = _normalize_inputs_to_uids(df, included_starting)
    exc_players_u = _normalize_inputs_to_uids(df, excluded_players)

    included_teams = set(included_teams or [])
    excluded_teams = set(excluded_teams or [])

    DEF, MID, FWD = formation

    # Decision variables (by UID)
    m = LpProblem("FPL_XI_with_Bench", LpMaximize)
    y = LpVariable.dicts("start", uids, 0, 1, cat="Binary")  # starters
    b = LpVariable.dicts("bench", uids, 0, 1, cat="Binary")  # bench

    # Common expressions
    start_expr      = lpSum(pts[u] * y[u] for u in uids)
    bench_expr      = lpSum(pts[u] * b[u] for u in uids)
    total_cost_expr = lpSum(price[u] * (y[u] + b[u]) for u in uids)
    bench_cost_expr = lpSum(price[u] * b[u] for u in uids)
    start_cost_expr = lpSum(price[u] * y[u] for u in uids)

    # Sizes
    m += lpSum(y[u] for u in uids) == 11
    m += lpSum(b[u] for u in uids) == 4

    # No overlap
    for u in uids:
        m += y[u] + b[u] <= 1

    # Budgets
    m += total_cost_expr <= BUDGET
    m += bench_cost_expr <= bench_budget

    # Starting formation
    m += lpSum(y[u] for u in uids if pos[u] == 'Goalkeeper') == 1
    m += lpSum(y[u] for u in uids if pos[u] == 'Defender')   == DEF
    m += lpSum(y[u] for u in uids if pos[u] == 'Midfielder') == MID
    m += lpSum(y[u] for u in uids if pos[u] == 'Forward')    == FWD

    # Full 15 positional caps (implies bench composition)
    for P, cap in SQUAD_CAPS.items():
        m += lpSum((y[u] + b[u]) for u in uids if pos[u] == P) == cap

    # Club cap across 15
    for c in df['Team'].unique():
        m += lpSum((y[u] + b[u]) for u in uids if team[u] == c) <= max_per_team

    # Exclusions (players & teams)
    for u in uids:
        if u in exc_players_u or team[u] in excluded_teams:
            m += y[u] == 0
            m += b[u] == 0

    # Included teams filter (if set, only pick from these teams)
    if included_teams:
        for u in uids:
            if team[u] not in included_teams:
                m += y[u] == 0
                m += b[u] == 0

    # Included players (must be in 15)
    for u in inc_players_u:
        m += y[u] + b[u] == 1

    # Included starters (must be in XI)
    for u in inc_start_u:
        m += y[u] == 1

    # -------- Stage 1: Maximize starting XI points --------
    m.objective = start_expr
    status = m.solve(PULP_CBC_CMD(msg=solver_msg))
    if LpStatus[status] != "Optimal":
        return False, None

    start_best = sum(pts[u] * value(y[u]) for u in uids)

    # Lock in optimal XI points (with a tiny tolerance for numerics)
    EPS = 1e-6
    m += start_expr >= start_best - EPS
    m += start_expr <= start_best + EPS

    # -------- Stage 2: Maximize bench points, keeping XI points optimal --------
    m.objective = bench_expr
    status = m.solve(PULP_CBC_CMD(msg=solver_msg))
    if LpStatus[status] != "Optimal":
        return False, None

    bench_best = sum(pts[u] * value(b[u]) for u in uids)

    # Lock in optimal bench points too
    m += bench_expr >= bench_best - EPS
    m += bench_expr <= bench_best + EPS

    # -------- Stage 3: Minimize total cost as a tie-breaker --------
    # PuLP models are "maximize", so maximize the negative cost.
    m.objective = -total_cost_expr
    status = m.solve(PULP_CBC_CMD(msg=solver_msg))
    if LpStatus[status] != "Optimal":
        return False, None

    # Collect solution
    starters = [u for u in uids if value(y[u]) > 0.5]
    benchers = [u for u in uids if value(b[u]) > 0.5]

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
    }
    return True, payload

def wildcard_team_11(
    BUDGET,
    df_merged,
    bench_budget=20.0,
    formations=None,
    included_players=None,     # Names or UIDs
    included_starting=None,    # Names or UIDs
    included_teams=None,
    excluded_players=None,     # Names or UIDs
    excluded_teams=None,
    max_per_team=3,
    outfile='optimized_team_with_bench.txt',
    solver_msg=False,
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
        )
        if ok:
            results.append(payload)
            # keep best by XI points, then lower total cost, then higher bench points
            key = (payload["starting_points"], -payload["total_budget_used"], payload["bench_points"])
            if best_key is None or key > best_key:
                best_key = key
                best = payload

    if not results:
        raise ValueError("No feasible squad found. Adjust budgets/constraints or formations.")

    # ---- Pretty output for ALL feasible formations ----
    with open(outfile, 'w', encoding='utf-8') as f:
        f.write("Optimized FPL Team (All Feasible Formations):\n")
        f.write(f"BUDGET: {BUDGET:.2f} | Bench budget cap: {bench_budget:.2f} | Max per team: {max_per_team}\n")
        f.write('=' * 75 + '\n\n')

        for payload in results:
            DEF, MID, FWD = payload["formation"]
            df_uid = payload["_df_uid"]  # indexed by UID

            def _print_row(fh, u):
                r = df_uid.loc[u]
                fh.write(f"{r['Name']:<25}{r['Team']:<15}{r['Position']:<15}{float(r['Price']):<10.1f}{float(r['Points']):<10.2f}\n")

            # Header for this formation
            f.write("Optimized FPL Team:\n")
            f.write(f"{DEF} - {MID} - {FWD}\n")
            f.write(f"{'Name':<25}{'Team':<15}{'Position':<15}{'Price':<10}{'Points':<10}\n")
            f.write('-' * 75 + '\n')

            # Starting XI grouped by position
            f.write("STARTING XI\n")
            pos_order = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
            for P in pos_order:
                for u in payload["starting_uids"]:
                    if df_uid.loc[u, 'Position'] == P:
                        _print_row(f, u)

            f.write('-' * 75 + '\n')
            f.write("BENCH\n")
            for u in payload["bench_uids"]:
                _print_row(f, u)

            f.write('-' * 75 + '\n')
            f.write(f"Starting XI points: {payload['starting_points']:.2f}\n")
            f.write(f"Bench points:      {payload['bench_points']:.2f}\n")
            f.write(f"Starting budget used: {payload['starting_budget_used']:.2f}\n")  # <-- NEW
            f.write(f"Bench budget used:    {payload['bench_budget_used']:.2f} / {bench_budget:.2f}\n")
            f.write(f"Total budget used:    {payload['total_budget_used']:.2f} / {BUDGET:.2f}\n")
            # Tag the best for clarity
            if payload is best:
                f.write("[BEST BY XI POINTS]\n")
            f.write('\n')

    # Return both: all results + best pointer
    return {
        "best": {
            "formation": best["formation"],
            "starting_points": best["starting_points"],
            "bench_points": best["bench_points"],
            "starting_budget_used": best["starting_budget_used"],
            "bench_budget_used": best["bench_budget_used"],
            "total_budget_used": best["total_budget_used"],
            "starting_uids": best["starting_uids"],
            "bench_uids": best["bench_uids"],
        },
        "all_results": [
            {
                "formation": p["formation"],
                "starting_points": p["starting_points"],
                "bench_points": p["bench_points"],
                "starting_budget_used": p["starting_budget_used"],
                "bench_budget_used": p["bench_budget_used"],
                "total_budget_used": p["total_budget_used"],
                "starting_uids": p["starting_uids"],
                "bench_uids": p["bench_uids"],
            }
            for p in results
        ],
    }