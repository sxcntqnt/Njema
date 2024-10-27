import click
import subprocess
import os
import json
import logging
import time
import psutil  # Requires the psutil library for process management
import socket
import smtplib
from dotenv import load_dotenv
from mtuMishi import mtumishi, web_driver

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define your context object for storing credentials
class Context:
    def __init__(self, username=None, password=None, api_key=None, api_secret=None,
                 account_number=None, service_type=None, identifier=None, name=None, plugin_folder="commands"):
        self.credentials = {
            'username': username,
            'password': password,
            'api_key': api_key,
            'api_secret': api_secret,
            'account_number': account_number
        }
        self.service_type = service_type
        self.identifier = identifier
        self.name = name  # Additional attribute
        self.plugin_folder = plugin_folder  # Additional attribute

    def __repr__(self):
        return (f"<Context(service_type={self.service_type}, identifier={self.identifier}, "
                f"credentials={self.credentials}, name={self.name}, plugin_folder={self.plugin_folder})>")


# Define the SportsBettingGroup class that encapsulates all functionalities
class SportsBettingGroup(click.Group):
    def __init__(self, name=None, plugin_folder="/home/kanairo/Private/cashathand/Njemz/Njema/betClient", **kwargs):
        super().__init__(name=name, **kwargs)
        self.plugin_folder = plugin_folder

        # Full path for each script
        self.bookie_scripts = {
            "1xbet": os.path.join(self.plugin_folder, "betClient_1xbet.py"),
            "betsafe": os.path.join(self.plugin_folder, "betClient_betsafe.py"),
            "hollywoodbets": os.path.join(self.plugin_folder, "betClient_hollywoodbets.py"),
            "mozzartbet": os.path.join(self.plugin_folder, "betClient_mozzartbet.py"),
            "solbet": os.path.join(self.plugin_folder, "betClient_solbet.py"),
            "22bet": os.path.join(self.plugin_folder, "betClient_22bet.py"),
            "betway": os.path.join(self.plugin_folder, "betClient_betway.py"),
            "ibet": os.path.join(self.plugin_folder, "betClient_ibet.py"),
            "oddibet": os.path.join(self.plugin_folder, "betClient_oddibet.py"),
            "sportika": os.path.join(self.plugin_folder, "betClient_sportika.py"),
            "888starz": os.path.join(self.plugin_folder, "betClient_888starz.py"),
            "betwinner": os.path.join(self.plugin_folder, "betClient_betwinner.py"),
            "inbetkenya": os.path.join(self.plugin_folder, "betClient_inbetkenya.py"),
            "palmsbet": os.path.join(self.plugin_folder, "betClient_palmsbet.py"),
            "sportpesa": os.path.join(self.plugin_folder, "betClient_sportpesa.py"),
            "bangbet": os.path.join(self.plugin_folder, "betClient_bangbet.py"),
            "bolyesports": os.path.join(self.plugin_folder, "betClient_bolyesports.py"),
            "instabets": os.path.join(self.plugin_folder, "betClient_instabets.py"),
            "parimatch": os.path.join(self.plugin_folder, "betClient_parimatch.py"),
            "sportybet": os.path.join(self.plugin_folder, "betClient_sportybet.py"),
            "betafriq": os.path.join(self.plugin_folder, "betClient_betafriq.py"),
            "bongobongo": os.path.join(self.plugin_folder, "betClient_bongobongo.py"),
            "jambobet": os.path.join(self.plugin_folder, "betClient_jambobet.py"),
            "pepetabet": os.path.join(self.plugin_folder, "betClient_pepetabet.py"),
            "starbet": os.path.join(self.plugin_folder, "betClient_starbet.py"),
            "betbureau": os.path.join(self.plugin_folder, "betClient_betbureau.py"),
            "captainsbet": os.path.join(self.plugin_folder, "betClient_captainsbet.py"),
            "jantabets": os.path.join(self.plugin_folder, "betClient_jantabets.py"),
            "pesaland": os.path.join(self.plugin_folder, "betClient_pesaland.py"),
            "strikebet": os.path.join(self.plugin_folder, "betClient_strikebet.py"),
            "betflame": os.path.join(self.plugin_folder, "betClient_betflame.py"),
            "chezacash": os.path.join(self.plugin_folder, "betClient_chezacash.py"),
            "kenyacharity": os.path.join(self.plugin_folder, "betClient_kenyacharity.py"),
            "pinnacle": os.path.join(self.plugin_folder, "betClient_pinnacle.py"),
            "tickbet": os.path.join(self.plugin_folder, "betClient_tickbet.py"),
            "ultrabet": os.path.join(self.plugin_folder, "betClient_ultrabet.py"),
            "betgr8": os.path.join(self.plugin_folder, "betClient_betgr8.py"),
            "dafabet": os.path.join(self.plugin_folder, "betClient_dafabet.py"),
            "kwachua": os.path.join(self.plugin_folder, "betClient_kwachua.py"),
            "playbet": os.path.join(self.plugin_folder, "betClient_playbet.py"),
            "worldsportbetting": os.path.join(self.plugin_folder, "betClient_worldsportbetting.py"),
            "betika": os.path.join(self.plugin_folder, "betClient_betika.py"),
            "dimbakenya": os.path.join(self.plugin_folder, "betClient_dimbakenya.py"),
            "kwikbet": os.path.join(self.plugin_folder, "betClient_kwikbet.py"),
            "playmaster": os.path.join(self.plugin_folder, "betClient_playmaster.py"),
            "betking": os.path.join(self.plugin_folder, "betClient_betking.py"),
            "flamingobets": os.path.join(self.plugin_folder, "betClient_flamingobets.py"),
            "ligibet": os.path.join(self.plugin_folder, "betClient_ligibet.py"),
            "betkwiff": os.path.join(self.plugin_folder, "betClient_betkwiff.py"),
            "forzza": os.path.join(self.plugin_folder, "betClient_forzza.py"),
            "mcheza": os.path.join(self.plugin_folder, "betClient_mcheza.py"),
            "saharagames": os.path.join(self.plugin_folder, "betClient_saharagames.py"),
            "betlion": os.path.join(self.plugin_folder, "betClient_betlion.py"),
            "gameguys": os.path.join(self.plugin_folder, "betClient_gameguys.py"),
            "melbet": os.path.join(self.plugin_folder, "betClient_melbet.py"),
            "scorepesa": os.path.join(self.plugin_folder, "betClient_scorepesa.py"),
            "betnare": os.path.join(self.plugin_folder, "betClient_betnare.py"),
            "geniusbet": os.path.join(self.plugin_folder, "betClient_geniusbet.py"),
            "mojabet": os.path.join(self.plugin_folder, "betClient_mojabet.py"),
            "shabiki": os.path.join(self.plugin_folder, "betClient_shabiki.py")
        }

    @click.group()
    @click.pass_context
    def group(self, ctx):
        """Group for sports betting commands."""
        ctx.ensure_object(Context)

    @group.command(name='tuma-onyo')
    @click.pass_context
    def send_alert(self, ctx, subject, message):
        """Send an email alert."""
        context = ctx.obj
        if not context or 'betting' not in context.credentials:
            click.echo("No clients initialized. Please authenticate first.")
            return

        try:
            with smtplib.SMTP(os.getenv('SMTP_SERVER')) as server:  # Update with your SMTP server details
                server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))  # Load from env
                server.sendmail(os.getenv('FROM_EMAIL'), os.getenv('TO_EMAIL'), f"Subject: {subject}\n\n{message}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    @group.command(name='chakata-matumizi')
    @click.pass_context
    def process_output(self, ctx, stdout, stderr, bookie_name):
        """Process the output of each betting client script."""
        context = ctx.obj
        if not context or 'betting' not in context.credentials:
            click.echo("No clients initialized. Please authenticate first.")
            return

        if stderr:
            logger.error(f"Error occurred while running {bookie_name}: {stderr.decode().strip()}")
            return

        if stdout:
            logger.info(f"Output from {bookie_name}: {stdout.decode().strip()}")
            try:
                # Parse JSON output if applicable (assuming the scripts output JSON)
                result_data = json.loads(stdout.decode())
                logger.info(f"Parsed result data for {bookie_name}: {result_data}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse output as JSON from {bookie_name}")

    @group.command(name='angalia-rasilimali')
    @click.pass_context
    def check_resource_usage(self, ctx):
        """Check CPU and memory usage of the process."""
        context = ctx.obj
        if not context or 'betting' not in context.credentials:
            click.echo("No clients initialized. Please authenticate first.")
            return

        try:
            mem_usage = psutil.virtual_memory().percent  # Overall memory usage
            cpu_usage = psutil.cpu_percent(interval=1)  # CPU usage
            logger.info(f"Memory Usage: {mem_usage:.2f}%, CPU Usage: {cpu_usage:.2f}%")
            return mem_usage < 90 and cpu_usage < 80  # Thresholds
        except Exception as e:
            logger.error(f"Resource check failed: {e}")
            return False

    @group.command(name='angalia-ufunguo')
    @click.pass_context
    def check_disk_usage(self, ctx):
        """Check overall disk usage."""
        context = ctx.obj
        if not context or 'betting' not in context.credentials:
            click.echo("No clients initialized. Please authenticate first.")
            return

        try:
            disk_usage = psutil.disk_usage('/').percent
            logger.info(f"Disk Usage: {disk_usage:.2f}%")
            return disk_usage < 90  # Example threshold
        except Exception as e:
            logger.error(f"Disk usage check failed: {e}")
            return False

    @group.command(name='angalia-mtandao')
    @click.pass_context
    def check_network_connectivity(self, ctx):
        """Check network connectivity."""
        context = ctx.obj
        if not context or 'betting' not in context.credentials:
            click.echo("No clients initialized. Please authenticate first.")
            return

        try:
            socket.create_connection(("www.google.com", 80))
            logger.info("Network connectivity is stable.")
            return True
        except OSError:
            logger.error("Network connectivity issue detected.")
            return False

    @group.command(name='fuatilia-mchakato')
    @click.pass_context
    def monitor_process(self, ctx, process, bookie_name):
        """Monitor the specified process for resource usage."""
        context = ctx.obj
        if not context or 'betting' not in context.credentials:
            click.echo("No clients initialized. Please authenticate first.")
            return

        while True:
            time.sleep(5)  # Check every 5 seconds
            if process.poll() is not None:  # Process has exited
                stdout, stderr = process.communicate()
                self.process_output(ctx, stdout, stderr, bookie_name)
                break

            if not self.check_resource_usage(ctx):
                logger.warning("Resource usage exceeded threshold.")
                self.send_alert("High Resource Usage", f"Resource usage exceeded threshold for '{bookie_name}'.")

    @group.command(name="chckauth")
    @click.pass_context
    def authenticate_command(self, ctx):
        """Authenticate with mtumishi and Google, then initialize clients."""
        context = ctx.obj
        # Ensure context contains the necessary data
        spreadsheet_id = context.get('spreadsheet_id')
        sheet_name = context.get('sheet_name')
        services = context.get('services')

        click.echo("Authenticating with mtumishi...")

        # Check authentication using mtumishi
        is_authenticated = mtumishi.authenticate(context.credentials['username'], context.credentials['password'])
        if not is_authenticated:
            click.echo(f"Authentication failed for {context.credentials['username']}. Exiting...")
            return

        click.echo(f"Authenticated {context.credentials['username']} with UltraBet. Initializing Google clients...")

        # Initialize and authenticate Google clients
        clients = mtumishi.initialize_google_auth_and_clients(ctx, spreadsheet_id, sheet_name, selected_services=services)
        if clients is None:
            click.echo("Google authentication failed. Exiting...")
            return

        click.echo("Clients initialized successfully.")


    @group.command(name="run-scripts")
    @click.argument('bookie', required=False)
    @click.pass_context
    def run_scripts(self,  bookie):
        """Run specific or all betting client scripts."""
        context = ctx.obj
        if not context or 'betting' not in context.get('credentials', {}):
            click.echo("No clients initialized. Please authenticate first.")
            return

        # Extract relevant data from the context
        spreadsheet_id = context.get('spreadsheet_id')
        sheet_name = context.get('sheet_name')

        processes = []
        bookie_list = [bookie] if bookie else self.bookie_scripts.keys()  # Run specific or all bookie scripts

        for bookie_name in bookie_list:
            script = self.bookie_scripts.get(bookie_name)
            if not script:
                logger.error(f"No script found for {bookie_name}. Skipping.")
                continue

            script_path = os.path.join(self.plugin_folder, script)

            client_info = context.get('credentials', {}).get(bookie_name)
            if client_info:
                username = client_info.get('username')
                password = client_info.get('password')

                if not username or not password:
                    logger.error(f"Missing credentials for {bookie_name}")
                    continue  # Skip if credentials are missing

                command = [
                    'python3',
                    script_path,
                    username,
                    password,
                    bookie_name,
                    spreadsheet_id,
                    sheet_name,
                    '--update-spreadsheet', '/path/to/your/client_secret.json'  # Modify as needed
                ]

                logger.info(f"Starting script for {bookie_name}")

                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                processes.append((process, bookie_name))

        # Wait for processes to complete and handle output
        for process, bookie_name in processes:
            stdout, stderr = process.communicate()
            self.process_output(ctx, stdout, stderr, bookie_name)


    @click.pass_context
    def uptimerobot(ctx):
        pass

    @group.command('uptmrbt_add')
    @click.option('--alert', '-a', default=True)
    @click.argument('name')
    @click.argument('url')
    @click.pass_obj
    def uptimerobot_add(ctx, name, url, alert):
        pass


# Create an instance of the SportsBettingGroup class
betting_group = SportsBettingGroup()
