import os
import time
import logging
from dotenv import load_dotenv
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from typing import List, Dict
from datetime import datetime
from selenium.webdriver.support.select import Select
from mtuMishi.web_driver import WebDriverSetup, BetMonth, BetHistoryTableColumn

# Constants
BET_URL = "https://www.bet.co.za"

# Configure logging
logging.basicConfig(level=logging.INFO)

# Solution for creating a set of constants found here
# https://codereview.stackexchange.com/questions/193090/python-constant-class-different-enum-implementation

# Betting History table columns
# | Ticket | Event Date | Tournament | Event | Selection | Bet Type | Stake | Potential Win | Status |


class GoogleAuthGroup:
    def __init__(self, credentials_file: str):
        self.credentials_file = credentials_file
        self.credentials = None
        self.authenticate()

    def authenticate(self):
        """Authenticate using Google Service Account."""
        try:
            self.credentials = service_account.Credentials.from_service_account_file(self.credentials_file)
            if self.credentials.expired:
                self.credentials.refresh(Request())
            print("Authentication successful!")
        except Exception as e:
            print(f"Authentication failed: {e}")

    def get_credentials(self) -> Optional[service_account.Credentials]:
        """Return the authenticated credentials."""
        return self.credentials

def fetch_credentials(google_auth: GoogleAuthGroup, workbook_id: str, sheet_name: str, service_type: str, identifier: str) -> dict:
    """Fetch credentials from Google Sheets based on the service type."""
    service = build('sheets', 'v4', credentials=google_auth.get_credentials())
    result = service.spreadsheets().values().get(spreadsheetId=workbook_id, range=sheet_name).execute()
    values = result.get('values', [])

    if not values:
        raise ValueError("No data found in the Google Sheet.")

    header = values[0]
    for row in values[1:]:
        if row and len(row) == len(header):
            data_dict = dict(zip(header, row))
            if data_dict.get('type').lower() == service_type.lower() and data_dict.get('name').lower() == identifier.lower():
                return {
                    'username': data_dict.get('username'),
                    'password': data_dict.get('password'),
                    'api_key': data_dict.get('api_key', None),
                    'api_secret': data_dict.get('api_secret', None),
                    'account_number': data_dict.get('account_number', None),
                }

    raise ValueError(f"No credentials found for {service_type}: {identifier}")


class BetClientGroup(GoogleAuthGroup):
    def __init__(self, credentials_file: str, workbook_id: str, sheet_name: str, bookmaker: str, headless=True):
        super().__init__(credentials_file, workbook_id, sheet_name, 'bookmaker', bookmaker)
        self.web_setup = WebDriverSetup(headless)
        self.driver = self.web_setup.driver
        self.client = BetClient(self.credentials['username'], self.credentials['password'])

    def sign_in(self):
        self.web_setup.open_session(BET_URL)
        self._input_credentials()


    def _input_credentials(self):
        self.driver.find_element_by_name("frmUsername").send_keys(self.credentials['username'])
        self.driver.find_element_by_name("frmPassword").send_keys(self.credentials['password'])
        self.driver.find_element_by_name("frmForceTerms").click()
        self.driver.find_element_by_name("submitted").click()


    def sign_out(self):
        """Log out of the https://www.bet.co.za site.
        """
        self.driver.find_element_by_xpath("//*[@id='block-logout']").click()
        self.web_setup.close_session()

    @property
    def timestamp(self):
        """Returns the current time displayed on https://www.bet.co.za site.

        Returns
        -------
        timestamp : str
            Current timestamp displayed on the site.
        """
        timestamp = self.driver.find_element_by_id("time").text.split("Your time: ")
        timestamp = timestamp[-1].strip()
        return timestamp

    @property
    def current_balance(self):
        """Returns the current account balance displayed on https://www.bet.co.za site.
        Returns
        -------
        account_balance : str
            Current account balance displayed on the site.
        """
        account_balance = (
            self.driver.find_element_by_id("blocklogout_userBalanceText").text)
        return account_balance

    def goto_betting_history(self):
        """Navigate the https://www.bet.co.za betting history page.
        """
        self.driver.find_element_by_link_text("My Betting History").click()

    def goto_account_history(self):
        """Navigate the https://www.bet.co.za account history page.
        """
        self.driver.find_element_by_link_text("My Account History").click()

    def filter_betting_history(self, status, month=BetMonth.LAST_7_DAYS,
                               year=str(datetime.now().year)):
        """Filter the https://www.bet.co.za betting history table according to the
        filter options.

        Parameters
        ----------
        status : BetStatus instance.
            Wager status.
        month : BetMonth instance
            Date filter value.
        year : str
            Years from 2011 to current.
        """
        # Get the filter form
        form_filter = self.driver.find_element_by_id("filter_form")
        # Create a selector object for dropdown tables
        selector = Select(form_filter.find_element_by_id("status"))
        # Select option in wager status dropdown
        selector.select_by_visible_text(status)

        if month != BetMonth.LAST_7_DAYS:
            selector = Select(form_filter.find_element_by_class_name("date_range"))
            # Select option in month dropdown
            selector.select_by_visible_text(month)

        if year != str(datetime.now().year):
            selector = Select(form_filter.find_element_by_class_name("year"))
            # Select option in year dropdown
            selector.select_by_visible_text(year)

        # Click on the 'Go' button to filter bets
        form_filter.find_element_by_class_name("inputBtn").click()

    def _get_number_of_pages_for_table(self):
        """

        Returns
        -------
        num_of_pages : int
            The maximum number of pages for the table.
        """
        # Pages can come in different forms
        # '' ==> means just one page
        # '12»' ==> means just two pages in total
        # '1234567»[12]' ==> means 12 pages in total
        pagination = self.driver.find_element_by_class_name("pagination")
        pagination_text = pagination.text
        num_of_pages = 0
        if pagination_text == "":
            # only one page to deal with
            num_of_pages = 1
        elif pagination_text.endswith("»"):
            # '12»' -> 2
            num_of_pages = int(pagination_text.split('»')[0][-1])
        elif pagination_text.endswith("]"):
            # '1234567»[12]' -> 12
            num_of_pages = int(pagination_text.split("[")[-1].split("]")[0])

        return num_of_pages

    def compute_money_invested(self):
        """Calculate the amount of money has been taken from the balance and placed
        in a bet(s).

        Returns
        -------
        money_invested : float
            The amount of money placed in a bet(s).
        """
        money_invested = 0.00
        num_of_pages = self._get_number_of_pages_for_table()
        # Get the table object
        table = self.driver.find_element_by_class_name("stdTable")
        for page in range(1, num_of_pages+1):
            if page > 1:
                # Need to get the pagination element again or else raises
                # StaleElementReferenceException
                pagination = self.driver.find_element_by_class_name("pagination")
                page_ = pagination.find_element_by_link_text('{}'.format(page))
                page_.click()

            # Get all the rows on column number 7 (Stake)
            stakes = table.find_elements_by_xpath(
                "//tr/td["+str(BetHistoryTableColumn.STAKE)+"]")

            for stake in stakes:
                money_invested += float(stake.text)

        return money_invested

class CryptoClientGroup(GoogleAuthGroup):
    """The Crypto client allows users to interact with cryptocurrency exchanges."""

    def __init__(self, credentials_file: str, workbook_id: str, sheet_name: str, exchange: str, service_type: str, identifier: str):
        super().__init__(credentials_file)
        credentials = fetch_credentials(self, workbook_id, sheet_name, service_type, identifier)
        self.exchange = exchange
        self.api_key = credentials.get('api_key')
        self.api_secret = credentials.get('api_secret')

    def connect(self):
        """Connect to the cryptocurrency exchange using provided API keys."""
        print(f"Connected to {self.exchange} with API key: {self.api_key}")


class ForexClientGroup(GoogleAuthGroup):
    """The Forex client allows users to interact with forex trading platforms."""

    def __init__(self, credentials_file: str, workbook_id: str, sheet_name: str, broker: str, service_type: str, identifier: str):
        super().__init__(credentials_file)
        credentials = fetch_credentials(self, workbook_id, sheet_name, service_type, identifier)
        self.broker = broker
        self.account_number = credentials.get('account_number')
        self.api_key = credentials.get('api_key')

    def connect(self):
        """Connect to the forex broker using provided credentials."""
        print(f"Connected to {self.broker} with account number: {self.account_number}")

def initialize_google_auth_and_clients(spreadsheet_id: str, sheet_name: str,
                                        selected_services: list = None) -> dict:
    load_dotenv()

    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
    if not credentials_file:
        print("Google credentials file path is not set.")
        return None

    google_auth_group = GoogleAuthGroup(credentials_file)
    service_credentials = google_auth_group.fetch_credentials(spreadsheet_id, sheet_name)

    # Initialize a matrix-like structure to hold clients
    clients = {
        'betting': {},
        'crypto': {},
        'forex': {}
    }

    for creds in service_credentials:
        if selected_services and creds['type'] not in selected_services:
            continue  # Skip this service if not selected

        service_type = creds['type']
        if service_type == 'betting':
            clients['betting'][creds['index']] = BetClientGroup(creds['username'], creds['password'])
        elif service_type == 'crypto':
            clients['crypto'][creds['index']] = CryptoClientGroup(
                creds['api_key'], creds['api_secret'])
        elif service_type == 'forex':
            clients['forex'][creds['index']] = ForexClientGroup(
                creds['broker'], creds['account_number'], creds['api_key'])

    return clients


