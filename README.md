# ⏳ Lifery Bot

A Telegram bot that reminds you of the transience of time by visualizing the weeks of your life lived. Inspired by Stoic philosophy and the concept of Memento Mori.

> "Remember death to truly live."

## 🚀 Features
* 📅 **Life Calendar:** The user enters their birth date, and the bot calculates the weeks lived (based on an average lifespan of 4680 weeks).
* 🔔 **Weekly Reminders:** Every Monday at 12:00 UTC, users receive a notification with the number of weeks passed and a motivating quote.
* 🌍 **Auto-Localization:** Automatically detects the user's language (EN/RU) based on Telegram settings.
* 🛡 **Robust Architecture:** Fully asynchronous code, resilient to high loads, restarts, and network failures.

## 🛠 Tech Stack
* **Python 3.13+**
* **python-telegram-bot** (Async version + JobQueue)
* **PostgreSQL** (Database)
* **SQLAlchemy + asyncpg** (Asynchronous ORM)
* **Docker & Docker Compose** (Containerization)

## ⚙️ Installation & Setup

### Prerequisites
* Docker & Docker Compose
* Git

### 1. Clone the repository
```bash
git clone https://github.com/notkurrent/lifery.git
cd lifery
```

### 2. Configuration
Create a `.env` file from the example:
```bash
cp .env.example .env
```

Open `.env` and populate it with your credentials:
* `BOT_TOKEN`: Get it from @BotFather
* `POSTGRES_USER` / `POSTGRES_PASSWORD`: Set your preferred database credentials

### 3. Run with Docker
Build and start the container in detached mode:
```bash
docker compose up -d --build
```

The bot will automatically:
1. Wait for the PostgreSQL database to be ready (Healthcheck).
2. Initialize the database schema (create tables).
3. Start the scheduler and polling loop.

## 🤝 Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License
[MIT](https://choosealicense.com/licenses/mit/)