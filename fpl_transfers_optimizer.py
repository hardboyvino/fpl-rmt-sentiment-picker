# Requires: requests, pandas, pulp
# Usage:
#   python fpl_transfers_from_csv.py --entry 123456 --preds my_predictions.csv
# Optional:
#   --max_transfers 5 --bench_budget 20 --formations "3-4-3,3-5-2,4-4-2"
#   --include Saka --include_start Haaland --exclude Muniz
#   --keep "O'Shea" --block_add "G.Jesus" --include_teams Spurs Arsenal
#   --exclude_teams "Nott'm Forest"
#
# Notes:
# - Scoring and prices come from YOUR CSV (Name,Price,Position,Team,Points).
# - Players missing from your CSV but currently owned are auto-added with Points=0.0
#   and price from FPL API, so the optimizer stays feasible (you’ll see a warning).
# - Bank is read from the FPL entry endpoint (in millions). Budget = CSV-cost of
#   your current 15 + bank.
# - Objective: maximize starting XI Points, then bench Points, then minimize total cost.
#
# What it does:
# - Uses YOUR CSV (Name,Price,Position,Team,Points) for scoring/prices.
# - Pulls current 15 and (optionally) bank from FPL API; you can override with --bank.
# - Optimizes 1..5 transfers to maximize next XI points; tie-break with bench points, then minimize total cost.
# - Obeys FPL constraints: 2/5/5/3 across 15, <=3 per team, budget, formation.
# - Outputs extra metrics: Points Out/In, Difference, Diff %, Budget Left.

import argparse
import sys
import unicodedata
from typing import Dict, List, Set, Tuple

import pandas as pd
import requests
from pulp import (
    LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD, LpStatus, value
)

POS_MAP = {1: "Goalkeeper", 2: "Defender", 3: "Midfielder", 4: "Forward"}
VALID_POS = set(POS_MAP.values())
SQUAD_CAPS = {"Goalkeeper": 2, "Defender": 5, "Midfielder": 5, "Forward": 3}
DEFAULT_FORMATIONS = [(3,4,3), (3,5,2), (4,4,2), (4,5,1), (5,3,2), (5,4,1), (4,3,3)]

# ------------------------ Utilities ------------------------ #

def _get_json(url: str) -> dict:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def _norm(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("’", "'").replace("`", "'").replace("´", "'")
    for ch in [".", "-", "_"]:
        s = s.replace(ch, " ")
    s = s.replace("&", "and")
    s = s.replace("’", "'").replace("'", "")
    return " ".join(s.lower().split())

def _key(name: str, team: str) -> str:
    return f"{_norm(name)}|{_norm(team)}"

# ------------------------ FPL API ------------------------ #

def fetch_bootstrap():
    data = _get_json("https://fantasy.premierleague.com/api/bootstrap-static/")
    elements = pd.DataFrame(data["elements"])
    teams = pd.DataFrame(data["teams"])
    team_map = teams.set_index("id")["name"].to_dict()
    elements["Team"] = elements["team"].map(team_map)
    elements["NameAPI"] = elements["web_name"]
    elements["PositionAPI"] = elements["element_type"].map(POS_MAP)
    elements["PriceAPI"] = elements["now_cost"].astype(float) / 10.0
    elements["PointsAPI"] = pd.to_numeric(elements["ep_next"], errors="coerce").fillna(0.0)
    return elements[["id", "NameAPI", "Team", "PositionAPI", "PriceAPI", "PointsAPI"]].copy()

def fetch_entry(entry_id: int):
    return _get_json(f"https://fantasy.premierleague.com/api/entry/{entry_id}/")

def fetch_picks(entry_id: int, event_id: int):
    return _get_json(f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{event_id}/picks/")

def get_current_event_id(entry_meta: dict, bootstrap_events_fallback: dict = None):
    # Primary: entry_meta.current_event
    cur = entry_meta.get("current_event")
    if cur:
        return int(cur)
    # Fallback: try bootstrap events (if passed), else fail
    if bootstrap_events_fallback is not None:
        cur_row = bootstrap_events_fallback.get("events", [])
        for e in cur_row:
            if e.get("is_current"):
                return int(e["id"])
    raise RuntimeError("Could not determine current gameweek for this entry.")

# ------------------------ CSV Pool ------------------------ #

def load_predictions_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected_cols = {"Name","Price","Position","Team","Points"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    df = df.copy()
    df["Name"] = df["Name"].astype(str)
    df["Team"] = df["Team"].astype(str)
    df["Position"] = df["Position"].astype(str)

    # Normalize types
    df["Price"]  = pd.to_numeric(df["Price"], errors="coerce")
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
    df = df.dropna(subset=["Price","Points"])

    # Enforce valid positions
    bad_pos = set(df["Position"].unique()) - VALID_POS
    if bad_pos:
        raise ValueError(f"CSV has invalid Position values: {bad_pos}. Expected one of {sorted(VALID_POS)}")

    # Build key for matching
    df["key"] = df.apply(lambda r: _key(r["Name"], r["Team"]), axis=1)
    if df["key"].duplicated().any():
        # Not fatal; but warn user
        dups = df[df["key"].duplicated(keep=False)].sort_values("key")
        print("Warning: duplicate Name+Team rows detected in CSV. Using all; optimizer may pick either.\n"
              f"Examples:\n{dups[['Name','Team','Price','Points']].head(6)}\n", file=sys.stderr)
    return df

# ------------------------ Matching current squad to CSV ------------------------ #

def map_current_ids_to_csv_rows(
    current_ids: List[int],
    elements_api: pd.DataFrame,
    preds_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, List[dict]]:
    """
    Returns:
      - pool_df: the *full optimization pool* (start from preds_df; add any missing owned players)
      - owned_df: rows corresponding to currently owned players
      - warnings: list of warning dicts for missing matches
    """
    api = elements_api.set_index("id")
    preds = preds_df.set_index("key")
    warnings = []

    # Build mapping id -> CSV key via (web_name, team name)
    id_to_key = {}
    for pid in current_ids:
        if pid not in api.index:
            continue
        nm = api.loc[pid, "NameAPI"]
        tm = api.loc[pid, "Team"]
        id_to_key[pid] = _key(nm, tm)

    # Rows for currently owned found directly in CSV
    found_keys = [id_to_key[i] for i in current_ids if id_to_key.get(i) in preds.index]
    if found_keys:
        owned_found = preds.loc[found_keys].copy()
        owned_found["key"] = owned_found.index  # <-- ensure 'key' is a real column
    else:
        owned_found = pd.DataFrame(columns=preds.columns)

    # Identify owned but not in CSV and create fallback rows from API
    missing_ids = [i for i in current_ids if id_to_key.get(i) not in preds.index]
    fallback_rows = []
    for pid in missing_ids:
        if pid not in api.index:
            continue
        nm = api.loc[pid, "NameAPI"]
        tm = api.loc[pid, "Team"]
        pos = api.loc[pid, "PositionAPI"]
        price = float(api.loc[pid, "PriceAPI"])

        # Score fallback sky-high so feasibility is guaranteed and they’re strongly preferred
        row = dict(Name=nm, Team=tm, Position=pos, Price=price, Points=-9999.0, key=_key(nm, tm)) 
        fallback_rows.append(row)
        warnings.append({
            "type": "csv_missing_player_added",
            "id": pid, "Name": nm, "Team": tm,
            "note": "Not found in CSV; added with Points=-9999.0 and price from FPL API."
        })

    owned_fallback = pd.DataFrame(fallback_rows) if fallback_rows else pd.DataFrame(columns=preds.columns)

    # Optimization pool = CSV + fallback rows (dedup by key, prefer CSV)
    pool_df = preds_df.copy()
    if not owned_fallback.empty:
        new_keys = [k for k in owned_fallback["key"] if k not in set(pool_df["key"])]
        pool_df = pd.concat([pool_df, owned_fallback[owned_fallback["key"].isin(new_keys)]], ignore_index=True)

    # Owned set (using pool rows)
    owned_df = pd.concat([owned_found.reset_index(drop=True), owned_fallback.reset_index(drop=True)], ignore_index=True)
    # Ensure 'key' exists and is filled for every row (handles mixed index/column cases)
    if "key" not in owned_df.columns:
        owned_df["key"] = owned_df.apply(lambda r: _key(r["Name"], r["Team"]), axis=1)
    else:
        mask = owned_df["key"].isna() | (owned_df["key"].astype(str).str.strip() == "")
        if mask.any():
            owned_df.loc[mask, "key"] = owned_df.loc[mask].apply(
                lambda r: _key(r["Name"], r["Team"]), axis=1
            )

    return pool_df.reset_index(drop=True), owned_df.reset_index(drop=True), warnings

def _arrange_best_xi_for_fixed_squad(
    selected_pids,  # list of PIDs in the final 15
    pts_dict,       # pid -> Points
    pos_dict,       # pid -> Position
    formation       # (DEF, MID, FWD)
):
    """
    Given a fixed 15-man squad, choose the best XI (y[i]) to maximize starting points
    subject to formation (1 GK, DEF/MID/FWD counts) and y[i] in {0,1}.
    Returns (y_selected, b_selected) as lists of PIDs.
    """
    DEF, MID, FWD = formation
    m = LpProblem("Arrange_Best_XI", LpMaximize)
    y = LpVariable.dicts("start", selected_pids, 0, 1, cat="Binary")

    # XI size
    m += lpSum(y[i] for i in selected_pids) == 11

    # Formation constraints
    m += lpSum(y[i] for i in selected_pids if pos_dict[i] == "Goalkeeper") == 1
    m += lpSum(y[i] for i in selected_pids if pos_dict[i] == "Defender")   == DEF
    m += lpSum(y[i] for i in selected_pids if pos_dict[i] == "Midfielder") == MID
    m += lpSum(y[i] for i in selected_pids if pos_dict[i] == "Forward")    == FWD

    # Objective: maximize starting points
    m.objective = lpSum(pts_dict[i] * y[i] for i in selected_pids)
    m.solve(PULP_CBC_CMD(msg=False))

    y_sel = [i for i in selected_pids if value(y[i]) > 0.5]
    b_sel = [i for i in selected_pids if i not in y_sel]
    return y_sel, b_sel

def _arrange_best_xi_over_formations_for_fixed_squad(
    selected_pids: List[int],
    pts_dict: Dict[int, float],
    pos_dict: Dict[int, str],
    formations: List[Tuple[int,int,int]],
):
    best = None
    best_key = None
    for f in formations:
        xi, bench = _arrange_best_xi_for_fixed_squad(selected_pids, pts_dict, pos_dict, f)
        pts_xi = sum(pts_dict[i] for i in xi)
        key = (pts_xi,)
        if best_key is None or key > best_key:
            best_key = key
            best = {"formation": f, "xi": xi, "bench": bench, "xi_points": pts_xi}
    return best


# ------------------------ Optimization ------------------------ #

def optimize_k(
    k: int,
    pool_df: pd.DataFrame,
    owned_df: pd.DataFrame,
    bank_m: float,
    formations: List[Tuple[int,int,int]],
    max_per_team: int = 3,
    bench_budget: float | None = None,          # <-- make optional
    include_names: Set[str] = None,
    include_start_names: Set[str] = None,
    exclude_names: Set[str] = None,
    include_teams: Set[str] = None,
    exclude_teams: Set[str] = None,
    block_add_names: Set[str] = None,
    solver_msg: bool = False,
    arrange_points_by_key: Dict[str, float] | None = None,
    arrange_over_formations: bool = True,
):
    """
    Choose transfers (≤ k), select a 15-man squad, and then arrange XI+bench.
    Multi-stage solve:
      1) Max XI points
      2) Max bench points (tie-break)
      3) Min total cost (tie-break)
    Finally, re-arrange the XI for the chosen 15 to guarantee the true best XI.
    """
    # Build synthetic PIDs
    df = pool_df.copy().reset_index(drop=True)
    df["PID"] = df.index
    id_list = df["PID"].tolist()

    # Dicts
    name = df.set_index("PID")["Name"].to_dict()
    team = df.set_index("PID")["Team"].to_dict()
    pos  = df.set_index("PID")["Position"].to_dict()
    price = df.set_index("PID")["Price"].astype(float).to_dict()
    pts   = df.set_index("PID")["Points"].astype(float).to_dict()

    # Owned PIDs via 'key'
    if "key" not in owned_df.columns:
        owned_df = owned_df.copy()
        owned_df["key"] = owned_df.apply(lambda r: _key(r["Name"], r["Team"]), axis=1)

    owned_keys = set(owned_df["key"])
    pid_by_key = df.set_index("key")["PID"].to_dict()
    current_pids = {pid_by_key[k] for k in owned_keys if k in pid_by_key}

    # Name→PID helper
    by_name: Dict[str, Set[int]] = df.groupby("Name")["PID"].apply(set).to_dict()
    def ids_for_names(names: Set[str]) -> Set[int]:
        out = set()
        for nm in names or []:
            out |= by_name.get(nm, set())
        return out

    inc_ids       = ids_for_names(include_names or set())
    inc_start_ids = ids_for_names(include_start_names or set())
    exc_ids       = ids_for_names(exclude_names or set())
    block_add_ids = ids_for_names(block_add_names or set())
    include_teams = set(include_teams or [])
    exclude_teams = set(exclude_teams or [])

    total_current_cost = float(owned_df["Price"].sum())

    best = None
    best_key = None

    for DEF, MID, FWD in formations:
        m = LpProblem("FPL_FromCSV", LpMaximize)
        x = LpVariable.dicts("in_squad", id_list, 0, 1, cat="Binary")
        y = LpVariable.dicts("start",    id_list, 0, 1, cat="Binary")
        b = LpVariable.dicts("bench",    id_list, 0, 1, cat="Binary")

        # Sizes
        m += lpSum(x[i] for i in id_list) == 15
        m += lpSum(y[i] for i in id_list) == 11
        m += lpSum(b[i] for i in id_list) == 4

        # Consistency
        for i in id_list:
            m += y[i] + b[i] <= x[i]

        # Formation (XI)
        m += lpSum(y[i] for i in id_list if pos[i] == "Goalkeeper") == 1
        m += lpSum(y[i] for i in id_list if pos[i] == "Defender")   == DEF
        m += lpSum(y[i] for i in id_list if pos[i] == "Midfielder") == MID
        m += lpSum(y[i] for i in id_list if pos[i] == "Forward")    == FWD

        # Full 15 caps
        for P, cap in SQUAD_CAPS.items():
            m += lpSum(x[i] for i in id_list if pos[i] == P) == cap

        # ≤3 per club across 15
        for club in df["Team"].unique():
            m += lpSum(x[i] for i in id_list if team[i] == club) <= max_per_team

        # Budget: new 15 within current_15_csv_cost + bank
        total_cost_expr = lpSum(price[i] * x[i] for i in id_list)
        m += total_cost_expr <= total_current_cost + bank_m

        # Bench soft cap (ONLY if explicitly provided)
        if bench_budget is not None:
            bench_cost_expr = lpSum(price[i] * b[i] for i in id_list)
            m += bench_cost_expr <= bench_budget

        # Transfers ≤ k
        removed = 15 - lpSum(x[i] for i in current_pids)
        added   = lpSum(x[i] for i in set(id_list) - current_pids)
        m += removed <= k
        m += added   <= k

        # Includes/excludes
        for i in id_list:
            if i in inc_ids:       m += x[i] == 1
            if i in inc_start_ids: m += y[i] == 1
            if i in exc_ids:       m += x[i] == 0
            if include_teams and team[i] not in include_teams: m += x[i] == 0
            if team[i] in exclude_teams:                       m += x[i] == 0
            # Only block if it's a *new* buy
            if i in block_add_ids and i not in current_pids:   m += x[i] == 0

        # Objectives (multi-stage)
        start_points = lpSum(pts[i] * y[i] for i in id_list)
        bench_points = lpSum(pts[i] * b[i] for i in id_list)

        # 1) Max XI points
        m.objective = start_points
        status = m.solve(PULP_CBC_CMD(msg=solver_msg))
        if LpStatus[status] != "Optimal":
            continue
        start_best = sum(pts[i] * value(y[i]) for i in id_list)
        EPS = 1e-6
        m += start_points >= start_best - EPS
        m += start_points <= start_best + EPS

        # 2) Max bench points (tie-break)
        m.objective = bench_points
        status = m.solve(PULP_CBC_CMD(msg=solver_msg))
        if LpStatus[status] != "Optimal":
            continue
        bench_best = sum(pts[i] * value(b[i]) for i in id_list)
        m += bench_points >= bench_best - EPS
        m += bench_points <= bench_best + EPS

        # 3) Min total cost (final tie-break)
        m.objective = -total_cost_expr
        status = m.solve(PULP_CBC_CMD(msg=solver_msg))
        if LpStatus[status] != "Optimal":
            continue

        # --- Retrieve the chosen 15 ---
        x_sel = [i for i in id_list if value(x[i]) > 0.5]
        # NOTE: y/b from this stage might be skewed if a bench cap was applied; we’ll re-arrange next.

        # Map PID -> 1GW arrangement points (fallback to preds pts if not provided)
        key_by_pid = df.set_index("PID")["key"].to_dict()
        if arrange_points_by_key is not None:
            arrange_pts_by_pid = {pid: float(arrange_points_by_key.get(key_by_pid[pid], pts[pid])) for pid in id_list}
        else:
            arrange_pts_by_pid = pts

        # --- Re-arrange best XI for the fixed squad (guarantees maximum XI points) ---
        y_sel, b_sel = _arrange_best_xi_for_fixed_squad(x_sel, pts, pos, (DEF, MID, FWD))

        # (A) Preds-based XI for THIS formation (used to rank solutions by preds)
        y_sel_pred, b_sel_pred = _arrange_best_xi_for_fixed_squad(x_sel, pts, pos, (DEF, MID, FWD))

        # (B) 1GW-based XI; allow ANY valid formation if requested (used for reporting/selection order)
        if arrange_over_formations:
            best_arr = _arrange_best_xi_over_formations_for_fixed_squad(x_sel, arrange_pts_by_pid, pos, formations)
            y_sel_arr, b_sel_arr = best_arr["xi"], best_arr["bench"]
            arr_formation = best_arr["formation"]
        else:
            y_sel_arr, b_sel_arr = _arrange_best_xi_for_fixed_squad(x_sel, arrange_pts_by_pid, pos, (DEF, MID, FWD))
            arr_formation = (DEF, MID, FWD)

        # Transfers
        out_pids = sorted(list(current_pids - set(x_sel)))
        in_pids  = sorted(list(set(x_sel) - current_pids))

        # Metrics
        start_pts  = sum(pts[i] for i in y_sel)
        bench_pts  = sum(pts[i] for i in b_sel)
        total_cost = sum(price[i] for i in x_sel)
        start_cost = sum(price[i] for i in y_sel)
        bench_cost = sum(price[i] for i in b_sel)

        # Preds metrics (used for 'best' selection across formation loops)
        start_pts_pred  = sum(pts[i] for i in y_sel_pred)
        bench_pts_pred  = sum(pts[i] for i in b_sel_pred)

        # 1GW arrangement metrics (for printing/sorting)
        start_pts_arr   = sum(arrange_pts_by_pid[i] for i in y_sel_arr)
        bench_pts_arr   = sum(arrange_pts_by_pid[i] for i in b_sel_arr)

        points_out = sum(pts[i] for i in out_pids)
        points_in  = sum(pts[i] for i in in_pids)
        points_diff = points_in - points_out
        points_diff_pct = points_diff / (points_out + 0.1)
        budget_left = (total_current_cost + bank_m) - total_cost

        key = (start_pts_pred, -total_cost, bench_pts_pred)

        payload = {
            "formation": (DEF, MID, FWD),
            "arrangement_formation": arr_formation,
            "selected": x_sel, 
            "starting": y_sel_arr, 
            "bench": b_sel_arr,
            "out": out_pids, 
            "in": in_pids,
            "starting_points": start_pts_pred, 
            "bench_points": bench_pts_pred,
            "starting_points_arr": start_pts_arr,
            "bench_points_arr": bench_pts_arr,
            "total_cost": total_cost, 
            "starting_cost": sum(price[i] for i in y_sel_arr),
            "bench_cost": sum(price[i] for i in b_sel_arr),
            "points_out": points_out, 
            "points_in": points_in,
            "points_diff": points_diff, 
            "points_diff_pct": points_diff_pct,
            "budget_left": budget_left,
            "_df": df,
        }
        if best_key is None or key > best_key:
            best_key = key
            best = payload

    return best

# ------------------------ Reporting ------------------------ #

def write_report(entry_id: int, bank_m: float, owned_df: pd.DataFrame, k_results: Dict[int, dict], outfile: str, arrange_points_by_key=None):
    def row_str(r, pts_override=None) -> str:
        pts_val = float(pts_override) if pts_override is not None else float(r["Points"])
        return f"{r['Name']:<22} {r['Team']:<15} {r['Position']:<12} {float(r['Price']):>5.1f}  {pts_val:>6.2f}"

    lines = []
    lines.append(f"FPL Optimization (predictions CSV) for Entry {entry_id}")
    lines.append(f"Bank: {bank_m:.2f} | Current-15 CSV cost: {owned_df['Price'].sum():.2f}")
    lines.append("="*96 + "\n")

    for k in sorted(k_results.keys()):
        arr_map = None
        # Build once from any result that has arrangement; or pass it in as a param if you prefer
        # (Simplest: re-use 'arrange_points_by_key' you created in main and pass it into write_report)

        res = k_results[k]
        if not res:
            lines.append(f"Transfers: {k}\nNO FEASIBLE SOLUTION\n" + "-"*96 + "\n")
            continue

        df = res["_df"].set_index("PID")
        DEF, MID, FWD = res.get("arrangement_formation", res["formation"])
        lines.append(f"Transfers: {k}  |  Formation: {DEF}-{MID}-{FWD}")

        xi_pts    = res.get("starting_points_arr", res["starting_points"])
        bench_pts = res.get("bench_points_arr",   res["bench_points"])
        lines.append(f"Projected XI points: {xi_pts:.2f} | Bench points: {bench_pts:.2f}")

        lines.append(f"Cost used: {res['total_cost']:.2f}  (XI {res['starting_cost']:.2f} / Bench {res['bench_cost']:.2f})")

        lines.append(f"Points Out: {res['points_out']:.2f}")
        lines.append(f"Points In: {res['points_in']:.2f}")
        lines.append(f"Points Difference: {res['points_diff']:.2f}")
        lines.append(f"Points Diff %: {res['points_diff_pct']*100:.2f}%")
        lines.append(f"Budget Left: {res['budget_left']:.2f}")

        lines.append(f"\nOUT:")
        for pid in res["out"]:
            r = df.loc[pid]
            lines.append("  " + row_str(r))

        lines.append("IN:")
        for pid in res["in"]:
            r = df.loc[pid]
            lines.append("  " + row_str(r))

        lines.append(f"\nSTARTING XI:")
        for P in ["Goalkeeper", "Defender", "Midfielder", "Forward"]:
            for pid in res["starting"]:
                if df.loc[pid, "Position"] == P:
                    pts_override = None
                    if arrange_points_by_key is not None:
                        key = df.loc[pid, "key"]
                        pts_override = arrange_points_by_key.get(key, df.loc[pid, "Points"])
                    lines.append("  " + row_str(df.loc[pid], pts_override))

        lines.append("BENCH:")
        for pid in res["bench"]:
            pts_override = None
            if arrange_points_by_key is not None:
                key = df.loc[pid, "key"]
                pts_override = arrange_points_by_key.get(key, df.loc[pid, "Points"])
            lines.append("  " + row_str(df.loc[pid], pts_override))

        # Simple captain suggestion: top XI by Points
        # Captain based on arrangement (1GW) if available, else preds
        def _pts_for(pid):
            if arrange_points_by_key is not None:
                return float(arrange_points_by_key.get(df.loc[pid, "key"], df.loc[pid, "Points"]))
            return float(df.loc[pid, "Points"])

        xi_sorted = sorted(res["starting"], key=lambda pid: _pts_for(pid), reverse=True)
        if xi_sorted:
            cap = df.loc[xi_sorted[0], "Name"]
            vc  = df.loc[xi_sorted[1], "Name"] if len(xi_sorted) > 1 else None
            lines.append(f"\nSuggested (C): {cap} | (VC): {vc}")


        lines.append("-"*96 + "\n")

    text = "\n".join(lines)
    print(text)
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\nSaved: {outfile}")

# ------------------------ CLI ------------------------ #

def parse_args():
    p = argparse.ArgumentParser(description="FPL optimizer using your predictions CSV as the scoring basis.")
    p.add_argument("--entry", type=int, required=True, help="FPL entry (manager) ID")
    p.add_argument("--preds", type=str, required=True, help="Path to CSV with prediction data (Name,Price,Position,Team,Points)")
    p.add_argument(
    "--arrange", type=str, default=None,
    help="Optional 1GW CSV used only to arrange/sort the XI/bench; transfers still optimized from --preds.")
    p.add_argument("--max_transfers", type=int, default=5)
    p.add_argument("--bench_budget", type=float, default=20.0)
    p.add_argument("--max_per_team", type=int, default=3)
    p.add_argument("--formations", type=str, default="3-4-3,3-5-2,4-4-2,4-5-1,5-3-2,5-4-1,4-3-3")
    p.add_argument("--include", nargs="*", default=[])
    p.add_argument("--include_start", nargs="*", default=[])
    p.add_argument("--exclude", nargs="*", default=[])
    p.add_argument("--keep", nargs="*", default=[])
    p.add_argument("--block_add", nargs="*", default=[])
    p.add_argument("--include_teams", nargs="*", default=[])
    p.add_argument("--exclude_teams", nargs="*", default=[])
    p.add_argument("--outfile", type=str, default=None)
    p.add_argument("--solver_msg", action="store_true")
    p.add_argument("--bank", type=float, default=None, help="Override bank in millions (e.g., 2.0)")
    return p.parse_args()

def main():
    args = parse_args()

    # Parse formations
    formations = []
    for tok in args.formations.split(","):
        tok = tok.strip()
        if tok:
            DEF, MID, FWD = map(int, tok.split("-"))
            formations.append((DEF, MID, FWD))
    if not formations:
        formations = DEFAULT_FORMATIONS

    # Load FPL API data
    bootstrap = _get_json("https://fantasy.premierleague.com/api/bootstrap-static/")
    elements_api = fetch_bootstrap()
    entry_meta = fetch_entry(args.entry)
    current_event = get_current_event_id(entry_meta, bootstrap)
    picks = fetch_picks(args.entry, current_event)
    current_ids = [p["element"] for p in picks.get("picks", [])]
    if len(current_ids) != 15:
        print(f"Warning: expected 15 current picks, got {len(current_ids)}", file=sys.stderr)

    # Determine bank (in millions): precedence is --bank > API > error
    bank_m_api = None
    try:
        bank_raw = entry_meta.get("bank", None)
        if bank_raw is not None:
            bank_m_api = float(bank_raw) / 10.0
    except Exception:
        bank_m_api = None

    if args.bank is not None:
        bank_m = float(args.bank)
    elif bank_m_api is not None:
        bank_m = bank_m_api
    else:
        sys.exit(
            "Bank balance not available from API. Please rerun with --bank <amount_in_millions>, "
            "e.g., --bank 2.0"
        )

    # Load predictions CSV & map current squad
    preds_df = load_predictions_csv(args.preds)
    arrange_points_by_key = None
    if args.arrange:
        arrange_df = load_predictions_csv(args.arrange)
        arrange_points_by_key = arrange_df.set_index("key")["Points"].astype(float).to_dict()

    pool_df, owned_df, warn = map_current_ids_to_csv_rows(current_ids, elements_api, preds_df)
    for w in warn:
        print(f"NOTE: {w['Name']} ({w['Team']}): {w['note']}", file=sys.stderr)

    # Respect --keep by forcing those names into the squad
    include_names = set(args.include or [])
    include_names |= (set(args.keep or []) & set(pool_df["Name"].unique()))

    results = {}
    max_k = max(0, min(5, int(args.max_transfers)))
    for k in range(0, max_k + 1):
        res = optimize_k(
            k=k,
            pool_df=pool_df,
            owned_df=owned_df,
            bank_m=bank_m,
            formations=formations,
            max_per_team=args.max_per_team,
            bench_budget=args.bench_budget,
            include_names=include_names,
            include_start_names=set(args.include_start or []),
            exclude_names=set(args.exclude or []),
            include_teams=set(args.include_teams or []),
            exclude_teams=set(args.exclude_teams or []),
            block_add_names=set(args.block_add or []),
            solver_msg=args.solver_msg,
            arrange_points_by_key=arrange_points_by_key,
            arrange_over_formations=True,
        )
        results[k] = res

    outfile = args.outfile or f"transfer_suggestions_from_csv_{args.entry}.txt"
    write_report(args.entry, bank_m, owned_df, results, outfile, arrange_points_by_key=arrange_points_by_key)

if __name__ == "__main__":
    main()
