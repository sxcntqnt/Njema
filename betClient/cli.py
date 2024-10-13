import click
from datetime import datetime

# Define SportsBettingGroup class with methods as commands
class SportsBettingGroup:

    @click.group(name="sportsbt")
    def sports_betting():
        """Manage sports betting portfolio."""
        pass

# Create an instance of the SportsBettingGroup class
betting_group = SportsBettingGroup()
