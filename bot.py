import discord
from discord.ext import commands, tasks
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

STOCKS_FILE = 'stocks.json'
stock_list = []

def load_stocks():
    try:
        with open(STOCKS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_stocks(stocks):
    with open(STOCKS_FILE, 'w') as f:
        json.dump(stocks, f)

@bot.event
async def on_ready():
    global stock_list
    stock_list
