#clanteam

from selenium import webdriver
import time

import sys
import pickle
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.request
import itertools
import re

try:
    f = open("obj/dict.pkl", 'rb')
    prices_d = pickle.loads(f.read())
except:
    prices_d = {}
print(prices_d)
import sqlite3
con = sqlite3.connect('cards.db', isolation_level=None)
cursor = con.cursor()
tb_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name='records'"

if not con.execute(tb_exists).fetchone():
    c = cursor.execute("CREATE TABLE records(Id TEXT PRIMARY KEY, CardName TEXT, SetName TEXT, BuyPrice REAL, SellPrice REAL, "
                "BotNameSeller TEXT, BotNameBuyer TEXT, Time TEXT, Number INT, Foil INT)")
else:
    print("Table exists")

class Price:

    def __init__(self):
        self.url = ""
        self.buy_price = 0.0
        self.sell_price = 0.0
        self.bot_name_buy = ""
        self.bot_name_sell = ""
        self.number = 0

    def __init__(self, url, buy_price, sell_price, bot_name_buy, bot_name_sell, number):
        self.url = url
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.bot_name_buy = bot_name_buy
        self.bot_name_sell = bot_name_sell
        self.number = number

    def __str__(self):
        return str(self.buy_price) + "\t" + self.bot_name_buy + "\t" + str(self.sell_price) + "\t" + self.bot_name_sell +"\t"



class Card:
    def __init__(self):
        self.name = ""
        self.set = ""
        self.foil = False
        self.prices = []

    def __init__(self, name, set, prices, foil):
        self.name = name
        self.set = set
        self.prices = [prices]
        self.foil = foil

    def AddPrice(self, price):
        self.prices.append(price)

    def __hash__(self):
        return hash(self.name + self.set)

    def MaxBuyPrice(self):
        prices = [price.buy_price for price in self.prices if price.buy_price > 0]
        try:
            return max(prices)
        except:
            return 0.0

    def MinSellPrice(self):
        prices = [price.sell_price for price in self.prices if price.sell_price > 0]
        try:
            return min(prices)
        except:
            return 100000.0

    def __str__(self):
        str1 = ""
        for price in self.prices:
            str1 += str(price)
        return self.name + "\t" + self.set + "\t" + str(self.foil) + "\t" + str1 + "\t" + str(self.MaxBuyPrice() - self.MinSellPrice())

import platform

if platform.system() == "Windows":
    chromedriver_path = r"C:\Users\meles\PycharmProjects\magic_bot\chromedriver.exe"
else:
    chromedriver_path = "/home/dmm2017/PycharmProjects/candle_factory/chromedriver"

option = webdriver.ChromeOptions()

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
driver_library = webdriver.Chrome(chromedriver_path, options= chrome_options)
driver_library.get("https://www.mtgowikiprice.com/")









class HotlistProcessor(object):

    def __init__(self):
        self.start_from = "BOO"
        self.set = "1"
        self.rows = []
        self.driver_hotlist = None
        self.start = None
        self.i = 0

    def openHotlist(self):
        url = "http://www.mtgotraders.com/hotlist/#/"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
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
                        raise E
                break
            except:
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
    def get_symbol(self, img_src):
        if img_src in prices_d.keys():
            return prices_d[img_src]
        else:
            print(img_src)
            symbol = sys.stdin.readline()
            prices_d[img_src] = symbol
            pickle.dump(prices_d, open("obj/dict.pkl", "wb"))
            return symbol

    def ParseMtgolibraryFoil(self, driver, card, parse_buyers = False):
        setname = card.set.upper()
        if setname.startswith("BOO"):
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
        bot_name = ""
        setname = card.set
        number = 0
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

                # print(e.find_elements_by_class_name("bot_name")[0].text)
                # print(e.find_elements_by_class_name("sell_quantity")[0].text)
                first = False
            except:
                continue
            images = e.find_element_by_class_name("sell_price_round")
            index = 0
            res = []
            for image in images.find_elements_by_tag_name('img'):
                index += 1
                img_src = image.get_attribute("src")
                symbol = self.get_symbol(img_src)
                res.append(symbol)
            # print("".join(res).replace('\n', ''))
            try:
                sell_price = float("".join(res).replace('\n', ''))
            except:
                sell_price = 100000
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
            images = e.find_element_by_class_name("buy_price_round")
            index = 0
            res = []
            for image in images.find_elements_by_tag_name('img'):
                index += 1
                img_src = image.get_attribute("src")
                symbol = self.get_symbol(img_src)
                res.append(symbol)
            try:
                buy_price = float("".join(res).replace('\n', ''))
            except:
                buy_price = -1
            if tickets > buy_price:
                break
        return Price(url, buy_price, sell_price, bot_name_buy, bot_name_sell, number)


    def ParseMtgolibrary(self, driver, card, parse_buyers = False):
        setname = card.set.upper()
        if setname.startswith("BOO"):
            return False
        setname, url, driver = self.MtgoLibraryGoToCard(driver, card)
        time.sleep(7)
        return self.ParseMtgolibraryInternal(driver, card, url, parse_buyers)

while True:
    processeor = HotlistProcessor()
    processeor.processHotlist()
exit(0)
new_pricelists = [#"https://www.mtggoldfish.com/index/DOM#online",
                  #"https://www.mtggoldfish.com/index/KLD#online",
                  #"https://www.mtggoldfish.com/index/AER#online",
                  "https://www.mtggoldfish.com/index/IN#online",
                  "https://www.mtggoldfish.com/index/M11#online",
                  "https://www.mtggoldfish.com/index/ARB#online",
                  "https://www.mtggoldfish.com/index/TPR#online"]

cards = []

def processPricelist(url):
    soup = BeautifulSoup(urllib.request.urlopen(url), 'html.parser')
    table = soup.findAll("table", {"class": "tablesorter-bootstrap-popover-online"})[0]
    rows1 = table.findChildren(['tr'])
    for i in range(1, len(rows1)):
        row = rows1[i]
        cells = row.find_all('td')
        cardname = cells[0].find('a').get_text()
        setname = cells[1].get_text()
        if setname == "DOM":
            setname = "DAR"
        price = float(cells[3].get_text())
        if price < 0.1:
            return
        price_struct = Price("", -1, price, "", "Cardbot4", 0)
        cards.append(Card(cardname, setname, price_struct))

for url in new_pricelists:
    processPricelist(url)

for card in cards:
    price = processeor.ParseMtgolibrary(driver_library, card, True)
    if price == False:
        continue

    if price.buy_price > price.sell_price + 0.05:
        print(card.name + " " + str(price))
        cursor.execute("INSERT OR REPLACE INTO records VALUES(?,?,?,?,?,?,?,?,?)",
                       [card.set + card.name, card.name, card.set, price.buy_price, price.sell_price, price.bot_name_sell,
                        price.bot_name_buy, datetime.now(), min(4, price.number)])

    else:
        print("No" + card.name)


