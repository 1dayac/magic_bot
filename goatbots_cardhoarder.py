from selenium import webdriver
import sqlite3
from datetime import datetime
from card import Card, Price
import time
from mtgolibrary import MtgoLibraryParser
chromedriver_path = r"C:\Users\dmm2017\Desktop\magic_bot\chromedriver.exe"

import win32api, win32con, win32process

def setaffinity():
    pid  = win32api.GetCurrentProcessId()
    mask = 3 # core 7
    handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
    win32process.SetProcessAffinityMask(handle, mask)
setaffinity()

class TopLevelProcessor(object):

    def __init__(self):
        self.processors = []
        self.main_processor = None
        self.database_path = "cards.db"
        con = sqlite3.connect('cards.db', isolation_level=None)
        self.cursor = con.cursor()
        tb_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name='records'"
        if not con.execute(tb_exists).fetchone():
            c = self.cursor.execute(
                "CREATE TABLE records(Id TEXT PRIMARY KEY, CardName TEXT, SetName TEXT, BuyPrice REAL, SellPrice REAL, "
                "BotNameSeller TEXT, BotNameBuyer TEXT, Time TEXT, Number INT, Foil INT)")
        else:
            print("Table exists")


    def RestartAll(self):
        for processor in self.processors:
            processor.restart()
        self.main_processor.restart()

    def AddMainProcessor(self, processor):
        self.main_processor = processor

    def AddProcessor(self, processor):
        self.processors.append(processor)


    def IsHighDiff(self, card):
        best_buy_price = card.BestBuyPrice()
        best_sell_price = card.BestSellPrice()
        print(best_buy_price)
        print(best_sell_price)
        return best_buy_price.buy_price - best_sell_price.sell_price >= 0.05


    def AddToDatabase(self, card):
        best_buy_price = card.BestBuyPrice()
        best_sell_price = card.BestSellPrice()
        print("High diff: " + best_sell_price.bot_name_sell + "," + str(best_sell_price.sell_price) + " " + best_buy_price.bot_name_buy + "," + str(best_buy_price.buy_price)+": " +
              str(best_buy_price.buy_price - best_sell_price.sell_price))
        self.cursor.execute("INSERT OR REPLACE INTO records VALUES(?,?,?,?,?,?,?,?,?,?)",
                       [card.set + card.name, card.name, card.set, best_buy_price.buy_price, best_sell_price.sell_price,
                        best_sell_price.bot_name_sell, best_buy_price.bot_name_buy,
                        datetime.now(), min(4, best_buy_price.number), 1 if card.foil else 0])

    def ParseCards(self):
        for card in self.main_processor.GetCards():
            for processor in self.processors:
                card.prices.append(processor.get_price(card))
            if self.IsHighDiff(card):
                self.AddToDatabase(card)


class GoatBotsParser(object):
    def __init__(self):
        self.main_url = "https://www.goatbots.com/prices"
        chrome_options = webdriver.ChromeOptions()
        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(chromedriver_path, options= chrome_options)
        self.second_driver = webdriver.Chrome(chromedriver_path, options= chrome_options)
        self.current_set = None
        self.card_count = 0


    def restart(self):
        self.second_driver.quit()
        self.main_url = "https://www.goatbots.com/prices"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option("prefs", prefs)
        self.second_driver = webdriver.Chrome(chromedriver_path, options= chrome_options)


    def ProcessRow(self, line):
        href_cell = line.find_element_by_css_selector('a')
        if "/search" in str(href_cell.get_attribute("href")):
            return None
        card_url = href_cell.get_attribute('href')
        self.second_driver.get(card_url)
        card_name = " ".join(self.second_driver.title.split(" ")[:-2])
        if "Full Set" in card_name or "Booster" in card_name:
            return None
        print(card_name)
        p = Price("", -5, 1000, "GoatBots3", "GoatBots3", 4)
        c = Card(card_name, self.current_set, p, 0)
        #return c
        price_block = self.second_driver.find_element_by_id("info_" + self.current_set.lower())
        all_h3 = price_block.find_elements_by_tag_name('h3')
        prices = []
        for h3 in all_h3:
            if "price_value" in h3.get_attribute("class"):
                prices.append(h3.text)
        try:
            buy_price = float(prices[0])
        except:
            buy_price = -1.0
        try:
            sell_price = float(prices[1])
        except:
            sell_price = 100000
        self.second_driver.find_element_by_class_name("cart_icon").click()
        self.second_driver.find_element_by_id("header_cart_icon").click()
        real_sell_price = float(self.second_driver.find_element_by_id("delivery_table").find_elements_by_tag_name("td")[3].find_element_by_tag_name("a").text)
        self.second_driver.find_element_by_id("form_cart_empty_cart").click()
        p = Price("", buy_price - (sell_price - real_sell_price), real_sell_price, "GoatBots3", "GoatBots3", 4)
        c = Card(card_name, self.current_set, p, 0)
        return c

    def GetSet(self):
        set_line = self.driver.find_element_by_xpath("//*[@id=\"text_left\"]/div[1]/h2/a").text
        return set_line[set_line.find("(") +1 : set_line.find(")")]

    def GetCards(self):
            self.driver.get(self.main_url)
            sets = self.driver.find_elements_by_class_name('cardset')
            refs = []
            min_iter = 40

            max_iter = 50
            current_iter = 0
            for set in sets:
                current_iter += 1
                if current_iter < min_iter:
                    continue

                if current_iter == max_iter:
                    break
                try:
                    print(set.find_element_by_tag_name('a').get_attribute('href'))
                    refs.append(set.find_element_by_tag_name('a').get_attribute('href'))
                except:
                    pass
            max_ref = 20
            current_ref = 0

            for ref in refs:
                current_ref += 1
                print("Processing " + ref)
                max_cards = 20
                current = 0
                self.driver.get(ref)
                print(ref)
                self.current_set = self.GetSet()
                for line in self.driver.find_element_by_id('pricesTable').find_elements_by_tag_name('tr'):
                    current += 1
                    if current == max_cards:
                        break
                    if "empty_row" in line.get_attribute('class'):
                        continue
                    if "card" in line.get_attribute('class'):
                        try:
                            card = self.ProcessRow(line)
                        except:
                            continue
                        if card is None:
                            continue
                        if card.MinSellPrice() < 0.3:
                            break
                        else:
                            self.card_count += 1
                            yield card
                            if self.card_count % 100 == 0:
                                self.restart()

class CardHoarderParser(object):
    def __init__(self):
        self.main_url = "https://www.cardhoarder.com/cards"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(chromedriver_path, options= chrome_options)
        self.driver.get(self.main_url)

    def restart(self):
        self.driver.quit()
        self.main_url = "https://www.cardhoarder.com/cards"
        chrome_options = webdriver.ChromeOptions()
        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(chromedriver_path, options= chrome_options)
        self.driver.get(self.main_url)

    def get_price(self, card):
        input_element = self.driver.find_element_by_id("card-search-input")
        input_element.clear()
        input_element.send_keys(card.name)
        self.driver.find_element_by_class_name("btn-search").click()
        table = self.driver.find_element_by_id("search-results-table")
        trs = table.find_elements_by_tag_name("tr")
        final_href = ""
        for tr in trs:
            try:
                reference = tr.find_element_by_tag_name("a").get_attribute('href')
                set = reference.split("/")[-1].split("-")[0].upper()
                if set != card.set or reference.endswith("-foil") or reference.endswith("#"):
                    continue
                final_href = reference
                break
            except:
                pass

        self.driver.get(final_href)
        panel_body = self.driver.find_element_by_class_name('panel-body')
        try:
            sell_price = float(panel_body.find_element_by_class_name('card-ordering-details').text.strip().split(" ")[0])
        except:
            sell_price = 100000.0
        try:
            buy_price = float(panel_body.find_element_by_tag_name('h4').text.split(" ")[-2])
        except:
            buy_price = -1.0
        return Price("", buy_price, sell_price, "CardBuyingBot3", "CardBot3", 4)
import sys, traceback

top_level_processor = TopLevelProcessor()
top_level_processor.AddMainProcessor(GoatBotsParser())
top_level_processor.AddProcessor(CardHoarderParser())
top_level_processor.AddProcessor(MtgoLibraryParser())
while True:
    try:
        top_level_processor.ParseCards()
        top_level_processor.RestartAll()
        break
    except:
        top_level_processor.RestartAll()
        print("Unexpected error:", sys.exc_info()[0])
        print("Unexpected error:", sys.exc_info()[1])
        traceback.print_exc(file=sys.stdout)
        pass
    time.sleep(600)