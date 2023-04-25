
import time

start_time = time.time()

# Import the pandas library so we can work with data
import pandas as pd

# Import the combinations function to create all possible combinations of players
from itertools import combinations

# Load the data from a file into a table called "table1"
table1 = pd.read_csv("tosin.csv")

# Load the data from another file into a table called "table2"
table2 = pd.read_csv("final.csv")

# Set the number of players we want to transfer and our maximum budget
transfers = 1
max_budget = 2.6

# Create a list of all possible combinations of players to remove from our current team
out_players = list(combinations(table1.index, transfers))

# Create a list of all possible combinations of players to add to our current team
in_players = [list(combo) for combo in combinations(table2.index, transfers)]

# Define a function that checks if a team has too many players
def team_count_violation(team, player_indices, player_table, max_count=3):
    # Count the number of players from the team in the list of player_indices
    count = sum(player_table.loc[player_indices, 'Team Name'] == team)
    # Return True if the count is greater than the allowed maximum count
    return count > max_count

# Helper function to check if the formation is valid
def valid_formation(formation, positions):
    g, d, m, f = formation
    return positions.get('G', 0) == g and positions.get('D', 0) == d and positions.get('M', 0) == m and positions.get('F', 0) == f

# List of possible formations
possible_formations = [
    (1, 3, 4, 3),
    (1, 3, 5, 2),
    (1, 4, 3, 3),
    (1, 4, 4, 2),
    (1, 4, 5, 1),
    (1, 5, 3, 2),
    (1, 5, 4, 1)
]

# Initialize variables to keep track of the best transfer combination and the difference in points
best_points_diff = 0
best_transfer = None
net_cost = 0

# Loop through all possible combinations of players to remove
for out_combo in out_players:
    # Loop through all possible combinations of players to add
    for in_combo in in_players:
        # Check if the positions being removed match the positions being added
        out_positions_list = sorted(table1.loc[list(out_combo)]['Position'].tolist())
        in_positions_list = sorted(table2.loc[in_combo]['Position'].tolist())
        if out_positions_list != in_positions_list:
            continue

        # Count how many players we have in each position before and after the transfers
        current_positions = table1.drop(list(out_combo))['Position'].value_counts()
        new_positions = table2.loc[in_combo]['Position'].value_counts()
        updated_positions = current_positions.add(new_positions, fill_value=0)

#         # Skip this combination if any position count is above the maximum limit
#         if updated_positions['D'] > 5 or updated_positions['M'] > 5 or updated_positions['F'] > 3 or updated_positions['G'] > 2:
#             continue

        # Skip this combination if the updated positions don't match any of the allowed formations
        if not any(valid_formation(formation, updated_positions) for formation in possible_formations):
            continue

        # Calculate how much money we would spend and save from these transfers
        out_cost = table1.loc[list(out_combo)]['Price'].sum()
        in_cost = table2.loc[in_combo]['Price'].sum()
        net_cost = in_cost - out_cost - max_budget

        # Skip this combination if we don't have enough money for it
        if net_cost > 0:
            continue

        # Create a new team with the transfers to check if we have too many players from a single team
        combined_team = pd.concat([table1.drop(list(out_combo)), table2.loc[in_combo]]).reset_index(drop=True)
        team_violation = False

        # Loop through all the teams in our new team
        for team in table2['Team Name'].unique():
            # Check if we have too many players from this team
            if team_count_violation(team, combined_team.index[combined_team['Team Name'] == team], combined_team):
                team_violation = True
                break

        # Skip this combination if we have too many players from a single team
        if team_violation:
            continue

        # Calculate how many more points we would get with these transfers
        out_points = table1.loc[list(out_combo)]['Points'].sum()
        in_points = table2.loc[in_combo]['Points'].sum()
        points_diff = in_points - out_points

        # Update the best transfer combination if this one gives us more points
        if points_diff > best_points_diff:
            best_points_diff = points_diff
            best_transfer = (out_combo, in_combo)

# Show the best transfer combination we found
if best_transfer is not None:
    print("Best transfer combination:")
    print("Out:", table1.loc[best_transfer[0]])  # Show the players we want to remove from our team
    print("In:", table2.loc[best_transfer[1]])   # Show the players we want to add to our team
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
