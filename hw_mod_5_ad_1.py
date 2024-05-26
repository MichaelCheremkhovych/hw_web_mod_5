import aiohttp
import asyncio
import datetime
import argparse
import json
import websockets
from typing import List, Dict, Any
from aiofile import async_open
from aiopath import AsyncPath

class CurrencyRateFetcher:
    API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

    def __init__(self, days: int, currencies: List[str]):
        # Перевіряємо, що кількість днів не перевищує 10
        if days > 10:
            raise ValueError("Cannot fetch data for more than 10 days")
        self.days = days
        self.currencies = currencies

    async def fetch_rate(self, session: aiohttp.ClientSession, date: str) -> Dict[str, Any]:
        # Формуємо URL для запиту
        url = f"{self.API_URL}{date}"
        async with session.get(url) as response:
            # Перевіряємо статус відповіді
            if response.status != 200:
                raise Exception(f"Failed to fetch data for {date}")
            # Повертаємо JSON-відповідь
            return await response.json()

    async def fetch_rates(self) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(self.days):
                # Формуємо дату для кожного дня
                date = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%d.%m.%Y')
                tasks.append(self.fetch_rate(session, date))
            # Виконуємо асинхронно всі запити
            return await asyncio.gather(*tasks)

class CurrencyRatePrinter:
    @staticmethod
    def print_rates(rates: List[Dict[str, Any]], currencies: List[str]):
        for rate in rates:
            date = rate.get('date', 'N/A')
            exchange_rate = rate.get('exchangeRate', [])
            print(f"Date: {date}")
            # Виводимо курси для кожної валюти
            for currency in currencies:
                currency_rate = next((item for item in exchange_rate if item["currency"] == currency), None)
                if currency_rate:
                    print(f"{currency}: Buy - {currency_rate['purchaseRate']}, Sell - {currency_rate['saleRate']}")
                else:
                    print(f"{currency}: No data available")
            print()

async def main(days: int, currencies: List[str]):
    fetcher = CurrencyRateFetcher(days, currencies)
    rates = await fetcher.fetch_rates()
    CurrencyRatePrinter.print_rates(rates, currencies)

def parse_args():
    parser = argparse.ArgumentParser(description="Currency rate fetcher")
    parser.add_argument('--days', type=int, default=1, help='Number of days to fetch rates for (up to 10)')
    parser.add_argument('--currencies', nargs='+', default=['USD', 'EUR'], help='List of currencies to fetch rates for')
    return parser.parse_args()

# Отримуємо аргументи командного рядка
args = parse_args()
asyncio.run(main(args.days, args.currencies))

