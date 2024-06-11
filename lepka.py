import telebot
from telebot import types

# Вставьте ваш токен ниже
API_TOKEN = 'API_TOKEN/'
ADMIN_CHAT_ID = 'ADMIN_CHAT_ID'

bot = telebot.TeleBot(API_TOKEN)

user_data = {}  # Хранилище для данных пользователя

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    # Если это администратор, показываем кнопку "Уведомление"
    if str(chat_id) == ADMIN_CHAT_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        notify_button = types.KeyboardButton("Уведомление")
        markup.add(notify_button)
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)
        return
    user_data[chat_id] = {}  # Создаем пустой словарь для данных пользователя
    bot.send_message(chat_id, "👋 Здравствуйте! Представьтесь, пожалуйста.")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text  # Сохраняем имя пользователя
    bot.send_message(chat_id, "📞 Пожалуйста, введите свой номер телефона.")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    chat_id = message.chat.id
    phone_number = message.text

    # Проверяем валидность номера телефона
    if not phone_number.isdigit() or len(phone_number) != 11:
        bot.send_message(chat_id, "❌ Неверный формат номера. Пожалуйста, введите номер телефона, состоящий из 11 цифр.")
        bot.register_next_step_handler(message, get_phone)
        return

    user_data[chat_id]['phone'] = phone_number  # Сохраняем номер телефона пользователя
    bot.send_message(chat_id, "📸Теперь прикрепите фото своего изделия. Когда закончите, нажмите Завершить.",
                     reply_markup=generate_finish_button())
    bot.register_next_step_handler(message, get_photos)

def get_photos(message):
    chat_id = message.chat.id
    if message.content_type == 'photo':
        if 'photos' not in user_data[chat_id]:
            user_data[chat_id]['photos'] = []  # Инициализируем список фотографий, если его нет
        user_data[chat_id]['photos'].append(message.photo[-1].file_id)  # Сохраняем файл ID фото
        bot.send_message(chat_id, "✅ Фото получено. Вы можете отправить ещё одно фото или нажмите Завершить, чтобы завершить.",
                         reply_markup=generate_finish_button())  # Добавляем кнопку "Завершить"
        bot.register_next_step_handler(message, get_photos)
    elif message.text.lower() == "завершить":
        send_data_to_admin(chat_id)
    else:
        bot.send_message(chat_id, "❗ Пожалуйста, отправьте фото.")
        bot.register_next_step_handler(message, get_photos)

def generate_finish_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    finish_button = types.KeyboardButton("Завершить")
    markup.add(finish_button)
    return markup

def send_data_to_admin(chat_id):
    if chat_id in user_data:
        # Отправляем информацию администратору
        info_message = (f"📝 Имя: {user_data[chat_id]['name']}\n"
                        f"📞 Телефон: {user_data[chat_id]['phone']}\n"
                        f"🆔 Chat ID: {chat_id}")

        # Отправляем все фотографии в одном сообщении
        if 'photos' in user_data[chat_id]:
            media = [types.InputMediaPhoto(photo_id) for photo_id in user_data[chat_id]['photos']]
            if media:
                media[0].caption = info_message  # Добавляем информацию о пользователе в подпись первой фотографии
                bot.send_media_group(ADMIN_CHAT_ID, media)
            else:
                bot.send_message(ADMIN_CHAT_ID, info_message)
        else:
            bot.send_message(ADMIN_CHAT_ID, info_message)

        bot.send_message(chat_id, "Спасибо❤️ Ваше изделие зарегистрировано!Когда изделие будет готово вам придет оповещение в этот чат✨")
        bot.send_message(chat_id, "Нажми кнопку домой и процесс начнётся заново 🏠", reply_markup=generate_home_button())  # Предлагаем нажать кнопку "Домой"
        del user_data[chat_id]  # Очищаем данные пользователя после отправки
    else:
        bot.send_message(chat_id, "Нет данных для отправки. Пожалуйста, начните с команды /start.")

def generate_home_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    home_button = types.KeyboardButton("🏠 Домой")
    markup.add(home_button)
    return markup

# Обработчик для получения уведомлений от администратора
@bot.message_handler(func=lambda message: message.text.lower() == "уведомление")
def notify_user(message):
    chat_id = message.chat.id
    if str(chat_id) == ADMIN_CHAT_ID:
        bot.send_message(chat_id, "Пожалуйста, введите ID пользователя для уведомления:")
        bot.register_next_step_handler(message, process_notify_id)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        notify_button = types.KeyboardButton("Уведомление")
        markup.add(notify_button)
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

def process_notify_id(message):
    try:
        chat_id = int(message.text)
        notification = "Чтобы выбрать дату, когда Вам удобно его забрать, напишите @my_namin"
        bot.send_message(chat_id, f"Ваше изделие готово. {notification}")
        bot.send_message(message.chat.id, "Уведомление успешно отправлено.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# Обработчик для кнопки "Домой"
@bot.message_handler(func=lambda message: message.text.lower() == "🏠 домой")
def go_home(message):
    send_welcome(message)  # Перенаправляем на начало процесса

# Запуск бота
bot.polling(none_stop=True)