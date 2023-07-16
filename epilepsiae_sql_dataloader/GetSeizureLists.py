import click
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os


@click.command()
@click.option(
    "--username",
    prompt="Your username",
    help="The username to login.",
    default="northeastern",
)
@click.option("--password", prompt="Your password", help="The password to login.")
def main(username, password):
    url = "https://epilepsiae.uniklinik-freiburg.de/"

    # setup selenium webdriver
    driver = (
        webdriver.Chrome()
    )  # or use .Chrome(), .Edge(), etc depending on your preference.
    driver.get(url)

    # login
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.XPATH, '//input[@type="submit"][@value="login"]').click()

    # find all anchor tags where the text has an underscore in it.
    anchors = driver.find_elements(By.TAG_NAME, "a")
    underscore_anchors = [a.text for a in anchors if "_" in a.text]

    for anchor_text in underscore_anchors:
        # navigate to "https://epilepsiae.uniklinik-freiburg.de/patients/{UNDER_TEXT}/seizurelist"
        driver.get(f"{url}patients/{anchor_text}/seizurelist")

        # wait for the page to load and get the page source
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "pre"))
        )  # assuming the raw text is inside a <pre> tag
        page_source = driver.page_source

        # create a directory for each patient if not exists
        os.makedirs(anchor_text, exist_ok=True)

        # write the page source to a file
        with open(f"{anchor_text}/seizurelist", "w") as f:
            f.write(page_source)

    driver.quit()


if __name__ == "__main__":
    main()
