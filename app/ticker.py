from collections import defaultdict
from datetime import datetime as dt
import json
from kiteconnect import KiteTicker
import logging
import os
from functools import reduce

logging.basicConfig(level=logging.DEBUG)


# NIFTY, BANKNIFTY
tokens = [256265]
#tokens = [260105]

def getAtmInstruments(ws, name, spot):
    rem = spot % 100
    quotient = spot // 100
    factor = 1 if (name == "NIFTY") else 2
    if rem <= 50:
        strikes = [quotient * 100, quotient * 100 + 50 * factor]
    else:
        strikes = [(quotient + 1) * 100, (quotient + 1) * 100 - 50 * factor]

    #logging.info(strikes)
    trades = filter(lambda ins: ins["strike"] in strikes and 
                                   ins["name"] == name, ws.instruments)
    #print(list(trades))
    sorted_trades = sorted(trades,
                           key=lambda i: dt.strptime(i["expiry"], "%Y-%m-%d"))

    return sorted_trades[:4]


def get_skew(cep, pep):
    return round((abs(cep - pep) / min(cep, pep)) * 100, 2)


def update_strike_list(ws, instruments):
    new_tokens = []
    for x in instruments:
        strike_list = ws.strike_list["NIFTY"][x["tradingsymbol"][-7:-2]]
        if x["instrument_token"] not in strike_list:
            strike_list.append(x["instrument_token"])
        new_tokens.append(x["instrument_token"])
    #print(ws.strike_list)
    return new_tokens


def place_order(ws, strike):
    trades = list(filter(lambda ins: ins["instrument_token"] in strike,
                    ws.instruments))
    print(trades[0]["tradingsymbol"], trades[1]["tradingsymbol"])
    ws.callback(trades)

# Callback for tick reception.
def on_ticks(ws, ticks):
    logging.info(list(map(lambda x: str(x["instrument_token"]) + ": " +
                          str(x["last_price"]), ticks)))
    if ws.stoploss > 0:
        if len(ticks) == 2:
            premium = reduce(lambda x, y: x + y, map(lambda x: x["last_price"], ticks))
            if premium > 75:
                print("stoploss triggered")
                ws.stoploss = 0
                ws.unsubscribe(tokens)
                trades = list(filter(lambda ins: ins["instrument_token"] in tokens,
                              ws.instruments))
                ws.callback(trades)
        return

    if len(ticks) == 1:
        instruments = getAtmInstruments(ws, "NIFTY", ticks[0]["last_price"])
        tokens.extend(update_strike_list(ws, instruments))
        ws.subscribe(tokens)
        ws.set_mode(ws.MODE_LTP, tokens)
    else:
        nf_strike_list = ws.strike_list["NIFTY"]
        keys = nf_strike_list.keys()
        for key in keys:
            strike = list(filter(lambda x: x["instrument_token"] in
                                   nf_strike_list[key], ticks))
            if len(strike) == 2:
                print('premium is ', strike[0]["last_price"] +
                      strike[1]["last_price"])
                skew = get_skew(strike[0]["last_price"], strike[1]["last_price"])
                if skew < 100:
                    print("place order with strike price: " + key)
                    if ws.order_placed == False:
                        ws.order_placed = True
                        ws.unsubscribe(tokens)
                        place_order(ws, nf_strike_list[key])
                        print("order placed")


# Callback for successful connection.
def on_connect(ws, response):
    logging.info("Successfully connected. Response: {}".format(response))
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_LTP, tokens)
    logging.info("Subscribe to tokens in Full mode: {}".format(tokens))


# Callback when current connection is closed.
def on_close(ws, code, reason):
    logging.info("Connection closed: {code} - {reason}".format(code=code, reason=reason))


# Callback when connection closed with error.
def on_error(ws, code, reason):
    logging.info("Connection error: {code} - {reason}".format(code=code, reason=reason))


# Callback when reconnect is on progress
def on_reconnect(ws, attempts_count):
    logging.info("Reconnecting: {}".format(attempts_count))


# Callback when all reconnect failed (exhausted max retries)
def on_noreconnect(ws):
    logging.info("Reconnect failed.")


def start_ticker(callback, stoploss = 0):

    kws = KiteTicker(os.environ["kite_api_key"], os.environ["kite_access_token"])
    kws.on_ticks = on_ticks
    kws.on_close = on_close
    kws.on_error = on_error
    kws.on_connect = on_connect
    kws.on_reconnect = on_reconnect
    kws.on_noreconnect = on_noreconnect
    kws.instruments = json.load(open('instruments.json', 'r'))
    kws.strike_list = {"NIFTY": defaultdict(list),
                       "BANKNIFTY": defaultdict(list)}
    kws.order_placed = False

    kws.callback = callback
    kws.stoploss = stoploss
    if stoploss > 0:
        tokens.clear()
        tokens.extend([13918210, 13918466])
    kws.connect(threaded=True)

    logging.info("kws connect complete")
    return kws
