import time
import pandas as pd
from itertools import combinations

start_time = time.time()

# Load the data from a file into a table called "table1"
table1 = pd.read_csv("team.csv")

# Load the data from another file into a table called "table2"
table2 = pd.read_csv("transferable_players_info.csv")

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
transfers = 1
budget_remaining = 7.5

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

# Convert out_players to a set for faster membership checks
out_players_set = set(out_players)

# Recursive function to generate all possible combinations of players to add
def generate_in_players(combo, start_index, in_players):
    if len(combo) == transfers:
        in_players.append(combo)
        return
    for i in range(start_index, len(table2.index)):
        generate_in_players(combo + [table2.index[i]], i + 1, in_players)

# Loop through all possible combinations of players to remove
for out_combo in out_players:
    # Filter table2 to only include players with the same position as the players being removed
    out_positions_set = set(table1.loc[list(out_combo)]["Position"])
    filtered_table2 = table2[table2["Position"].isin(out_positions_set)]

    # Create a list of all possible combinations of players to add to our current team
    in_players = []
    generate_in_players([], 0, in_players)

    # Loop through all possible combinations of players to add
    for in_combo in in_players:
        # Calculate the net cost of the transfers
        net_cost = (sum(table1.loc[list(out_combo)]["Price"]) + budget_remaining) - sum(table2.loc[in_combo]["Price"])

        # Skip this combination if we don't have enough money for it
        if net_cost < 0:
            continue

        # Get the positions of the players to add
        in_positions_set = set(table2.loc[in_combo]["Position"])

        # Check if the positions being removed match the positions being added
        if out_positions_set != in_positions_set:
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
            out_points = sum(table1.loc[list(out_combo)]["Points"])
            in_points = sum(table2.loc[in_combo]["Points"])
            points_diff = in_points - out_points

            if points_diff > best_points_diff:
                best_points_diff = points_diff
                best_transfer = (out_combo, in_combo)


# Show the best transfer combination we found
if best_transfer is not None:
    print("\nBest transfer combination:")
    print("\nOut:", table1.loc[list(best_transfer[0])])  # Show the players we want to remove from our team
    print("\nIn:", table2.loc[best_transfer[1]])  # Show the players we want to add to our team
    print("\nPoints difference:", best_points_diff)  # Show the difference in points for this transfer combination
    out_cost = sum(table1.loc[list(best_transfer[0])]["Price"])
    in_cost = sum(table2.loc[best_transfer[1]]["Price"])
    net_cost = (out_cost + budget_remaining) - in_cost
    print(f"Budget Left: {net_cost}")
else:
    print("No valid transfer combination found.")  # If no valid transfer was found, print this message

# Record end time
end_time = time.time()

# Calculate the total execution time
execution_time = end_time - start_time

# Print the execution time
print("\nExecution time: {:.2f} seconds".format(execution_time))