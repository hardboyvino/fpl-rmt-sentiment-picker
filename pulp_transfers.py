import time
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum
from pprint import pprint

start_time = time.time()

# Load the data from a file into a table called "table1"
# table1 = pd.read_csv("team_niyi.csv")
# table1 = pd.read_csv("team_joy.csv")
table1 = pd.read_csv("team_tosin.csv")
# table1 = pd.read_csv("mod_challenge_players.csv")

# Load the data from another file into a table called "transferable_players_info.csv"
# table2 = pd.read_csv("transferable_players_niyi.csv")
# table2 = pd.read_csv("transferable_players_joy.csv")
table2 = pd.read_csv("transferable_players_tosin.csv")

# Combine teams from table1 and table2
unique_teams = set(table1["Team"].unique()).union(table2["Team"].unique())

# Create a dictionary with teams as keys and counts as zero
team_counts = {team: 0 for team in unique_teams}

# Count the number of occurrences of every team in table1 and update the dictionary
for team in table1["Team"]:
    team_counts[team] += 1

# Remove players already in table1 from table2
table2 = table2[~table2["Name"].isin(table1["Name"])]

# Set the number of players we want to transfer and our maximum budget
# transfers = 1
# budget_remaining = 1.0
# budget_remaining = 0.5
budget_remaining = 3.8

players_not_to_remove = ["O'Shea"]  # Replace with the names of the players you don't want to remove
players_not_to_add = ['Tielemans', 'Butler-Oyedeji', 'G.Jesus', 'Füllkrug', 'Ferguson', 'Ings', 'Antonio']  # Replace with the names of the players you don't want to add

# Remove the players we don't want to consider for removal from table1
table1 = table1[~table1["Name"].isin(players_not_to_remove)]

# Remove the players we don't want to consider for adding from table2
table2 = table2[~table2["Name"].isin(players_not_to_add)]

# Initialize list to store all the results
all_results = []

# Loop over the number of transfers 1 to 12
for transfers in range(2, 3):

    # Initialize the problem
    prob = LpProblem("OptimalTransfers", LpMaximize)

    # Define variables for players to remove and add
    remove_vars = LpVariable.dicts("Remove", table1.index, 0, 1, cat="Binary")
    add_vars = LpVariable.dicts("Add", table2.index, 0, 1, cat="Binary")

    # Add the objective function: maximize the difference in points
    prob += lpSum(add_vars[i] * table2.loc[i, "Points"] for i in table2.index) - \
            lpSum(remove_vars[i] * table1.loc[i, "Points"] for i in table1.index)

    # Constraint: exactly 'transfers' players to be transferred out
    prob += lpSum(remove_vars[i] for i in table1.index) == transfers

    # Constraint: exactly 'transfers' players to be transferred in
    prob += lpSum(add_vars[i] for i in table2.index) == transfers

    # Constraint: total cost must not exceed available budget
    prob += lpSum(remove_vars[i] * table1.loc[i, "Price"] for i in table1.index) + budget_remaining >= \
            lpSum(add_vars[i] * table2.loc[i, "Price"] for i in table2.index)

    # Constraint: maintain position counts
    for position in table1["Position"].unique():
        prob += lpSum(remove_vars[i] for i in table1.index if table1.loc[i, "Position"] == position) == \
                lpSum(add_vars[i] for i in table2.index if table2.loc[i, "Position"] == position)

    # Add constraint to ensure no more than 3 players from any team
    for team in unique_teams:
        prob += lpSum(add_vars[i] for i in table2.index if table2.loc[i, "Team"] == team) + \
                team_counts.get(team, 0) - lpSum(remove_vars[i] for i in table1.index if table1.loc[i, "Team"] == team) <= 3

    # # Constraint: Do not remove players projected to score more than 5.5 points
    # for i in table1.index:
    #     if table1.loc[i, "Points"] >= 1:
    #         prob += remove_vars[i] == 0

    # # Constraint: Allow only transfers if there's at least a 50% gain in points
    # prob += lpSum(add_vars[i] * table2.loc[i, 'Points'] for i in table2.index) >= 1.2 * lpSum(remove_vars[i] *
    # table1.loc[i, 'Points'] for i in table1.index)

    print(table1)
    print(table2)

    # Solve the problem
    prob.solve()

    # Check and print the results
    best_transfer_out = [i for i in table1.index if remove_vars[i].varValue >= 1]
    best_transfer_in = [i for i in table2.index if add_vars[i].varValue >= 1]

    if best_transfer_out and best_transfer_in:
        result = {
            'transfers': transfers,
            'out': table1.loc[best_transfer_out],
            'in': table2.loc[best_transfer_in],
            'points_out': sum(table1.loc[best_transfer_out]['Points']),
            'points_in': sum(table2.loc[best_transfer_in]['Points']),
            'points_diff': (sum(table2.loc[best_transfer_in]['Points']) - sum(table1.loc[best_transfer_out]['Points'])) / (sum(table1.loc[best_transfer_out]['Points']) + 0.1),
            'budget_left': sum(table1.loc[best_transfer_out]["Price"]) + budget_remaining - sum(table2.loc[best_transfer_in]["Price"]),

        }
        all_results.append(result)

    else:
        result = {
            'transfers': transfers,
            'out': 'None',
            'in': 'No valid transfer combination found.',
            'points_out': 0,
            'points_in': 0,
            'points_diff': 0,
            'budget_left': 0,
        }

        all_results.append(result)

# Write results to a txt file
with open("transfer_results.txt", "w", encoding='utf-8') as file:
    for result in all_results:
        file.write(f"Transfers: {result['transfers']}\n")
        file.write(f"Out: \n{result['out']}\n")
        file.write(f"In: \n{result['in']}\n")
        file.write(f"Points Out: {result['points_out'] * 3:.2f}\n")
        file.write(f"Points In: {result['points_in'] * 3:.2f}\n")
        file.write(f"Points Difference: {(result['points_in'] - result['points_out']) * 3:.2f}\n")
        file.write(f"Points Diff %: {result['points_diff'] * 100:.2f}%\n")
        file.write(f"Budget Left: {result['budget_left']:.2f}\n")
        file.write("\n------------------------------\n")

# Record end time
end_time = time.time()

# Calculate the total execution time
execution_time = end_time - start_time

# Print the execution time
print(f"\nExecution time: {execution_time:.2f} seconds")
