"""
Utility functions used in the main program.
"""

def get_words_rmt_page(By, driver, filename, re, rmt_pages,unicodedata):
    """Get all the words on the pages into a string text.\n
    All the text are normalized\n
    The text are written into a file and then read to split each word as a new line using regex"""
    for page in rmt_pages:
        driver.get(page)

        # get all the text on the entire page
        rmt_page = driver.find_element(By.XPATH, "/html/body").text

        # normalise the text
        rmt_page = unicodedata.normalize("NFKD", rmt_page).encode("ascii", "ignore").decode("ascii")

        # write all the text into a textfile
        with open(filename, "a") as f:
            f.write(rmt_page)

    # read the text file and split all the words into individual words in a list
    with open(filename, "r") as file:
        data = file.read()
        lines = re.split(r"[^A-Za-z0-9]", data)

    # convert all the words in the list to lowercase
    all_words = [word.lower() for word in lines]

    return all_words