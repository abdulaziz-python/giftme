from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from app.models.database import User, Transaction, WonGift, Gift, Broadcast, TransactionStatus
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import base64
from typing import Dict, List, Optional
import os
from app.core.config import settings

class StatisticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_stats(self) -> Dict:
        try:
            total_users = await self.session.scalar(select(func.count(User.id)))
            
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            new_users_today = await self.session.scalar(
                select(func.count(User.id)).where(
                    func.date(User.created_at) == today
                )
            )
            
            new_users_week = await self.session.scalar(
                select(func.count(User.id)).where(
                    func.date(User.created_at) >= week_ago
                )
            )
            
            new_users_month = await self.session.scalar(
                select(func.count(User.id)).where(
                    func.date(User.created_at) >= month_ago
                )
            )
            
            active_users_today = await self.session.scalar(
                select(func.count(User.id)).where(
                    func.date(User.last_activity) == today
                )
            )
            
            premium_users = await self.session.scalar(
                select(func.count(User.id)).where(User.is_premium == True)
            )
            
            blocked_users = await self.session.scalar(
                select(func.count(User.id)).where(User.is_blocked == True)
            )
            
            return {
                "total_users": total_users or 0,
                "new_users_today": new_users_today or 0,
                "new_users_week": new_users_week or 0,
                "new_users_month": new_users_month or 0,
                "active_users_today": active_users_today or 0,
                "premium_users": premium_users or 0,
                "blocked_users": blocked_users or 0
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {
                "total_users": 0,
                "new_users_today": 0,
                "new_users_week": 0,
                "new_users_month": 0,
                "active_users_today": 0,
                "premium_users": 0,
                "blocked_users": 0
            }
    
    async def get_revenue_stats(self) -> Dict:
        try:
            total_revenue = await self.session.scalar(
                select(func.sum(Transaction.amount)).where(
                    Transaction.status == TransactionStatus.COMPLETED.value
                )
            )
            
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            revenue_today = await self.session.scalar(
                select(func.sum(Transaction.amount)).where(
                    and_(
                        Transaction.status == TransactionStatus.COMPLETED.value,
                        func.date(Transaction.completed_at) == today
                    )
                )
            )
            
            revenue_week = await self.session.scalar(
                select(func.sum(Transaction.amount)).where(
                    and_(
                        Transaction.status == TransactionStatus.COMPLETED.value,
                        func.date(Transaction.completed_at) >= week_ago
                    )
                )
            )
            
            revenue_month = await self.session.scalar(
                select(func.sum(Transaction.amount)).where(
                    and_(
                        Transaction.status == TransactionStatus.COMPLETED.value,
                        func.date(Transaction.completed_at) >= month_ago
                    )
                )
            )
            
            total_transactions = await self.session.scalar(
                select(func.count(Transaction.id)).where(
                    Transaction.status == TransactionStatus.COMPLETED.value
                )
            )
            
            return {
                "total_revenue": total_revenue or 0,
                "revenue_today": revenue_today or 0,
                "revenue_week": revenue_week or 0,
                "revenue_month": revenue_month or 0,
                "total_transactions": total_transactions or 0,
                "average_transaction": (total_revenue / total_transactions) if total_transactions and total_revenue else 0
            }
        except Exception as e:
            print(f"Error getting revenue stats: {e}")
            return {
                "total_revenue": 0,
                "revenue_today": 0,
                "revenue_week": 0,
                "revenue_month": 0,
                "total_transactions": 0,
                "average_transaction": 0
            }
    
    async def get_gift_stats(self) -> Dict:
        try:
            total_gifts_won = await self.session.scalar(select(func.count(WonGift.id)))
            
            gifts_today = await self.session.scalar(
                select(func.count(WonGift.id)).where(
                    func.date(WonGift.won_at) == datetime.utcnow().date()
                )
            )
            
            most_popular_gifts = await self.session.execute(
                select(Gift.name, func.count(WonGift.id).label('count'))
                .join(WonGift)
                .group_by(Gift.id, Gift.name)
                .order_by(desc('count'))
                .limit(5)
            )
            
            popular_gifts = [{"name": row.name, "count": row.count} for row in most_popular_gifts]
            
            total_gift_value = await self.session.scalar(
                select(func.sum(Gift.star_count))
                .join(WonGift)
            )
            
            return {
                "total_gifts_won": total_gifts_won or 0,
                "gifts_today": gifts_today or 0,
                "most_popular_gifts": popular_gifts,
                "total_gift_value": total_gift_value or 0
            }
        except Exception as e:
            print(f"Error getting gift stats: {e}")
            return {
                "total_gifts_won": 0,
                "gifts_today": 0,
                "most_popular_gifts": [],
                "total_gift_value": 0
            }
    
    async def generate_user_growth_chart(self) -> Optional[str]:
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            result = await self.session.execute(
                select(
                    func.date(User.created_at).label('date'),
                    func.count(User.id).label('count')
                )
                .where(User.created_at >= thirty_days_ago)
                .group_by(func.date(User.created_at))
                .order_by('date')
            )
            
            data = [(row.date, row.count) for row in result]
            
            if not data:
                return None
            
            # Create directory if it doesn't exist
            os.makedirs(settings.CHARTS_DIR, exist_ok=True)
            
            df = pd.DataFrame(data, columns=['date', 'count'])
            df['cumulative'] = df['count'].cumsum()
            
            plt.figure(figsize=(12, 10))
            
            # First subplot - Daily new users
            plt.subplot(2, 1, 1)
            plt.plot(df['date'], df['count'], marker='o', linewidth=2, markersize=6)
            plt.title('📈 Daily New Users (Last 30 Days)', fontsize=14, fontweight='bold')
            plt.xlabel('Date')
            plt.ylabel('New Users')
            plt.grid(True, alpha=0.3)
            
            # Second subplot - Cumulative user growth
            plt.subplot(2, 1, 2)
            plt.plot(df['date'], df['cumulative'], marker='s', linewidth=2, markersize=6, color='green')
            plt.title('📊 Cumulative User Growth', fontsize=14, fontweight='bold')
            plt.xlabel('Date')
            plt.ylabel('Total Users')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            chart_path = f"{settings.CHARTS_DIR}/user_growth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
        except Exception as e:
            print(f"Error generating user growth chart: {e}")
            return None
    
    async def generate_revenue_chart(self) -> Optional[str]:
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            result = await self.session.execute(
                select(
                    func.date(Transaction.completed_at).label('date'),
                    func.sum(Transaction.amount).label('revenue'),
                    func.count(Transaction.id).label('transactions')
                )
                .where(
                    and_(
                        Transaction.status == TransactionStatus.COMPLETED.value,
                        Transaction.completed_at >= thirty_days_ago
                    )
                )
                .group_by(func.date(Transaction.completed_at))
                .order_by('date')
            )
            
            data = [(row.date, row.revenue, row.transactions) for row in result]
            
            if not data:
                return None
            
            # Create directory if it doesn't exist
            os.makedirs(settings.CHARTS_DIR, exist_ok=True)
            
            df = pd.DataFrame(data, columns=['date', 'revenue', 'transactions'])
            
            plt.figure(figsize=(12, 10))
            
            # First subplot - Daily revenue
            plt.subplot(2, 1, 1)
            plt.bar(df['date'], df['revenue'], alpha=0.7, color='gold')
            plt.title('💰 Daily Revenue (Last 30 Days)', fontsize=14, fontweight='bold')
            plt.xlabel('Date')
            plt.ylabel('Revenue (Stars)')
            plt.grid(True, alpha=0.3)
            
            # Second subplot - Daily transactions
            plt.subplot(2, 1, 2)
            plt.bar(df['date'], df['transactions'], alpha=0.7, color='skyblue')
            plt.title('🔄 Daily Transactions', fontsize=14, fontweight='bold')
            plt.xlabel('Date')
            plt.ylabel('Number of Transactions')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            chart_path = f"{settings.CHARTS_DIR}/revenue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
        except Exception as e:
            print(f"Error generating revenue chart: {e}")
            return None
