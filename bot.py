import os
import telebot
import requests
import csv
import random
import urllib.parse
from io import StringIO

# === CONFIGURACIÓN ===
TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

# ID de Afiliado de Amazon (Reemplaza este cuando tengas el tuyo)
AMAZON_TAG = "tu_codigo_amazon-20"

bot = telebot.TeleBot(TOKEN)
user_data = {}

# ------------------------
# 1. BIENVENIDA Y PAÍS
# ------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🇦🇷 Argentina", callback_data="set_AR"))
    markup.add(telebot.types.InlineKeyboardButton("🌎 Otros países", callback_data="set_OTHER"))
    
    bot.reply_to(
        message,
        "✨ *Radar VIP* ✨\n¡El buscador definitivo de oportunidades! 🚀\n\n¿Desde qué país te comunicas?",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ------------------------
# 2. GESTIÓN DEL PAÍS
# ------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais_code = call.data.split("_")[1]
    
    if pais_code == "OTHER":
        bot.edit_message_text(
            "🌎 *¡Próximamente!*\n\nEstamos construyendo nuestra red para llegar a tu país paso a paso. ¡Te avisaremos muy pronto cuando estemos operativos allí!",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        return

    user_data[call.message.chat.id] = {'pais': 'AR'}
    
    bot.edit_message_text(
        "✅ *País configurado: Argentina*\n\n¿Qué producto estás buscando hoy? Escríbelo aquí abajo:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# ------------------------
# 3. EL BUSCADOR MASTER Y MONETIZACIÓN
# ------------------------
@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id

    if chat_id not in user_data or user_data[chat_id]['pais'] != 'AR':
        bot.reply_to(message, "Por favor, usa /start para seleccionar tu país primero.")
        return

    query = message.text.strip().lower()
    query_url_amz = query.replace(' ', '+')
    query_url_ml = query.replace(' ', '-')

    msg_buscando = bot.send_message(chat_id, "🔍 *Buscando los mejores precios para ti...*", parse_mode="Markdown")

    try:
        r = requests.get(URL_SHEET)
        r.encoding = 'utf-8'
        csv_reader = list(csv.reader(StringIO(r.text)))

        resultados_directos = ""
        mis_productos_vip = []

        for i, columnas in enumerate(csv_reader):
            if i == 0 or len(columnas) < 3:
                continue 

            nombre = columnas[0].strip()
            pais_excel = columnas[1].strip().upper()
            link = columnas[2].strip()

            if pais_excel == "AR":
                mis_productos_vip.append((nombre, link))
                if query in nombre.lower():
                    resultados_directos += f"✔️ *{nombre}*\n🔗 [Comprar ahora]({link})\n\n"

        res = f"🎯 *Resultados para:* _{message.text}_\n\n"

        if resultados_directos:
            res += f"📦 *¡Lo tenemos en stock!*\n{resultados_directos}"

        # === LÓGICA DE MONETIZACIÓN ALIEXPRESS ===
        busqueda_base = f"https://www.aliexpress.com/wholesale?SearchText={query_url_amz}"
        busqueda_codificada = urllib.parse.quote(busqueda_base, safe='')
        # Aquí inyectamos tu código _c3MIbod9
        aliexpress_deep_link = f"https://s.click.aliexpress.com/deep_link.htm?aff_short_key=_c3MIbod9&dl_target_url={busqueda_codificada}"

        res += "🌐 *Buscar en tiendas globales (Mejores precios):*\n"
        res += f"🛒 [Ver opciones en Amazon](https://www.amazon.com/s?k={query_url_amz}&tag={AMAZON_TAG})\n"
        res += f"🛍️ [Ver opciones en AliExpress]({aliexpress_deep_link})\n"
        res += f"🤝 [Ver opciones en Mercado Libre](https://listado.mercadolibre.com.ar/{query_url_ml})\n\n"

        res += "🔥 *Oportunidades VIP del día:*\n"
        if mis_productos_vip:
            destacados = random.sample(mis_productos_vip, min(3, len(mis_productos_vip)))
            for p_nombre, p_link in destacados:
                res += f"💎 [{p_nombre}]({p_link})\n"
        else:
            res += "Estamos actualizando nuestro catálogo VIP.\n"

        bot.edit_message_text(res, chat_id, msg_buscando.message_id, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        print("ERROR:", e)
        bot.edit_message_text("⚠️ Hubo un error al consultar nuestras bases de datos. Por favor, intenta nuevamente en unos segundos.", chat_id, msg_buscando.message_id)

# ------------------------
# RUN
# ------------------------
print("🔥 RADAR VIP ESTÁ EN LÍNEA Y MONETIZANDO...")

bot.remove_webhook()
bot.polling(none_stop=True)
