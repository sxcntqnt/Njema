from datetime import datetime
import os, pprint
import click
from dotenv import load_dotenv
from betClient.cli import betting_group
from ccxtClient import crypto_group
from forexClient import forex_group
from mtuMishi.mtumishi import send_clients_creds , fetch_credentials, GoogleAuthGroup


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


@click.command(name='creds')
@click.option('--service', type=click.Choice(['betting', 'crypto', 'forex']), required=True)
@click.pass_context
def fetch_creds(ctx, service):
    """Authenticate and fetch credentials for the specified service."""

    # Load environment variables from .env file
    load_dotenv()

    # Get the Google credentials file path from environment variables
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
    if not credentials_file:
        click.echo("Google credentials file path is not set.")
        return

    # Initialize the context object if it's None
    if ctx.obj is None:
        ctx.obj = {}

    # Step 1: Authenticate
    google_auth = GoogleAuthGroup(credentials_file)

    try:
        google_auth.authenticate()  # Authenticate using the service account
        click.echo("Authentication successfully completed!")

        # Step 2: Fetch credentials for the specified service
        spreadsheet_id, sheet_name = get_spreadsheet_info(service)
        if not spreadsheet_id or not sheet_name:
            click.echo(f"Spreadsheet ID or Sheet Name is not set in the environment for {service}.")
            return

        # Fetch credentials and store them in the context
        ctx.obj.setdefault('clients_dict', {})
        clients_dict = fetch_credentials(google_auth, spreadsheet_id, sheet_name, service)

        # Check if credentials were fetched
        if not clients_dict:
            click.echo("No credentials found.")
            return

        ctx.obj['clients_dict']['credentials'] = {service: clients_dict['credentials'][service]}
        click.echo(f"Fetched credentials for {service}: {ctx.obj['clients_dict']['credentials'][service]}")

        # Step 3: Initialize clients for the specified service using stored credentials
        click.echo("Checking if credentials are available in the context...")

        # Ensure the context has the necessary credentials
        if 'credentials' not in ctx.obj['clients_dict'] or service not in ctx.obj['clients_dict']['credentials']:
            click.echo("No credentials available. Please run the fetch_creds command first.")
            return

        # Call send_clients_creds to initialize the clients using the fetched credentials
        updated_clients_dict = send_clients_creds(ctx.obj['clients_dict'], service)

        # Update context with initialized clients
        ctx.obj['clients_dict'] = updated_clients_dict
        click.echo(f"Clients for '{service}' have been initialized and are now available for use.")

    except Exception as e:
        click.echo(f"Error: {e}")


@click.command(name='signin')
@click.option('--service', type=str, required=True, help='Comma-separated list of services to fetch credentials for (e.g., betting,crypto,forex).')
@click.pass_context
def sign_in(ctx, service):
    """Sign in to the specified service."""
    # Access the clients from the context
    clients = ctx.obj.get('clients')
    sessions = ctx.obj.setdefault('sessions', {})  # Initialize sessions if not already present

    # Handle betting sign-in
    if service == 'betting':
        username = click.prompt('Your username')
        password = click.prompt('Your password', hide_input=True)
        client = clients.get('betting')

        if client:
            client.sign_in(username, password)  # Ensure this method is implemented in BetClientGroup
            sessions['betting'] = client  # Store session
            click.echo("Signed in to betting successfully!")
        else:
            click.echo("Betting client not initialized.")

    # Handle crypto sign-in
    elif service == 'crypto':
        client = clients.get('crypto')

        if client:
            client.sign_in()  # Ensure this method is implemented in CryptoClientGroup
            sessions['crypto'] = client  # Store session
            click.echo("Crypto client signed in successfully!")
        else:
            click.echo("Crypto client not initialized.")

    # Handle forex sign-in
    elif service == 'forex':
        client = clients.get('forex')

        if client:
            client.sign_in()  # Ensure this method is implemented in ForexClientGroup
            sessions['forex'] = client  # Store session
            click.echo("Forex client signed in successfully!")
        else:
            click.echo("Forex client not initialized.")

# You may want to implement a command to list active sessions
@click.command(name='list_sessions')
@click.option('--service', type=str, required=True, help='Comma-separated list of services to fetch credentials for (e.g., betting,crypto,forex).')
@click.pass_context
def list_sessions(ctx):
    """List currently active sessions."""
    # Access the sessions from the context
    sessions = ctx.obj.get('sessions', {})

    if not sessions:
        click.echo("No active sessions found.")
        return

    for service, session in sessions.items():
        status = "Active" if session else "Not signed in"
        click.echo(f"{service.capitalize()} session: {status}")

@click.command(name='sign_out')
@click.option('--service', type=click.Choice(['betting', 'crypto', 'forex']), required=True)
@click.pass_context
def sign_out(ctx, service):
    """Sign out from the specified service."""
    # Access the clients and sessions from the context
    clients = ctx.obj.get('clients', {})
    sessions = ctx.obj.get('sessions', {})

    client = clients.get(service)

    if client and sessions.get(service):
        client.sign_out()  # Implement sign-out logic in client
        sessions[service] = None  # Clear the session
        click.echo(f"Signed out from {service} successfully!")
    else:
        click.echo(f"{service.capitalize()} client not initialized or not signed in.")

@click.command()
@click.option('--service', type=str, required=True, help='Comma-separated list of services to fetch credentials for (e.g., betting,crypto,forex).')
@click.pass_context
def current_balance():
    """Show the current balance."""
    client = clients.get('betting')  # Adjust if necessary
    balance = client.current_balance
    click.echo(balance)

# Add groups for betting, crypto, and forex to the main CLI
main_cli.add_command(betting_group.group)
main_cli.add_command(crypto_group.crypto)
main_cli.add_command(forex_group.forex)


# Add combined commands for authentication and credential retrieval
main_cli.add_command(fetch_creds)

# Add commands for managing sessions
main_cli.add_command(sign_in)
main_cli.add_command(sign_out)
main_cli.add_command(list_sessions)  # New command to list active sessions

# Add a command to get the current balance (assuming you have it defined)
main_cli.add_command(current_balance)

main_cli.add_command(betting_group.send_alert)
main_cli.add_command(betting_group.process_output)
main_cli.add_command(betting_group.check_resource_usage)
main_cli.add_command(betting_group.check_disk_usage)
main_cli.add_command(betting_group.check_network_connectivity)
main_cli.add_command(betting_group.monitor_process)
main_cli.add_command(betting_group.run_scripts)

# Add standalone commands for date and time
main_cli.add_command(date)
main_cli.add_command(time)

if __name__ == "__main__":
    main_cli()
