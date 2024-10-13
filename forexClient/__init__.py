import click
from datetime import datetime

# Define SportsBettingGroup class with methods as commands
class forexGroup:

    @click.group()
    def forex():
        """Manage your forex portfolio."""
        pass

# Create an instance of the SportsBettingGroup class
forex_group = forexGroup()
