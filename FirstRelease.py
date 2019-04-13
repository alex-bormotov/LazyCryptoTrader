import telebot
import mpu.io
import os
import sys
import json
import re
from telebot import types
import ccxt
import time
from time import sleep

f = open("telegram_api.conf", "r")
bot = telebot.TeleBot(f.read().split()[0])

exchange = None
key = ""
secret = ""
exchange_fee = 0.1
data = {}

signals_data = None
pair = None
coin = None
buy = None
sdd = None
stop_loss = None
sell_1 = None
sell_2 = None
sell_3 = None
sell_4 = None
sell_5 = None
amount = None
selected_sell_target = None
balance_btc = None
balance_coin = None
buy_after_exchange_fee = None
orders_executed = []

example_signal_post = "#BTG /BTC\n\nПокупка 311200 и ниже \n\nЦели:\n391100\n491100\n591100\n691100\n791100\n\nСтоп ставим на 221100\n\nВыделяем до 10% от депозита"


@bot.message_handler(content_types=["text"])
def hello_user(message):

    markup = types.ReplyKeyboardMarkup()
    itembtna = types.KeyboardButton("/start")
    markup.row(itembtna)
    bot.send_message(
        message.from_user.id,
        "Hello "
        + str(message.from_user.username)
        + " ;)\nBelow signals post example.\n"
        + "You must forward posts to me in same format only!\n",
        reply_markup=markup,
    )
    if doesFileExists("%s.json" % message.from_user.id):
        with open("%s.json" % message.from_user.id, "r") as read_file:

            global data
            global key
            global secret
            global exchange

            data = json.load(read_file)
            key = data["key"]
            secret = data["secret"]
            exchange = ccxt.binance(
                {"apiKey": key, "secret": secret, "enableRateLimit": True}
            )

        bot.send_message(message.from_user.id, example_signal_post)

        bot.send_message(
            message.from_user.id,
            "You are registered already! Forward signal message to me ...",
        )
        bot.register_next_step_handler(message, get_forward)

    else:
        bot.send_message(
            message.from_user.id, "Nope! I don't find config file, lets create one..."
        )

        bot.send_message(message.from_user.id, "Enter Binance API KEY:")
        bot.register_next_step_handler(message, get_key)


def doesFileExists(filePathAndName):
    return os.path.exists(filePathAndName)


def get_key(message):
    global key
    if len(message.text) == 64:
        key = message.text
        bot.send_message(message.from_user.id, "Enter Binance SECRET KEY:")
        bot.register_next_step_handler(message, get_secret)
    else:
        bot.send_message(message.from_user.id, "Wrong API KEY! Try again...")
        bot.register_next_step_handler(message, get_key)


def get_secret(message):
    global secret
    global exchange
    if len(message.text) == 64:
        secret = message.text

        bot.send_message(
            message.from_user.id,
            "Ok, You are registered! Forward signal message to me ...",
        )
        bot.register_next_step_handler(message, get_forward)
        data = {"key": key, "secret": secret}
        mpu.io.write("%s.json" % message.from_user.id, data)
        exchange = ccxt.binance(
            {"apiKey": key, "secret": secret, "enableRateLimit": True}
        )
    else:
        bot.send_message(message.from_user.id, "Wrong API SECRET! Try again...")
        bot.register_next_step_handler(message, get_secret)


def get_forward(message):

    global signals_data
    global pair
    global buy
    global stop_loss
    global sell_1
    global sell_2
    global sell_3
    global sell_4
    global sell_5
    global exchange
    global sdd

    signals_data = message.text

    if len(str(signals_data)) >= 50:
        pair_pos_start = signals_data.find("#")
        pair_pos_end = signals_data.find("BTC")
        sdd = signals_data[pair_pos_start:pair_pos_end]
        pair = re.sub(r"[^A-Za-z]", "", sdd) + "/BTC"

        buy_pos_start = signals_data.find("Покупка")
        buy_tmp = re.findall(r"[-+]?\d*\.\d+|\d+", (signals_data[buy_pos_start:]))[0]
        total = 10000000
        buy = float("0." + str(buy_tmp).zfill(len(str(total))))

        stop_loss_pos_start = signals_data.find("Стоп")
        stop_loss_tmp = re.findall(
            r"[-+]?\d*\.\d+|\d+", (signals_data[stop_loss_pos_start:])
        )[0]
        total = 10000000
        stop_loss = float("0." + str(stop_loss_tmp).zfill(len(str(total))))

        sell_pos_start = signals_data.find("Цели")
        until_stop_loss_pos = signals_data.find("Стоп")
        sell_tmp = re.findall(
            r"[-+]?\d*\.\d+|\d+", (signals_data[sell_pos_start:until_stop_loss_pos])
        )
        if len(sell_tmp) == 5:
            total = 10000000
            sell_1 = float("0." + str(sell_tmp[0]).zfill(len(str(total))))
            sell_2 = float("0." + str(sell_tmp[1]).zfill(len(str(total))))
            sell_3 = float("0." + str(sell_tmp[2]).zfill(len(str(total))))
            sell_4 = float("0." + str(sell_tmp[3]).zfill(len(str(total))))
            sell_5 = float("0." + str(sell_tmp[4]).zfill(len(str(total))))
        elif len(sell_tmp) == 4:
            total = 10000000
            sell_1 = float("0." + str(sell_tmp[0]).zfill(len(str(total))))
            sell_2 = float("0." + str(sell_tmp[1]).zfill(len(str(total))))
            sell_3 = float("0." + str(sell_tmp[2]).zfill(len(str(total))))
            sell_4 = float("0." + str(sell_tmp[3]).zfill(len(str(total))))
            sell_5 = None
        elif len(sell_tmp) == 3:
            total = 10000000
            sell_1 = float("0." + str(sell_tmp[0]).zfill(len(str(total))))
            sell_2 = float("0." + str(sell_tmp[1]).zfill(len(str(total))))
            sell_3 = float("0." + str(sell_tmp[2]).zfill(len(str(total))))
            sell_4 = None
            sell_5 = None
        elif len(sell_tmp) == 2:
            total = 10000000
            sell_1 = float("0." + str(sell_tmp[0]).zfill(len(str(total))))
            sell_2 = float("0." + str(sell_tmp[1]).zfill(len(str(total))))
            sell_3 = None
            sell_4 = None
            sell_5 = None
        elif len(sell_tmp) == 1:
            total = 10000000
            sell_1 = float("0." + str(sell_tmp[0]).zfill(len(str(total))))
            sell_2 = None
            sell_3 = None
            sell_4 = None
            sell_5 = None

        bot.send_message(message.from_user.id, "Signal received")
        bot.send_message(message.from_user.id, "Pair is: " + str(pair))
        bot.send_message(message.from_user.id, "Buy is: " + str(buy))
        bot.send_message(message.from_user.id, "Stop_loss is: " + str(stop_loss))

        if sell_1 is not None:
            bot.send_message(message.from_user.id, "Sell 1 is: " + str(sell_1))
        if sell_2 is not None:
            bot.send_message(message.from_user.id, "Sell 2 is: " + str(sell_2))
        if sell_3 is not None:
            bot.send_message(message.from_user.id, "Sell 3 is: " + str(sell_3))
        if sell_4 is not None:
            bot.send_message(message.from_user.id, "Sell 4 is: " + str(sell_4))
        if sell_5 is not None:
            bot.send_message(message.from_user.id, "Sell 5 is: " + str(sell_5))

        bot.send_message(message.from_user.id, "Which sell target do you choose? ")
        bot.register_next_step_handler(message, select_sell)

    else:
        bot.send_message(message.from_user.id, "Nope, not typing to me! Forward only!")
        bot.register_next_step_handler(message, get_forward)


def select_sell(message):

    global sell_1
    global sell_2
    global sell_3
    global sell_4
    global sell_5
    global selected_sell_target

    global balance_coin
    global balance_btc
    global coin

    if (
        (message.text == "1" and sell_1 is not None)
        or (message.text == "2" and sell_2 is not None)
        or (message.text == "3" and sell_3 is not None)
        or (message.text == "4" and sell_4 is not None)
        or (message.text == "5" and sell_5 is not None)
    ):
        if message.text == "1":
            selected_sell_target = sell_1
        elif message.text == "2":
            selected_sell_target = sell_2
        elif message.text == "3":
            selected_sell_target = sell_3
        elif message.text == "4":
            selected_sell_target = sell_4
        elif message.text == "5":
            selected_sell_target = sell_5
        bot.send_message(
            message.from_user.id, "Selected sell is: " + str(selected_sell_target)
        )

        coin = re.sub(r"[^A-Za-z]", "", sdd)
        balance_fetch = exchange.fetch_balance()
        balance_coin = float(balance_fetch["free"][coin])
        bot.send_message(
            message.from_user.id, "YOUR " + coin + " balance is: " + str(balance_coin)
        )

        balance_btc = float(balance_fetch["free"]["BTC"])

        bot.send_message(
            message.from_user.id, "YOUR BTC balance is: " + str(balance_btc) + " "
        )
        bot.send_message(
            message.from_user.id,
            "How much '%' from your BTC balance to use for this trade?\nEnter in percents only!\nFor example: 10",
        )
        bot.register_next_step_handler(message, get_amount)

    else:
        bot.send_message(
            message.from_user.id, "Make your choose, and type to me 1 or 2 or 3 ... "
        )
        bot.register_next_step_handler(message, select_sell)


def get_amount(message):

    global amount
    global balance_coin
    global balance_btc
    global buy_after_exchange_fee
    global coin

    min_trade_amount = 5 / exchange.fetch_ticker("BTC/USDT")["low"]

    try:
        if (float(message.text) > 0) and (float(message.text) < 101):
            amount = (float(balance_btc) / 100) * float(message.text)
            if amount > min_trade_amount:
                buy_after_exchange_fee = (amount / buy) - (
                    ((amount / buy) / 100) * exchange_fee
                )  # Fee in coin
                bot.send_message(
                    message.from_user.id, "I will use: " + str(amount) + " BTC"
                )
                bot.send_message(
                    message.from_user.id,
                    "We will get: " + str(buy_after_exchange_fee)[:10] + " " + coin,
                )
                bot.send_message(
                    message.from_user.id,
                    "Type to me: \n\n\n YES, place orders, I am totaly sure.",
                )
                bot.register_next_step_handler(message, trader)
            else:
                bot.send_message(
                    message.from_user.id,
                    "You try to use"
                    + " "
                    + str(amount)
                    + " BTC\n"
                    + "But, min amount to trade amount "
                    + str(min_trade_amount)[:8]
                    + " BTC! ~$5",
                )
                bot.register_next_step_handler(message, get_amount)
    except:
        bot.send_message(message.from_user.id, "Type correct number!")
        bot.register_next_step_handler(message, get_amount)


def trader(message):

    if message.text == "YES, place orders, I am totaly sure.":
        bot.send_message(message.from_user.id, "Preparing to trade ...")
        buy_order(message)
        bot.register_next_step_handler(message, buy_order)
    else:
        bot.send_message(message.from_user.id, "Just type it..")
        bot.register_next_step_handler(message, trader)


def buy_order(message):

    global amount
    global pair
    global buy
    global exchange
    global orders_executed
    global buy_order_fee

    type = "limit"
    side = "buy"
    amount_to_buy_exchange = amount / buy
    params = {}

    buy_order = exchange.create_order(
        pair, type, side, amount_to_buy_exchange, buy, params
    )
    orders_executed.append(buy_order["id"])

    bot.send_message(message.from_user.id, "Buy order placed")
    bot.send_message(message.from_user.id, "Buy order id add to orders_executed")
    bot.send_message(
        message.from_user.id, "Buy order id is: " + str(orders_executed[0])
    )
    check_order_status_and_sell(message)
    bot.register_next_step_handler(message, check_order_status_and_sell)


def check_order_status_and_sell(message):

    while True:

        global orders_executed
        global pair
        global exchange

        params = {}

        if exchange.fetchOrder(orders_executed[0], pair, params)["status"] == "closed":
            bot.send_message(message.from_user.id, "Ready for Sell")
            sell_order(message)
            bot.register_next_step_handler(message, sell_order)
            break
        else:
            pass
            buy_order_status = exchange.fetchOrder(orders_executed[0], pair, params)[
                "status"
            ]
            bot.send_message(
                message.from_user.id, "Buy order id is: " + str(buy_order_status)
            )
            bot.send_message(message.from_user.id, "waiting for execute ...")
            time.sleep(30)


def sell_order(message):

    global pair
    global exchange
    global orders_executed
    global selected_sell_target
    global stop_loss
    global buy_after_exchange_fee

    buy_after_exchange_fee = float(str(buy_after_exchange_fee)[:10])
    bot.send_message(message.from_user.id, buy_after_exchange_fee)
    bot.send_message(message.from_user.id, str(orders_executed[0]))

    stop_loss_limit_order = exchange.create_order(
        pair,
        "stop_loss_limit",
        "sell",
        buy_after_exchange_fee,
        selected_sell_target,
        {"stopPrice": stop_loss},
    )
    bot.send_message(message.from_user.id, "Stop limit placed")

    os.execl(sys.executable, sys.executable, *sys.argv)


bot.polling(none_stop=True, interval=0)
