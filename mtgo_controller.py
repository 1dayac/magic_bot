import sqlite3
from transitions import Machine, State
from pywinauto.application import Application
import pyautogui
import sys
import os
from enum import Enum
import math
import traceback

class TradeStatus(Enum):
    SUCCESS = 1
    BOT_OFFLINE = 2
    TRADE_REJECTED = 3
    BIG_FAILURE = 4
    NONE = 5


trusted_sell_bots = ["MTGO_Megastore2", "MTGO_Megastore", "MTGO_Megastore3", "MTGO_Megastore4", "MTGO_Megastore5", "HotListBot3","HotListBot2", "JaceCardBot", "AjaniCardBot", "GarrukCardBot", "SuperCardBot2", "ManaTraders_Seller3", "ManaTraders_Seller2", "Manatraders_seller3", "Manatraders_seller2",
                 "Blacklotusbot", "Power9bot", "SuperCardBot", "SuperCardBot2", "Applegrove", "CalebDBot", "CalebDBot2", "The_MTGO_Bazaar_1", "The_MTGO_Bazaar_2",
                "MagicCardMarket2", "MagicCardMarket", "MagicCardMarketFoil", "Manatraders_seller1", "botomagic", "staplesomagic", "VRTStoreBuyBot",
                "MTGOCardMarket", "MTGOCardMarket1","MTGOCardMarket2", "VRTStorebot3", "VRTStorebot2", "VRTSToreBot2", "VRTStorebot", "VRTSToreBot", "Manatraders_booster1", "ManaTraders_Seller1", "Manatraders_seller1",
                "11101969a", "11101969b", "ManaTraders_Seller4", "Manatraders_seller4", "ManaTraders_Seller5", "Manatraders_seller5", "Cheapest_Prices_1", "Cheapest_Prices", "Cheapest_Prices_2", "Cheapest_Prices_3",
                     "Cheapest_Prices_4", "Vintage-Cardbot", "Vintage-Cardbot2", "__BOT__Platinum"]

trusted_buy_bots = ["HotListBot3", "HotListBot2", "Power9bot", "CalebDBot", "CalebDBot2", "botomagic", "staplesomagic", "SuperCardBot", "SuperCardBot2", "GarrukCardBot", "VRTStoreBuyBot"]

class NoConfirmTradeException(Exception):
    pass


set_abbr = {"AER" : "Aether Revolt", "AKH" : "Amonkhet", "EXP" : "Zendikar Expeditions", "PZ2" : "You Make the Cube",  "MRD" : "Mirrodin", "KLD" : "Kaladesh", "EMN" : "Eldritch Moon", "ISD" : "Innistrad",
            "OGW" : "Oath of the Gatewatch", "DKA" : "Dark Ascension", "CMD" : "Commander (2011 Edition)", "ZEN" : "Zendikar", "XLN" : "Ixalan", "RIX" : "Rivals of Ixalan", "AVR" : "Avacyn Restored",
            "GTC" : "Gatecrash", "MOR" : "Morningtide", "HOU" : "Hour of Devastation", "SOI" : "Shadows over Innistrad", "A25" : "Masters 25",
            "BFZ" : "Battle for Zendikar", "JOU" : "Journey into Nyx",  "IMA" : "Iconic Masters", "ORI" : "Magic Origins", "TPR" : "Tempest Remastered", "WL" : "Weatherlight","DTK" : "Dragons of Tarkir", "FRF" : "Fate Reforged",
            "M15" : "Magic 2015", "M14" : "Magic 2014", "M13" : "Magic 2013", "M12" : "Magic 2012", "M11" : "Magic 2011",
            "MMA" : "Modern Masters (2013 Edition)", "MM2" : "Modern Masters (2015 Edition)", "MM3" : "Modern Masters (2017 Edition)", "RTR" : "Return to Ravnica", "WWK" : "Worldwake", "ARB" : "Alara Reborn", "EVE" : "Eventide",
            "SHM" : "Shadowmoor", "10E" : "Tenth Edition", "9ED" : "Ninth Edition", "8ED" : "Eighth Edition", "7E" : "Seventh Edition", "LRW" : "Lorwyn",
            "PLC" : "Planar Chaos", "VMA" : "Vintage Masters",  "TSP" : "Time Spiral", "CSP" : "Coldsnap", "DIS" : "Dissension", "AP" : "Apocalypse",
            "GPT" : "Guild Pact", "VI" : "Visions", "DAR": "Dominaria", "SOK" : "Saviors of Kamigawa", "BOK" : "Betrayers of Kamigawa", "CHK" : "Champions of Kamigawa",
            "ST" : "Stronghold", "TE" : "Tempest", "MI" : "Mirage", "ONS" : "Onslaught", "JUD" : "Judgment", "OD" : "Odyssey",
            "NE" : "Nemesis", "MM" : "Mercadian Masques", "THS" : "Theros", "ROE" : "Rise of the Eldrazi", "UZ" : "Urza's Saga", "UL" : "Urza's Legacy",
            "M10" : "Magic 2010", "SCG" : "Scourge","UD" : "Urza's Destiny", "LGN" : "Legions", "CON" : "Conflux", "C14" : "Commander 2014",
            "ARB" : "Alara Reborn", "ALA" : "Shards of Alara", "DST" : "Darksteel", "FUT" : "Future Sight", "EMA" : "Eternal Masters", "MS2" : "Kaladesh Inventions",
			"MS3" : "Amonkhet Invocations", "RAV" : "Ravnica: City Of Guilds", "5DN" : "Fifth Dawn", "MBS" : "Mirrodin Besieged", "SOM" : "Scars of Mirrodin", "NPH" : "New Phyrexia",
            "ME4" : "Masters Edition IV", "ME3" : "Masters Edition III", "MED" : "Masters Edition I", "IN" : "Invasion", "BNG" : "Born of the Gods", "KTK" : "Khans of Tarkir", "TOR" : "Torment", "TSB" : "Time Spiral Timeshifted"}

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


con = sqlite3.connect(sys.argv[1], isolation_level=None)
cursor = con.cursor()

def go_to_rectangle(rect, sleep = 0):
    pyautogui.moveTo((rect.left + rect.right)/2, (rect.top + rect.bottom)/2)
    time.sleep(sleep)


def double_click_multiple(window, times):
    rect = window.rectangle()
    for i in range(times):
        double_click_rectangle(rect)

def double_click_rectangle(rect, sleep = 0):
    pyautogui.click((rect.left + rect.right)/2, (rect.top + rect.bottom)/2, clicks=2, interval=0.1)
    time.sleep(sleep)

def click_rectangle(rect, sleep = 0):
    pyautogui.click((rect.left + rect.right)/2, (rect.top + rect.bottom)/2)
    time.sleep(sleep)

def right_click_rectangle(rect, sleep = 0):
    pyautogui.rightClick((rect.left + rect.right)/2, (rect.top + rect.bottom)/2)
    time.sleep(sleep)

def click_collection(app):
    click_rectangle(app.top_window().window(auto_id="CollectionButton").rectangle(), 5)

def click_trade(app):
    click_rectangle(app.top_window().window(auto_id="TradeButton", found_index = 0).rectangle(), 5)

def click_ok_button(app):
    click_rectangle(app.top_window().window(auto_id="OkButton").rectangle(), 5)

def close_chat(app):
    while True:
        try:
            print("Try to close chat")
            click_rectangle(app.top_window().window(auto_id="CloseButtom", found_index=0).rectangle())
            time.sleep(1)
            break
        except:
            pass

def get_tix_number(app, botname):
    import io
    import sys
    stringio = io.StringIO()
    previous_stdout = sys.stdout
    sys.stdout = stringio
    app.top_window().window(auto_id="ChatItemsControl").print_control_identifiers()
    sys.stdout = previous_stdout
    string = stringio.getvalue()
    num_of_tix = 0
    if botname.startswith("Hot"):
        pos = string.rfind("Take")
        pos1 = string.find(" ", pos + 1) + 1
        pos2 = string.find(" ", pos1)
        num_of_tix = int(string[pos1: pos2])
        print("Taking " + str(num_of_tix) + " tix")
    else:
        pos = string.rfind("Please take up to")
        pos1 = string.find(" ", pos + 1) + 1
        pos2 = string.find(" ", pos1)
        num_of_tix = math.floor(float(string[pos1: pos2]))
        print("Taking " + str(num_of_tix) + " tix")
    return num_of_tix


states_my = [State(name = 'initial'), State(name = 'login', on_enter = ['login']), State(name = 'buy', on_enter = ['buy_card']), State(name = 'update_binder_after_buying', on_enter = ['update_binder_after_buy']),
                                         State(name = 'sell', on_enter = ['sell_card']), State(name = 'update_binder_after_selling', on_enter = ['update_binder_after_sell']), State(name = 'close', on_enter = ['close_mtgo'])]

transitions = [
    { 'trigger': 'go_to_login', 'source': 'initial', 'dest': 'login' },
    {'trigger': 'go_to_buy', 'source': 'buy', 'dest': 'buy'},
    {'trigger': 'go_to_sell', 'source': 'sell', 'dest': 'sell'},
    { 'trigger': 'go_to_buy', 'source': 'login', 'dest': 'buy' },
    {'trigger': 'go_to_buy', 'source': 'update_binder_after_selling', 'dest': 'buy'},
    { 'trigger': 'go_to_update', 'source': 'buy', 'dest': 'update_binder_after_buying'} ,
    { 'trigger': 'go_to_sell', 'source': 'update_binder_after_buying', 'dest': 'sell' },
    {'trigger': 'go_to_update', 'source': 'sell', 'dest': 'update_binder_after_selling'},
    {'trigger': 'go_to_buy', 'source': 'update_binder_after_selling', 'dest': 'buy'},

    {'trigger': 'go_to_restart', 'source': 'update_binder_after_selling', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'sell', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'buy', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'update_binder_after_buying', 'dest': 'close'},

    {'trigger': 'go_to_login', 'source': 'close', 'dest': 'login'}
]

import subprocess, time

start = time.time()

class MTGO_bot(object):
    def __init__(self):
        try:
            self.app = Application(backend="uia").connect(path='MTGO.exe')
            self.db_record = ""
            self.trade_status = TradeStatus.NONE
        except:
            subprocess.Popen(['cmd.exe', '/c', r'C:\Users\IEUser\Desktop\mtgo.appref-ms'])
            time.sleep(5)
            self.app = Application(backend="uia").connect(path='MTGO.exe')
            self.db_record = ""
            self.trade_status = TradeStatus.NONE


    def close_mtgo(self):
        os.system("taskkill /f /im  MTGO.exe")

    def login(self):
        print("Starting...")
        try:
            self.app.top_window().window(auto_id="UsernameTextBox").type_keys("VerzillaBot")
            self.app.top_window().window(auto_id="PasswordBox").type_keys("Lastborn220")
            time.sleep(2.5)
            self.app.top_window().window(auto_id="PasswordBox").type_keys("{ENTER}")
            pyautogui.press('enter')

            time.sleep(20)
            click_collection(self.app)
            time.sleep(10)
            click_trade(self.app)
            time.sleep(10)
            click_collection(self.app)
            click_rectangle(self.app.top_window().window(title="ABinder", found_index=0).rectangle())
        except:
            pass

    def switch_bot(self):
        if self.db_record[6] == "HotListBot3":
            self.db_record[6] = "HotListBot4"
        elif self.db_record[6] == "HotListBot4":
            self.db_record[6] = "HotListBot2"
        elif self.db_record[6] == "HotListBot2":
            self.db_record[6] = "HotListBot3"
        self.app.top_window().window(auto_id="searchTextBox").type_keys(self.db_record[6] + "{ENTER}")


    def click_bot_trade(self, botname):
        index = 0
        while True:
            try:
                index += 1
                if index == 5:
                    return False
                go_to_rectangle(self.app.top_window().window(title=botname).rectangle())
                click_rectangle(self.app.top_window().window(title="Trade", found_index=1).rectangle())
                time.sleep(1)
                click_ok_button(self.app)
                return True
            except:
                pass

    def is_trade_cancelled(self):
        try:
            self.app.top_window().window(title="Trade Canceled", found_index=1).rectangle()
            click_rectangle(self.app.top_window().window(auto_id="OkButton", found_index=0).rectangle())
            return True
        except:
            return False

    def is_trade_stalled(self):
        try:
            click_rectangle(self.app.top_window().window(title="Trade Request", found_index=0).window(title="Cancel", found_index = 0).rectangle())
            return True
        except:
            return False

    def buy_card(self):
        end = time.time()
        if end - start > 72000:
            exit(-1)
        try:
            self.trade_status = TradeStatus.NONE
            print("Go to buy card...")
            cursor = con.cursor()
            command = "SELECT * FROM records ORDER BY RANDOM() LIMIT 1;"
            records = cursor.execute(command).fetchall()
            while len(records) == 0:
                time.sleep(10)
                records = cursor.execute(command).fetchall()
            self.db_record = list(records[0])

            while  self.db_record[5] not in trusted_sell_bots or self.db_record[6] not in trusted_buy_bots or self.db_record[9]:
                command = "DELETE FROM records WHERE Id = ?;"
                cursor.execute(command, [self.db_record[0]]).fetchall()
                command = "SELECT * FROM records ORDER BY RANDOM() LIMIT 1;"
                records = cursor.execute(command).fetchall()
                while len(records) == 0:
                    time.sleep(10)
                    records = cursor.execute(command).fetchall()
                self.db_record = list(records[0])

            print("Buying " + str(self.db_record[8]) + "x"+ self.db_record[1] + "(" + self.db_record[2] + ") from " +  self.db_record[5])
            if self.db_record[5] == "Applegrove":
                self.db_record[5] = "AppleGrove"
            if self.db_record[5] == "VRTStorebot3":
                self.db_record[5] = "VRTStoreBot3"
            if self.db_record[5] == "VRTStorebot2":
                self.db_record[5] = "VRTStoreBot2"
            if self.db_record[5] == "VRTStorebot":
                self.db_record[5] = "VRTStoreBot"
            if self.db_record[5] == "VRTSToreBot":
                self.db_record[5] = "VRTStoreBot"
            if self.db_record[5] == "VRTSToreBot2":
                self.db_record[5] = "VRTStoreBot2"
            if self.db_record[5] == "VRTSToreBot3":
                self.db_record[5] = "VRTStoreBot3"
            if self.db_record[5] == "Manatraders_booster1":
                self.db_record[5] = "ManaTraders_Booster1"
            if self.db_record[5] == "Manatraders_seller1":
                self.db_record[5] = "ManaTraders_Seller1"
            if self.db_record[5] == "Manatraders_seller2":
                self.db_record[5] = "ManaTraders_Seller2"
            if self.db_record[5] == "Manatraders_seller3":
                self.db_record[5] = "ManaTraders_Seller3"
            if self.db_record[5] == "Manatraders_seller4":
                self.db_record[5] = "ManaTraders_Seller4"
            if self.db_record[5] == "Manatraders_seller5":
                self.db_record[5] = "ManaTraders_Seller5"
            if self.db_record[5] == "Vintage-Cardbot2":
                self.db_record[5] = "Vintage-cardbot2"

            click_trade(self.app)
            self.app.top_window().window(auto_id="searchTextBox").type_keys(self.db_record[5] + "{ENTER}")

            if not self.click_bot_trade(self.db_record[5]):
                print("Bot is offline")
                return
            time.sleep(8)

            while self.is_trade_cancelled():
                self.click_bot_trade(self.db_record[5])
                time.sleep(5)

            if self.is_trade_stalled():
                return


            print(2)

            try:
                click_rectangle(self.app.top_window().window(auto_id="FilterCards-ResetFilterText").rectangle())
                self.app.top_window().window(auto_id="searchTextBox").type_keys(self.db_record[1].replace(" ", "{SPACE}") + "{ENTER}")
            except:
                return
            print(3)
            click_rectangle(self.app.top_window().window(auto_id="FilterCards-HeaderSet-Text").rectangle())
            click_rectangle(self.app.top_window().window(auto_id="FilterCards-Option" + set_abbr[self.db_record[2]]).rectangle())
            time.sleep(0.5)
            print(4)

            try:
                for i in range(0, int(self.db_record[8])):
                    double_click_rectangle(self.app.top_window().child_window(title_re="Item: Card", found_index = 0).rectangle())
            except:
                self.trade_status = TradeStatus.BIG_FAILURE
                return
                double_click_rectangle(self.app.top_window().window(auto_id="CollectionLayoutView", found_index = 0).rectangle())
            print(5)

            time.sleep(2)
            click_rectangle(self.app.top_window().window(title="Submit", found_index=1).rectangle())
            time.sleep(10)
            try:
                click_rectangle(self.app.top_window().window(title="Submit", found_index=1).rectangle())
            except:
                pass
            print(6)
            time.sleep(1)
            index = 0
            while True:
                try:
                    index += 1
                    click_rectangle(self.app.top_window().window(title="Confirm Trade", found_index=1).rectangle())
                    break
                except:
                    time.sleep(1)
                    if index >= 10:
                        self.trade_status = TradeStatus.BIG_FAILURE
                        return
                    pass
            print(4)
            close_chat(self.app)
            print(5)
            index = 0
            while True:
                try:
                    index += 1
                    time.sleep(2)
                    click_rectangle(self.app.top_window().window(title="Added to your Collection:", found_index = 0).window(auto_id="TitleBarCloseButton").rectangle())
                    break
                except:
                    try:
                        click_rectangle(self.app.top_window().window(auto_id="OkButton", found_index=0).rectangle())
                        break
                    except:
                        if index >= 20:
                            self.trade_status = TradeStatus.BIG_FAILURE
                            return
                        pass

            command = "DELETE FROM records WHERE Id = ?;"
            cursor.execute(command, [self.db_record[0]]).fetchall()
            self.trade_status = TradeStatus.SUCCESS
        except:
            print("Unexpected error:", sys.exc_info()[0])
            traceback.print_exc(file=sys.stdout)
            command = "DELETE FROM records WHERE Id = ?;"
            cursor.execute(command, [self.db_record[0]]).fetchall()
            self.trade_status = TradeStatus.BIG_FAILURE

    def sell_card(self):
        try:
            self.trade_status = TradeStatus.NONE
            print("Go to sell card...")
            print("Selling " + self.db_record[0] + " to " +  self.db_record[6])
            while True:
                try:
                    click_trade(self.app)
                    break
                except:
                    time.sleep(1)

            self.app.top_window().window(auto_id="searchTextBox").type_keys(self.db_record[6] + "{ENTER}")

            self.click_bot_trade(self.db_record[6])
            time.sleep(8)

            while self.is_trade_cancelled():
                self.switch_bot()
                self.click_bot_trade(self.db_record[6])
                time.sleep(2)

            try:
                self.app.top_window().window(title="Trade Canceled", found_index=1).rectangle()
                return
            except:
                pass

            #try:
            #    self.app.top_window().window(auto_id="ChatSendEditBox").type_keys("sell{ENTER}")
            #except:
            #    return
            #self.app.top_window().window(auto_id="ChatSendEditBox").type_keys("{ENTER}")

            num_of_tix = get_tix_number(self.app, self.db_record[6])
            if num_of_tix != 0:
                click_rectangle(self.app.top_window().window(title="Other Products", found_index=1).rectangle())
                double_click_multiple(self.app.top_window().child_window(title_re="Item: CardSlot: Event", found_index=0), num_of_tix)

            click_rectangle(self.app.top_window().window(title="Submit", found_index=1).rectangle())
            time.sleep(5)
            try:
                click_rectangle(self.app.top_window().window(title="Submit", found_index=1).rectangle())
            except:
                pass
            time.sleep(5)

            while True:
                index = 0
                try:
                    index += 1
                    click_rectangle(self.app.top_window().window(title="Confirm Trade", found_index=1).rectangle())
                    time.sleep(1)
                    break
                except:
                    if index == 10:
                        raise NoConfirmTradeException()
                    pass

            close_chat(self.app)
            while True:
                try:
                    print("Trying to close window with stuff")
                    click_rectangle(self.app.top_window().window(title="Added to your Collection:", found_index = 0).window(auto_id="TitleBarCloseButton").rectangle())
                    time.sleep(1)
                    break
                except:
                    try:
                        print("Trying to close window without stuff")
                        click_rectangle(self.app.top_window().window(auto_id="OkButton", found_index=0).rectangle())
                        break
                    except:
                        pass

            self.trade_status = TradeStatus.SUCCESS
        except NoConfirmTradeException:
            try:
                click_rectangle(self.app.top_window().window(title="Cancel Trade", found_index=0).rectangle())
                close_chat(self.app)
            except:
                print(sys.exc_info()[0])
                print(sys.exc_info()[1])
                traceback.print_exc(file=sys.stdout)
                pass
        except:
            print("Unexpected error:", sys.exc_info()[0])
            print("Unexpected error:", sys.exc_info()[1])
            traceback.print_exc(file=sys.stdout)
            self.trade_status = TradeStatus.BIG_FAILURE

    def update_binder_after_buy(self):
        self.trade_status = TradeStatus.NONE
        print("Go to update values...")
        while True:
            try:
                click_collection(self.app)
                break
            except:
                time.sleep(1)
        time.sleep(1)
        click_rectangle(self.app.top_window().window(title="Cards", found_index=1).rectangle())
        time.sleep(1)
        self.app.top_window().window(auto_id="searchTextBox").type_keys(self.db_record[1].replace(" ", "{SPACE}") + "{ENTER}")
        time.sleep(0.5)
        try:
            double_click_multiple(self.app.top_window().child_window(title_re="Item: Card", found_index = 0), int(self.db_record[8]) + 1)
        except:
            pass

    def update_binder_after_sell(self):
        self.trade_status = TradeStatus.NONE
        print("Go to update values...")
        click_collection(self.app)
        time.sleep(1)
        click_rectangle(self.app.top_window().window(title="Other Products", found_index=1).rectangle())
        self.app.top_window().window(auto_id="searchTextBox").type_keys("event{SPACE}tickets{ENTER}")
        right_click_rectangle(self.app.top_window().child_window(title_re="Item: CardSlot: Event", found_index=0).rectangle())
        try:
            click_rectangle(self.app.top_window().child_window(title_re="Add All to", found_index=0).rectangle())
        except:
            try:
                click_rectangle(self.app.top_window().child_window(title_re="Add 1 to", found_index=0).rectangle())
            except:
                pyautogui.moveRel(-10, 0)
                pyautogui.click()
                pass

    def close(self):
        pass

my_bot = MTGO_bot()
my_MTGO_bot_Machine = Machine(model=my_bot, states=states_my, transitions=transitions, initial='initial')
print(my_bot.state)

my_bot.go_to_login()
while (True):
    while True:
        if my_bot.trade_status == TradeStatus.SUCCESS:
            break
        if my_bot.trade_status == TradeStatus.NONE or my_bot.trade_status == TradeStatus.BOT_OFFLINE:
            my_bot.go_to_buy()
        if my_bot.trade_status == TradeStatus.BIG_FAILURE:
            my_bot.go_to_restart()
            my_bot.__init__()
            my_bot.go_to_login()
            my_bot.go_to_buy()

    my_bot.go_to_update()

    if my_bot.trade_status == TradeStatus.NONE or my_bot.trade_status == TradeStatus.BOT_OFFLINE:
        my_bot.go_to_sell()

    if my_bot.trade_status == TradeStatus.BIG_FAILURE:
        my_bot.go_to_restart()
        my_bot.__init__()
        my_bot.go_to_login()
        continue

    my_bot.go_to_update()

#app = Application(backend="uia").start("notepad.exe")

