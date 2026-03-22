import os
import telebot
import requests
import csv

# 1. LLAVE DE SEGURIDAD
TOKEN = os.environ.get('TOKEN')

# 2. CONEXIÓN AL EXCEL (Asegurate que el Excel esté "Publicado en la web")
SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

bot = telebot.TeleBot(TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🇦🇷 Argentina", callback_data="set_AR"))
    markup.add(telebot.types.InlineKeyboardButton("🇺🇾 Uruguay", callback_data="set_UY"))
    bot.reply_to(message, "✨ **Radar VIP** ✨\nSeleccioná tu país para ver mi stock:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = {'pais': pais}
    bot.edit_message_text(f"✅ **Configurado para {pais}**. ¿Qué buscás?", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.reply_to(message, "⚠️ Poné /start primero.")
        return

    query = message.text.lower().strip()
    pais_usuario = user_data[chat_id]['pais'].upper().strip()
    
    try:
        # Descarga el CSV
        response = requests.get(URL_SHEET)
        decoded_content = response.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        rows = list(cr)
        
        respuesta = f"🔍 **Resultados para: {message.text}**\n\n"
        bloque_mio = ""
        encontrado = False

        for row in rows[1:]:
            if len(row) >= 3:
                # LIMPIEZA TOTAL (Para que no falle por una mayúscula o un espacio)
                nombre_excel = str(row[0]).lower().strip()
                pais_excel = str(row[1]).upper().strip()
                link_excel = str(row[2]).strip()
                
                # BUSQUEDA: ¿La palabra está en el nombre? ¿El país coincide?
                if query in nombre_excel and pais_excel == pais_usuario:
                    bloque_mio += f"🌟 **DISPONIBLE:** {row[0]}\n🔗 [Link Directo]({link_excel})\n\n"
                    encontrado = True

        if encontrado:
            respuesta += "🔥 **PRODUCTOS EN STOCK** 🔥\n" + bloque_mio + "---\n"
        else:
            respuesta += "❌ No tengo ese producto en stock (chequeá que en el Excel diga 'AR' en la columna B).\n\n"

        # TIENDAS GENERALES
        link_amz = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
        link_ml = f"https://www.mercadolibre.com.ar/jm/search?as_word={query.replace(' ', '%20')}"
        respuesta += f"📦 **Otras opciones:**\n🔹 [Amazon]({link_amz}) | [Mercado Libre]({link_ml})\n"
        
        bot.send_message(chat_id, respuesta, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        bot.send_message(chat_id, "Error al conectar con el inventario.")

bot.polling()
