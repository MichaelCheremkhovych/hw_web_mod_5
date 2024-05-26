import aiohttp
import asyncio
import datetime
from typing import List, Dict, Any

class CurrencyRateFetcher:
    API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

    def __init__(self, days: int):
        if days > 10:
            raise ValueError("Cannot fetch data for more than 10 days")
        self.days = days

    async def fetch_rate(self, session: aiohttp.ClientSession, date: str) -> Dict[str, Any]:
        url = f"{self.API_URL}{date}"
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch data for {date}")
            return await response.json()

    async def fetch_rates(self) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(self.days):
                date = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%d.%m.%Y')
                tasks.append(self.fetch_rate(session, date))
            return await asyncio.gather(*tasks)

class CurrencyRatePrinter:
    @staticmethod
    def print_rates(rates: List[Dict[str, Any]]):
        for rate in rates:
            date = rate.get('date', 'N/A')
            exchange_rate = rate.get('exchangeRate', [])
            usd_rate = next((item for item in exchange_rate if item["currency"] == "USD"), None)
            eur_rate = next((item for item in exchange_rate if item["currency"] == "EUR"), None)

            print(f"Date: {date}")
            if usd_rate:
                print(f"USD: Buy - {usd_rate['purchaseRate']}, Sell - {usd_rate['saleRate']}")
            else:
                print("USD: No data available")

            if eur_rate:
                print(f"EUR: Buy - {eur_rate['purchaseRate']}, Sell - {eur_rate['saleRate']}")
            else:
                print("EUR: No data available")

            print()

async def main(days: int):
    fetcher = CurrencyRateFetcher(days)
    rates = await fetcher.fetch_rates()
    CurrencyRatePrinter.print_rates(rates)

if __name__ == "__main__":
    days = int(input("Enter the number of days (up to 10): "))
    asyncio.run(main(days))
