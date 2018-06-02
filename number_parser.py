import pickle
import sys
import queue
from card import Card, Price
from selenium import webdriver
import time



class QueueWithMaxCapacity(object):
    def __init__(self, capacity = 100):
        self.limit = capacity
        self.queue = queue.Queue()

    def add(self, item):
        if self.queue.qsize() > self.limit:
            self.queue.get()
        self.queue.put(item)

import platform
if platform.system() == "Windows":
    chromedriver_path = r"C:\Users\dmm2017\Desktop\magic_bot\chromedriver.exe"
else:
    chromedriver_path = "/home/dmm2017/PycharmProjects/candle_factory/chromedriver"

class DigitsClassifier(object):


    def ParseMtgolibraryInternal(self, driver, card, url, botname, sellprice_original):
        bot_name_original = botname

        setname = card.set
        elem = driver.find_elements_by_class_name("sell_row")

        if len(elem) == 0:
            return False
        for e in elem:
            try:
                table_setname = e.find_elements_by_class_name("setname")[0].text
                if table_setname != setname:
                    continue
                bot_name_sell = e.find_elements_by_class_name("bot_name")[0].text
                if bot_name_sell != bot_name_original:
                    continue
            except:
                continue
            sell_price_original = str(sellprice_original)
            images = e.find_element_by_class_name("sell_price_round")
            images_srcs = [image.get_attribute("src") for image in images.find_elements_by_tag_name('img')]
            if len(images_srcs) != len(sell_price_original):
                return
            for i in range(len(images_srcs)):
                if images_srcs[i] not in self.super_dict.keys():
                    self.super_dict[images_srcs[i]] = {}
                if sell_price_original[i] not in self.super_dict[images_srcs[i]].keys():
                    self.super_dict[images_srcs[i]][sell_price_original[i]] = 0
                self.super_dict[images_srcs[i]][sell_price_original[i]] += 1



    def ParseMtgolibrary(self, driver, card, botname, sellprice):
        setname, url, driver = self.MtgoLibraryGoToCard(driver, card)
        time.sleep(7)
        return self.ParseMtgolibraryInternal(driver, card, url, botname, sellprice)

    def MtgoLibraryGoToCard(self, driver, card):
        setname = card.set.upper()
        input_element = driver.find_element_by_id("_cardskeyword")
        input_element.clear()
        input_element.send_keys(card.name + " " + setname)
        driver.find_elements_by_css_selector("button")[1].click()
        url = driver.current_url
        return setname, url, driver

    def __init__(self):
        try:
            f = open("obj/dict.pkl", 'rb')
            self.prices_d = pickle.loads(f.read())
        except:
            self.prices_d = {}
        self.old_prices = QueueWithMaxCapacity(100)
        self.super_dict = {}
        self.index = 0


    def smart_way(self, img_src):
        if self.old_prices.queue.qsize() < 50:
            return False
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        driver_library = webdriver.Chrome(chromedriver_path, options=chrome_options)
        driver_library.get("https://www.mtgowikiprice.com/")
        index = 1
        print("Run smart algorithm for digit recognition")
        index = 0
        for (card, botname, sell_price) in list(self.old_prices.queue.queue):
            self.ParseMtgolibrary(driver_library, card, botname, sell_price)
            index += 1
            print("Parsing page number " + str(index))
        temp_solution = {}
        for img_src in self.super_dict.keys():
            candidate_key = max(self.super_dict[img_src], key=self.super_dict[img_src].get)
            temp_solution[img_src] = candidate_key
        if len(temp_solution.keys()) == 11 and len(temp_solution.values()) == len(set(temp_solution.values())):
            for key in temp_solution.keys():
                self.prices_d[key] = temp_solution[key]
            self.super_dict.clear()
            pickle.dump(self.prices_d, open("obj/dict.pkl", "wb"))
            return True
        self.super_dict.clear()
        return False



    def get_symbol(self, img_src):
        if img_src in self.prices_d.keys():
            return self.prices_d[img_src]
        elif self.smart_way(img_src):
            return self.prices_d[img_src]
        else:
            print(img_src)
            symbol = sys.stdin.readline()
            self.prices_d[img_src] = symbol
            pickle.dump(self.prices_d, open("obj/dict.pkl", "wb"))
            return symbol

    def get_price(self, e, botname, card):
        find_sell_price = False
        if len(e.find_elements_by_class_name("sell_price_round")):
            find_sell_price = True
        images = None
        if find_sell_price:
            images = e.find_element_by_class_name("sell_price_round")
        else:
            images = e.find_element_by_class_name("buy_price_round")

        index = 0
        res = []
        for image in images.find_elements_by_tag_name('img'):
            index += 1
            img_src = image.get_attribute("src")
            symbol = self.get_symbol(img_src)
            res.append(symbol)
        # print("".join(res).replace('\n', ''))
        if find_sell_price:
            try:
                sell_price = float("".join(res).replace('\n', ''))
            except:
                sell_price = 100000
            self.old_prices.add((card, botname, sell_price))
            return sell_price
        else:
            try:
                buy_price = float("".join(res).replace('\n', ''))
            except:
                buy_price = -1
            return buy_price