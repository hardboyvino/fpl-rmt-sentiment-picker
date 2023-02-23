from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from collections import Counter
import pandas as pd
import re

from player_name_variations import player_name_vars
from all_player_names import get_all_player_names
from utils import count_player_occurence, get_all_comments_and_replies, merge_dfs, wildcard_team
from rmt_page_links import post_ids_25

rmt_page_text = "rmt.txt"
player_count_csv = "players.csv"
file1 = "players.csv"
file2 = "Random Regression.csv"
BUDGET = 83.3

files = ["rmt.csv", player_count_csv, file1, "comments.txt", "optimized_team.txt"]

# open all the web addresses in headless mode so it does not open a browser tab for the program
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")

serve = Service(r"path-to-chromedriver")
driver = webdriver.Chrome(options=options, service=serve)

for f in files:
    # open a new rmt.txt file and if it exists, wipe it clean; then close it
    new_file = open(f, "w")
    new_file.close()


all_players = get_all_player_names(driver, pd)

# import all the various player name variations
player_var_names = player_name_vars()

# get all words
all_words = get_all_comments_and_replies(post_ids_25, re)

# count the number of times a player name was mentioned
count_player_occurence(all_players, all_words, Counter, pd, player_count_csv, player_var_names)

# get wildcard team
df_merged = merge_dfs(file1, file2, pd)
wildcard_team(BUDGET, df_merged)
