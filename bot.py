import os
import cv2
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import DatabaseManager, create_collage
from config import *
bot = TeleBot(API_TOKEN)
manager = DatabaseManager('prizes.db')

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    if user_id in [user[0] for user in manager.get_users()]:
        bot.reply_to(message, "Ты уже зарегистрирован!")
    else:
        manager.add_user(user_id, message.from_user.username)
        bot.reply_to(message, """Привет! Добро пожаловать! 
Ты успешно зарегистрирован!
Каждый час тебе будут приходить новые картинки и у тебя будет шанс их получить!
Для этого нужно быстрее всех нажать на кнопку 'Получить!'.
Только три первых пользователя получат картинку!""")
        

def gen_markup(prize_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Получить!", callback_data=prize_id))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    prize_id = call.data
    user_id = call.message.chat.id
    if manager.get_winners_count(prize_id) < 3:
        res = manager.add_winner(user_id, prize_id)
        if res:
            img = manager.get_prize_img(prize_id)
            with open(f'img/{img}', 'rb') as photo:
                bot.send_photo(user_id, photo, caption="Поздравляем! Ты получил картинку!")
        else:
            bot.send_message(user_id, 'Ты уже получил картинку!')
    else:
        bot.send_message(user_id, "К сожалению, ты не успел получить картинку! Попробуй в следующий раз!")


@bot.message_handler(commands=['my_score'])
def get_my_score(message):
    user_id = message.chat.id
    images_info = manager.get_winners_img(user_id)
    if not images_info:
        bot.send_message(user_id, "У вас нет призов.")
        return

    prizes = [x[0] for x in images_info]
    image_paths = [f'img/{img}' for img in prizes if os.path.exists(f'img/{img}')] + \
                  [f'hidden_img/{img}' for img in prizes if os.path.exists(f'hidden_img/{img}')]

    collage = create_collage(image_paths)
    if collage is None:
        bot.send_message(user_id, "Не удалось создать коллаж. Убедитесь, что у вас есть призы.")
        return

    collage_path = 'collage.png'
    cv2.imwrite(collage_path, collage)
    with open(collage_path, 'rb') as photo:
        bot.send_photo(user_id, photo, caption="Вот ваш коллаж с призами!")

@bot.message_handler(commands=['rating'])
def handle_rating(message):
    res = manager.get_rating()
    res = [f'| @{x[0]:<11} | {x[1]:<11}|\n{"_"*26}' for x in res]
    res = '\n'.join(res)
    res = f'|USER_NAME    |COUNT_PRIZE|\n{"_"*26}\n' + res
    bot.send_message(message.chat.id, res)

if __name__ == '__main__':
    bot.polling(none_stop=True)