import pandas as pd
from itertools import combinations
import time

def suggest_transfers(current_team_csv, transferable_players_csv, transfers=2, budget_remaining=5.3):
    # Load the data from files
    table1 = pd.read_csv(current_team_csv)
    table2 = pd.read_csv(transferable_players_csv)

    # Prepare unique team list and counts
    unique_teams = set(table1["Team"]).union(set(table2["Team"]))
    team_counts = table1["Team"].value_counts().to_dict()
    for team in unique_teams:
        if team not in team_counts:
            team_counts[team] = 0

    # Filter out players already in the team and unwanted players
    table2 = table2[~table2["Name"].isin(table1["Name"])]
    players_not_to_remove = []  # Replace with names of players not to remove
    players_not_to_add = []  # Replace with names of players not to add
    table1 = table1[~table1["Name"].isin(players_not_to_remove)]
    table2 = table2[~table2["Name"].isin(players_not_to_add)]

    # Precompute positions for quick lookup
    position_dict1 = table1.set_index("Name")["Position"].to_dict()
    position_dict2 = table2.set_index("Name")["Position"].to_dict()

    # Generate all possible combinations of players to remove
    out_players = list(combinations(table1.index, transfers))

    # Initialize variables for the best transfer
    best_points_diff = float('-inf')
    best_transfer = None

    # Create a mapping of teams to counts in the current team
    current_team_counts = table1["Team"].value_counts().to_dict()
    for team in unique_teams:
        if team not in current_team_counts:
            current_team_counts[team] = 0

    # Iterate over each combination of players to remove
    for out_combo in out_players:
        out_positions = [position_dict1[table1.loc[idx, "Name"]] for idx in out_combo]
        out_price = sum(table1.loc[idx, "Price"] for idx in out_combo)
        out_points = sum(table1.loc[idx, "Points"] for idx in out_combo)

        # Filter table2 to include only players with matching positions
        possible_in_players = table2[table2["Position"].isin(out_positions)]

        # Generate all possible combinations of players to add
        in_players = list(combinations(possible_in_players.index, transfers))

        for in_combo in in_players:
            in_price = sum(possible_in_players.loc[idx, "Price"] for idx in in_combo)
            in_points = sum(possible_in_players.loc[idx, "Points"] for idx in in_combo)

            # Calculate the net cost and check the budget
            net_cost = (out_price + budget_remaining) - in_price
            if net_cost < 0:
                continue

            # Check position constraints
            in_positions = [position_dict2[possible_in_players.loc[idx, "Name"]] for idx in in_combo]
            if sorted(out_positions) != sorted(in_positions):
                continue

            # Check team constraints
            temp_team_counts = current_team_counts.copy()
            for idx in out_combo:
                temp_team_counts[table1.loc[idx, "Team"]] -= 1
            valid_transfer = True
            for idx in in_combo:
                team = possible_in_players.loc[idx, "Team"]
                if temp_team_counts[team] < 3:
                    temp_team_counts[team] += 1
                else:
                    valid_transfer = False
                    break

            if not valid_transfer:
                continue

            # Calculate points difference
            points_diff = in_points - out_points
            if points_diff > best_points_diff:
                best_points_diff = points_diff
                best_transfer = (out_combo, in_combo, net_cost)

    # Return the best transfer combination found
    if best_transfer:
        out_players = table1.loc[list(best_transfer[0])].to_dict(orient='records')
        in_players = table2.loc[list(best_transfer[1])].to_dict(orient='records')
        return out_players, in_players, best_points_diff, best_transfer[2]
    else:
        return None, None, None, None

start_time = time.time()

print(suggest_transfers('team copy.csv', 'transferable_players_info.csv'))

# Record end time
end_time = time.time()

# Calculate the total execution time
execution_time = end_time - start_time

# Print the execution time
print("\nExecution time: {:.2f} seconds".format(execution_time))