import os
import telebot
import requests
import csv
import random
from io import StringIO

# === CONFIGURACIÓN ===
TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

# Tus IDs de Afiliado (Reemplaza estos valores con los tuyos)
AMAZON_TAG = "tu_codigo_amazon-20"
# Nota: AliExpress requiere generar links desde su portal, pero esta URL hace la búsqueda directa.
# Si tienes un script de deep-linking de AliExpress, puedes envolver esta URL.

bot = telebot.TeleBot(TOKEN)
user_data = {}

# ------------------------
# 1. BIENVENIDA Y PAÍS
# ------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # Botón para el mercado validado
    markup.add(telebot.types.InlineKeyboardButton("🇦🇷 Argentina", callback_data="set_AR"))
    # Botón para la expansión futura
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
    
    # Si elige otro país, lo dejamos en espera
    if pais_code == "OTHER":
        bot.edit_message_text(
            "🌎 *¡Próximamente!*\n\nEstamos construyendo nuestra red para llegar a tu país paso a paso. ¡Te avisaremos muy pronto cuando estemos operativos allí!",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        return

    # Si elige Argentina, guardamos y avanzamos
    user_data[call.message.chat.id] = {'pais': 'AR'}
    
    bot.edit_message_text(
        "✅ *País configurado: Argentina*\n\n¿Qué producto estás buscando hoy? Escríbelo aquí abajo:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# ------------------------
# 3. EL BUSCADOR MASTER
# ------------------------
@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id

    # Verificar si el usuario ya eligió país
    if chat_id not in user_data or user_data[chat_id]['pais'] != 'AR':
        bot.reply_to(message, "Por favor, usa /start para seleccionar tu país primero.")
        return

    query = message.text.strip().lower()
    query_url_amz = query.replace(' ', '+')
    query_url_ml = query.replace(' ', '-')

    # Mensaje temporal de espera (Mejora la UX)
    msg_buscando = bot.send_message(chat_id, "🔍 *Buscando los mejores precios para ti...*", parse_mode="Markdown")

    try:
        # Consultar el Google Sheet
        r = requests.get(URL_SHEET)
        r.encoding = 'utf-8'
        csv_reader = list(csv.reader(StringIO(r.text)))

        resultados_directos = ""
        mis_productos_vip = []

        # Procesar filas
        for i, columnas in enumerate(csv_reader):
            if i == 0 or len(columnas) < 3:
                continue  # Saltar encabezado o filas vacías

            nombre = columnas[0].strip()
            pais_excel = columnas[1].strip().upper()
            link = columnas[2].strip()

            if pais_excel == "AR":
                # Guardar TODOS los productos de AR para la sección VIP
                mis_productos_vip.append((nombre, link))
                
                # Si coincide con la búsqueda del usuario
                if query in nombre.lower():
                    resultados_directos += f"✔️ *{nombre}*\n🔗 [Comprar ahora]({link})\n\n"

        # --- CONSTRUIR EL MENSAJE FINAL ---
        res = f"🎯 *Resultados para:* _{message.text}_\n\n"

        # 1. Coincidencias exactas en tu stock
        if resultados_directos:
            res += f"📦 *¡Lo tenemos en stock!*\n{resultados_directos}"

        # 2. Enlaces de Afiliados (Búsqueda global)
        res += "🌐 *Buscar en tiendas globales (Mejores precios):*\n"
        res += f"🛒 [Ver opciones en Amazon](https://www.amazon.com/s?k={query_url_amz}&tag={AMAZON_TAG})\n"
        res += f"🛍️ [Ver opciones en AliExpress](https://www.aliexpress.com/wholesale?SearchText={query_url_amz})\n"
        res += f"🤝 [Ver opciones en Mercado Libre](https://listado.mercadolibre.com.ar/{query_url_ml})\n\n"

        # 3. La sección VIP (Upsell automático)
        res += "🔥 *Oportunidades VIP del día:*\n"
        if mis_productos_vip:
            # Selecciona hasta 3 productos aleatorios para no saturar el chat
            destacados = random.sample(mis_productos_vip, min(3, len(mis_productos_vip)))
            for p_nombre, p_link in destacados:
                res += f"💎 [{p_nombre}]({p_link})\n"
        else:
            res += "Estamos actualizando nuestro catálogo VIP.\n"

        # Reemplazar el mensaje de "Buscando..." por los resultados reales
        bot.edit_message_text(res, chat_id, msg_buscando.message_id, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        print("ERROR:", e)
        bot.edit_message_text("⚠️ Hubo un error al consultar nuestras bases de datos. Por favor, intenta nuevamente en unos segundos.", chat_id, msg_buscando.message_id)

# ------------------------
# RUN
# ------------------------
print("🔥 RADAR VIP ESTÁ EN LÍNEA...")

bot.remove_webhook()
bot.polling(none_stop=True)
