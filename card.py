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

    def BestSellPrice(self):
        best_price = None
        for price in self.prices:
            if price == None:
                continue
            if best_price == None:
                best_price = price
            elif price.sell_price < best_price.sell_price:
                best_price = price
        return best_price


    def BestBuyPrice(self):
        best_price = None
        for price in self.prices:
            if price == None:
                continue
            if best_price == None:
                best_price = price
            elif price.buy_price > best_price.buy_price:
                best_price = price
        return best_price

