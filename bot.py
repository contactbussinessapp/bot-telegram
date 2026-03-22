import os
import telebot
import requests
import csv
from io import StringIO

TOKEN = os.environ.get('TOKEN')

SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

bot = telebot.TeleBot(TOKEN)
user_data = {}

# ------------------------
# START
# ------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🇦🇷 Argentina", callback_data="set_AR"))
    markup.add(telebot.types.InlineKeyboardButton("🇺🇾 Uruguay", callback_data="set_UY"))
    
    bot.reply_to(
        message,
        "✨ *Radar VIP* ✨\nSeleccioná tu país:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ------------------------
# SET COUNTRY
# ------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = {'pais': pais}
    
    bot.edit_message_text(
        f"✅ *País: {pais}*\n\nAhora escribí lo que buscás:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# ------------------------
# SEARCH
# ------------------------
@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id

    if chat_id not in user_data:
        bot.reply_to(message, "Poné /start")
        return

    query = message.text.strip().lower()
    pais_usuario = user_data[chat_id]['pais']

    try:
        r = requests.get(URL_SHEET)
        r.encoding = 'utf-8'

        csv_reader = csv.reader(StringIO(r.text))

        resultados = ""

        for i, columnas in enumerate(csv_reader):
            if i == 0:
                continue  # encabezado

            if len(columnas) < 3:
                continue

            nombre = columnas[0].strip().lower()
            pais_excel = columnas[1].strip().upper()
            link = columnas[2].strip()

            if query in nombre and pais_excel == pais_usuario:
                resultados += f"🌟 *{columnas[0].strip()}*\n🔗 [Ver Producto]({link})\n\n"

        if resultados:
            res = f"🔍 *Resultados en Stock:*\n\n{resultados}"
        else:
            res = f"🔍 No se encontró *{message.text}* en stock.\n\n"

        res += "📦 *Otras tiendas:*\n"
        res += f"🔹 [Amazon](https://www.amazon.com/s?k={query.replace(' ', '+')})\n"
        res += f"🔹 [Mercado Libre](https://www.mercadolibre.com.ar/jm/search?as_word={query.replace(' ', '%20')})"

        bot.send_message(chat_id, res, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        print("ERROR:", e)
        bot.send_message(chat_id, "⚠️ Error al leer productos.")

# ------------------------
# RUN
# ------------------------
print("🔥 BOT FUNCIONANDO...")

bot.remove_webhook()   # 🔥 FIX ERROR 409
bot.polling(none_stop=True)
