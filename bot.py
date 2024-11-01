import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import BOT_KEY as API_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# Command: /weather
@dp.message(Command("weather"))
async def weather_start(message: types.Message):
    await message.answer("Введите город отправления:")

@dp.message(lambda message: message.text is not None)
async def receive_start_point(message: types.Message):
    start_point = message.text
    await message.answer("Отлично! Теперь введите город назначения:")

@dp.message(lambda message: message.text is not None)
async def receive_end_point(message: types.Message):
    end_point = message.text

    forecast_markup = InlineKeyboardMarkup(row_width=2)
    forecast_markup.add(
        InlineKeyboardButton(callback_data="forecast_3", text="3 дневный прогноз"),
        InlineKeyboardButton(callback_data="forecast_7", text="7 дневный прогноз")
    )

    await message.answer("Выберите прогнозный период:", reply_markup=forecast_markup)

@dp.callback_query(lambda c: c.data and c.data.startswith("forecast_"))
async def process_forecast(callback_query: types.CallbackQuery):
    pass
# не успел(



# Command: /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я Погодо-проверятель-4500. Чтобы начать, напишите /help")


@dp.message(Command("help"))
async def send_help(message: types.Message):
    help_text = (
        "/start - Приветствие\n"
        "/help - Список комманд\n"
        "/weather - Получить прогноз погоды"
    )
    await message.reply(help_text)



@dp.error
async def handle_errors(update, exception):
    logging.exception(f"Произошла ошибка: {exception}")
    return True

async def send_error_message(message, error_text):
    await message.reply(f"Ошибка: {error_text}")



async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
