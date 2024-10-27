import os
import pprint
import time
import logging
import click
from dotenv import load_dotenv
from typing import Optional
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional
from datetime import datetime
from selenium.webdriver.support.select import Select
from mtuMishi.web_driver import WebDriverSetup, BetMonth, BetHistoryTableColumn
from google.oauth2 import service_account
import gspread
from google.auth.transport.requests import Request

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
        self.gc = None  # gspread client
        self.authenticate()

    def pass_dict(f):
        """Custom decorator to pass a dictionary to a Click command."""
        @click.pass_context
        def wrapper(ctx, *args, **kwargs):
            # Pass the context object to the wrapped function
            _dict = ctx.obj  # Get the dictionary from the context
            return f(_dict, *args, **kwargs)  # Pass the dictionary to the function
        return wrapper

    # Add method for setting up the web driver
    def setup_web_driver(self, headless=True):
        self.web_setup = WebDriverSetup(headless)
        self.driver = self.web_setup.driver

    def authenticate(self):
        """Authenticate using Google Service Account."""
        if self.credentials is None:
            click.echo("Initializing.............!")
            try:
                # Load the service account credentials
                self.credentials = service_account.Credentials.from_service_account_file(self.credentials_file)
                # Set the required scopes
                self.credentials = self.credentials.with_scopes([
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"
                ])
                self.gc = gspread.authorize(self.credentials)  # Authorize gspread
                click.echo("Authentication successful!")
            except Exception as e:
                click.echo(f"Authentication failed: {e}")
        else:
            click.echo("Using already authenticated credentials.")

    def get_credentials(self):
        """Return the authenticated credentials."""
        return self.credentials

    def get_gspread_client(self):
        """Return the authorized gspread client."""
        return self.gc

    def get_service_sheets(self):
        """Return the Google Sheets service client."""
        if self.credentials:
            return build('sheets', 'v4', credentials=self.credentials,cache_discovery=False)
        else:
            click.echo("No valid credentials found.")
            return None

    def sign_in(self):
        self.web_setup.open_session(BET_URL)
        self._input_credentials()

    def _input_credentials(self):
        self.driver.find_element_by_name("frmUsername").send_keys(self.credentials['username'])
        self.driver.find_element_by_name("frmPassword").send_keys(self.credentials['password'])
        self.driver.find_element_by_name("frmForceTerms").click()
        self.driver.find_element_by_name("submitted").click()

    def sign_out(self):
        """Log out of the betting site."""
        self.driver.find_element_by_xpath("//*[@id='block-logout']").click()
        self.web_setup.close_session()

    @property
    def timestamp(self):
        """Returns the current time displayed on the betting site."""
        timestamp = self.driver.find_element_by_id("time").text.split("Your time: ")
        timestamp = timestamp[-1].strip()
        return timestamp

    @property
    def current_balance(self):
        """Returns the current account balance displayed on the betting site."""
        account_balance = self.driver.find_element_by_id("blocklogout_userBalanceText").text
        return account_balance

    def goto_betting_history(self):
        """Navigate to the betting history page."""
        self.driver.find_element_by_link_text("My Betting History").click()

    def goto_account_history(self):
        """Navigate to the account history page."""
        self.driver.find_element_by_link_text("My Account History").click()

    def filter_betting_history(self, status, month=BetMonth.LAST_7_DAYS, year=str(datetime.now().year)):
        """Filter the betting history table according to the filter options."""
        form_filter = self.driver.find_element_by_id("filter_form")
        selector = Select(form_filter.find_element_by_id("status"))
        selector.select_by_visible_text(status)

        if month != BetMonth.LAST_7_DAYS:
            selector = Select(form_filter.find_element_by_class_name("date_range"))
            selector.select_by_visible_text(month)

        if year != str(datetime.now().year):
            selector = Select(form_filter.find_element_by_class_name("year"))
            selector.select_by_visible_text(year)

        form_filter.find_element_by_class_name("inputBtn").click()

    def _get_number_of_pages_for_table(self):
        """Returns the maximum number of pages for the table."""
        pagination = self.driver.find_element_by_class_name("pagination")
        pagination_text = pagination.text
        num_of_pages = 0
        if pagination_text == "":
            num_of_pages = 1
        elif pagination_text.endswith("»"):
            num_of_pages = int(pagination_text.split('»')[0][-1])
        elif pagination_text.endswith("]"):
            num_of_pages = int(pagination_text.split("[")[-1].split("]")[0])

        return num_of_pages

    def compute_money_invested(self):
        """Calculate the total amount of money placed in bets."""
        money_invested = 0.00
        num_of_pages = self._get_number_of_pages_for_table()
        table = self.driver.find_element_by_class_name("stdTable")
        for page in range(1, num_of_pages + 1):
            if page > 1:
                pagination = self.driver.find_element_by_class_name("pagination")
                page_ = pagination.find_element_by_link_text('{}'.format(page))
                page_.click()

            stakes = table.find_elements_by_xpath("//tr/td[" + str(BetHistoryTableColumn.STAKE) + "]")
            for stake in stakes:
                money_invested += float(stake.text)

        return money_invested


def fetch_credentials(google_auth: GoogleAuthGroup, workbook_id: str, sheet_name: str, service_type: str) -> Optional[list]:
    """Fetch credentials from Google Sheets using googleapiclient based on the specified service type."""

    service_sheets = google_auth.get_service_sheets()
    if not service_sheets:
        click.echo("Google Sheets service could not be initialized.")
        return []

    click.echo(f"Accessing Sheet: ID={workbook_id}, Name={sheet_name}")

    try:
        range_name = "A:Z"
        result = service_sheets.spreadsheets().values().get(
            spreadsheetId=workbook_id,
            range=range_name
        ).execute()

        values = result.get('values', [])
        if not values or len(values) <= 1:
            click.echo(f"No data found in the Google Sheet: {sheet_name}. Please check if there are any entries.")
            return []

    except Exception as error:
        click.echo(f"An error occurred while accessing Google Sheet: {error}")
        return []

    header = values[0]
    if not header:
        click.echo("Header is empty.")
        return []

    credentials_list = []

    expected_headers = {
        "betting": ["Bookie", "Username", "Password"],
        "crypto": ["CRYPTO EXCHANGE", "API KEY", "API SECRET", "VPN-ENABLED", "PASSWORD"],
        "forex": ["Broker", "Account Number", "API Key", "API Secret"]
    }.get(service_type.lower())

    if expected_headers is None:
        click.echo(f"Unknown service type: {service_type}.")
        return []

    header_indices = {name.strip().lower(): index for index, name in enumerate(header)}

    # Check if the expected headers are present
    for expected_header in expected_headers:
        if expected_header.lower() not in header_indices:
            click.echo(f"Missing expected header: {expected_header}.")
            return []

    # Iterate over rows, skipping the header
    for row in values[1:]:
        if row is None or len(row) == 0:
            click.echo("Row is empty or None.")
            continue

        # Create a dictionary for the current row
        data_dict = {header[index].strip().lower(): row[index].strip() if index < len(row) else None for index in range(len(header))}
        click.echo(f"Row data: {data_dict}")

        # Check if all required fields are populated
        if all(data_dict.get(key.lower()) is not None for key in expected_headers):
            # Store the credentials for valid rows based on service type
            credentials_list.append({
                'bookie': data_dict.get('bookie'),
                'username': data_dict.get('username'),
                'password': data_dict.get('password')
            } if service_type.lower() == "betting" else {
                'crypto_exchange': data_dict.get('crypto exchange'),
                'api_key': data_dict.get('api key'),
                'api_secret': data_dict.get('api secret'),
                'vpn_enabled': data_dict.get('vpn-enabled'),
                'password': data_dict.get('password')
            } if service_type.lower() == "crypto" else {
                'broker': data_dict.get('broker'),
                'account_number': data_dict.get('account number'),
                'api_key': data_dict.get('api key'),
                'api_secret': data_dict.get('api secret')
            })
        else:
            click.echo(f"Row skipped due to missing fields: {row}")

    clients_dict = {'credentials': {service_type: credentials_list}}

    if not credentials_list:
        click.echo(f"No valid credentials found for service type: {service_type}.")
        return []

    return clients_dict  # Return credentials without initializing clients


def send_clients_creds(clients_dict: dict, service: str) -> dict:
    click.echo(f"Current credentials object after fetching: {clients_dict}")

    # Get the credentials for the specified service
    creds_list = clients_dict.get('credentials', {}).get(service)
    if not creds_list:
        click.echo(f"No credentials found for {service}. Please fetch the credentials first.")
        return clients_dict

    click.echo(f"Stored credentials for {service}: {creds_list}")

    # Define client_classes dictionary to map service types to their respective client classes
    client_classes = {
        'betting': BetClientGroup,
        'crypto': CryptoClientGroup,
        'forex': ForexClientGroup
    }

    # Initialize a section in clients_dict for this service if not already done
    clients_dict.setdefault(service, {'clients': []})

    # Check if the service is supported
    if service not in client_classes:
        click.echo(f"Service '{service}' is not recognized.")
        return clients_dict

    # Initialize clients based on the credentials provided
    for creds in creds_list:
        try:
            client_cls = client_classes[service]
            client = None

            # Initialize the appropriate client based on the service
            if service == 'betting':
                # Initialize the betting client group
                betting_client = client_cls(
                    clients_dict,  # Pass the clients_dict if needed for fetching credentials
                    creds['bookie'],  # Assuming these fields exist in creds
                    creds['username'],
                    creds['password']
                )
                betting_client.connect()  # Call the connect method to set up the client
                clients_dict[service]['clients'].append(betting_client)
                click.echo(f"Successfully initialized client for {creds['bookie']}.")

            elif service == 'crypto':
                client = client_cls(
                    clients_dict,  # Pass the clients_dict
                    creds.get('workbook_id'),  # Assuming workbook_id is needed
                    creds.get('sheet_name'),
                    creds['crypto_exchange'],
                    'crypto',  # service_type can be hardcoded or derived from service
                    creds['identifier']
                )
                client.connect()  # Call the connect method to set up the client
                clients_dict[service]['clients'].append(client)
                click.echo(f"Successfully initialized crypto client for {creds['crypto_exchange']}.")

            elif service == 'forex':
                client = client_cls(
                    clients_dict,  # Pass the clients_dict
                    creds.get('workbook_id'),  # Assuming workbook_id is needed
                    creds.get('sheet_name'),
                    creds['broker'],
                    'forex',  # service_type can be hardcoded or derived from service
                    creds['identifier']
                )
                client.connect()  # Call the connect method to set up the client
                clients_dict[service]['clients'].append(client)
                click.echo(f"Successfully initialized forex client for {creds['broker']}.")

        except Exception as e:
            click.echo(f"Failed to initialize {service} client: {e}")

    click.echo("All clients are now initialized and available for further use.")
    return clients_dict

class BetClientGroup(GoogleAuthGroup):
    def __init__(self, clients_dict: dict, workbook_id: str, sheet_name: str, bookmaker: str, headless=True):
        # Initialize the parent class with the credentials file
        credentials_file = clients_dict.get('credentials_file')  # Fetch from clients_dict
        super().__init__(credentials_file)

        # Fetch credentials specific to the betting client using the provided bookmaker
        self.credentials = clients_dict.get('credentials', {}).get('betting', {}).get(bookmaker)

        # Check if credentials were provided successfully
        if not self.credentials:
            raise ValueError(f"No credentials found for bookmaker: {bookmaker}")

        # Store bookmaker information for use in connect
        self.bookie = self.credentials['bookie']  # Assuming bookie is part of credentials
        self.headless = headless  # Store headless preference for use in connect

    def connect(self):
        """Connect to the betting client."""
        # Set up the web driver using the method from the parent class
        self.setup_web_driver(self.headless)

        # Initialize the betting client with provided credentials
        self.client = BetClient(self.credentials['username'], self.credentials['password'])

        # Print a confirmation message upon successful connection
        print(f"Connected to betting client for {self.bookie}.")

class CryptoClientGroup(GoogleAuthGroup):
    """The Crypto client allows users to interact with cryptocurrency exchanges."""

    def __init__(self, clients_dict: dict, workbook_id: str, sheet_name: str, exchange: str, service_type: str, identifier: str):
        # Initialize the parent class with the credentials file
        credentials_file = clients_dict.get('credentials_file')
        super().__init__(credentials_file)

        # Fetch credentials specific to the cryptocurrency client using the provided credentials
        self.credentials = clients_dict.get('credentials', {}).get(service_type, {}).get(identifier)

        # Check if credentials were provided successfully
        if not self.credentials:
            raise ValueError(f"No credentials found for exchange: {identifier}")

        # Store exchange and credentials for use in connect
        self.exchange = exchange
        self.api_key = self.credentials.get('api_key')
        self.api_secret = self.credentials.get('api_secret')  # Assuming this is needed for CryptoClient
        self.headless = True  # Set default or receive as parameter if needed

    def connect(self):
        """Connect to the cryptocurrency exchange using provided API keys."""
        # Set up the web driver using the method from the parent class
        self.setup_web_driver(self.headless)

        # Initialize the cryptocurrency client with provided credentials
        self.client = CryptoClient(self.api_key, self.api_secret)  # Assuming CryptoClient is the appropriate class

        # Print a confirmation message upon successful connection
        print(f"Connected to {self.exchange} with API key: {self.api_key}")


class ForexClientGroup(GoogleAuthGroup):
    """The Forex client allows users to interact with forex trading platforms."""

    def __init__(self, clients_dict: dict, workbook_id: str, sheet_name: str, broker: str, service_type: str, identifier: str):
        # Initialize the parent class with the credentials file
        credentials_file = clients_dict.get('credentials_file')
        super().__init__(credentials_file)

        # Fetch credentials specific to the forex client using the provided credentials
        self.credentials = clients_dict.get('credentials', {}).get(service_type, {}).get(identifier)

        # Check if credentials were provided successfully
        if not self.credentials:
            raise ValueError(f"No credentials found for broker: {identifier}")

        # Store broker and credentials for use in connect
        self.broker = broker
        self.account_number = self.credentials.get('account_number')
        self.api_key = self.credentials.get('api_key')
        self.headless = True  # Set default or receive as parameter if needed

    def connect(self):
        """Connect to the forex broker using provided credentials."""
        # Set up the web driver using the method from the parent class
        self.setup_web_driver(self.headless)

        # Initialize the forex client with provided credentials
        self.client = ForexClient(self.account_number, self.api_key)  # Assuming ForexClient is the appropriate class

        # Print a confirmation message upon successful connection
        print(f"Connected to {self.broker} with account number: {self.account_number}")

    # Additional methods for forex operations can be added here
