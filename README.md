[![Actions Status](https://github.com/kmadisa/mind-your-stonks/workflows/Mind%20Your%20Stonks/badge.svg)](https://github.com/kmadisa/mind-your-stonks/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub last commit](https://img.shields.io/github/last-commit/kmadisa/mind-your-stonks.svg)
![GitHub issues](https://img.shields.io/github/issues/kmadisa/mind-your-stonks.svg)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ce9da614c0034a3ca373513e119705e0)](https://www.codacy.com/manual/katleho.madisa47/mind-your-stonks?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=kmadisa/mind-your-stonks&amp;utm_campaign=Badge_Grade)

# Mind your *stonks*

![35a1ly](https://user-images.githubusercontent.com/16665803/78668014-4390fb00-78da-11ea-8a81-4d3de52417f1.jpg)

## The Story
[BET.co.za](https://bet.co.za) does not have an easier way to track the changes in the user's account balance. All that it displays is the current account balance. In order to get an idea of **how much you had vs how much you have** in your account, you have to sift through lots and lots of pages on the transaction history, not to mention the brutal experience the user will have to go through to compute the **account's balance at a particular moment in time** from all that information.

The purpose of this project is to provide [BET.co.za](https://bet.co.za) clients an easier way to keep track of the changes occurring in their account balance.

Basically there is utility script that run and log into the client's [BET.co.za](https://bet.co.za) account (using [Selenium](https://selenium-python.readthedocs.io/)) and read the value of the current balance and uploads the data to a [Google Sheets](https://docs.google.com/spreadsheets/u/0/), where then it can be visualized.


&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **AND JUST LIKE THAT YOU KNOW THE RISE & FALL OF YOUR STONKS !!!!**


## Get Started

1. Obtain Google API for authentication:
    *   Follow the instructions [here](https://gspread.readthedocs.io/en/latest/oauth2.html#oauth-credentials)

2. Ensure that `geckodriver` for Firefox is installed.
    *   Download [geckodriver](https://github.com/mozilla/geckodriver)
        *   ```wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz```
        *   Extract: ```tar -xvzf geckodriver-v0.24.0-linux64.tar.gz```
    *   `sudo cp geckodriver /usr/local/bin`

3. Install the library:
    *   `python setup.py install`

4. Upload a copy of the [spreadsheet](https://docs.google.com/spreadsheets/d/1k--fJt5qC191RMHH3D2MbhRhaIJb__WTEBjOL1rcksc/edit?usp=sharing) to your own GDrive or [GSpeadsheet](https://docs.google.com/spreadsheets).

![Screenshot from 2019-12-10 15-32-48](https://user-images.githubusercontent.com/16665803/70533841-8debb080-1b62-11ea-82a6-a4aa9e188ef3.png)
Figure 1. A snapshot of the spreadsheet and the respective columns (Note: Numbers may or may not have been doctored!).

#### Table columns
   * *Date*: date reading was made (yyyy-mm-dd).
   * *Timestamp*: indicated when the script logged into the account hh:mm PM/AM.
   * *Balance*: the current balance in the account in S.A rands.
   * *Money in bets*: the amount of money placed in a bet which is still unresolved.
   * *Actual Loss/Gain*: difference between the previous known balance and the current one
                         (+ money in bets).
   * *% Increase*: calculated from the previous known balance and the current one (+ money in bets).

##### Other fields
   * *Opening Balance*: te amount of money in the account at the first of the month.
   * *Closing Balance*: te amount of money in the account at the end of the current month.
   * *Graph*: a plot of the account's balance.

## Usage

```bash
python query_balance.py -h
usage: query_balance.py [-h] [--update-spreadsheet UPDATE_SPREADSHEET]
                        username password

Scrape the BET.co.za website to obtain the account balance. It also writes the
data to a Google Spreadsheet.

positional arguments:
  username              Bet.co.za registered email address
  password              Bet.co.za account password.

optional arguments:
  -h, --help            show this help message and exit
  --update-spreadsheet UPDATE_SPREADSHEET
                        Update spreadsheet with new data. This requires the
                        client_secret.json file for authentication. It is
                        downloaded from the Google Developers' Console.
```

Typical usage:
```bash
query_balance.py $USERNAME $PASSWORD --update-spreadsheet ./client_secrets.json
```

## Github Actions automated daily balance reader
Github Actions can automatically run your Google App Engine based application, by encrypting your `clients_secrets.json` file and pushing it to `GitHub`.
See example: https://github.com/kmadisa/mind-your-stonks/blob/master/.github/workflows/update_stonks_sheet.yml


## Feedback

Feel free to fork it or send me a PR to improve it.
