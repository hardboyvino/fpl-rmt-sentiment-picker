"""
Utility functions used in the main program.
"""
from pulp import *

def get_words_rmt_page(By, driver, filename, re, rmt_pages, unicodedata):
    """Get all the words on the pages into a string text.\n
    All the text are normalized\n
    The text are written into a file and then read to split each word as a new line using regex"""
    for page in rmt_pages:
        driver.get(page)

        # get all the text on the entire page
        rmt_page = driver.find_element(By.XPATH, "/html/body").text

        # normalise the text
        rmt_page = unicodedata.normalize("NFKD", rmt_page).encode("ascii", "ignore").decode("ascii")

        # write all the text into a textfile
        with open(filename, "a") as f:
            f.write(rmt_page)

    # read the text file and split all the words into individual words in a list
    with open(filename, "r") as file:
        data = file.read()
        lines = re.split(r"[^A-Za-z0-9]", data)

    # convert all the words in the list to lowercase
    all_words = [word.lower() for word in lines]

    return all_words


def count_player_occurence(all_players, all_words, Counter, pd, player_count_csv, player_var_names):
    """The various words from the rmt pages are compared to the possible player name variations\n
    If a variation is found, the count is updated against the proper name of the EPL player.\n
    Player names are counted and arranged in descending order, returned as a CSV file"""

    # count how many times each word occures in the all_words list
    count = Counter(all_words)

    df = pd.Series(count)
    df.to_csv("rmt.csv")

    for k, v in player_var_names.items():
        for key, value in count.items():
            if key in v:
                try:
                    all_players[k] += value
                except KeyError:
                    all_players[k] = 1

    all_players = {k: v for k, v in sorted(all_players.items(), key=lambda item: item[1], reverse=True)}

    df = pd.Series(all_players)
    df.to_csv(player_count_csv)


def merge_dfs(file1, file2, pd):
    """Merge the players file and the complete scrape from FFHub website."""
    import pandas as pd

    df1 = pd.read_csv(file1)
    df1 = df1.rename(columns={"": "Player", "0": "Points"})

    df2 = pd.read_csv(file2)
    df2 = df2.rename(columns={"Name": "Player", "Team Name": "Team", "Price": "Cost"})
    df2["Player"] = df2["Player"].str.strip()

    df_merged = df1.merge(df2, on="Player", how="inner")

    df_merged = df_merged.drop(["Predict", "Predict3GW"], axis=1)
    return df_merged


def wildcard_team(BUDGET, df_merged):
    """Create a wildcard team based on the team"s money remaining.\n
    Selection is to maximise the player mention occurence."""
    # Create a pandas dataframe with players and their respective stats (e.g. cost, points, etc.)
    player_data = df_merged

    # Set up optimization problem
    model = LpProblem("FPL Optimization", LpMaximize)

    # Define decision variables
    players = list(player_data["Player"])
    x = LpVariable.dicts("x", players, cat="Binary")

    # Define objective function
    model += lpSum([player_data.loc[i, "Points"] * x[player_data.loc[i, "Player"]] for i in range(len(player_data))])

    # Add constraints
    model += lpSum([player_data.loc[i, "Cost"] * x[player_data.loc[i, "Player"]] for i in range(len(player_data))]) <= BUDGET # Total budget constraint
    model += lpSum([x[player_data.loc[i, "Player"]] for i in range(len(player_data))]) == 11 # Squad size constraint
    model += lpSum([x[player_data.loc[i, "Player"]] for i in range(len(player_data)) if player_data.loc[i, "Position"] == "G"]) == 1 # GK position constraint
    model += lpSum([x[player_data.loc[i, "Player"]] for i in range(len(player_data)) if player_data.loc[i, "Position"] == "D"]) == 3 # DEF position constraint
    model += lpSum([x[player_data.loc[i, "Player"]] for i in range(len(player_data)) if player_data.loc[i, "Position"] == "M"]) == 5 # MID position constraint
    model += lpSum([x[player_data.loc[i, "Player"]] for i in range(len(player_data)) if player_data.loc[i, "Position"] == "F"]) == 2 # FWD position constraint

    # Add constraint to limit the number of players from each Premier League team to at most 3
    prem_teams = player_data["Team"].unique()
    for team in prem_teams:
        model += lpSum([x[player_data.loc[i, "Player"]] for i in range(len(player_data)) if player_data.loc[i, "Team"] == team]) <= 3

    # Solve optimization problem
    model.solve()

    # Print optimized team
    print("Optimized FPL Team:")
    for i in range(len(player_data)):
        if x[player_data.loc[i, "Player"]].value() == 1:
            print(player_data.loc[i, "Player"], player_data.loc[i, "Team"], player_data.loc[i, "Position"], player_data.loc[i, "Cost"], player_data.loc[i, "Points"], player_data.loc[i, "Team"])
