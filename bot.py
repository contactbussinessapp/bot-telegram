import os
import telebot
import requests
import csv

TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
# Usamos el formato export directo para evitar bloqueos de Google
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

bot = telebot.TeleBot(TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🇦🇷 Argentina", callback_data="set_AR"))
    markup.add(telebot.types.InlineKeyboardButton("🇺🇾 Uruguay", callback_data="set_UY"))
    bot.reply_to(message, "✨ **Radar VIP** ✨\nSeleccioná tu país para ver mis productos y ofertas:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = {'pais': pais}
    bot.edit_message_text(f"✅ **Configurado para {pais}**. ¿Qué producto buscás de mi stock?", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.reply_to(message, "⚠️ Por favor, seleccioná tu país con /start")
        return

    query = message.text.lower().strip()
    pais_usuario = user_data[chat_id]['pais'].upper().strip()
    
    try:
        response = requests.get(URL_SHEET)
        decoded_content = response.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        rows = list(cr)
        
        respuesta = f"🔍 **Resultados para: {message.text}**\n\n"
        encontrado_mio = False
        bloque_mio = ""

        # Revisamos fila por fila del Excel
        for row in rows[1:]: # Salteamos el encabezado
            if len(row) >= 3:
                # Limpiamos los datos del Excel para que no fallen por un espacio
                nombre_prod = str(row[0]).lower().strip()
                pais_prod = str(row[1]).upper().strip()
                link_prod = str(row[2]).strip()
                
                # LA CLAVE: Si la palabra que pusiste está DENTRO del nombre y el país es igual
                if query in nombre_prod and pais_prod == pais_usuario:
                    bloque_mio += f"🌟 **MI PRODUCTO:** {row[0]}\n🔗 [Link Directo]({link_prod})\n\n"
                    encontrado_mio = True

        if encontrado_mio:
            respuesta += "🔥 **RECOMENDADOS DEL SELLO** 🔥\n" + bloque_mio + "---\n"
        else:
            respuesta += "❌ No encontré ese producto exacto en mi stock actual.\n\n"

        # TIENDAS GENERALES (Para que no se quede vacío)
        respuesta += "📦 **Búsqueda en tiendas generales:**\n"
        link_amz = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
        link_ml = f"https://www.mercadolibre.com.ar/jm/search?as_word={query.replace(' ', '%20')}"
        
        respuesta += f"🔹 [Amazon]({link_amz}) | [Mercado Libre]({link_ml})\n"
        
        bot.send_message(chat_id, respuesta, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        bot.send_message(chat_id, "Hubo un problema al leer el inventario.")

bot.polling()
