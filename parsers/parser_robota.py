from enum import StrEnum
from urllib.parse import urljoin

from pip._internal.models import candidate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import CHROME_DRIVER_PATH, BASE_URL_ROBOTA


class PeriodType(StrEnum):
    TODAY = "Today"
    THREE_DAYS = "ThreeDays"
    WEEK = "Week"
    MONTH = "Month"
    THREE_MONTHS = "default"
    YEAR = "Year"
    ALL = "All"


class RobotaParser:
    DRIVER_PATH = CHROME_DRIVER_PATH
    URL = BASE_URL_ROBOTA

    def __init__(self, position: str, city: str = 'ukraine', page: int = 1, **kwargs) -> None:
        self.driver = self.init_driver()
        self.temp_employer_list = []
        self.filter = f'{position}/{city}'
        if params := ''.join([f'&{key}="{value}"' for key, value in kwargs.items() if value]):
            self.filter += f'?page={page}{params}' if page > 1 else f'?{params[1:]}'
        self.url = urljoin(self.URL, self.filter)
        print(self.url)

    def init_driver(self):
        options = Options()
        options.add_argument('--headless')
        return webdriver.Chrome(service=Service(self.DRIVER_PATH), options=options)

    def get_soup_cards(self):
        self.driver.get(self.url)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'alliance-employer-cvdb-cv-list-card.santa-outline-none'))
            )
            cards = self.driver.find_elements(By.CSS_SELECTOR, 'alliance-employer-cvdb-cv-list-card.santa-outline-none')
            return cards
        except Exception as e:
            print(f"Error or no cards found: {e}")
            return []

    def get_content(self):
        card_employer_list = []
        for card in self.get_soup_cards():
            try:
                candidate = {}

                candidate = {
                    'link': self.get_employer_link(card),
                    'position': self.get_employer_position(card),
                    'name': self.get_employer_name(card),
                    'location': self.get_employer_location(card),
                    'salary': self.get_employer_salary(card),
                    'experience': self.get_employer_experience(card)
                }


                if candidate not in card_employer_list:
                    card_employer_list.append(candidate)
            except Exception as e:
                print("Error parsing card:", e)
        return card_employer_list

    def get_employer_link(self, card):
        candidate_link = card.find_element(By.CSS_SELECTOR, 'a.santa-no-underline')
        return candidate_link.get_attribute('href')

    def get_employer_position(self, card):
        return card.find_element(By.CSS_SELECTOR, 'p[data-id="cv-speciality"]').text.strip()

    def get_employer_name(self, card):
        return card.find_element(By.CSS_SELECTOR, 'p.santa-pr-20.santa-typo-regular.santa-truncate').text.strip()

    def get_employer_location(self, card):
        return card.find_element(By.CSS_SELECTOR, 'p[data-id="cv-city-tag"]').text.strip()

    def get_employer_salary(self, card):
        try:
            salary_element = card.find_elements(By.CSS_SELECTOR,
                                                'div.santa-flex.santa-items-center.santa-space-x-10.santa-pr-20.santa-whitespace-nowrap p.santa-typo-secondary')
            for elem in salary_element:
                if "грн" in elem.text or "$" in elem.text or "€" in elem.text:
                    salary = elem.text.strip()
                    break
            else:
                salary = None
            return salary
        except Exception:
            return None

    def get_employer_experience(self, card):
        try:
            experience = card.find_element(
                By.CSS_SELECTOR, 'p.santa-mt-0.santa-mb-10.santa-typo-regular.santa-text-black-700'
            ).text.strip()
            return experience
        except Exception:
            return None


class RobotaContent:
    def __init__(self, position: str, city: str, **kwargs):
        self.employers_list = []
        self.temp_employers = {}
        self.position = position.replace(' ', '-').lower()
        self.city = city.lower() if city else 'ukraine'
        self.kwargs = kwargs

    def get_info(self):
        print(f'robota.ua: {self.position}')
        page = 1
        while True:
            parser = RobotaParser(
                position=self.position,
                city=self.city,
                page=page,
                **self.kwargs
            )
            content = parser.get_content()
            parser.driver.quit()
            if not content:
                print(f"No more cards found on page {page}. Stopping.")
                return self.employers_list

            if content == self.temp_employers:
                break
            print(f"Page {page}: Found {len(content)} candidates")
            for item in content:
                if item not in self.employers_list:
                    self.employers_list.append(item)
            self.temp_employers = content
            page += 1

        return self.employers_list
