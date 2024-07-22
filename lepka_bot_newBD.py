import telebot
from telebot import types
import sqlite3
from database import (init_db, add_order, get_user_by_chat_id, get_new_orders,
                      update_order_status)

API_TOKEN = 'API_TOKEN'
ADMIN_CHAT_ID = 'ADMIN_CHAT_ID'
bot = telebot.TeleBot(API_TOKEN)

user_data = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user = get_user_by_chat_id(chat_id)
    if str(chat_id) == ADMIN_CHAT_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        # notify_button = types.KeyboardButton("Уведомление")
        new_orders_button = types.KeyboardButton("Новые заказы")
        markup.add(new_orders_button)
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)
    elif user:
        user_data[chat_id] = {
            'name': user[1],
            'phone': user[2],
            'comment': user[3],
            'photos': []
        }
        bot.send_message(chat_id, "📸 Теперь прикрепите фото своего изделия. Когда закончите, нажмите Завершить.",
                         reply_markup=generate_finish_button())
        bot.register_next_step_handler(message, get_photos)
    else:
        user_data[chat_id] = {}
        bot.send_message(chat_id, "👋 Здравствуйте! Представьтесь, пожалуйста.")
        bot.register_next_step_handler(message, get_name)


def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text
    bot.send_message(chat_id, "📞 Пожалуйста, введите свой номер телефона.")
    bot.register_next_step_handler(message, get_phone)


def get_phone(message):
    chat_id = message.chat.id
    phone_number = message.text
    if not phone_number.isdigit() or len(phone_number) != 11:
        bot.send_message(chat_id, "❌ Неверный формат номера. Пожалуйста, введите номер телефона, состоящий из 11 цифр.")
        bot.register_next_step_handler(message, get_phone)
    else:
        user_data[chat_id]['phone'] = phone_number
        bot.send_message(chat_id, "📸 Теперь прикрепите фото своего изделия. Когда закончите, нажмите Завершить.",
                         reply_markup=generate_finish_button())
        bot.register_next_step_handler(message, get_photos)


def get_photos(message):
    chat_id = message.chat.id
    if message.content_type == 'photo':
        if 'photos' not in user_data[chat_id]:
            user_data[chat_id]['photos'] = []
        user_data[chat_id]['photos'].append(message.photo[-1].file_id)
        bot.send_message(chat_id,
                         "✅ Фото получено. Вы можете отправить ещё одно фото или нажмите Завершить, чтобы завершить.",
                         reply_markup=generate_finish_button())
        bot.register_next_step_handler(message, get_photos)
    elif message.text.lower() == "завершить":
        bot.send_message(chat_id, "✏️ Пожалуйста, оставьте комментарий к вашему изделию.")
        bot.register_next_step_handler(message, get_comment)
    else:
        bot.send_message(chat_id, "❗ Пожалуйста, отправьте фото.")
        bot.register_next_step_handler(message, get_photos)


def generate_finish_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    finish_button = types.KeyboardButton("Завершить")
    markup.add(finish_button)
    return markup


def get_comment(message):
    chat_id = message.chat.id
    comment = message.text.strip()
    if not comment:
        bot.send_message(chat_id,
                         "❗ Комментарий не может быть пустым. Пожалуйста, оставьте комментарий к вашему изделию.")
        bot.register_next_step_handler(message, get_comment)
    else:
        user_data[chat_id]['comment'] = comment
        add_order(user_data[chat_id]['name'], user_data[chat_id]['phone'], user_data[chat_id]['comment'], chat_id)
        send_data_to_admin(chat_id)


def send_data_to_admin(chat_id):
    if chat_id in user_data:
        info_message = (f"📝 Имя: {user_data[chat_id]['name']}\n"
                        f"📞 Телефон: {user_data[chat_id]['phone']}\n"
                        f"💬 Комментарий: {user_data[chat_id]['comment']}\n"
                        f"🆔 Chat ID: {chat_id}")
        if 'photos' in user_data[chat_id]:
            media = [types.InputMediaPhoto(photo_id) for photo_id in user_data[chat_id]['photos']]
            if media:
                media[0].caption = info_message
                bot.send_media_group(ADMIN_CHAT_ID, media)
            else:
                bot.send_message(ADMIN_CHAT_ID, info_message)
        else:
            bot.send_message(ADMIN_CHAT_ID, info_message)
        bot.send_message(chat_id,
                         "Спасибо❤️ Ваше изделие зарегистрировано! Когда изделие будет готово, вам придет оповещение в этот чат✨")
        bot.send_message(chat_id, "Нажми кнопку домой и процесс начнётся заново 🏠", reply_markup=generate_home_button())
        del user_data[chat_id]
    else:
        bot.send_message(chat_id, "Нет данных для отправки. Пожалуйста, начните с команды /start.")


def generate_home_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    home_button = types.KeyboardButton("🏠 Домой")
    markup.add(home_button)
    return markup


# @bot.message_handler(func=lambda message: message.text.lower() == "уведомление")
# def notify_user(message):
#     chat_id = message.chat.id
#     if str(chat_id) == ADMIN_CHAT_ID:
#         bot.send_message(chat_id, "Пожалуйста, введите ID пользователей для уведомления, разделённые запятыми:")
#         bot.register_next_step_handler(message, process_notify_ids)
#     else:
#         markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#         notify_button = types.KeyboardButton("Уведомление")
#         markup.add(notify_button)
#         bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)


# def process_notify_ids(message):
#     try:
#         ids_text = message.text
#         user_ids = [user_id.strip() for user_id in ids_text.split(',')]
#         for user_id in user_ids:
#             user_id = int(user_id)
#             bot.send_message(user_id,
#                              "📣Ваш заказ готов к выдаче! Чтобы выбрать дату, когда Вам удобно его забрать, напишите @my_namin.")
#             mark_as_notified(user_id)
#         bot.send_message(message.chat.id, "Уведомления отправлены.")
#     except ValueError:
#         bot.send_message(message.chat.id, "Неверный формат. Пожалуйста, введите правильные ID пользователей.")


@bot.message_handler(func=lambda message: message.text.lower() == "новые заказы")
def show_new_orders(message):
    chat_id = message.chat.id
    if str(chat_id) == ADMIN_CHAT_ID:
        orders = get_new_orders()
        if orders:
            for order in orders:
                order_message = (f"🆔 Order ID: {order[0]}\n"
                                 f"📝 Имя: {order[1]}\n"
                                 f"📞 Телефон: {order[2]}\n"
                                 f"💬 Комментарий: {order[3]}\n"
                                 f"🆔 Chat ID: {order[4]}")
                markup = types.InlineKeyboardMarkup()
                button = types.InlineKeyboardButton(text="Отправить уведомление", callback_data=f"notify_{order[0]}")
                markup.add(button)
                bot.send_message(chat_id, order_message, reply_markup=markup)
        else:
            bot.send_message(chat_id, "Нет новых заказов.")
    else:
        bot.send_message(chat_id, "У вас нет доступа к этой команде.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("notify_"))
def handle_notification(call):
    order_number = int(call.data.split("_")[1])
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('SELECT chat_id FROM orders WHERE order_number = ?', (order_number,))
    chat_id = c.fetchone()[0]
    conn.close()

    bot.send_message(chat_id,
                     "📣Ваш заказ готов к выдаче! Чтобы выбрать дату, когда Вам удобно его забрать, напишите @my_namin.")
    update_order_status(order_number, 'closed')  # Закрываем заказ
    bot.answer_callback_query(call.id, text="Уведомление отправлено.")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)


@bot.message_handler(func=lambda message: message.text.lower() == "🏠 домой")
def go_home(message):
    send_welcome(message)


if __name__ == '__main__':
    init_db()
    bot.polling(none_stop=True)
