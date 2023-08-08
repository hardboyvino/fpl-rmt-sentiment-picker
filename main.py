from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from chromedriver_py import binary_path
import pandas as pd
from player_name_variations import player_name_variations
from all_player_names import get_all_player_names, get_all_players_information
from utils import (
    get_all_comments_and_replies,
    merge_dfs,
    wildcard_team,
    count_rmt_word_occurence,
    count_player_fpl_occurence,
    add_new_players_to_variation,
)
from rmt_page_links import preseason

# File Paths and Constants
rmt_word_count_file = "rmt_word_counts.csv"
player_mentions_csv = "players_mentions.csv"
player_name_variations_file = "player_name_variations.csv"
player_details_csv = "player_details.csv"
reddit_comments_file = "reddit_comments.txt"
optimized_team_file = "optimized_team.txt"
BUDGET = 83.0
files = [rmt_word_count_file, player_mentions_csv, reddit_comments_file, optimized_team_file]

# Set Up Selenium WebDriver
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")

service = Service(binary_path)
driver = webdriver.Chrome(options=options, service=service)

# Clear Contents of Files
for file in files:
    new_file = open(file, "w")
    new_file.close()

# Get Player Information
html = get_all_players_information(driver)
player_mention_counts = get_all_player_names(html)

# Load Player Name Variations
player_name_variations_dict = player_name_variations(player_name_variations_file)

# Add New Players to Variations
player_name_variations_dict = add_new_players_to_variation(player_mention_counts, player_name_variations_dict)
player_name_variations_dict = {k: v for k, v in sorted(player_name_variations_dict.items(), key=lambda item: item[0], reverse=False)}

# Update Player Variation File
player_name_variations_df = pd.Series(player_name_variations_dict)
player_name_variations_df.to_csv(player_name_variations_file, header=None)

# Load Comments and Replies
rmt_words_list = get_all_comments_and_replies(preseason, reddit_comments_file)

# Count Word Occurrences in Comments
word_counts_df = count_rmt_word_occurence(rmt_words_list, rmt_word_count_file)
word_counts_df.pop("")

# Count Player FPL Mentions
count_player_fpl_occurence(player_mention_counts, player_mentions_csv, player_name_variations_dict, word_counts_df)

# Merge DataFrames
merged_player_details_df = merge_dfs(player_mentions_csv, player_details_csv)

# Create Wildcard Team
wildcard_team(BUDGET, merged_player_details_df)

# Save Final DataFrame
merged_player_details_df.to_csv("complete_player_info.csv", index=False)
