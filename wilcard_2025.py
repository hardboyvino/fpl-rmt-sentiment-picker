from utils_2025 import wildcard_team, wildcard_team_11, bench_team, wildcard_team_challenge
import pandas as pd

BUDGET = 81
df = pd.read_csv('transferable_players_tosin.csv')

included_players=['Haaland', 'M.Salah', 'Henderson']

# Create Wildcard Team
wildcard_team_11(BUDGET, df)