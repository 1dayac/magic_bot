#clanteam

from selenium import webdriver
import time
import sys
from datetime import datetime
import re
from mtgolibrary import MtgoLibraryParser
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


import win32api, win32con, win32process

def setaffinity():
    return
    pid  = win32api.GetCurrentProcessId()
    mask = 3 # core 7
    handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
    win32process.SetProcessAffinityMask(handle, mask)
setaffinity()

import platform

if platform.system() == "Windows":
    chromedriver_path = r"C:\Users\IEUser\Desktop\magic_bot\chromedriver.exe"
else:
    chromedriver_path = "/home/dmm2017/PycharmProjects/candle_factory/chromedriver"


class HotlistProcessor(object):

    def __init__(self):
        self.start_from = "1"
        self.set = "1"
        self.rows = []
        self.driver_hotlist = None
        self.start = None
        self.i = 0
        self.mtgolibrary_parser = MtgoLibraryParser()

    def restart(self):
        self.start_from = "1"
        self.set = "1"
        self.rows = []
        self.driver_hotlist.quit()
        self.driver_hotlist = None
        self.start = None
        self.i = 0
        self.mtgolibrary_parser.restart()

    def openHotlist(self):
        url = "http://www.mtgotraders.com/hotlist/#/"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        self.driver_hotlist = webdriver.Chrome(chromedriver_path, options = chrome_options)
        self.driver_hotlist.get(url)
        time.sleep(60)
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
                        raise Exception
                break
            except:
                print(sys.exc_info()[1])
                while True:
                    try:
                        temp_i = self.i
                        self.restart()
                        self.i = temp_i
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
        if is_basic_land(card) or ((card.set == "MS2" or card.set == "MS3") and card.foil):
            return

        p = self.mtgolibrary_parser.get_price(card)

        if not p:
            return

        if price - p.sell_price > 0.025 and p.sell_price != 10000:
            print("High diff: " + p.bot_name_sell + " " + str(price - p.sell_price))
            cursor.execute("INSERT OR REPLACE INTO records VALUES(?,?,?,?,?,?,?,?,?,?)",
                           [setname + cardname, cardname, setname, price, p.sell_price, p.bot_name_sell, "HotListBot3",
                            datetime.now(), min(4, p.number), 1 if foil else 0])


while True:
    try:
        processeor = HotlistProcessor()
        processeor.processHotlist()
    except:
        processeor.restart()
