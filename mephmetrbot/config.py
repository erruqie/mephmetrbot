import os
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
DATABASE_URL = os.environ.get('DATABASE_URL')
ADMINS = os.environ.get('ADMINS').split(',')

bot = Bot(token=BOT_TOKEN)