from datetime import datetime
import os
import click
from dotenv import load_dotenv
from betClient.cli import betting_group
from ccxtClient import crypto_group
from forexClient import forex_group
from mtuMishi.mtumishi import initialize_google_auth_and_clients


# Load environment variables from .env file
load_dotenv()

def get_spreadsheet_info(service):
    """Get spreadsheet ID and sheet name based on the service."""
    if service == 'betting':
        return (os.getenv('BETTING_SPREADSHEET_ID'), os.getenv('BETTING_SHEET_NAME'))
    elif service == 'crypto':
        return (os.getenv('CRYPTO_SPREADSHEET_ID'), os.getenv('CRYPTO_SHEET_NAME'))
    elif service == 'forex':
        return (os.getenv('FOREX_SPREADSHEET_ID'), os.getenv('FOREX_SHEET_NAME'))
    else:
        raise ValueError("Invalid service type.")


# Main CLI Group
@click.group()
def main_cli():
    print("Hello, welcome to Njema!")

# General commands
@click.command()
def date():
    """Show current date."""
    click.echo(datetime.utcnow().date().isoformat())

@click.command()
def time():
    """Show current time."""
    click.echo(datetime.utcnow().isoformat())


@click.command(name='initcli')
@click.option('--service', type=str, required=True, help='Comma-separated list of services to initialize (e.g., betting,crypto,forex).')
def initialize_clients(service):
    """Initialize clients for the specified services."""
    # Split the input string into a list
    services = [s.strip() for s in service.split(',')]

    for svc in services:
        spreadsheet_id, sheet_name = get_spreadsheet_info(svc)

        if not spreadsheet_id or not sheet_name:
            click.echo(f"Spreadsheet ID or Sheet Name is not set in the environment for {svc}.")
            return

        clients = initialize_google_auth_and_clients(spreadsheet_id, sheet_name)
        click.echo(f"Clients for {svc} initialized successfully!")


@click.command(name='authcreds')
@click.argument('credentials_file', type=click.Path(exists=True), required=False)
def authenticate_and_get_credentials(credentials_file=None):
    """Authenticate using Google Service Account and get authenticated credentials."""
    # Check if an environment variable is set if no command-line argument is provided
    if credentials_file is None:
        credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')

    if credentials_file is None:
        click.echo("No credentials file provided. Please set the GOOGLE_CREDENTIALS_FILE environment variable or provide a file.")
        return

    # Authenticate
    auth = GoogleAuth(credentials_file)
    try:
        auth.authenticate()
        click.echo("Authentication successful!")

        # Get credentials
        credentials = auth.get_credentials()
        if credentials:
            click.echo("Authenticated credentials:")
            click.echo(credentials)
        else:
            click.echo("No credentials found.")

    except Exception as e:
        click.echo(f"Authentication failed: {e}")

# Assuming clients is a dictionary that holds instances for different services
sessions = {
    'betting': None,
    'crypto': None,
    'forex': None
}

@click.command()
@click.option('--service', type=click.Choice(['betting', 'crypto', 'forex']), required=True)
def sign_in(service):
    """Sign in to the specified service."""
    
    # Handle betting sign-in
    if service == 'betting':
        username = click.prompt('Your username')
        password = click.prompt('Your password', hide_input=True)
        client = clients.get('betting')
        
        if client:
            client.sign_in(username, password)  # Implement sign-in logic in client
            sessions['betting'] = client  # Store session
            click.echo("Signed in to betting successfully!")
        else:
            click.echo("Betting client not initialized.")

    # Handle crypto sign-in
    elif service == 'crypto':
        client = clients.get('crypto')
        
        if client:
            client.sign_in()  # Implement sign-in logic in client
            sessions['crypto'] = client  # Store session
            click.echo("Crypto client signed in successfully!")
        else:
            click.echo("Crypto client not initialized.")

    # Handle forex sign-in
    elif service == 'forex':
        client = clients.get('forex')
        
        if client:
            client.sign_in()  # Implement sign-in logic in client
            sessions['forex'] = client  # Store session
            click.echo("Forex client signed in successfully!")
        else:
            click.echo("Forex client not initialized.")

# You may want to implement a command to list active sessions
@click.command()
def list_sessions():
    """List currently active sessions."""
    for service, session in sessions.items():
        status = "Active" if session else "Not signed in"
        click.echo(f"{service.capitalize()} session: {status}")

@click.command()
@click.option('--service', type=click.Choice(['betting', 'crypto', 'forex']), required=True)
def sign_out(service):
    """Sign out from the specified service."""
    client = clients.get(service)
    
    if client:
        client.sign_out()  # Implement sign-out logic in client
        sessions[service] = None  # Clear the session
        click.echo(f"Signed out from {service} successfully!")
    else:
        click.echo(f"{service.capitalize()} client not initialized or not signed in.")

@click.command()
def current_balance():
    """Show the current balance."""
    client = clients.get('betting')  # Adjust if necessary
    balance = client.current_balance
    click.echo(balance)

# Add groups for betting, crypto, and forex to the main CLI
main_cli.add_command(betting_group.sports_betting)
main_cli.add_command(crypto_group.crypto)
main_cli.add_command(forex_group.forex)


# Add combined commands for authentication and credential retrieval
main_cli.add_command(initialize_clients)
main_cli.add_command(authenticate_and_get_credentials)

# Add commands for managing sessions
main_cli.add_command(sign_in)
main_cli.add_command(sign_out)
main_cli.add_command(list_sessions)  # New command to list active sessions

# Add a command to get the current balance (assuming you have it defined)
main_cli.add_command(current_balance)

# Add standalone commands for date and time
main_cli.add_command(date)
main_cli.add_command(time)

