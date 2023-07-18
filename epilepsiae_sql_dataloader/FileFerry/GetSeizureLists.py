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
@click.option(
    "--packages",
    multiple=True,
    default=["inv_30", "PA_inv", "comp", "surf_30"],
    help="List of packages to download data for.",
)
def main(username, password, packages):
    base_url = "https://epilepsiae.uniklinik-freiburg.de/"

    # setup selenium webdriver
    driver = webdriver.Chrome()
    driver.get(base_url)

    # login
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.XPATH, '//input[@type="submit"][@value="login"]').click()

    for package in packages:
        package_url = f"{base_url}packages/{package}"

        driver.get(package_url)

        # find all anchor tags where the text has an underscore in it.
        anchors = driver.find_elements(By.TAG_NAME, "a")
        underscore_anchors = [a.text for a in anchors if "_" in a.text]

        for anchor_text in underscore_anchors:
            if anchor_text in packages:
                continue
            seizure_list_url = f"{base_url}patients/{anchor_text}/seizurelist"
            try:
                driver.get(seizure_list_url)

                # wait for the page to load and get the <pre> element
                pre_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "pre"))
                )
                seizure_list_text = pre_element.text

                # create a directory for each patient if not exists
                os.makedirs(f"seizurelists/{package}/{anchor_text}", exist_ok=True)

                # write the text to a file
                with open(
                    f"seizurelists/{package}/{anchor_text}/seizure_list", "w"
                ) as f:
                    f.write(seizure_list_text)
            except Exception as e:
                print(f"Failed to process {seizure_list_url}. Error: {e}")

    driver.quit()


if __name__ == "__main__":
    main()
