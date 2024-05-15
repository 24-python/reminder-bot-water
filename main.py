import telebot
import datetime
import time
import threading
import random

bot = telebot.TeleBot('YOUR_TOKEN_HERE')
user_reminders = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Я бот-напоминальщик питья воды! Как тебя зовут?")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    name = message.text
    bot.send_message(message.chat.id, f"Приятно познакомиться, {name}! Сколько напоминаний в день ты хотел бы получать?")
    bot.register_next_step_handler(message, set_reminder_count, name)

def set_reminder_count(message, name):
    try:
        count = int(message.text)
        user_reminders[message.chat.id] = {'name': name, 'count': count, 'times': []}
        bot.send_message(message.chat.id, "Пожалуйста, укажите время напоминаний в формате ЧЧ:ММ, разделяя их запятой (например, 08:00, 14:00, 20:00).")
        bot.register_next_step_handler(message, set_reminder_times)
    except ValueError:
        bot.send_message(message.chat.id, "Введите пожалуйста числовое значение.")
        bot.register_next_step_handler(message, set_reminder_count, name)


def validate_time(time_str):
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False


def set_reminder_times(message):
    times_str = message.text.split(',')
    times = [time.strip() for time in times_str if validate_time(time.strip())]  # Only add valid times

    expected_count = user_reminders[message.chat.id]['count']
    if len(times) != expected_count:
        response_text = (f"Вы указали {len(times)} корректных временных меток, но запрашивали {expected_count}.\n"
                         "Введите '+ время' чтобы добавить время (например, '+ 23:00').\n"
                         "Введите '- время' чтобы удалить время (например, '- 14:00').\n"
                         "Введите 'ок', если хотите сохранить указанные напоминания.")
        bot.send_message(message.chat.id, response_text)
        bot.register_next_step_handler(message, adjust_reminder_times)
    else:
        user_reminders[message.chat.id]['times'] = times
        bot.send_message(message.chat.id, "Спасибо! Ваши напоминания установлены.")
        reminder_thread = threading.Thread(target=send_reminders, args=(message.chat.id,))
        reminder_thread.start()


def adjust_reminder_times(message):
    user_input = message.text.strip()
    chat_id = message.chat.id

    if user_input.lower() == 'ок':
        bot.send_message(chat_id, "Ваши напоминания сохранены!")
        reminder_thread = threading.Thread(target=send_reminders, args=(chat_id,))
        reminder_thread.start()
    else:
        action, _, time_value = user_input.partition(' ')
        time_value = time_value.strip()

        if action == '+' and validate_time(time_value) and time_value not in user_reminders[chat_id]['times']:
            user_reminders[chat_id]['times'].append(time_value)
        elif action == '-' and time_value in user_reminders[chat_id]['times']:
            user_reminders[chat_id]['times'].remove(time_value)

        current_times = ', '.join(user_reminders[chat_id]['times'])
        bot.send_message(chat_id,
                         f"Текущие времена напоминаний: {current_times}\nПродолжайте корректировать или напишите 'ок' для сохранения.")
        bot.register_next_step_handler(message, adjust_reminder_times)

@bot.message_handler(commands=['fact'])
def fact_message(message):
    facts = [
        "Вода — одно из самых распространённых веществ на Земле. Она покрывает около 71% поверхности планеты.",
        "Природная вода содержит много примесей. Они влияют на её цвет, вкус, запах и прозрачность.",
        "Вода играет важную роль в жизни человека. Без неё люди могут продержаться максимум пять дней."
    ]
    random_fact = random.choice(facts)
    bot.reply_to(message, f"Это факт! {random_fact}")

@bot.message_handler(commands=['help'])
def help_message(message):
    help_text = (
        "Команды бота:\n"
        "/start - начать напоминания о необходимости пить воду.\n"
        "/fact - получить интересный факт о воде."
    )
    bot.reply_to(message, help_text)

def send_reminders(chat_id):
    reminders = user_reminders[chat_id]['times']
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        if now in reminders:
            bot.send_message(chat_id, "Время пить воду!")
            time.sleep(61)  # Pause to avoid multiple messages
        time.sleep(1)

bot.polling(none_stop=True)