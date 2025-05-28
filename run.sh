#!/bin/bash

echo "🚀 Starting Telegram Gift Roulette Bot..."

if [ ! -f .env ]; then
    echo "❌ .env file not found! Please copy .env.example to .env and configure it."
    exit 1
fi

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗄️ Running database migrations..."
alembic upgrade head

echo "🎯 Starting the application..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
