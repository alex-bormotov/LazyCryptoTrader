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
from numbers import Number

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

    bot.send_message(
        message.from_user.id,
        "Привет "
        + str(message.from_user.username)
        + "\n"
        + "Если тебе нужно будет меня перезагрузить отправь мне /restart",
    )
    bot.send_message(
        message.from_user.id,
        "Ниже пример поста с сигналами.\nТы должен пересылать мне посты только в таком формате!\n",
    )
    bot.send_message(message.from_user.id, example_signal_post)

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
            bot.send_message(
                message.from_user.id,
                "Ты уже зарегистрирован, так что можешь переслать мне пост с сигналами ...",
            )
            bot.register_next_step_handler(message, get_forward)

    else:
        bot.send_message(
            message.from_user.id, "Я не нашел твою учетку, давай создадим ее ..."
        )
        bot.send_message(message.from_user.id, "Введи Binance API KEY:")
        bot.register_next_step_handler(message, get_key)


def doesFileExists(filePathAndName):
    return os.path.exists(filePathAndName)


def get_key(message):

    global key

    if message.text == "/restart":
        restart_bot(message)

    elif len(message.text) == 64:
        key = message.text
        bot.send_message(message.from_user.id, "Введи Binance SECRET KEY:")
        bot.register_next_step_handler(message, get_secret)
    else:
        bot.send_message(
            message.from_user.id, "Неправильный API KEY! Проверь и введи снова..."
        )
        bot.register_next_step_handler(message, get_key)


def get_secret(message):

    global secret
    global exchange

    if message.text == "/restart":
        restart_bot(message)

    elif len(message.text) == 64:
        secret = message.text

        bot.send_message(
            message.from_user.id,
            "Поздравляю, твоя учетка создана! Теперь можешь переслать мне пост с сигналами ...",
        )
        bot.register_next_step_handler(message, get_forward)
        data = {"key": key, "secret": secret}
        mpu.io.write("%s.json" % message.from_user.id, data)
        exchange = ccxt.binance(
            {"apiKey": key, "secret": secret, "enableRateLimit": True}
        )
    else:
        bot.send_message(
            message.from_user.id, "Неправильный API SECRET! Проверь и введи снова..."
        )
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

    if (len(str(signals_data)) >= 50) or (message.text == "/restart"):
        if message.text == "/restart":
            restart_bot(message)
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

        bot.send_message(
            message.from_user.id, "Я получил сигналы из поста, выглядят так:"
        )
        bot.send_message(message.from_user.id, "Пара: " + str(pair))
        bot.send_message(message.from_user.id, "Покупка: " + str(buy))
        bot.send_message(message.from_user.id, "Стоп лосс: " + str(stop_loss))

        if sell_1 is not None:
            bot.send_message(
                message.from_user.id, "Первая цель продажи: " + str(sell_1)
            )
        if sell_2 is not None:
            bot.send_message(
                message.from_user.id, "Вторая цель продажи: " + str(sell_2)
            )
        if sell_3 is not None:
            bot.send_message(
                message.from_user.id, "Третья цель продажи: " + str(sell_3)
            )
        if sell_4 is not None:
            bot.send_message(
                message.from_user.id, "Четвертая цель продажи: " + str(sell_4)
            )
        if sell_5 is not None:
            bot.send_message(message.from_user.id, "Пятая цель продажи: " + str(sell_5))

        bot.send_message(
            message.from_user.id, "Какую цель продажи будем использовать? "
        )
        bot.register_next_step_handler(message, select_sell)

    else:
        bot.send_message(
            message.from_user.id,
            "Нет, писать мне не надо! Мне можно только пересылать сообщения!",
        )
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
        or (message.text == "/restart")
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
        elif message.text == "/restart":
            restart_bot(message)

        bot.send_message(
            message.from_user.id, "Выбранная цель продажи: " + str(selected_sell_target)
        )

        coin = re.sub(r"[^A-Za-z]", "", sdd)
        balance_fetch = exchange.fetch_balance()
        balance_coin = float(balance_fetch["free"][coin])
        bot.send_message(
            message.from_user.id, "Твой " + coin + " баланс: " + str(balance_coin)
        )

        balance_btc = float(balance_fetch["free"]["BTC"])

        bot.send_message(
            message.from_user.id, "Твой BTC баланс: " + str(balance_btc) + " "
        )
        bot.send_message(
            message.from_user.id,
            "Какой процент от твоего BTC баланса будем использовать для этого трейда?\nОтправь мне желаемый процент (числом)\n10, например",
        )
        bot.register_next_step_handler(message, get_amount)

    else:
        bot.send_message(
            message.from_user.id, "Я принимаю только числа, вроде 1, 2, 3, 4 или 5 "
        )
        bot.register_next_step_handler(message, select_sell)


def get_amount(message):

    global amount
    global balance_coin
    global balance_btc
    global buy_after_exchange_fee
    global coin

    min_trade_amount = 10 / exchange.fetch_ticker("BTC/USDT")["low"]

    try:
        amount = (float(balance_btc) / 100) * float(message.text)
        if amount <= balance_btc and amount > 0:
            if amount > min_trade_amount:
                buy_after_exchange_fee = (amount / buy) - (
                    ((amount / buy) / 100) * exchange_fee
                )  # Fee in coin
                bot.send_message(
                    message.from_user.id,
                    "В трейде будет использовано: " + str(amount) + " BTC",
                )
                bot.send_message(
                    message.from_user.id,
                    "За них мы получим: "
                    + str(buy_after_exchange_fee)[:10]
                    + " "
                    + coin,
                )
                bot.send_message(
                    message.from_user.id, "Чтобы подтвердить трейд напиши мне: YES"
                )
                bot.register_next_step_handler(message, trader)
            else:
                bot.send_message(
                    message.from_user.id,
                    "Ты хочешь ипользовать"
                    + " "
                    + str(amount)
                    + " BTC\n"
                    + "Но минимальная сумма для трейда "
                    + str(min_trade_amount)[:8]
                    + " BTC! ~$10",
                )
                bot.register_next_step_handler(message, get_amount)

        else:
            bot.send_message(
                message.from_user.id, "Это больше твое BTC баланса, попробуй снова!"
            )
            bot.register_next_step_handler(message, get_amount)

    except:
        bot.send_message(message.from_user.id, "Введи корректный процент (число)!")
        bot.register_next_step_handler(message, get_amount)


def trader(message):

    if message.text == "/restart":
        restart_bot(message)
    elif message.text == "YES":
        bot.send_message(message.from_user.id, "Подготавливаю ...")
        buy_order(message)
        bot.register_next_step_handler(message, buy_order)
    else:
        bot.send_message(
            message.from_user.id,
            "Просто напиши YES (да, большими Американскими буквами)",
        )
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

    bot.send_message(
        message.from_user.id,
        "Разместил ордер на покупку, как исполниться напишу тебе ...",
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
            bot.send_message(
                message.from_user.id, "Ордер на покупку исполнен, готовлю продажу ..."
            )
            sell_order(message)
            bot.register_next_step_handler(message, sell_order)
            break
        else:
            pass
            buy_order_status = exchange.fetchOrder(orders_executed[0], pair, params)[
                "status"
            ]
            bot.send_message(
                message.from_user.id, "Жду исполнения ордера на покупку ..."
            )
            time.sleep(30)


def sell_order(message):

    global pair
    global exchange
    global orders_executed
    global selected_sell_target
    global stop_loss
    global buy_after_exchange_fee

    buy_after_exchange_fee = float(str(buy_after_exchange_fee)[:10])

    stop_loss_limit_order = exchange.create_order(
        pair,
        "stop_loss_limit",
        "sell",
        buy_after_exchange_fee,
        selected_sell_target,
        {"stopPrice": stop_loss},
    )
    bot.send_message(
        message.from_user.id, "Ордер на продажу и стоп лосс размещены, желаю профита ;)"
    )
    bot.send_message(
        message.from_user.id,
        "Чтобы снова воспользоваться моими услугами отправь мне /start :)",
    )

    os.execl(sys.executable, sys.executable, *sys.argv)


def restart_bot(message):

    if message.text == "/restart":
        bot.send_message(
            message.from_user.id, "Рестарт завершен, отправь мне /start для начала..."
        )
        os.execl(sys.executable, sys.executable, *sys.argv)


bot.polling(none_stop=True, interval=0)
