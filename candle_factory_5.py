#clanteam

from selenium import webdriver
import time

import sys
import pickle
from datetime import datetime
import signal


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
                "BotNameSeller TEXT, BotNameBuyer TEXT, Time TEXT, Number INT)")
else:
    print("Table exists")

class Price:

    def __init__(self):
        self.url = ""
        self.buy_price = 0.0
        self.sell_price = 0.0
        self.bot_name = ""
        self.number = 0

    def __init__(self, url, buy_price, sell_price, bot_name, number):
        self.url = url
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.bot_name = bot_name
        self.number = number

    def __str__(self):
        return str(self.buy_price) + "\t" + str(self.sell_price) + "\t"



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

import platform

if platform.system() == "Windows":
    chromedriver_path = r"C:\Users\IEUser\Desktop\magic_bot\magic_bot\chromedriver.exe"
else:
    chromedriver_path = "/home/dmm2017/PycharmProjects/candle_factory/chromedriver"

option = webdriver.ChromeOptions()

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
driver_library = webdriver.Chrome(chromedriver_path, options= chrome_options)
driver_library.get("https://www.mtgowikiprice.com/")









class HotlistProcessor(object):

    def __init__(self):
        self.start_from = "1"
        self.set = "1"
        self.rows = []
        self.driver_hotlist = None
        self.start = None

    def openHotlist(self):
        url = "http://www.mtgotraders.com/hotlist/#/"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        driver_hotlist = webdriver.Chrome(chromedriver_path, options = chrome_options)
        driver_hotlist.get(url)
        time.sleep(4)
        elems = driver_hotlist.find_elements_by_class_name('btn')
        elems[0].click()
        elems_2 = driver_hotlist.find_element_by_xpath(
            "//*[@id=\"mainContent\"]/div[2]/div[1]/div[2]/div[4]/div[1]/span[2]/span/ul/li[5]")
        elems_2.click()
        time.sleep(4)
        table = driver_hotlist.find_element_by_id('main-table')
        rows = table.find_elements_by_tag_name('tr')
        return driver_hotlist, rows







    def processHotlist(self):
        self.driver_hotlist, self.rows = self.openHotlist()
        self.start = time.time()
        for row in self.rows:
            try:
                self.processRow(row)
                end = time.time()
                if end - self.start > 600:
                    raise Exception
            except:
                while True:
                    try:
                        #self.driver_hotlist.quit()
                        self.driver_hotlist = None
                        self.driver_hotlist, self.rows = self.openHotlist()
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
        if cardname.endswith("*") or price < 0.05:
            return

        print(setname + " " + cardname + " " + str(price))
        card = Card(cardname, setname, price)
        p = self.ParseMtgolibrary(driver_library, card)
        if not p:
            return

        if price - p.sell_price > 0.05 and p.sell_price != 10000:
            print("High diff: " + p.bot_name + " " + str(price - p.sell_price))
            cursor.execute("INSERT OR REPLACE INTO records VALUES(?,?,?,?,?,?,?,?,?)",
                           [setname + cardname, cardname, setname, price, p.sell_price, p.bot_name, "HotListBot3",
                            datetime.now(), min(4, p.number)])
    def get_symbol(self, img_src):
        if img_src in prices_d.keys():
            return prices_d[img_src]
        else:
            symbol = sys.stdin.readline()
            prices_d[img_src] = symbol
            pickle.dump(prices_d, open("obj/dict.pkl", "wb"))
            return symbol

    def ParseMtgolibrary(self, driver, card):
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
        number = 0
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
                number = int(e.find_elements_by_class_name("sell_quantity")[0].text)
                bot_name = e.find_elements_by_class_name("bot_name")[0].text
                if not bot_name.startswith("ManaTrade") and first != True:
                    continue
                if bot_name == "":
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
                print(img_src)
                symbol = self.get_symbol(img_src)
                res.append(symbol)
            # print("".join(res).replace('\n', ''))
            try:
                sell_price = float("".join(res).replace('\n', ''))
            except:
                sell_price = 100000
            break
        return Price(url, 0, sell_price, bot_name, number)


processeor = HotlistProcessor()
processeor.processHotlist()