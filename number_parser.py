import pickle
import sys
import queue
from card import Card, Price

class QueueWithMaxCapacity(object):
    def __init__(self, capacity = 100):
        self.limit = capacity
        self.queue = queue.Queue()

    def add(self, item):
        if self.queue.size() > self.limit:
            self.queue.get()
        self.queue.add(item)

class DigitsClassifier(object):

    def __init__(self):
        try:
            f = open("obj/dict.pkl", 'rb')
            self.prices_d = pickle.loads(f.read())
        except:
            self.prices_d = {}
        self.old_prices = QueueWithMaxCapacity(100)

    def get_symbol(self, img_src):
        if img_src in self.prices_d.keys():
            return self.prices_d[img_src]
        else:
            print(img_src)
            symbol = sys.stdin.readline()
            self.prices_d[img_src] = symbol
            pickle.dump(self.prices_d, open("obj/dict.pkl", "wb"))
            return symbol

    def get_price(self, e, card, bot_name):
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
            return sell_price
        else:
            try:
                buy_price = float("".join(res).replace('\n', ''))
            except:
                buy_price = -1
            return buy_price