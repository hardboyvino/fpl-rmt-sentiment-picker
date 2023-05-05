"""
Utility functions used in the main program.
"""
from pulp import *
import praw


def get_words_rmt_page(By, driver, filename, re, rmt_pages, unicodedata):
    """Get all the words on the pages into a string text.
    All the text are normalized
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


def get_all_comments_and_replies(post_ids, re):
    """Use PRAW, a Python wrapper for the Reddit API to get all the comments and replies for a given post

    First authenticate with Reddit account using 
    client ID, 
    client secret, 
    username, 
    password, 
    and user agent(a fancy name for your project name).

    Retrieve the post with the given ID using the reddit.submission(id='post_id') method"""

    reddit = praw.Reddit(
        client_id="your_client_id",
        client_secret="your_client_secret",
        username="your_username",
        password="your_password",
        user_agent="your_user_agent",
    )

    # Open a text file for appending
    with open("comments.txt", "a", encoding="utf-8") as file:
        # Loop through the post IDs
        for post_id in post_ids:
            # Retrieve the post with the given ID
            post = reddit.submission(id=post_id)

            # Get all the comments and their replies
            post.comments.replace_more(limit=None)

            # Loop through the comments and their replies
            for comment in post.comments.list():
                file.write(comment.body + "\n")
                for reply in comment.replies:
                    file.write(reply.body + "\n")

    with open("comments.txt", "r", encoding="utf-8") as file:
        data = file.read()
        lines = re.split(r"[^A-Za-z0-9]", data)

        # convert all the words in the list to lowercase
    all_words = [word.lower() for word in lines]

    return all_words


def count_player_occurence(all_players, all_words, Counter, pd, player_count_csv, player_var_names):
    """The various words from the rmt pages are compared to the possible player name variations
    If a variation is found, the count is updated against the proper name of the EPL player.
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
    df1 = df1.rename(columns={"Unnamed: 0": "Name", "0": "Points"})

    df2 = pd.read_csv(file2)
    df2 = df2.rename(columns={"Names": "Name", "Team": "Team Name", "Cost (£M)": "Price"})
    df2["Name"] = df2["Name"].str.strip()

    df_merged = df1.merge(df2, on="Name", how="inner")

    # df_merged = df_merged.drop(["Predict", "Predict3GW"], axis=1)
    return df_merged


def wildcard_team(BUDGET, df_merged):
    """Create a wildcard team based on the team"s money remaining.
    Selection is to maximise the player mention occurence."""
    # Create a pandas dataframe with players and their respective stats (e.g. cost, points, etc.)
    player_data = df_merged

    # Define list of excluded teams
    excluded_teams = []

    # Define list of excluded players
    excluded_players = []

    with open('optimized_team.txt', 'w', encoding="utf-8") as f:
        for DEF in [3, 4, 5]:
            for MID in [3, 4, 5]:
                for FWD in [1, 2, 3]:
                    if DEF + MID + FWD == 10:
                        # Set up optimization problem
                        model = LpProblem("FPL Optimization", LpMaximize)

                        # Define decision variables
                        players = list(player_data['Name'])
                        x = LpVariable.dicts("x", players, cat='Binary')

                        # Define objective function
                        model += lpSum([player_data.loc[i, 'Points'] * x[player_data.loc[i, 'Name']] for i in range(len(player_data))])

                        # Add constraints
                        model += lpSum([player_data.loc[i, 'Price'] * x[player_data.loc[i, 'Name']] for i in range(len(player_data))]) <= BUDGET # Total budget constraint
                        model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data))]) == 11 # Squad size constraint
                        model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'G']) == 1 # GK position constraint
                        model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'D']) == DEF # DEF position constraint
                        model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'M']) == MID # MID position constraint
                        model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'F']) == FWD # FWD position constraint

                        # existing_team_dfdd constraint to limit the number of players from each Premier League team to at most 3
                        prem_teams = player_data['Team Name'].unique()
                        for team in prem_teams:
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Team Name'] == team]) <= 3
                        
                        # Add constraint to set decision variables for players in excluded teams to 0
                        for i in range(len(player_data)):
                            if player_data.loc[i, 'Team Name'] in excluded_teams:
                                model += x[player_data.loc[i, 'Name']] == 0

                        # Add constraint to set decision variables for excluded players to 0
                        for i in range(len(player_data)):
                            if player_data.loc[i, 'Name'] in excluded_players:
                                model += x[player_data.loc[i, 'Name']] == 0

                        # Solve optimization problem
                        model.solve()

                        # Output optimized team to text file
                        f.write("Optimized FPL Team:\n")
                        f.write(f"{DEF} - {MID} - {FWD}\n")
                        for i in range(len(player_data)):
                            if x[player_data.loc[i, 'Name']].value() == 1:
                                f.write(f"{player_data.loc[i, 'Name']} {player_data.loc[i, 'Team Name']} {player_data.loc[i, 'Position']} {player_data.loc[i, 'Price']} {player_data.loc[i, 'Points']}\n")
                        f.write(f"Total points: {value(model.objective)}\n")
                        f.write("\n")
