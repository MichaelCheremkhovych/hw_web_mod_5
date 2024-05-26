import websockets
import aiohttp
import asyncio
import datetime
from aiofile import async_open
from aiopath import AsyncPath
from typing import List

# Набір підключених клієнтів
clients = set()

# Логування команд у файл
async def log_command(command: str):
    async with async_open(AsyncPath('chat.log'), 'a') as afp:
        await afp.write(f"{datetime.datetime.now()}: {command}\n")

# Отримання курсу валют для поточної дати
async def fetch_currency_rate(currency: str):
    async with aiohttp.ClientSession() as session:
        date = datetime.datetime.now().strftime('%d.%m.%Y')
        url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                rate = next((item for item in data['exchangeRate'] if item['currency'] == currency), None)
                if rate:
                    return f"{currency}: Buy - {rate['purchaseRate']}, Sell - {rate['saleRate']}"
                else:
                    return f"No data for {currency}"
            else:
                return "Failed to fetch data"

# Обробка команди exchange
async def exchange_command(params: List[str]):
    days = 1 if len(params) == 0 else int(params[0])
    currencies = ['USD', 'EUR']
    results = []
    for i in range(days):
        date = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%d.%m.%Y')
        async with aiohttp.ClientSession() as session:
            url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = []
                    for currency in currencies:
                        rate = next((item for item in data['exchangeRate'] if item['currency'] == currency), None)
                        if rate:
                            rates.append(f"{currency}: Buy - {rate['purchaseRate']}, Sell - {rate['saleRate']}")
                        else:
                            rates.append(f"No data for {currency}")
                    results.append(f"Date: {date}\n" + "\n".join(rates))
                else:
                    results.append(f"Failed to fetch data for {date}")
    return "\n\n".join(results)

# Обробка повідомлень від клієнта
async def handle_client(websocket, path):
    clients.add(websocket)
    try:
        async for message in websocket:
            if message.startswith("exchange"):
                params = message.split()[1:]
                result = await exchange_command(params)
                await log_command(message)
                await websocket.send(result)
            else:
                for client in clients:
                    if client != websocket:
                        await client.send(message)
    finally:
        clients.remove(websocket)

# Запуск веб-сокет сервера
async def main():
    server = await websockets.serve(handle_client, "localhost", 12345)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
