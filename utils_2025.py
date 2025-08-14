"""
Utility functions used in the main program.
"""
from pulp import *
import praw
import prawcore
import time
from collections import Counter
import pandas as pd
import re


def get_words_rmt_page(By, driver, filename, rmt_pages, unicodedata):
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
    rmt_words_list = [word.lower() for word in lines]

    return rmt_words_list


def get_all_comments_and_replies(post_ids, filename):
    """Use PRAW, a Python wrapper for the Reddit API to get all the comments and replies for a given post

    First authenticate with Reddit account using 
    client ID, 
    client secret, 
    username, 
    password, 
    and user agent(a fancy name for your project name).

    Retrieve the post with the given ID using the reddit.submission(id='post_id') method"""

    reddit = praw.Reddit(
        client_id="_CnliAoBAepRzqyfI-TCXA",
        client_secret="QcIyAG-IsoB3fL8zdJjlpyaiBxSZ1g",
        username="docvampirina",
        password="xv8wHG?nVv$W4,4",
        user_agent="fpl_player_selector",
    )

    while post_ids:
        try:
            # Open a text file for appending
            with open(filename, "a", encoding="utf-8") as file:
                # Loop through the post IDs
                for post_id in post_ids:
                    print(f"Starting {post_id} from {post_ids}.")
                    # Retrieve the post with the given ID
                    post = reddit.submission(id=post_id)

                    # Get all the comments and their replies
                    post.comments.replace_more(limit=None)

                    # Loop through the comments and their replies
                    for comment in post.comments.list():
                        file.write(comment.body + "\n")
                        for reply in comment.replies:
                            file.write(reply.body + "\n")
                    
                    print(f"Done going through {post_id} and now sleeping for 30 seconds!")
                    post_ids.remove(post_id)
                    time.sleep(30)


        except prawcore.exceptions.TooManyRequests as e:
            print(f"Rate limit exceeded. Sleeping for 30 seconds.")
            time.sleep(30)


def get_word_list_from_comments(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = file.read()
        lines = re.split(r"[^A-Za-z0-9]", data)

    # convert all the words in the list to lowercase
    rmt_words_list = [word.lower() for word in lines]

    return rmt_words_list


def count_rmt_word_occurence(rmt_words_list, rmt_word_count_file):
    """Count how many times each words from RMT comments occurs and turns the data into a CSV"""

    # count how many times each word occures in the rmt_words_list list
    count = Counter(rmt_words_list)

    df = pd.Series(count)
    df = df.sort_index()
    df.to_csv(rmt_word_count_file)

    return count

def count_player_fpl_occurence(all_players, player_count_csv, player_var_names, count, unavailable, chance_25_percent, chance_50_percent, chance_75_percent):
    """The various words from the rmt pages are compared to the possible player name variations
    If a variation is found, the count is updated against the proper name of the EPL player.
    Player names are counted and arranged in descending order, returned as a CSV file"""
    for k, v in player_var_names.items():
        v_stripped = v.strip("[]").split(',')
        v = [item.strip(" '") for item in v_stripped]
        for key, value in count.items():
            if key in v:
                try:
                    all_players[k] += value
                except KeyError:
                    all_players[k] = 1

        # If the player is injured or a doubt, reduce their value accordingly
        if k in unavailable:
            all_players[k] = 0
        elif k in chance_25_percent:
            all_players[k] *= 0.25
        elif k in chance_50_percent:
            all_players[k] *= 0.5
        elif k in chance_75_percent:
            all_players[k] *= 0.75

    all_players = {k: v for k, v in sorted(all_players.items(), key=lambda item: item[1], reverse=True)}

    df = pd.Series(all_players)
    df.to_csv(player_count_csv)

def add_new_players_to_variation(all_players, player_var):
    print("\nThe new players added are: ")
    for key in all_players.keys():
        if key not in list(player_var.keys()):
            print(key)
            player_var[key] = []

    print()
    return player_var

def merge_dfs(file1, file2):
    """Merge the players file and the complete scrape from FFHub website."""
    df1 = pd.read_csv(file1)
    df1 = df1.rename(columns={"Unnamed: 0": "Name", "0": "Points"})

    df2 = pd.read_csv(file2)
    # df2 = df2.rename(columns={"Names": "Name", "Team": "Team", "Cost (£M)": "Price"})
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
    excluded_players = ['Chilwell', 'Olsen', 'Ramsdale', 'Flekken', 'Strakosha', 'Robertson', 'Awoniyi']

    with open('optimized_team.txt', 'w', encoding="utf-8") as f:
        for DEF in [3, 4, 5]:
            for MID in [3, 4, 5]:
                for FWD in [1, 2, 3]:
        # for DEF in [5]:
        #     for MID in [5]:
        #         for FWD in [3]:
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
                        model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data))]) == 10 # Squad size constraint
                        model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Goalkeeper']) == 0 # GK position constraint
                        model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Defender']) == DEF # DEF position constraint
                        model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Midfielder']) == MID # MID position constraint
                        model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Forward']) == FWD # FWD position constraint

                        # existing_team_dfdd constraint to limit the number of players from each Premier League team to at most 3
                        prem_teams = player_data['Team'].unique()
                        for team in prem_teams:
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Team'] == team]) <= 3
                        
                        # Add constraint to set decision variables for players in excluded teams to 0
                        for i in range(len(player_data)):
                            if player_data.loc[i, 'Team'] in excluded_teams:
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
                        f.write(f"{'Name':<25}{'Team':<15}{'Position':<15}{'Price':<10}{'Points':<10}\n")
                        f.write('-' * 75 + '\n')  # Drawing a line for clarity

                        for i in range(len(player_data)):
                            if x[player_data.loc[i, 'Name']].value() == 1:
                                f.write(f"{player_data.loc[i, 'Name']:<25}{player_data.loc[i, 'Team']:<15}{player_data.loc[i, 'Position']:<15}{player_data.loc[i, 'Price']:<10}{player_data.loc[i, 'Points']:<10}\n")

                        f.write('-' * 75 + '\n')  # Drawing another line
                        f.write(f"Total points: {value(model.objective):.2f}\n")
                        f.write("\n")


def wildcard_team_11(BUDGET, df_merged, included_teams=None, included_players=None):
    """Create a wildcard team based on the team"s money remaining.
    Selection is to maximise the player mention occurence."""
    # Create a pandas dataframe with players and their respective stats (e.g. cost, points, etc.)
    player_data = df_merged

    # Define list of excluded teams
    excluded_teams = []

    # Define list of excluded players
    # excluded_players = ['Guéhi', 'Cash', 'Kelleher', 'Ederson M.', 'Colwill', 'Digne']
    excluded_players = ['Sarabia', 'Muniz', 'Schär', 'João Pedro']

    # Initialize the list of included players if not provided
    if included_players is None:
        included_players = []

    with open('optimized_team.txt', 'w', encoding="utf-8") as f:
        for GK in [1]:
            for DEF in [3, 4, 5]:
                for MID in [3, 4, 5]:
                    for FWD in [1, 2, 3]:
                        if GK + DEF + MID + FWD == 11:
                            # Set up optimization problem
                            model = LpProblem("FPL Optimization", LpMaximize)

                            # Define decision variables
                            players = list(player_data['Name'])
                            x = LpVariable.dicts("x", players, cat='Binary')

                            # Define objective function
                            model += lpSum([player_data.loc[i, 'Points'] * x[player_data.loc[i, 'Name']] for i in range(len(player_data))])

                            # Add constraints
                            model += lpSum([player_data.loc[i, 'Price'] * x[player_data.loc[i, 'Name']] for i in range(len(player_data))]) <= BUDGET  # Total budget constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data))]) == 11  # Squad size constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Goalkeeper']) == GK  # GK position constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Defender']) == DEF  # DEF position constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Midfielder']) == MID  # MID position constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Forward']) == FWD  # FWD position constraint

                            # No limit to how many players from a team
                            prem_teams = player_data['Team'].unique()
                            for team in prem_teams:
                                model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Team'] == team]) <= 3

                            # Add constraint to set decision variables for players in excluded teams to 0
                            if included_teams:
                                for i in range(len(player_data)):
                                    if player_data.loc[i, 'Team'] not in included_teams:
                                        model += x[player_data.loc[i, 'Name']] == 0
                            else:
                                for i in range(len(player_data)):
                                    if player_data.loc[i, 'Team'] in excluded_teams:
                                        model += x[player_data.loc[i, 'Name']] == 0

                            # Add constraint to set decision variables for excluded players to 0
                            for i in range(len(player_data)):
                                if player_data.loc[i, 'Name'] in excluded_players:
                                    model += x[player_data.loc[i, 'Name']] == 0

                            # Add constraint to include specific players
                            for i in range(len(player_data)):
                                if player_data.loc[i, 'Name'] in included_players:
                                    model += x[player_data.loc[i, 'Name']] == 1

                            # Solve optimization problem
                            model.solve()

                            # Calculate total budget used
                            total_budget_used = sum(player_data.loc[i, 'Price'] for i in range(len(player_data)) if x[player_data.loc[i, 'Name']].value() == 1)

                            # Output optimized team to text file
                            f.write("Optimized FPL Team:\n")
                            f.write(f"{DEF} - {MID} - {FWD}\n")
                            f.write(f"{'Name':<25}{'Team':<15}{'Position':<15}{'Price':<10}{'Points':<10}\n")
                            f.write('-' * 75 + '\n')  # Drawing a line for clarity

                            for i in range(len(player_data)):
                                if x[player_data.loc[i, 'Name']].value() == 1:
                                    f.write(f"{player_data.loc[i, 'Name']:<25}{player_data.loc[i, 'Team']:<15}{player_data.loc[i, 'Position']:<15}{player_data.loc[i, 'Price']:<10}{player_data.loc[i, 'Points']:<10}\n")

                            f.write('-' * 75 + '\n')  # Drawing another line
                            f.write(f"Total points: {value(model.objective):.2f}\n")
                            f.write(f"Total budget used: {total_budget_used:.2f}\n")
                            f.write("\n")



def bench_team(BUDGET, df_merged):
    """Create a bench team based on the team"s money remaining.
    Selection is to maximise the player mention occurence."""
    # Create a pandas dataframe with players and their respective stats (e.g. cost, points, etc.)
    player_data = df_merged

    # Define list of excluded teams
    # excluded_teams = ['Liverpool', 'Man City', 'Arsenal', 'Spurs', 'Man Utd', 'Chelsea', 'Sheffield Utd', 'Luton', 'Burnley']
    excluded_teams = ['Wolves', 'Newcastle']

    # Define list of excluded players
    excluded_players = ['Virgil', 'Luis Díaz', 'João Pedro', 'Evanilson', 'Iwobi', 'Sessegnon', 'Muniz', 'Bradley']

    with open('optimized_bench_team.txt', 'w', encoding="utf-8") as f:
        for GK in [1]:
            for DEF in [0, 1, 2]:
                for MID in [0, 1, 2]:
                    for FWD in [0, 1, 2]:
                        if GK + DEF + MID + FWD == 4:
                            # Set up optimization problem
                            model = LpProblem("FPL Optimization", LpMaximize)

                            # Define decision variables
                            players = list(player_data['Name'])
                            x = LpVariable.dicts("x", players, cat='Binary')

                            # Define objective function
                            model += lpSum([player_data.loc[i, 'Points'] * x[player_data.loc[i, 'Name']] for i in range(len(player_data))])

                            # Add constraints
                            model += lpSum([player_data.loc[i, 'Price'] * x[player_data.loc[i, 'Name']] for i in range(len(player_data))]) <= BUDGET # Total budget constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data))]) == 4 # Squad size constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Goalkeeper']) == GK # GK position constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Defender']) == DEF # DEF position constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Midfielder']) == MID # MID position constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Forward']) == FWD # FWD position constraint

                            # existing_team_dfdd constraint to limit the number of players from each Premier League team to at most 3
                            prem_teams = player_data['Team'].unique()
                            for team in prem_teams:
                                model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Team'] == team]) <= 1
                            
                            # Add constraint to set decision variables for players in excluded teams to 0
                            for i in range(len(player_data)):
                                if player_data.loc[i, 'Team'] in excluded_teams:
                                    model += x[player_data.loc[i, 'Name']] == 0

                            # Add constraint to set decision variables for excluded players to 0
                            for i in range(len(player_data)):
                                if player_data.loc[i, 'Name'] in excluded_players:
                                    model += x[player_data.loc[i, 'Name']] == 0

                            # Solve optimization problem
                            model.solve()

                            # Calculate total budget used
                            total_budget_used = sum(player_data.loc[i, 'Price'] for i in range(len(player_data)) if x[player_data.loc[i, 'Name']].value() == 1)

                            # Output optimized team to text file
                            f.write("Optimized FPL Team:\n")
                            f.write(f"{DEF} - {MID} - {FWD}\n")
                            f.write(f"{'Name':<25}{'Team':<15}{'Position':<15}{'Price':<10}{'Points':<10}\n")
                            f.write('-' * 75 + '\n')  # Drawing a line for clarity

                            for i in range(len(player_data)):
                                if x[player_data.loc[i, 'Name']].value() == 1:
                                    f.write(f"{player_data.loc[i, 'Name']:<25}{player_data.loc[i, 'Team']:<15}{player_data.loc[i, 'Position']:<15}{player_data.loc[i, 'Price']:<10}{player_data.loc[i, 'Points']:<10}\n")

                            f.write('-' * 75 + '\n')  # Drawing another line
                            f.write(f"Total points: {value(model.objective):.2f}\n")
                            f.write(f"Total budget used: {total_budget_used:.2f}\n")
                            f.write("\n")


def wildcard_team_challenge(BUDGET, df_merged, included_teams=None, included_players=None):
    """Create a wildcard team based on the team's money remaining.
    Selection is to maximize the player mention occurrence and allows selection from specific teams."""
    
    # Create a pandas dataframe with players and their respective stats (e.g. cost, points, etc.)
    player_data = df_merged

    # Define list of excluded teams
    excluded_teams = []

    # Define list of excluded players
    excluded_players = []

    # Initialize the list of included players if not provided
    if included_players is None:
        included_players = []

    with open('optimized_team_challenge.txt', 'w', encoding="utf-8") as f:
        for GK in [1]:
            for DEF in [1, 2]:
                for MID in [1, 2]:
                    for FWD in [1, 2]:
                        if GK + DEF + MID + FWD == 5:
                            # Set up optimization problem
                            model = LpProblem("FPL Optimization", LpMaximize)

                            # Define decision variables
                            players = list(player_data['Name'])
                            x = LpVariable.dicts("x", players, cat='Binary')

                            # Define objective function
                            model += lpSum([player_data.loc[i, 'Points'] * x[player_data.loc[i, 'Name']] for i in range(len(player_data))])

                            # Add constraints
                            model += lpSum([player_data.loc[i, 'Price'] * x[player_data.loc[i, 'Name']] for i in range(len(player_data))]) <= BUDGET  # Total budget constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data))]) == 5  # Squad size constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Goalkeeper']) == GK  # GK position constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Defender']) == DEF  # DEF position constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Midfielder']) == MID  # MID position constraint
                            model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Position'] == 'Forward']) == FWD  # FWD position constraint

                            # No limit to how many players from a team
                            prem_teams = player_data['Team'].unique()
                            for team in prem_teams:
                                model += lpSum([x[player_data.loc[i, 'Name']] for i in range(len(player_data)) if player_data.loc[i, 'Team'] == team]) <= 5

                            # Add constraint to set decision variables for players in excluded teams to 0
                            if included_teams:
                                for i in range(len(player_data)):
                                    if player_data.loc[i, 'Team'] not in included_teams:
                                        model += x[player_data.loc[i, 'Name']] == 0
                            else:
                                for i in range(len(player_data)):
                                    if player_data.loc[i, 'Team'] in excluded_teams:
                                        model += x[player_data.loc[i, 'Name']] == 0

                            # Add constraint to set decision variables for excluded players to 0
                            for i in range(len(player_data)):
                                if player_data.loc[i, 'Name'] in excluded_players:
                                    model += x[player_data.loc[i, 'Name']] == 0

                            # Add constraint to include specific players
                            for i in range(len(player_data)):
                                if player_data.loc[i, 'Name'] in included_players:
                                    model += x[player_data.loc[i, 'Name']] == 1

                            # Solve optimization problem
                            model.solve()

                            # Calculate total budget used
                            total_budget_used = sum(player_data.loc[i, 'Price'] for i in range(len(player_data)) if x[player_data.loc[i, 'Name']].value() == 1)

                            # Output optimized team to text file
                            f.write("Optimized FPL Team:\n")
                            f.write(f"{DEF} - {MID} - {FWD}\n")
                            f.write(f"{'Name':<25}{'Team':<15}{'Position':<15}{'Price':<10}{'Points':<10}\n")
                            f.write('-' * 75 + '\n')  # Drawing a line for clarity

                            for i in range(len(player_data)):
                                if x[player_data.loc[i, 'Name']].value() == 1:
                                    f.write(f"{player_data.loc[i, 'Name']:<25}{player_data.loc[i, 'Team']:<15}{player_data.loc[i, 'Position']:<15}{player_data.loc[i, 'Price']:<10}{player_data.loc[i, 'Points']:<10}\n")

                            f.write('-' * 75 + '\n')  # Drawing another line
                            f.write(f"Total points: {value(model.objective):.2f}\n")
                            f.write(f"Total budget used: {total_budget_used:.2f}\n")
                            f.write("\n")
