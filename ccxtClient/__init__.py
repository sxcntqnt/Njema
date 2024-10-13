import click
from datetime import datetime

# Define SportsBettingGroup class with methods as commands
class cryptoGroup:

    @click.group()
    def crypto():
        """Manage crypto  portfolio."""
        pass

# Create an instance of the SportsBettingGroup class
crypto_group = cryptoGroup()
