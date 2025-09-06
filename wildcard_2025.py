from utils_2025 import wildcard_team_11, wildcard_compare_3gw_1gw, free_hit_1gw, sort_dataframe
import pandas as pd

df1 = pd.read_csv('1gw.csv')
df3 = pd.read_csv('3gw.csv')

# Sort the dfs
df1 = sort_dataframe(df1)
df3 = sort_dataframe(df3)

VALID_FORMATIONS = [(3,4,3), (3,5,2), (4,4,2), (4,5,1), (5,3,2), (5,4,1), (4,3,3)]
# VALID_FORMATIONS = [(1,1,3), (1,2,2), (1,3,1), (2,1,2), (2,2,1), (3,1,1)]

# 1) Wildcard mimic (3GW select) + best arrangement for 1GW
wildcard_compare_3gw_1gw(
    BUDGET=100.0,
    df_3gw=df3,
    df_1gw=df1,
    bench_budget=20,
    formations=VALID_FORMATIONS,     # try all allowed shapes
    # included_players=['Saka'],       # must be somewhere in the 15
    # included_starting=[],            # must be in XI (optional)
    excluded_players=['Wan-Bissaka', 'Cunha'],      # block entirely
    # excluded_teams=['Wolves'],       # block entirely
    max_per_team=3,
    use_bench=True,
    outfile='wildcard_vs_1gw.txt',
)

# 2) Free Hit (1GW only)
free_hit_1gw(
    BUDGET=100.0,
    df_1gw=df1,
    bench_budget=20,
    formations=VALID_FORMATIONS,     # try all allowed shapes
    # included_players=['Saka'],       # must be somewhere in the 15
    # included_starting=[],            # must be in XI (optional)
    excluded_players=['Wan-Bissaka', 'Cunha'],      # block entirely
    # excluded_teams=['Wolves'],       # block entirely
    max_per_team=3,
    use_bench=True,
    outfile='free_hit_1gw.txt',
)

# 3) Wildcard by 3GW only
best = wildcard_team_11(
    BUDGET=100.0,
    df_merged=df3,          # your merged player dataframe
    bench_budget=20,               # reserve for the 4 bench players
    formations=VALID_FORMATIONS,     # try all allowed shapes
    # included_players=['Saka'],       # must be somewhere in the 15
    # included_starting=[],            # must be in XI (optional)
    excluded_players=['Wan-Bissaka', 'Cunha'],      # block entirely
    # excluded_teams=['Wolves'],       # block entirely
    max_per_team=3,
    use_bench=True,
    outfile='wildcard_3gw.txt',
    # outfile='optimized_challenge_team.txt',
)


