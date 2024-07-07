import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

API_TOKEN = '7103008469:AAEd0QyoCEUEsWzCnFsvbHR7mt0orLxawoo'
API1_URL = 'http://142.93.110.148:7000/places/by-username'
REPORT_URL = 'http://142.93.110.148:7020/api/v1/download_report'
SENSORS_API_URL = 'http://142.93.110.148:6000/historical/data'
ADMINS_API_URL = 'http://142.93.110.148:7000/user/by-place-id'
MANAGE_SENSORS_API_URL = 'http://142.93.110.148:7000/get-sensors-by-place-id'
MANAGE_SENSOR_API_URL = 'http://142.93.110.148:7000/sensor/manage'


async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user if update.message else update.callback_query.from_user
    username = user.username

    if not username:
        await update.message.reply_text("Error: You need to create a username in Telegram settings.")
        return

    context.user_data['username'] = username

    response = requests.get(f"{API1_URL}?adminUsername={username}")

    if response.status_code != 200:
        await update.message.reply_text("No places found for your username. Please contact the administrator.")
        return

    places = response.json()

    keyboard = [
        [InlineKeyboardButton(f"Place ID: {place['placeID']}", callback_data=place['placeID']) for place in places],
        [InlineKeyboardButton("Back", callback_data='back_to_help')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Choose a place:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.edit_text("Choose a place:", reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'back_to_help':
        await help_command(update, context)
        return

    if query.data == 'download_report':
        await download_report(update, context)
        return

    if query.data == 'read_sensors':
        await read_sensors(update, context)
        return

    if query.data == 'fetch_admins':
        await fetch_admins(update, context)
        return

    if query.data == 'manage_sensors':
        await manage_sensors(update, context)
        return

    if query.data.startswith('read_'):
        await read_sensor_data(update, context)
        return

    if query.data.startswith('toggle_'):
        await toggle_sensor(update, context)
        return

    context.user_data['placeID'] = query.data
    actions_keyboard = [
        [InlineKeyboardButton("Download Report", callback_data='download_report')],
        [InlineKeyboardButton("Read Sensors Measurements", callback_data='read_sensors')],
        [InlineKeyboardButton("Fetch Admins", callback_data='fetch_admins')],
        [InlineKeyboardButton("Manage Sensors", callback_data='manage_sensors')],
        [InlineKeyboardButton("Back", callback_data='back_to_places')]
    ]
    reply_markup = InlineKeyboardMarkup(actions_keyboard)

    current_text = query.message.text
    new_text = f"Place {query.data} selected. Choose an action:"

    if current_text != new_text:
        await query.edit_message_text(text=new_text, reply_markup=reply_markup)


async def back_to_places(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    username = context.user_data['username']

    response = requests.get(f"{API1_URL}?adminUsername={username}")
    places = response.json()

    keyboard = [
        [InlineKeyboardButton(f"Place ID: {place['placeID']}", callback_data=place['placeID']) for place in places],
        [InlineKeyboardButton("Back", callback_data='back_to_help')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    current_text = query.message.text
    new_text = "Choose a place:"

    if current_text != new_text:
        await query.edit_message_text(text=new_text, reply_markup=reply_markup)


async def help_command(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user if update.message else update.callback_query.from_user
    username = user.username

    help_text = (
        "Welcome to the bot!\n\n"
        "Here are the available commands and options:\n\n"
        "/start - Start the bot and select a place\n"
        "/help - Show this help message\n"
        "In the main menu, you can select a place from the list.\n"
        "In the place selection menu, you can choose an action for the selected place."
    )

    if update.message:
        await update.message.reply_text(help_text)
    else:
        await update.callback_query.message.reply_text(help_text)


async def download_report(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("Generating the report, please wait...")

    response = requests.get(REPORT_URL, stream=True)

    if response.status_code == 200:
        file_name = "report.pdf"
        file = response.raw

        await query.message.reply_document(document=InputFile(file, filename=file_name))
    else:
        await query.message.reply_text("Failed to download the report.")


async def read_sensors(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    place_id = context.user_data.get('placeID')
    if not place_id:
        await query.message.reply_text("No place selected. Please select a place first.")
        return

    sensors_keyboard = [
        [InlineKeyboardButton("Read Temperature", callback_data=f'read_temperature_{place_id}')],
        [InlineKeyboardButton("Read Humidity", callback_data=f'read_humidity_{place_id}')],
        [InlineKeyboardButton("Read Smoke", callback_data=f'read_smoke_{place_id}')],
        [InlineKeyboardButton("Back", callback_data='back_to_places')]
    ]
    reply_markup = InlineKeyboardMarkup(sensors_keyboard)

    await query.message.edit_text("Choose a sensor to read:", reply_markup=reply_markup)


async def read_sensor_data(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    place_id = context.user_data.get('placeID')
    if not place_id:
        await query.message.reply_text("No place selected. Please select a place first.")
        return

    sensor_name = query.data.split('_')[1]

    params = {
        'sensor_name': sensor_name,
        'place_id': place_id,
        'limit': 1
    }

    response = requests.get(SENSORS_API_URL, params)

    if response.status_code == 200:
        data = response.json()
        if data:
            last_value = data[0]['value']
            await query.message.reply_text(f"The last {sensor_name} measurement: {last_value}")
        else:
            await query.message.reply_text(f"No data available for {sensor_name}.")
    else:
        await query.message.reply_text("Failed to retrieve sensor data.")


async def fetch_admins(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    place_id = context.user_data.get('placeID')
    if not place_id:
        await query.message.reply_text("No place selected. Please select a place first.")
        return

    params = {
        'placeID': place_id
    }

    response = requests.get(ADMINS_API_URL, params)

    if response.status_code == 200:
        admins = response.json()
        if admins:
            admins_list = "\n".join([admin for admin in admins])
            await query.message.reply_text(f"Admins for place ID {place_id}:\n\n{admins_list}")
        else:
            await query.message.reply_text(f"No admins found for place ID {place_id}.")
    else:
        await query.message.reply_text("Failed to retrieve admins.")


async def manage_sensors(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    place_id = context.user_data.get('placeID')
    if not place_id:
        await query.message.reply_text("No place selected. Please select a place first.")
        return

    params = {
        'placeID': place_id
    }

    response = requests.get(MANAGE_SENSORS_API_URL, params)

    if response.status_code == 200:
        sensor_states = response.json()
        sensors_keyboard = []
        for sensor, state in sensor_states.items():
            action_text = "Turn off" if state else "Turn on"
            sensors_keyboard.append([InlineKeyboardButton(f"{action_text} {sensor.capitalize()}",
                                                          callback_data=f'toggle_{sensor}_{place_id}')])

        sensors_keyboard.append([InlineKeyboardButton("Back", callback_data='back_to_places')])
        reply_markup = InlineKeyboardMarkup(sensors_keyboard)

        await query.message.edit_text("Manage Sensors:", reply_markup=reply_markup)
    else:
        await query.message.reply_text("Failed to retrieve sensor states.")


async def toggle_sensor(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    place_id = context.user_data.get('placeID')
    if not place_id:
        await query.message.reply_text("No place selected. Please select a place first.")
        return

    sensor_name, place_id = query.data.split('_')[1], query.data.split('_')[2]

    params = {
        'placeID': place_id
    }

    response = requests.get(MANAGE_SENSORS_API_URL, params)
    if response.status_code == 200:
        sensor_states = response.json()
        current_state = sensor_states.get(sensor_name)
        new_state = not current_state

        payload = {
            "placeID": int(place_id),
            "sensorName": sensor_name,
            "status": new_state
        }

        print(payload)

        response = requests.put(MANAGE_SENSOR_API_URL, json=payload)

        print(response)

        if response.status_code == 200:
            new_action_text = "Turn off" if new_state else "Turn on"
            await query.message.edit_text(f"Sensor '{sensor_name}' is now {'on' if new_state else 'off'}.")
        else:
            await query.message.reply_text("Failed to update the sensor state.")
    else:
        await query.message.reply_text("Failed to retrieve sensor states.")


def main() -> None:
    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CallbackQueryHandler(back_to_places, pattern='back_to_places'))
    application.add_handler(CallbackQueryHandler(help_command, pattern='back_to_help'))
    application.add_handler(CallbackQueryHandler(download_report, pattern='download_report'))
    application.add_handler(CallbackQueryHandler(read_sensors, pattern='read_sensors'))
    application.add_handler(
        CallbackQueryHandler(read_sensor_data, pattern='read_temperature_|read_humidity_|read_smoke_'))
    application.add_handler(CallbackQueryHandler(fetch_admins, pattern='fetch_admins'))
    application.add_handler(CallbackQueryHandler(manage_sensors, pattern='manage_sensors'))
    application.add_handler(CallbackQueryHandler(toggle_sensor, pattern='toggle_'))

    application.run_polling()


if __name__ == '__main__':
    main()
