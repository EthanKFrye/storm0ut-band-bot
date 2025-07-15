import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import random
import os
from config import BOT_TOKEN, MY_ID  # Убедитесь, что MY_ID тоже в config.py

# --- Вывод текущей директории ---
print("Текущая папка:", os.getcwd())

# --- Настройка Google Sheets ---
def get_data_from_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds ",
        "https://www.googleapis.com/auth/spreadsheets ",
        "https://www.googleapis.com/auth/drive.file "
    ]

    # Используем относительный путь к JSON-файлу
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials/elaboration-stormout-v-1-2.json", scope
    )
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key("1DUDry3rQJc6Lvmw43a7h92_Zje1moN7yJ75NRq9Vpho")
    sheet = spreadsheet.worksheet("Hello, World!")

    expected_headers = ["BAND MEMBER", "NICKNAME", "MEMBER ID", "GREETING", "FAN_GREETING"]

    records = sheet.get_all_records(expected_headers=expected_headers)

    group_members = {}
    fan_greetings = []

    for record in records:
        member_id = record['MEMBER ID']
        name = record['BAND MEMBER']
        nickname = record['NICKNAME']
        greeting = record.get('GREETING', '')
        fan_greeting = record.get('FAN_GREETING', '')

        # Для участников группы
        if member_id and greeting:
            if member_id not in group_members:
                group_members[member_id] = {
                    'name': name,
                    'nickname': nickname,
                    'greetings': []
                }
            group_members[member_id]['greetings'].append(greeting)

        # Для фанатов
        if fan_greeting:
            fan_greetings.append(fan_greeting)

    return {
        'group_members': group_members,
        'fan_greetings': fan_greetings
    }


# --- Логирование действий в таблицу (опционально) ---
def log_action(user_id, username, action):
    """Логирует действия пользователя только в Google Таблицу"""
    try:
        scope = [
            "https://spreadsheets.google.com/feeds ",
            "https://www.googleapis.com/auth/spreadsheets ",
            "https://www.googleapis.com/auth/drive.file "
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials/elaboration-stormout-v-1-2.json", scope
        )
        client = gspread.authorize(creds)

        spreadsheet = client.open_by_key("1DUDry3rQJc6Lvmw43a7h92_Zje1moN7yJ75NRq9Vpho")

        # Проверяем наличие листа Logs
        try:
            sheet = spreadsheet.worksheet("Logs")
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title="Logs", rows="1000", cols="20")
            sheet.append_row(["USER ID", "USERNAME", "ACTION", "TIMESTAMP"])

        # Записываем событие
        sheet.append_row([user_id, username, action, "=NOW()"])

    except Exception as e:
        # Не выводим ошибки в консоль, если не нужно
        pass

# --- Telegram handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Стартуем!", callback_data='start_pressed')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Нажми кнопку ниже:', reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username or str(user_id)

    data = context.bot_data.get('sheet_data', {})
    group_members = data.get('group_members', {})
    fan_greetings = data.get('fan_greetings', [])

    log_action(user_id, username, "button_pressed")

    if user_id in group_members:
        member = group_members[user_id]
        greeting = random.choice(member['greetings']).format(
            name=member['name'],
            nickname=member['nickname']
        )
        await query.message.edit_text(greeting)
    elif fan_greetings:
        greeting = random.choice(fan_greetings)
        await query.message.edit_text(greeting)
    else:
        await query.message.edit_text("Привет!")


# --- Загрузка данных из таблицы при старте бота ---
async def post_init(application):
    sheet_data = get_data_from_sheet()
    application.bot_data['sheet_data'] = sheet_data
    print("Данные загружены из таблицы")
    print(f"Число участников: {len(sheet_data['group_members'])}")
    print(f"Число фраз для фанатов: {len(sheet_data['fan_greetings'])}")


# --- Основной запуск ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен...")
    app.run_polling()


if __name__ == '__main__':
    main()
