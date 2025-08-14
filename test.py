    # reddit = praw.Reddit(
    #     client_id="_CnliAoBAepRzqyfI-TCXA",
    #     client_secret="QcIyAG-IsoB3fL8zdJjlpyaiBxSZ1g",
    #     username="docvampirina",
    #     password="xv8wHG?nVv$W4,4",
    #     user_agent="fpl_player_selector",
    # )

    # reddit = praw.Reddit(
    #     client_id="client_id",
    #     client_secret="secret_key",
    #     username="username",
    #     password="password",
    #     user_agent="fpl_player_selector",
    # )


# serve = Service(r"C:\Users\Adeniyi Babalola\Documents\GitHub\fpl-rmt-sentiment-picker\chromedriver.exe")

# serve = Service(r"link to chromedriver")

# import pandas as pd

# df = pd.read_csv("rmt_word_counts.csv")

# df.sort_values(inplace=True, by="Unnamed: 0")

# print(df.head(30))
from utils import wildcard_team, wildcard_team_11, bench_team, wildcard_team_challenge
import pandas as pd

BUDGET = 81
# df = pd.read_csv('transferable_players_tosin.csv')
df_challenge = pd.read_csv('challenge_niyi.csv')

# included_players=['Haaland', 'M.Salah', 'Henderson']

# Create Wildcard Team
# wildcard_team_11(BUDGET, df)
# bench_team(37, df)
wildcard_team_challenge(100, df_challenge)