"""
Get all the EPL Player names from fplform.com.

There is a helpful table that has all the player names as the first column.
"""


def get_all_player_names(driver, pd):
    """Scrape fplform.com for the names of all players in FPL"""
    # go to this site because they have a cool table with all players and some data
    driver.get("https://www.fplform.com/fpl-player-data")

    html = driver.page_source

    # get the first (only) table on the page
    df = pd.read_html(html)
    df = df[0]

    # create a list with all the player names
    players = (df.loc[:, "Name"]).tolist()

    # create a dictionary with all football players and initial count of [], using the player names list
    all_players = {}
    for player in players:
        all_players[player] = 0

    return all_players
