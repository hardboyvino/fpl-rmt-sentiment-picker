from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from collections import Counter
import pandas as pd
import re
import unicodedata

from player_name_variations import player_name_vars
from all_player_names import get_all_player_names
from utils import get_words_rmt_page, count_player_occurence
from rmt_page_links import gw23

rmt_page_text = "rmt.txt"
player_count_csv = "players.csv"

# open all the web addresses in headless mode so it does not open a browser tab for the program
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")

serve = Service(chromedriver.exe)
driver = webdriver.Chrome(options=options, service=serve)

# open a new rmt.txt file and if it exists, wipe it clean; then close it
new_file = open(rmt_page_text, "w")
new_file.close()


all_players = get_all_player_names(driver, pd)

# import all the various player name variations
player_var_names = player_name_vars()

# go to all the reddit rmt pages
rmt_pages = gw23

# get all the words on the rmt pages
all_words = get_words_rmt_page(By, driver, rmt_page_text, re, rmt_pages, unicodedata)

# count the number of times a player name was mentioned
count_player_occurence(all_players, all_words, Counter, pd, player_count_csv, player_var_names)
