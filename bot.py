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
        json.dump(stocks, f, indent=4)

@bot.event
async def on_ready():
    global stock_list
    stock_list = load_stocks()
    print(f'{bot.user} 已上線！目前追蹤 {len(stock_list)} 支股票')
    print('可用指令: /addstock <代碼>, /delstock <代碼>, /stocks, /price <代碼>')

@bot.command(name='addstock')
async def add_stock(ctx, symbol: str):
    try:
        symbol = symbol.upper()
        stock = yf.Ticker(symbol)
        info = stock.info
        if 'longName' in info:
            new_stock = {
                'symbol': symbol,
                'name': info.get('longName', 'Unknown'),
                'added': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            if new_stock not in stock_list:
                stock_list.append(new_stock)
                save_stocks(stock_list)
                await ctx.send(f'✅ 已新增 `{info["longName"]} ({symbol})` 到追蹤清單')
            else:
                await ctx.send(f'❌ `{symbol}` 已存在清單中')
        else:
            await ctx.send(f'❌ 找不到股票代碼 `{symbol}`')
    except Exception as e:
        await ctx.send(f'錯誤: {str(e)}')

@bot.command(name='delstock')
async def del_stock(ctx, symbol: str):
    global stock_list
    symbol = symbol.upper()
    original_len = len(stock_list)
    stock_list = [s for s in stock_list if s['symbol'] != symbol]
    if len(stock_list) < original_len:
        save_stocks(stock_list)
        await ctx.send(f'✅ 已移除 `{symbol}`')
    else:
        await ctx.send(f'❌ 清單中沒有 `{symbol}`')

@bot.command(name='stocks')
async def list_stocks(ctx):
    if stock_list:
        msg = '**📈 追蹤股票清單:**\n'
        for stock in stock_list:
            msg += f'`{stock["symbol"]}` - {stock["name"]}\n'
        await ctx.send(msg)
    else:
        await ctx.send('📭 清單目前為空，使用 `/addstock <代碼>` 新增股票')

@bot.command(name='price')
async def get_price(ctx, symbol: str):
    try:
        symbol = symbol.upper()
        stock = yf.Ticker(symbol)
        data = stock.history(period='2d')
        if not data.empty:
            current = data['Close'].iloc[-1]
            prev = data['Close'].iloc[-2] if len(data) > 1 else current
            change = current - prev
            change_pct = (change / prev) * 100 if prev != 0 else 0
            info = stock.info
            name = info.get('longName', symbol)
            emoji = '🟢' if change >= 0 else '🔴'
            msg = f'{emoji} **{name} ({symbol})**\n'
            msg += f'💰 現價: ${current:.2f}\n'
            msg += f'📊 漲跌: ${change:.2f} ({change_pct:+.2f}%)\n'
            msg += f'⏰ 更新: {datetime.now().strftime("%H:%M:%S")} CST'
            await ctx.send(msg)
        else:
            await ctx.send(f'❌ 無法取得 `{symbol}` 即時價格')
    except Exception as e:
        await ctx.send(f'錯誤: {str(e)}')

@bot.command(name='help')
async def help_cmd(ctx):
    embed = discord.Embed(title='📈 股票追蹤 Bot 說明', color=0x00ff00)
    embed.add_field(name='/addstock <代碼>', value='新增股票到追蹤清單 (如: /addstock TSLA)', inline=False)
    embed.add_field(name='/delstock <代碼>', value='移除追蹤股票', inline=False)
    embed.add_field(name='/stocks', value='顯示所有追蹤股票', inline=False)
    embed.add_field(name='/price <代碼>', value='查詢即時股價 (如: /price AAPL)', inline=False)
    embed.add_field(name='/help', value='顯示此說明', inline=False)
    await ctx.send(embed=embed)

# 每小時檢查價格變化 (可選)
@tasks.loop(hours=1)
async def price_check():
    channel = bot.get_channel(YOUR_CHANNEL_ID)  # 替換成你的 Discord 頻道 ID
    if channel and stock_list:
        for stock in stock_list:
            ticker = yf.Ticker(stock['symbol'])
            data = ticker.history(period='2d')
            if len(data) > 1:
                current = data['Close'].iloc[-1]
                prev = data['Close'].iloc[-2]
                change_pct = ((current - prev) / prev) * 100
                if abs(change_pct) > 5:  # 漲跌超過 5%
                    await channel.send(f'🚨 {stock["name"]} ({stock["symbol"]}) 變動 {change_pct:+.1f}%')

if __name__ == '__main__':
    print('Bot 啟動中... 請輸入你的 Bot Token')
    # 改成這樣（已安全）：
    TOKEN = input('請輸入 Bot Token: ')  # 執行時手動輸入
    bot.run(TOKEN)
