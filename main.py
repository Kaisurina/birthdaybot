import asyncio
import datetime
import logging
import os
import random

import aioschedule
from aiogram import Bot, Dispatcher, executor
from google.oauth2 import service_account
from googleapiclient import discovery
from pyunsplash import PyUnsplash

from config import SCOPES, SHEETNAME, SPREADSHEET_ID, TOKEN, UNSPLASH_API_KEY
from formaters import CustomFormatter, FileCustomFormatter

BASE_DIR = 'sent'
FILE_LOGS = 'logs.log'

# logging
FMT = '{"time": "%(asctime)s", "name": "[%(name)s]","levelname": "%(levelname)s", "message": "%(message)s"},'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create stdout handler for logging to the console (logs all five levels)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(CustomFormatter(FMT))

# Create file handler for logging to a file (logs all five levels)
file_handler = logging.FileHandler(FILE_LOGS)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(FileCustomFormatter(
    FMT))

# Add both handlers to the logger
logger.addHandler(stdout_handler)
logger.addHandler(file_handler)

# bot
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# global variables
creds = None
pu = PyUnsplash(api_key=UNSPLASH_API_KEY)


def get_credentials():
    return service_account.Credentials.from_service_account_file(
        'service.json', scopes=SCOPES)


def get_random_photo() -> str:
    try:
        photos = pu.photos(
            type_='random', collections='kLghIbYB9TE', count=1, featured=True)
        [photo] = photos.entries
        photo = photo.link_download
        return photo
    except:
        return "https://img.freepik.com/free-vector/detailed-birthday-lettering_52683-58875.jpg?w=2000"


async def parse_table():
    try:
        service = discovery.build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets().values()

        # Получаем данные
        with open("congratulations.txt", "r", encoding='utf-8') as f:
            answers = f.read().split("\n")
        users = sheet.get(spreadsheetId=SPREADSHEET_ID,
                          range=f'{SHEETNAME}!A3:A').execute().get('values', [])
        dates = sheet.get(spreadsheetId=SPREADSHEET_ID,
                          range=f'{SHEETNAME}!F3:F').execute().get('values', [])
        ids = sheet.get(spreadsheetId=SPREADSHEET_ID,
                        range=f'{SHEETNAME}!AE3:AE').execute().get('values', [])
        chat_ids = sheet.get(spreadsheetId=SPREADSHEET_ID,
                             range=f'{SHEETNAME}!AF3:AF').execute().get('values', [])

        await send_message(users, dates, ids, answers, chat_ids)
    except Exception as err:
        logger.error(err)


async def send_message(users, dates, ids, answers, chat_ids):
    for id, chat_id, user, date in zip(ids, chat_ids, users, dates):
        if chat_id and id:
            chat_id = chat_id[0]
            id = id[0]
            try:
                birhday_date = datetime.datetime.strptime(
                    date[0], '%d.%m.%Y')
            except:
                birhday_date = datetime.datetime.today() - datetime.timedelta(days=1)
            # Сегоднящняя дата
            today = datetime.datetime.today()
            # Сравниваем
            if birhday_date.day == today.day and birhday_date.month == today.month:
                if not os.path.exists(BASE_DIR):
                    os.makedirs(BASE_DIR)
                if os.path.exists(chat_id):
                    with open(os.path.join(BASE_DIR, chat_id), 'r', encoding='utf-8') as f:
                        sent = f.read().split("\n")
                else:
                    sent = []
                filtered_answers = list(
                    filter(lambda x: x not in sent, answers))
                # Получаем рандомное поздравление
                if filtered_answers:
                    text = random.choice(filtered_answers)
                    logger.info(f'Random choose, {text=}')
                    user = user[0]
                    # Получаем ИМЯ
                    user_name = user.split(' ')[1]
                    bot_msg = f"[{user_name}](tg://user?id={id}), {text}"
                    try:
                        photo = get_random_photo()
                        await bot.send_photo(chat_id, photo=photo, caption=bot_msg, parse_mode="Markdown")
                        logger.info(
                            f'Congratulation for {user=}, with {id=} in {chat_id=} successfully send')
                        with open(os.path.join(BASE_DIR, chat_id), 'a', encoding='utf-8') as f:
                            f.write(f'{text}\n')
                    except:
                        logger.error(
                            f'Failed to send message for {user=}, with {id=}, to {chat_id=}')


async def scheduler():
    aioschedule.every().day.at("07:00").do(parse_table)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    creds = get_credentials()
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
