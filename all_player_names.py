import pandas as pd


def get_all_player_names(html):
    """
    Scrape fplform.com to extract the names of all players in the English Premier League (EPL).

    This function scrapes the provided HTML content from the fplform.com website to extract the names
    of all players participating in the English Premier League (EPL). It creates a dictionary where
    player names are the keys and initial mention counts are set to 0.

    Parameters:
    html (str): The HTML content of the fplform.com website page.

    Returns:
    dict: A dictionary containing player names as keys and initial mention counts as values.
    """
    df = pd.read_html(html)[0]
    players = df["Name"].tolist()
    all_players = {player: 0 for player in players}
    sorted_players = {
        k: v
        for k, v in sorted(all_players.items(), key=lambda item: item[0], reverse=False)
    }
    return sorted_players


def get_all_players_information(driver):
    """
    Scrape fplform.com to retrieve information about all players in the English Premier League (EPL).

    This function navigates to the fplform.com website's player data page using the provided WebDriver.
    It scrapes the player data table to extract player information such as price, name, position, and team name.
    The extracted information is then saved to a CSV file named "new_merged.csv".

    Parameters:
    driver: WebDriver object used for web scraping.

    Returns:
    str: The HTML content of the fplform.com website page.
    """
    driver.get("https://www.fplform.com/fpl-player-data")
    html = driver.page_source
    df = pd.read_html(html)[0]

    # Get the desired columns from the entire table
    df = df.iloc[:, [3, 0, 1, 2]]

    # Rename columns for clarity
    df.columns = ["Price", "Name", "Position", "Team Name"]

    # # Filter out specific entry (example: "Onana" as a midfielder)
    # df = df[(df["Name"] != "Onana") | (df["Position"] != "Midfielder")]

    # Save the data to CSV
    df.to_csv("player_details.csv", index=False)

    return html
