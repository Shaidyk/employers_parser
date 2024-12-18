# Work Parser Telegram Bot

This project is designed for parsing job vacancies using a Telegram bot.

## Project Setup

### Step 1: Create the `.env` File

Create a `.env` file in the root directory of the project based on the `.env.example` file. Specify the required variables:

```env
TG_BOT_TOKEN=<Your_Telegram_Bot_Token>
CHROME_DRIVER_PATH=<Full_Path_To_Chromedriver>
```

### Step 2: Ensure Chrome is Installed

1. Check your Chrome version by visiting:
   ```
   chrome://settings/help
   ```
2. Make sure the Chrome version matches the ChromeDriver version.

### Step 3: Download ChromeDriver

1. Download ChromeDriver from the official website:
   [ChromeDriver Download](https://chromedriver.chromium.org/downloads)
2. Select the version that matches your Chrome browser.

### Step 4: Place ChromeDriver in the Project

1. Place the downloaded `chromedriver` in the project directory as specified in `.env_example`.
2. Set the **full path** to `chromedriver` in the `.env` file under the variable `CHROME_DRIVER_PATH`.

Example:
```
CHROME_DRIVER_PATH=/home/username/work_parser/chromedriver
```

### Step 5: Install Dependencies

Create a virtual environment and install the required dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate  # For Linux/Mac
.\.venv\Scripts\activate  # For Windows
pip install -r requirements.txt
```

### Step 6: Run the Project

Start the Telegram bot with the following command:
```bash
python tg_bot/bot_handler.py
```

## Notes

- Ensure that the `TG_BOT_TOKEN` variable contains your Telegram bot token.
- If the Chrome and ChromeDriver versions do not match, the project will not work correctly.

### Happy Parsing!
