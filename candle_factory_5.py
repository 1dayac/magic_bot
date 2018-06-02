#clanteam

from selenium import webdriver
import time
import sys
from datetime import datetime
import re
from number_parser import DigitsClassifier
from card import Card, Price

import sqlite3
con = sqlite3.connect('cards.db', isolation_level=None)
cursor = con.cursor()
tb_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name='records'"

if not con.execute(tb_exists).fetchone():
    c = cursor.execute("CREATE TABLE records(Id TEXT PRIMARY KEY, CardName TEXT, SetName TEXT, BuyPrice REAL, SellPrice REAL, "
                "BotNameSeller TEXT, BotNameBuyer TEXT, Time TEXT, Number INT, Foil INT)")
else:
    print("Table exists")

def is_basic_land(card):
    return card.name == "Swamp" or card.name == "Island" or card.name == "Mountain" or card.name == "Plains" or card.name == "Forest" or card.name.startswith("Urza's")


import platform

if platform.system() == "Windows":
    chromedriver_path = r"C:\Users\dmm2017\Desktop\magic_bot\chromedriver.exe"
else:
    chromedriver_path = "/home/dmm2017/PycharmProjects/candle_factory/chromedriver"

option = webdriver.ChromeOptions()

chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")
driver_library = webdriver.Chrome(chromedriver_path, options= chrome_options)
driver_library.get("https://www.mtgowikiprice.com/")



class HotlistProcessor(object):

    def __init__(self):
        self.start_from = "1"
        self.set = "1"
        self.rows = []
        self.driver_hotlist = None
        self.start = None
        self.i = 0
        self.digit_clasiffier = DigitsClassifier()

    def openHotlist(self):
        url = "http://www.mtgotraders.com/hotlist/#/"
        chrome_options = webdriver.ChromeOptions()
        #chrome_options.add_argument("--headless")
        self.driver_hotlist = webdriver.Chrome(chromedriver_path, options = chrome_options)
        self.driver_hotlist.get(url)
        time.sleep(4)
        elems = self.driver_hotlist.find_elements_by_class_name('btn')
        elems[0].click()
        elems_2 = self.driver_hotlist.find_element_by_xpath(
            "//*[@id=\"mainContent\"]/div[2]/div[1]/div[2]/div[4]/div[1]/span[2]/span/ul/li[5]")
        elems_2.click()
        time.sleep(4)
        table = self.driver_hotlist.find_element_by_id('main-table')
        rows = table.find_elements_by_tag_name('tr')
        return rows


    def get_price(self, e, botname, card):
        return self.digit_clasiffier.get_price(e, botname, card)

    def processHotlist(self):
        self.rows = self.openHotlist()
        self.start = time.time()
        while True:
            try:
                while self.i < len(self.rows):
                    self.processRow(self.rows[self.i])
                    self.i += 1
                    end = time.time()
                    if end - self.start > 600:
                        raise Exception
                break
            except:
                print(sys.exc_info()[1])
                while True:
                    try:
                        self.driver_hotlist.quit()
                        self.driver_hotlist = None
                        self.rows = self.openHotlist()
                        print(len(self.rows))
                        time.sleep(5)
                        self.start = time.time()
                        break
                    except:
                        pass

    def processRow(self, row):
        columns = row.find_elements_by_tag_name('td')
        if len(columns) < 3:
            return
        setname = columns[0].text
        self.set = setname
        cardname = columns[1].text

        price = float(columns[3].text)
        if setname < self.start_from:
            return
        if price < 0.05:
            return
        foil = cardname.endswith("*")
        if foil:
            cardname = cardname[:-7]

        print(setname + " " + cardname + " " + str(price))
        price_struct = Price("", price, 10000, "Hotlistbot3", "", 0)
        card = Card(cardname, setname, price_struct, foil)
        if is_basic_land(card):
            return
        p = None
        if not foil:
            p = self.ParseMtgolibrary(driver_library, card)
        if foil:
            p = self.ParseMtgolibraryFoil(driver_library, card)

        if not p:
            return

        if price - p.sell_price > 0.05 and p.sell_price != 10000:
            print("High diff: " + p.bot_name_sell + " " + str(price - p.sell_price))
            cursor.execute("INSERT OR REPLACE INTO records VALUES(?,?,?,?,?,?,?,?,?,?)",
                           [setname + cardname, cardname, setname, price, p.sell_price, p.bot_name_sell, "HotListBot3",
                            datetime.now(), min(4, p.number), 1 if foil else 0])

    def ParseMtgolibraryFoil(self, driver, card, parse_buyers = False):
        setname = card.set.upper()
        if setname.startswith("BOO") or setname.startswith("PRM"):
            return False
        setname, url, driver = self.MtgoLibraryGoToCard(driver, card)
        try:
            link = driver.find_element_by_link_text('View Foil')
        except:
            return False
        link.click()
        time.sleep(4)
        return self.ParseMtgolibraryInternal(driver, card, url, parse_buyers)

    def MtgoLibraryGoToCard(self, driver, card):
        setname = card.set.upper()
        input_element = driver.find_element_by_id("_cardskeyword")
        input_element.clear()
        input_element.send_keys(card.name + " " + setname)
        driver.find_elements_by_css_selector("button")[1].click()
        url = driver.current_url
        return setname, url, driver

    def ParseMtgolibraryInternal(self, driver, card, url, parse_buyers):
        setname = card.set
        elem = driver.find_elements_by_class_name("sell_row")
        buy_price = -1
        sell_price = 10000
        if len(elem) == 0:
            return False
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
                if not bot_name_sell.startswith("ManaTrade") and first != True:
                    continue
                if bot_name_sell == "":
                    continue
                first = False
            except:
                continue
            sell_price = self.get_price(e, bot_name_sell, card)
            break
        if not parse_buyers:
            return Price(url, 0, sell_price, "", bot_name_sell, number)

        elem2 = driver.find_elements_by_class_name("buy_row")
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
            buy_price = self.get_price(e, bot_name_buy, card)
            if tickets > buy_price:
                break
        return Price(url, buy_price, sell_price, bot_name_buy, bot_name_sell, number)


    def ParseMtgolibrary(self, driver, card, parse_buyers = False):
        setname = card.set.upper()
        if setname.startswith("BOO") or setname.startswith("PRM"):
            return False
        setname, url, driver = self.MtgoLibraryGoToCard(driver, card)
        time.sleep(7)
        return self.ParseMtgolibraryInternal(driver, card, url, parse_buyers)

while True:

    try:
        processeor = HotlistProcessor()
        processeor.processHotlist()
    except:
        pass
