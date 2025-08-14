from utils_2025 import wildcard_team_11
import pandas as pd

# BUDGET = 81
df = pd.read_csv('transferable_players_tosin.csv')
VALID_FORMATIONS = [(3,4,3), (3,5,2), (4,4,2), (4,5,1), (5,3,2), (5,4,1), (4,3,3)]

# Example usage
best = wildcard_team_11(
    BUDGET=100.0,
    df_merged=df,          # your merged player dataframe
    bench_budget=20.0,               # reserve for the 4 bench players
    formations=VALID_FORMATIONS,     # try all allowed shapes
    # included_players=['Saka'],       # must be somewhere in the 15
    # included_starting=[],            # must be in XI (optional)
    # excluded_players=['Muniz'],      # block entirely
    # excluded_teams=['Wolves'],       # block entirely
    max_per_team=3,
    outfile='optimized_team_with_bench.txt',
)

# Check the file 'optimized_team_with_bench.txt' for the formatted printout
