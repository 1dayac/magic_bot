#clanteam

from selenium import webdriver
import time
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import sys
from datetime import datetime
prices_d = {}

import sqlite3
con = sqlite3.connect('cards.db', isolation_level=None)
cursor = con.cursor()
tb_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name='records'"

if not con.execute(tb_exists).fetchone():
    c = cursor.execute("CREATE TABLE records(Id TEXT, CardName TEXT, SetName TEXT, BuyPrice REAL, SellPrice REAL, "
                "BotNameSeller TEXT, BotNameBuyer TEXT, Time TEXT)")
else:
    print("Table exists")

class Price:

    def __init__(self):
        self.url = ""
        self.buy_price = 0.0
        self.sell_price = 0.0
        self.bot_name = ""

    def __init__(self, url, buy_price, sell_price, bot_name):
        self.url = url
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.bot_name = bot_name

    def __str__(self):
        return str(self.buy_price) + "\t" + str(self.sell_price) + "\t"


def ParseMtgolibrary(driver, card):
    setname = card.set.upper()
    if setname.startswith("BOO"):
        return False
    input_element = driver.find_element_by_id("_cardskeyword")
    input_element.clear()
    input_element.send_keys(card.name + " " + setname)
    driver.find_elements_by_css_selector("button")[1].click()
    url = driver.current_url
    time.sleep(7)
    bot_name = ""
    elem = driver.find_elements_by_class_name("sell_row")
    buy_price = -1
    sell_price = 10000
    if len(elem) == 0:
        return False
    first = True
    for e in elem:
        price = ""
        try:
            table_setname = e.find_elements_by_class_name("setname")[0].text
            if table_setname != setname:
                continue

            bot_name = e.find_elements_by_class_name("bot_name")[0].text
            if not bot_name.startswith("ManaTrade") and first != True:
                continue
            if bot_name == "":
                continue

            #print(e.find_elements_by_class_name("bot_name")[0].text)
            #print(e.find_elements_by_class_name("sell_quantity")[0].text)
            first = False
        except:
            continue
        images = e.find_element_by_class_name("sell_price_round")
        index = 0
        res = []
        for image in images.find_elements_by_tag_name('img'):
            index += 1
            img_src = image.get_attribute("src")
            print(img_src)
            if img_src in prices_d.keys():
                res.append(prices_d[img_src])
                continue
            symbol = sys.stdin.readline()
            prices_d[img_src] = symbol
            res.append(symbol)
        #print("".join(res).replace('\n', ''))
        try:
            sell_price = float("".join(res).replace('\n', ''))
        except:
            sell_price = 100000
        break

    return Price(url, 0, sell_price, bot_name)

class Card:
    def __init__(self):
        self.name = ""
        self.set = ""
        self.prices = []

    def __init__(self, name, set, prices):
        self.name = name
        self.set = set
        self.prices = [prices]

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
        return self.name + "\t" + self.set + "\t" + str1 + "\t" + str(self.MaxBuyPrice() - self.MinSellPrice())


chromedriver_path = "/home/dmm2017/PycharmProjects/candle_factory/chromedriver"

driver_library = webdriver.Chrome(chromedriver_path)
driver_library.get("https://www.mtgowikiprice.com/")




def processRow(row):
    columns = row.find_elements_by_tag_name('td')
    if len(columns) < 3:
        return
    setname = columns[0].text
    cardname = columns[1].text
    price = float(columns[3].text)

    if cardname.endswith("*") or price < 0.05:
        return

    print(setname + " " + cardname + " " + str(price))
    card = Card(cardname, setname, price)
    p = ParseMtgolibrary(driver_library, card)
    if not p:
        return


    if price - p.sell_price > 0.05 and p.sell_price != 10000:
        print("High diff: " + p.bot_name + " " + str(price - p.sell_price))
        cursor.execute("INSERT INTO records VALUES(?,?,?,?,?,?,?,?)",
                       [setname + cardname, cardname, setname, price, p.sell_price, p.bot_name, "HotListBot3",
                        datetime.now()])



def processHotlist():
    url = "http://www.mtgotraders.com/hotlist/#/"
    driver_hotlist = webdriver.Chrome(chromedriver_path)
    driver_hotlist.get(url)
    time.sleep(4)
    elems = driver_hotlist.find_elements_by_class_name('btn')
    elems[0].click()
    elems_2 = driver_hotlist.find_element_by_xpath("//*[@id=\"mainContent\"]/div[2]/div[1]/div[2]/div[4]/div[1]/span[2]/span/ul/li[5]")
    elems_2.click()
    time.sleep(4)
    table = driver_hotlist.find_element_by_id('main-table')
    rows = table.find_elements_by_tag_name('tr')
    for row in rows:
        processRow(row)

processHotlist()

