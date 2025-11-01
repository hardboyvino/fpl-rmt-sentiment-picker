import os
import sys
import importlib
import pandas as pd

# --- Ensure we can import the weights modules ---
HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_DIRS = [
    HERE,
    os.path.join(HERE, "weights_modules"),
]

for d in CANDIDATE_DIRS:
    if d not in sys.path and os.path.isdir(d):
        sys.path.append(d)

from utils_2025 import wildcard_team_11, wildcard_compare_3gw_1gw, free_hit_1gw, sort_dataframe


# ----------------------------
# Weight-aware point adjuster
# ----------------------------
def adjust_points(row: pd.Series,
                  pos_weights: dict,
                  pos_effect: dict,
                  price_weights: dict,
                  price_effect: dict,
                  team_weights: dict,
                  team_effect: dict) -> float:
    base_points = float(row['Points'])

    # Position adjustment uses nested dict if available
    position = row['Position']
    pos_weight_map = pos_weights.get(position, {})
    pos_effect_map = pos_effect.get(position, {})

    # Price bracket in 0.5 steps
    price_bracket = round(float(row['Price']) * 2) / 2

    # Pull weights/effectiveness with sensible fallbacks
    pos_weight = pos_weight_map.get(price_bracket, 1.0) if isinstance(pos_weight_map, dict) else 1.0
    pos_effectiveness = pos_effect_map.get(price_bracket, 1.0) if isinstance(pos_effect_map, dict) else 1.0

    price_weight = price_weights.get(price_bracket, 0.5)
    price_effectiveness = price_effect.get(price_bracket, 1.0)

    team = row['Team']
    team_weight = team_weights.get(team, 0.5)
    team_effectiveness = team_effect.get(team, 1.0)

    adjusted_points = base_points * (
        (pos_weight * 0.5 + pos_effectiveness * 0.5) *
        (price_weight * 0.5 + price_effectiveness * 0.5) *
        (team_weight * 0.5 + team_effectiveness * 0.5)
    )
    return float(adjusted_points)


# ----------------------------
# Load weights dynamically
# ----------------------------
def load_weights(method_key: str, horizon: str):
    """
    method_key: e.g. 'blended', 'fixture_form', 'normalized'
    horizon: '1gw' or '3gw'
    returns: dict with all six weight objects
    """
    module_name = f"{method_key}_{horizon}"
    mod = importlib.import_module(module_name)
    return {
        "POS_WEIGHTS": getattr(mod, "POS_WEIGHTS"),
        "POS_EFFECTIVENESS": getattr(mod, "POS_EFFECTIVENESS"),
        "PRICE_WEIGHTS": getattr(mod, "PRICE_WEIGHTS"),
        "PRICE_EFFECTIVENESS": getattr(mod, "PRICE_EFFECTIVENESS"),
        "TEAM_WEIGHTS": getattr(mod, "TEAM_WEIGHTS"),
        "TEAM_EFFECTIVENESS": getattr(mod, "TEAM_EFFECTIVENESS"),
    }


# ----------------------------
# Runner for each method
# ----------------------------
def run_for_method(method_key: str,
                   budget: float = 100.0,
                   bench_budget: float = 20.0,
                   max_per_team: int = 3,
                   excluded_players=['Isak', 'N.Gonzalez'],
                   use_bench: bool = True,
                   formations=None):
    if formations is None:
        formations = [(3,4,3), (3,5,2), (4,4,2), (4,5,1), (5,3,2), (5,4,1), (4,3,3)]

    # Filenames for each method
    df1_path = f"{method_key}_1gw.csv"
    df3_path = f"{method_key}_3gw.csv"

    if not os.path.exists(df1_path):
        raise FileNotFoundError(f"Missing file: {df1_path}")
    if not os.path.exists(df3_path):
        raise FileNotFoundError(f"Missing file: {df3_path}")

    # Load base data
    df1 = pd.read_csv(df1_path)
    df3 = pd.read_csv(df3_path)

    # Load weights for both horizons
    w1 = load_weights(method_key, "1gw")
    w3 = load_weights(method_key, "3gw")

    # Adjust and save per-horizon dataframes
    df1['Points'] = df1.apply(lambda row: adjust_points(
        row,
        w1["POS_WEIGHTS"],
        w1["POS_EFFECTIVENESS"],
        w1["PRICE_WEIGHTS"],
        w1["PRICE_EFFECTIVENESS"],
        w1["TEAM_WEIGHTS"],
        w1["TEAM_EFFECTIVENESS"],
    ), axis=1)

    df3['Points'] = df3.apply(lambda row: adjust_points(
        row,
        w3["POS_WEIGHTS"],
        w3["POS_EFFECTIVENESS"],
        w3["PRICE_WEIGHTS"],
        w3["PRICE_EFFECTIVENESS"],
        w3["TEAM_WEIGHTS"],
        w3["TEAM_EFFECTIVENESS"],
    ), axis=1)

    # Sort
    df1 = sort_dataframe(df1)
    df3 = sort_dataframe(df3)

    # Create output folder per method
    output_dir = os.path.join("outputs", method_key)
    os.makedirs(output_dir, exist_ok=True)

    # Save adjusted CSVs
    adj1_out = os.path.join(output_dir, f"{method_key}_1gw_adjusted.csv")
    adj3_out = os.path.join(output_dir, f"{method_key}_3gw_adjusted.csv")
    df1.to_csv(adj1_out, index=False)
    df3.to_csv(adj3_out, index=False)

    # 1) Wildcard mimic (3GW select) + best arrangement for 1GW
    wildcard_compare_3gw_1gw(
        BUDGET=budget,
        df_3gw=df3,
        df_1gw=df1,
        bench_budget=bench_budget,
        formations=formations,
        max_per_team=max_per_team,
        excluded_players=excluded_players,
        use_bench=use_bench,
        outfile=os.path.join(output_dir, f"wildcard_vs_1gw__{method_key}.txt"),
    )

    # 2) Free Hit (1GW only)
    free_hit_1gw(
        BUDGET=budget,
        df_1gw=df1,
        bench_budget=bench_budget,
        formations=formations,
        max_per_team=max_per_team,
        excluded_players=excluded_players,
        use_bench=use_bench,
        outfile=os.path.join(output_dir, f"free_hit_1gw__{method_key}.txt"),
    )

    # 3) Wildcard by 3GW only
    wildcard_team_11(
        BUDGET=budget,
        df_merged=df3,
        bench_budget=bench_budget,
        formations=formations,
        max_per_team=max_per_team,
        excluded_players=excluded_players,
        use_bench=use_bench,
        outfile=os.path.join(output_dir, f"wildcard_3gw__{method_key}.txt"),
    )


# ----------------------------
# Main entry point
# ----------------------------
def main():
    methods = ["blended", "fixture_form", "normalized"]
    for m in methods:
        print(f"\n=== Running method: {m} ===")
        run_for_method(m)


if __name__ == "__main__":
    main()
