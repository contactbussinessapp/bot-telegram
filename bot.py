import os
import telebot
import requests

TOKEN = os.environ.get('TOKEN')
# ID de tu Sheet verificado
SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

bot = telebot.TeleBot(TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🇦🇷 Argentina", callback_data="set_AR"))
    markup.add(telebot.types.InlineKeyboardButton("🇺🇾 Uruguay", callback_data="set_UY"))
    bot.reply_to(message, "✨ **Radar VIP** ✨\nSeleccioná tu país:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = {'pais': pais}
    bot.edit_message_text(f"✅ **País: {pais}**. ¿Qué buscás?", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.reply_to(message, "Poné /start")
        return

    query = message.text.lower().strip()
    pais_usuario = user_data[chat_id]['pais']
    
    try:
        # Traemos el Excel como texto puro
        r = requests.get(URL_SHEET)
        r.encoding = 'utf-8'
        lineas = r.text.splitlines()
        
        resultados_mios = ""
        
        # RASTREO MANUAL (Más seguro que el lector de CSV común)
        for i, linea in enumerate(lineas):
            if i == 0: continue # Saltamos el encabezado
            
            columnas = linea.split(',')
            if len(columnas) >= 3:
                nombre = columnas[0].strip().lower()
                pais_excel = columnas[1].strip().upper()
                link = columnas[2].strip()
                
                # Si la palabra está en el nombre y el país coincide
                if query in nombre and pais_excel == pais_usuario:
                    resultados_mios += f"🌟 **{columnas[0].strip()}**\n🔗 [Ver Producto]({link})\n\n"

        # Armamos la respuesta final
        if resultados_mios:
            res = f"🔍 **Resultados en Stock:**\n\n{resultados_mios}"
        else:
            res = f"🔍 No se encontró '{message.text}' en nuestro stock.\n\n"

        # Tiendas generales fijas abajo
        res += "📦 **Otras tiendas:**\n"
        res += f"🔹 [Amazon](https://www.amazon.com/s?k={query.replace(' ', '+')}) | [Mercado Libre](https://www.mercadolibre.com.ar/jm/search?as_word={query.replace(' ', '%20')})"
        
        bot.send_message(chat_id, res, parse_mode="Markdown", disable_web_page_preview=True)
    except:
        bot.send_message(chat_id, "Error de conexión.")

bot.polling()
