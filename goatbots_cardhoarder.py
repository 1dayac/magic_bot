from selenium import webdriver
import sqlite3
import datetime
from card import Card, Price

chromedriver_path = r"C:\Users\dmm2017\Desktop\magic_bot\chromedriver.exe"

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



    def AddMainProcessor(self, processor):
        self.main_processor = processor

    def AddProcessor(self, processor):
        self.processors.append(processor)


    def IsHighDiff(self, card):
        best_buy_price = card.BestBuyPrice()
        best_sell_price = card.BestSellPrice()
        return best_buy_price.buy_price - best_sell_price.sell_price >= 0.05


    def AddToDatabase(self, card):
        best_buy_price = card.BestBuyPrice()
        best_sell_price = card.BestSellPrice()
        print("High diff: " + best_sell_price.bot_name_sell + ", " + best_buy_price.bot_name_buy + ": " +
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
        option = webdriver.ChromeOptions()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(chromedriver_path, options= chrome_options)
        self.second_driver = webdriver.Chrome(chromedriver_path, options= chrome_options)
        self.current_set = None

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
        p = Price("", buy_price, sell_price, "GoatBots3", "GoatBots3", 4)
        c = Card(card_name, self.current_set, p, 0)
        return c

    def GetSet(self):
        set_line = self.driver.find_element_by_xpath("//*[@id=\"text_left\"]/div[1]/h2/a").text
        return set_line[set_line.find("(") +1 : set_line.find(")")]

    def GetCards(self):
        self.driver.get(self.main_url)
        sets = self.driver.find_elements_by_class_name('cardset')
        refs = []
        max_iter = 200
        current_iter = 0
        for set in sets:
            current_iter += 1
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
                    card = self.ProcessRow(line)
                    if card == None:
                        continue
                    else:
                        yield card

class CardHoarderParser(object):
    def __init__(self):
        self.main_url = "https://www.cardhoarder.com/cards"
        option = webdriver.ChromeOptions()
        chrome_options = webdriver.ChromeOptions()
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

top_level_processor = TopLevelProcessor()
top_level_processor.AddMainProcessor(GoatBotsParser())
top_level_processor.AddProcessor(CardHoarderParser())
top_level_processor.ParseCards()