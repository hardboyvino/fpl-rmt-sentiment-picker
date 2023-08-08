"""
Because users use all forms of spellings for each player, this file used as a repository of the different player name spellings.

This file is updated on a weekly basis to keep up with the new weird spellings.
"""
import csv


def player_name_variations(name_variation_file):
    """
    Read the player name variations from a CSV file and store them in a dictionary.

    This function reads the player name variations from the specified CSV file and creates a dictionary
    where the player's proper name is the key and the corresponding list of spelling variations is the value.
    The CSV file is expected to have two columns: the proper name in the first column and the variations
    in the second column.

    Parameters:
    name_variation_file (str): The path to the CSV file containing player name variations.

    Returns:
    dict: A dictionary where keys are player proper names and values are lists of spelling variations.
    """
    player_variations_dict = {}
    with open(name_variation_file, mode="r", encoding="utf-8") as input_file:
        reader = csv.reader(input_file)
        player_variations_dict = {rows[0]: rows[1:] for rows in reader}

    return player_variations_dict
