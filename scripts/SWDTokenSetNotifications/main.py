from datetime import datetime
import os
import sys
import time
from discord import Webhook, RequestsWebhookAdapter
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
import urllib
from pexpect import TIMEOUT
import telegram
from web3 import Web3
from emojis import getEmoji
from polygonGET import (
    checkAddress,
    comparePositions,
    getName,
    getPositions,
    getSymbol,
    initConnection,
    lastPositions,
    updateFile,
)
from dotenv import load_dotenv

load_dotenv()
ADDRESSES = [
    "0x25ad32265c9354c29e145c902ae876f6b69806f2",  # Alpha Portfolio
    "0x71b41b3b19aac53ca4063aec2d17fc3caeb38026",  # Macro Trend BTC
    "0x72Ca52512b93E8D67309aF0C14C1A225bcbd3548",  # Macro Trend ETH
    "0xabcc2102065ba01c6df1a5a5a57158f452403b70",  # Quantum Momentum BTC
    "0x9984d846a3dc77aa0488f3758976b149e8475995",  # Quantum Momentum ETH
    "0x20ab4cb8f8da39582bc92da954ab1bb128f4e244",  # Quantum Momentum MATIC
    "0x58f7C5707Ba8E09B5e61ceBe8821f65434372344",  # Buy the Dip BTC
    "0x07A79127182a1c303d11eCDa951310EC1C2E1444",  # Buy the Dip ETH
    "0xb87352B4C3EB9daEd09cD4996dFf85c122394912",  # Buy the Dip MATIC
    # "0xf2aa5ccea80c246a71e97b418173fcc956408d3f",  # Discretionary BTC
    # "0x72b467cacbdbec5918d8eec0371ca33e6fd42421",  # Discretionary ETH
    # "0xab80a6e2909c8089ebd84f331c05bbefa3276cd2",  # Discretionary MATIC
    # "0x62135f85899d97aed95f4405d710208e68b99f39",  # DeFi Value Index
    # "0xB4f78a05ab16CD3e6d0100112D0CC431942859Bb",  # BTC Momentum Index
    # "0xd3ef811331a98d24a2B2FB64cEBeEa5aF31b2568",  # ETH Momentum Index
    # "0xDFdDd9811796F72bA32a031724f5B1403CD48B91",  # MATIC Momentum Index
    # "0xB5253C58b8a361d9901922b23eC9fB9E7d38C98a",  # DPI Momentum Index
    # "0xad2b726fd2bd3a7f8f4b3929152438eba637ef19",  # SWD Momentum Index
    # "0x55a40b33CFf2eb062e7aa76506B7De711F2B2aff",  # Polygon Ecosystem In dex
]  # contract addresS

PIPE = os.getenv("TSN_PIPE")
TELEGRAM_BOT_TOKEN = os.getenv("TSN_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TSN_TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK_URL = os.getenv("TSN_DISCORD_WEBHOOK_URL")
TIMEOUT = int(os.getenv("TSN_TIMEOUT"))


def prepareMessage(w3, obj, address):
    title = getName(w3, address).replace("INDEX", "Index")
    telegram = f"<b>⚠️{title} Rebalance Alert⚠️</b>\n\n"
    sSymbol = getSymbol(w3, address)
    emoji = getEmoji(sSymbol)
    discord = f"{emoji} **{title} Rebalance Alert** {emoji}\n\n"
    for i in obj:
        if len(obj[i]) != 0:
            for x in range(len(i)):
                try:
                    t = ""
                    t2 = ""
                    if i == "in":
                        t2 = " is in 📈\n\n"
                    elif i == "out":
                        t2 = " is out 📉\n\n"
                    elif i == "pout":
                        t = "Partial "
                        t2 = " is out 📉\n\n"
                    elif i == "pin":
                        t = "More "
                        t2 = " is in 📈\n\n"
                    else:
                        continue
                    symbol = getSymbol(w3, obj[i][x])
                    telegram += f"{t}${symbol}{t2}"
                    discord += f"{t}${symbol}{t2}"
                except IndexError:
                    pass
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"👉 Buy ${getSymbol(w3, address)} on Polygon 👈",
                    url=f"https://tokensets.com/v2/set/polygon/{address.lower()}",
                )
            ]
        ]
    )
    discord += f"👇Buy ${getSymbol(w3, address)} on Polygon👇\n\nhttps://tokensets.com/v2/set/polygon/{address.lower()}"

    return telegram, discord, reply_markup


def telegramNotification(message, reply_markup):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    try:
        bot.sendMessage(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
        print(f"\n{now} - Message send to Telegram:")
    except Exception as inst:
        print(f"ERROR with Telegram {now}: {inst}")


def discordNotification(message):
    dc = Webhook.from_url(DISCORD_WEBHOOK_URL, adapter=RequestsWebhookAdapter())
    dc.send(message)
    now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    print(f"{now} - Message send to Dicord")


def mainLoop():
    for address in ADDRESSES:

        w3 = initConnection(PIPE)
        if checkAddress(w3, address):
            continue
        address = Web3.toChecksumAddress(address)
        positions = getPositions(w3, address)
        lastPos = lastPositions(positions, address)
        obj = comparePositions(lastPos, positions)
        if obj == None:
            now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            sys.stdout.write(
                f"\r{now} -- TIMEOUT {TIMEOUT} SEC: No updates with {address} "
            )
            sys.stdout.flush()
            time.sleep(TIMEOUT)
            continue
        telegramMsg, discordMsg, reply_markup = prepareMessage(w3, obj, address)
        updateFile(positions, address)
        telegramNotification(message=telegramMsg, reply_markup=reply_markup)
        discordNotification(discordMsg)


def main():
    while True:
        mainLoop()


if __name__ == "__main__":
    main()
