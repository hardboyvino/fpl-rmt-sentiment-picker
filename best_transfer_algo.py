import time

start_time = time.time()

# Import the pandas library so we can work with data
import pandas as pd

# Import the combinations function to create all possible combinations of players
from itertools import combinations

# Load the data from a file into a table called "table1"
table1 = pd.read_csv("team.csv")

# Load the data from another file into a table called "table2"
table2 = pd.read_csv("finals.csv")

# Combine team names from table1 and table2
unique_teams = set(table1["Team Name"].unique()).union(table2["Team Name"].unique())

# Create a dictionary with team names as keys and counts as zero
team_counts = {team: 0 for team in unique_teams}

# Count the number of occurrences of every team in table1 and update the dictionary
for team in table1["Team Name"]:
    team_counts[team] += 1

print(team_counts)

# Remove players already in table1 from table2
table2 = table2[~table2["Name"].isin(table1["Name"])]

# Set the number of players we want to transfer and our maximum budget
transfers = 2
max_budget = 1.8

players_not_to_remove = []  # Replace with the names of the players you don't want to remove
players_not_to_add = []  # Replace with the names of the players you don't want to add

# Remove the players we don't want to consider for removal from table1
table1 = table1[~table1["Name"].isin(players_not_to_remove)]

# Remove the players we don't want to consider for adding from table2
table2 = table2[~table2["Name"].isin(players_not_to_add)]

# Create a list of all possible combinations of players to remove from our current team
out_players = list(combinations(table1.index, transfers))

# Initialize variables to keep track of the best transfer combination and the difference in points
best_points_diff = 0
best_transfer = None
net_cost = 0

# Loop through all possible combinations of players to remove
for out_combo in out_players:
    # Filter table2 to only include players with the same position as the players being removed
    out_positions_list = sorted(table1.loc[list(out_combo)]["Position"].tolist())
    filtered_table2 = table2[table2["Position"].isin(out_positions_list)]

    # Create a list of all possible combinations of players to add to our current team
    in_players = [list(combo) for combo in combinations(filtered_table2.index, transfers)]

    # Loop through all possible combinations of players to add
    for in_combo in in_players:
        # Calculate how much money we would spend and save from these transfers
        out_cost = table1.loc[list(out_combo)]["Price"].sum()
        in_cost = table2.loc[in_combo]["Price"].sum()
        net_cost = (out_cost + max_budget) - in_cost

        # Skip this combination if we don't have enough money for it
        if net_cost < 0:
            continue

        # Get the positions of the players to add
        in_positions_list = sorted(table2.loc[in_combo]["Position"].tolist())

        # Check if the positions being removed match the positions being added
        if out_positions_list != in_positions_list:
            continue

        # Check if adding a player violates the "max 3 players from any team" rule
        updated_team_counts = team_counts.copy()
        for out_player, in_player in zip(out_combo, in_combo):
            out_team = table1.loc[out_player]["Team Name"]
            in_team = table2.loc[in_player]["Team Name"]

            updated_team_counts[out_team] -= 1
            if in_team in updated_team_counts:
                updated_team_counts[in_team] += 1
            else:
                updated_team_counts[in_team] = 1

        if all(count <= 3 for count in updated_team_counts.values()):
            out_points = table1.loc[list(out_combo)]["Points"].sum()
            in_points = table2.loc[in_combo]["Points"].sum()
            points_diff = in_points - out_points

            if points_diff > best_points_diff:
                best_points_diff = points_diff
                best_transfer = (out_combo, in_combo)

# Show the best transfer combination we found
if best_transfer is not None:
    print("Best transfer combination:")
    print("Out:", table1.loc[list(best_transfer[0])])  # Show the players we want to remove from our team
    print("In:", table2.loc[best_transfer[1]])  # Show the players we want to add to our team
    print("Points difference:", best_points_diff)  # Show the difference in points for this transfer combination
    print(f"Budget Left: {net_cost}")
else:
    print("No valid transfer combination found.")  # If no valid transfer was found, print this message

# Record end time
end_time = time.time()

# Calculate the total execution time
execution_time = end_time - start_time

# Print the execution time
print("Execution time: {:.2f} seconds".format(execution_time))
