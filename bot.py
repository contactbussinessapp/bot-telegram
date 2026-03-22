import os
import telebot
import requests
import csv

# Usa el TOKEN que ya tenés cargado en la pestaña Environment de Render
TOKEN = os.environ.get('TOKEN')

# Tu ID de Google Sheets (Ya está configurado con tu link)
SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

bot = telebot.TeleBot(TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # Por ahora solo Argentina, como quedamos
    markup.add(telebot.types.InlineKeyboardButton("🇦🇷 Argentina", callback_data="set_AR"))
    bot.reply_to(message, "✅ **Radar Activo**. Seleccioná tu país para empezar:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = {'pais': pais}
    bot.edit_message_text(f"📍 **Configurado para {pais}**. Escribí qué producto buscás:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.reply_to(message, "Por favor, poné /start primero para elegir tu país.")
        return

    query = message.text.lower()
    pais = user_data[chat_id]['pais']
    
    try:
        # 1. Busca en tu Google Sheets
        response = requests.get(URL_SHEET)
        decoded_content = response.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
        
        respuesta = f"🔍 **Resultados para: {message.text}**\n\n"
        encontrado = False

        for row in my_list[1:]:
            if len(row) >= 4:
                nombre_excel = str(row[0]).lower()
                pais_excel = str(row[1]).upper()
                # Verifica si la búsqueda está dentro del nombre del producto
                if query in nombre_excel and pais_excel == pais:
                    respuesta += f"🌟 **RECOMENDADO:** {row[0]}\n🔗 [Ver Producto en ML]({row[2]})\n\n"
                    encontrado = True

        # 2. Links de tiendas generales (Corregidos para que funcionen siempre)
        respuesta += "📦 **Otras tiendas internacionales:**\n"
        
        # Link Amazon
        link_amazon = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
        # Link Mercado Libre Argentina
        link_ml = f"https://www.mercadolibre.com.ar/jm/search?as_word={query.replace(' ', '%20')}"
        # Link AliExpress
        link_ali = f"https://es.aliexpress.com/wholesale?SearchText={query.replace(' ', '+')}"

        respuesta += f"🔹 [Buscar en Amazon]({link_amazon})\n"
        respuesta += f"🔹 [Buscar en Mercado Libre]({link_ml})\n"
        respuesta += f"🔹 [Buscar en AliExpress]({link_ali})\n"
        
        bot.send_message(chat_id, respuesta, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        bot.send_message(chat_id, "Hubo un error al conectar con la base de datos. Intentá de nuevo.")
        print(f"Error: {e}")

bot.polling()
