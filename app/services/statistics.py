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
    
    async def get_revenue_stats(self) -> Dict:
        total_revenue = await self.session.scalar(
            select(func.sum(Transaction.amount)).where(
                Transaction.status == TransactionStatus.COMPLETED
            )
        )
        
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        revenue_today = await self.session.scalar(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.status == TransactionStatus.COMPLETED,
                    func.date(Transaction.completed_at) == today
                )
            )
        )
        
        revenue_week = await self.session.scalar(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.status == TransactionStatus.COMPLETED,
                    func.date(Transaction.completed_at) >= week_ago
                )
            )
        )
        
        revenue_month = await self.session.scalar(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.status == TransactionStatus.COMPLETED,
                    func.date(Transaction.completed_at) >= month_ago
                )
            )
        )
        
        total_transactions = await self.session.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.status == TransactionStatus.COMPLETED
            )
        )
        
        return {
            "total_revenue": total_revenue or 0,
            "revenue_today": revenue_today or 0,
            "revenue_week": revenue_week or 0,
            "revenue_month": revenue_month or 0,
            "total_transactions": total_transactions or 0,
            "average_transaction": (total_revenue / total_transactions) if total_transactions else 0
        }
    
    async def get_gift_stats(self) -> Dict:
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
    
    async def generate_user_growth_chart(self) -> str:
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
        
        df = pd.DataFrame(data, columns=['date', 'count'])
        df['cumulative'] = df['count'].cumsum()
        
        plt.style.use('seaborn-v0_8')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        ax1.plot(df['date'], df['count'], marker='o', linewidth=2, markersize=6)
        ax1.set_title('📈 Daily New Users (Last 30 Days)', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('New Users')
        ax1.grid(True, alpha=0.3)
        
        ax2.plot(df['date'], df['cumulative'], marker='s', linewidth=2, markersize=6, color='green')
        ax2.set_title('📊 Cumulative User Growth', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Total Users')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        os.makedirs(settings.CHARTS_DIR, exist_ok=True)
        chart_path = f"{settings.CHARTS_DIR}/user_growth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    async def generate_revenue_chart(self) -> str:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        result = await self.session.execute(
            select(
                func.date(Transaction.completed_at).label('date'),
                func.sum(Transaction.amount).label('revenue'),
                func.count(Transaction.id).label('transactions')
            )
            .where(
                and_(
                    Transaction.status == TransactionStatus.COMPLETED,
                    Transaction.completed_at >= thirty_days_ago
                )
            )
            .group_by(func.date(Transaction.completed_at))
            .order_by('date')
        )
        
        data = [(row.date, row.revenue, row.transactions) for row in result]
        
        if not data:
            return None
        
        df = pd.DataFrame(data, columns=['date', 'revenue', 'transactions'])
        
        plt.style.use('seaborn-v0_8')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        ax1.bar(df['date'], df['revenue'], alpha=0.7, color='gold')
        ax1.set_title('💰 Daily Revenue (Last 30 Days)', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Revenue (Stars)')
        ax1.grid(True, alpha=0.3)
        
        ax2.bar(df['date'], df['transactions'], alpha=0.7, color='skyblue')
        ax2.set_title('🔄 Daily Transactions', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Number of Transactions')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        chart_path = f"{settings.CHARTS_DIR}/revenue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
