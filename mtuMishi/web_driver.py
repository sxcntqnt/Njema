import time
import psutil

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options
from loguru import logger
from aenum import Constant

TIMEOUT = 60


def disable_images_firefox_profile():
    """Summary
    Returns:
        Object: FirefoxProfile
    """
    # Get the Firefox profile object
    firefoxProfile = webdriver.FirefoxProfile()
    # Disable images
    firefoxProfile.set_preference("permissions.default.image", 2)
    # Disable Flash
    firefoxProfile.set_preference(
        "dom.ipc.plugins.enabled.libflashplayer.so", "false"
    )
    # Set the modified profile while creating the browser object
    return firefoxProfile

class BetHistoryTableColumn(Constant):
    (TICKET, EVENT_DATE, TOURNAMENT, EVENT, SELECTION, BET_TYPE,
     STAKE, POTENTIAL_WIN, STATUS) = range(1, 10)


class BetStatus(Constant):
    ALL = "Filter by wager status"
    UNSETTLED = "Unsettled"
    WON = "Won"
    LOST = "Lost"
    VOID = "Void"


class BetMonth(Constant):
    (JANUARY, FEBRUARY, MARCH, APRIL, MAY, JUNE, JULY,
     AUGUST, SEPTEMBER, OCTOBER, NOVEMBER, DECEMBER) = range(1, 13)
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30"
    ALL = "all"


class WebDriverSetup(object):

    def __init__(self, headless):
        self._timeout = TIMEOUT
        self._options = Options()
        self._options.headless = headless
        self._profile = disable_images_firefox_profile()
        self.logger = logger

        self.driver = webdriver.Firefox(
            firefox_profile=self._profile, options=self._options, timeout=self._timeout
        )
        time.sleep(0.3)
        if self._options.headless:
            self.logger.info("Headless Firefox Initialized.")

    def open_session(self, url):
        try:
            self.logger.debug(f"Navigating to {url}.")
            self.driver.get(url)
            self.driver.set_page_load_timeout(self._timeout)
            self.logger.debug("Successfully opened the url.")
            time.sleep(0.5)
        except TimeoutException:
            self.logger.exception("Timed-out while loading page.")
            self.close_session()

    def close_session(self):
        """Close browser and cleanup"""
        self.logger.info("Closing the browser...")
        self.driver.close()
        self.driver.quit()
        time.sleep(10)
        PROCNAME = "geckodriver"
        self.logger.info("Cleaning up by killing {} process", PROCNAME)
        _ = [
            proc.terminate()
            for proc in psutil.process_iter()
            if proc.name() == PROCNAME
        ]
        self.logger.info("Done...")

