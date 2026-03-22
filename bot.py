import os
import telebot
import requests
import csv

# Lee el Token de la configuración de Render (Seguro)
TOKEN = os.environ.get('TOKEN')

# Tu ID de Google Sheets nuevo
SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

bot = telebot.TeleBot(TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🇦🇷 Argentina", callback_data="set_AR"))
    bot.reply_to(message, "✅ **Radar Activo**. Seleccioná tu país para buscar:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = {'pais': pais}
    bot.edit_message_text(f"📍 **Configurado para {pais}**. Escribí qué buscás (ej: caña o kunnan).", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.reply_to(message, "Primero poné /start para elegir país.")
        return

    query = message.text.lower()
    pais = user_data[chat_id]['pais']
    
    try:
        response = requests.get(URL_SHEET)
        decoded_content = response.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
        
        respuesta = f"🔍 **Resultados para: {query}**\n\n"
        encontrado = False

        # Busca en tu Excel
        for row in my_list[1:]:
            if len(row) >= 4:
                nombre_excel = str(row[0]).lower()
                pais_excel = str(row[1]).upper()
                if query in nombre_excel and pais_excel == pais:
                    respuesta += f"🌟 **RECOMENDADO:** {row[0]}\n🔗 [Ver Producto]({row[2]})\n\n"
                    encontrado = True

        # Agrega links generales siempre
        respuesta += "📦 **Otras tiendas:**\n"
        respuesta += f"🔹 [Amazon](https://www.amazon.com/s?k={query.replace(' ', '+')})\n"
        respuesta += f"🔹 [Mercado Libre](https://lista.mercadolibre.com.ar/{query.replace(' ', '-')})\n"
        
        bot.send_message(chat_id, respuesta, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        bot.send_message(chat_id, "Error al leer la base de datos. Intentá más tarde.")
        print(f"Error: {e}")

bot.polling()
