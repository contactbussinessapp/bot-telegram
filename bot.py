import os
import telebot
import requests
import csv

TOKEN = os.environ.get('TOKEN')
# Este link es más directo para que Google no lo bloquee
SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0'

bot = telebot.TeleBot(TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # Volvemos a poner los botones de país que te gustaban
    markup.add(telebot.types.InlineKeyboardButton("🇦🇷 Argentina", callback_data="set_AR"))
    markup.add(telebot.types.InlineKeyboardButton("🇺🇾 Uruguay", callback_data="set_UY"))
    bot.reply_to(message, "✨ **Radar VIP Global** ✨\nSeleccioná tu ubicación para activar las ofertas personalizadas:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = {'pais': pais}
    bot.edit_message_text(f"✅ **Configurado para {pais}**. Escribí qué buscás (ej: auto, caña, música):", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.reply_to(message, "⚠️ Por favor, seleccioná tu país con /start")
        return

    query = message.text.lower().strip()
    pais = user_data[chat_id]['pais']
    
    try:
        # Forzamos la descarga del Excel cada vez para que no se guarde info vieja
        response = requests.get(URL_SHEET)
        decoded_content = response.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
        
        respuesta = f"🔍 **Resultados para: {message.text}**\n\n"
        encontrado_en_excel = False

        # 1. BUSQUEDA EN TU STOCK (Google Sheets)
        bloque_recomendados = ""
        for row in my_list[1:]:
            if len(row) >= 3:
                nombre_prod = str(row[0]).lower()
                pais_prod = str(row[1]).upper().strip()
                link_prod = str(row[2])
                
                # Si la palabra está en el nombre y el país coincide
                if query in nombre_prod and pais_prod == pais:
                    bloque_recomendados += f"🌟 **RECOMENDADO:** {row[0]}\n🔗 [Ver ahora]({link_prod})\n\n"
                    encontrado_en_excel = True

        if encontrado_en_excel:
            respuesta += bloque_recomendados + "---\n"

        # 2. TIENDAS GENERALES
        respuesta += "📦 **Otras tiendas internacionales:**\n"
        link_amz = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
        link_ml = f"https://www.mercadolibre.com.ar/jm/search?as_word={query.replace(' ', '%20')}"
        link_ali = f"https://es.aliexpress.com/wholesale?SearchText={query.replace(' ', '+')}"

        respuesta += f"🔹 [Amazon]({link_amz}) | [Mercado Libre]({link_ml}) | [AliExpress]({link_ali})\n"
        
        bot.send_message(chat_id, respuesta, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        bot.send_message(chat_id, "❌ Error al conectar con el inventario.")

bot.polling()
