from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GSHEET_JSON_KEYFILE_PATH = os.getenv("GSHEET_JSON_KEYFILE_PATH")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
MY_ID = 7163743546
