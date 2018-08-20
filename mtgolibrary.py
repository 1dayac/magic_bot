from selenium import webdriver
import sqlite3
from datetime import datetime
from card import Card, Price
import time
import platform
import re
from number_parser import DigitsClassifier
from trusted_bots import *

if platform.system() == "Windows":
    chromedriver_path = r"C:\Users\dmm2017\Desktop\magic_bot\chromedriver.exe"
else:
    chromedriver_path = "/home/dmm2017/PycharmProjects/candle_factory/chromedriver"


class MtgoLibraryParser(object):
    def __init__(self):
        self.main_url = "https://www.mtgowikiprice.com/"
        chrome_options = webdriver.ChromeOptions()
        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(chromedriver_path, options= chrome_options)
        self.driver.get(self.main_url)
        self.digit_clasiffier = DigitsClassifier()
        self.card_count = 0

    def restart(self):
        self.driver.quit()
        self.main_url = "https://www.mtgowikiprice.com/"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(chromedriver_path, options= chrome_options)
        self.driver.get(self.main_url)

    def ParseMtgolibraryFoil(self, card, parse_buyers = False):
        setname = card.set.upper()
        if setname.startswith("BOO") or setname.startswith("PRM"):
            return False
        setname, url = self.MtgoLibraryGoToCard(card)
        try:
            link = self.driver.find_element_by_link_text('View Foil')
        except:
            return False
        link.click()
        time.sleep(4)
        return self.ParseMtgolibraryInternal(card, url, parse_buyers)


    def get_price_from_image(self, e, botname, card):
        return self.digit_clasiffier.get_price(e, botname, card)

    def MtgoLibraryGoToCard(self, card):
        setname = card.set.upper()
        input_element = self.driver.find_element_by_id("_cardskeyword")
        input_element.clear()
        input_element.send_keys(card.name + " " + setname)
        self.driver.find_elements_by_css_selector("button")[1].click()
        url = self.driver.current_url
        return setname, url

    def ParseMtgolibraryInternal(self, card, url, parse_buyers):
        setname = card.set
        elem = self.driver.find_elements_by_class_name("sell_row")
        buy_price = -1
        sell_price = 10000
        if len(elem) == 0:
            return None
        first = True
        number = 0
        bot_name_sell = ""
        for e in elem:
            try:
                table_setname = e.find_elements_by_class_name("setname")[0].text
                if table_setname != setname:
                    continue
                number = int(e.find_elements_by_class_name("sell_quantity")[0].text)
                bot_name_sell = e.find_elements_by_class_name("bot_name")[0].text
                if bot_name_sell == "":
                    continue
                if bot_name_sell not in trusted_sell_bots:
                    print("Best price - " + bot_name_sell)
                    continue
            except:
                continue
            sell_price = self.get_price_from_image(e, bot_name_sell, card)
            break
        if not parse_buyers:
            return Price(url, 0, sell_price, "", bot_name_sell, number)

        elem2 = self.driver.find_elements_by_class_name("buy_row")
        bot_name_buy = ""
        number = 0
        for e in elem2:
            try:
                bot_name_buy = e.find_elements_by_class_name("bot_name")[0].get_attribute('textContent').strip()
                number = int(e.find_elements_by_class_name("buy_quantity")[0].get_attribute('textContent').strip().replace("+", ""))

                if bot_name_buy == "":
                    continue

                table_setname = e.find_elements_by_class_name("setname")[0].get_attribute('textContent').strip()
                if table_setname != setname:
                    continue

                tickets = float(re.split("[+\-]", e.find_elements_by_class_name("tickets")[0].get_attribute('textContent').strip())[0])
            except:
                continue
            buy_price = self.get_price_from_image(e, bot_name_buy, card)
            if tickets > buy_price:
                break
        return Price(url, buy_price, sell_price, bot_name_buy, bot_name_sell, number)


    def ParseMtgolibrary(self, card, parse_buyers = False):
        setname = card.set.upper()
        if setname.startswith("BOO") or setname.startswith("PRM"):
            return None
        setname, url = self.MtgoLibraryGoToCard(card)
        time.sleep(7)
        return self.ParseMtgolibraryInternal(card, url, parse_buyers)

    def get_price(self, card):
        self.card_count += 1
        if self.card_count % 100 == 0:
            self.restart()
        if card.foil:
            return self.ParseMtgolibraryFoil(card)
        else:
            return self.ParseMtgolibrary(card)