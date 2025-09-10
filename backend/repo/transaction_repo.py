import aiosqlite
from typing import List
from datetime import datetime, timedelta
from decimal import Decimal

from models import Transaction


class TransactionRepo:
    def __init__(self):
        pass

    async def get_recent_transactions(self, portfolio_id: int = 1, days: int = 7) -> List[Transaction]:
        """DB에서 최근 거래 기록 조회"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()

            async with aiosqlite.connect("porta.db") as db:
                cursor = await db.execute(
                    """
                    SELECT id, portfolio_id, ticker, transaction_type, shares, price,
                        transaction_date, fee, currency, exchange, notes, created_at
                    FROM transactions
                    WHERE portfolio_id = ? AND transaction_date >= ?
                    ORDER BY transaction_date DESC, created_at DESC
                    """,
                    (portfolio_id, cutoff_date),
                )
                rows = await cursor.fetchall()

                transactions = []
                for row in rows:
                    transactions.append(
                        Transaction(
                            id=row[0],
                            portfolio_id=row[1],
                            ticker=row[2],
                            transaction_type=row[3],
                            shares=Decimal(str(row[4])),
                            price=Decimal(str(row[5])),
                            transaction_date=row[6],
                            fee=Decimal(str(row[7])),
                            currency=row[8],
                            exchange=row[9],
                            notes=row[10],
                            created_at=row[11],
                        )
                    )
                return transactions
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return []
