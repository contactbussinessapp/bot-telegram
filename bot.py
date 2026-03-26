import logging, random, os, requests, csv, asyncio
from io import StringIO
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# -------- CONFIG --------
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU00GJR_bjeMwu_2SdaU_Lrym18DZYQKYA0-uW7mzw_2KMbcNYfCAD34mLjHZpKRZH3oOviud0agl3/pub?gid=0&single=true&output=csv"
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError("Falta TELEGRAM_TOKEN")

SELECCION_PAIS, EN_BUSQUEDA = range(2)
logging.basicConfig(level=logging.INFO)

# -------- DATA --------
def obtener_datos():
    try:
        r = requests.get(CSV_URL, timeout=10)
        f = StringIO(r.content.decode('utf-8'))
        return list(csv.DictReader(f))
    except:
        return []

def safe_get(datos, indices):
    return [datos[i] for i in indices if i < len(datos)]

# -------- BUSCADOR --------
def buscar_productos(datos, idxs, query):
    palabras = query.lower().split()

    resultados = []
    relacionados = []

    for i in idxs:
        if i >= len(datos):
            continue

        item = datos[i]
        texto = (str(item.get('Producto','')) + " " + str(item.get('Keywords',''))).lower()

        score = sum(1 for p in palabras if p in texto)

        if score > 0:
            resultados.append((score, item))
        else:
            relacionados.append(item)

    resultados.sort(reverse=True, key=lambda x: x[0])

    principales = [x[1] for x in resultados[:5]]
    sugeridos = random.sample(relacionados, min(3, len(relacionados)))

    return principales, sugeridos

# -------- BOT --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [['🇦🇷 AR', '🇨🇱 CL'], ['🇺🇾 UY', '🌎 GLOBAL']]
    await update.message.reply_text(
        "✨ *RADAR VIP GLOBAL* ✨\n¿Desde dónde nos visitas?",
        reply_markup=ReplyKeyboardMarkup(botones, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return SELECCION_PAIS

async def seleccionar_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_datos()
    if not datos:
        await update.message.reply_text("Error cargando datos.")
        return ConversationHandler.END

    op = update.message.text.upper()

    if 'AR' in op:
        context.user_data['p'] = 'AR'
        ofertas = safe_get(datos, range(1,8))

        msg = "🇦🇷 *OPORTUNIDADES DEL DÍA*\n\n"
        for r in ofertas:
            msg += f"🔥 *{r['Producto']}*\n🔗 {r['Link']}\n\n"

        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué andás buscando?")

    elif 'CL' in op:
        context.user_data['p'] = 'CL'
        idxs = list(range(97,185)) + [186]
        azar = random.sample(safe_get(datos, idxs), 3)

        msg = "🇨🇱 *DESTACADOS*\n\n"
        for r in azar:
            msg += f"✨ *{r['Producto']}*\n🔗 {r['Link']}\n\n"

        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué buscái?")

    elif 'UY' in op:
        context.user_data['p'] = 'UY'
        idxs = [185,186]
        azar = random.sample(safe_get(datos, idxs), 2)

        msg = "🇺🇾 *SUGERENCIAS*\n\n"
        for r in azar:
            msg += f"🇺🇾 *{r['Producto']}*\n🔗 {r['Link']}\n\n"

        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué buscás, bo?")

    else:
        context.user_data['p'] = 'GL'
        idxs = [186]
        globales = safe_get(datos, idxs)

        msg = "🌎 *GLOBAL DEALS*\n\n"
        for r in globales:
            msg += f"📦 *{r['Producto']}*\n🔗 {r['Link']}\n\n"

        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("What are you looking for? / ¿Qué buscas?")

    return EN_BUSQUEDA

async def ejecutar_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_datos()
    query = update.message.text
    p = context.user_data.get('p')

    if p == 'AR':
        idxs = list(range(1,97)) + [186]
    elif p == 'CL':
        idxs = list(range(97,185)) + [186]
    elif p == 'UY':
        idxs = [185,186]
    else:
        idxs = [186]

    principales, sugeridos = buscar_productos(datos, idxs, query)

    if principales:
        msg = "✅ *Encontré esto para vos:*\n\n"
        for x in principales:
            msg += f"📍 *{x['Producto']}*\n🔗 {x['Link']}\n\n"

        msg += "\n💡 *También podría interesarte:*\n\n"
        for s in sugeridos:
            msg += f"👉 {s['Producto']}\n"

        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text("😕 No encontré eso, pero mirá esto:")
        for s in sugeridos:
            await update.message.reply_text(f"🌎 {s['Producto']}\n🔗 {s['Link']}")

    return EN_BUSQUEDA

# -------- MAIN COMPATIBLE RENDER + PYTHON 3.14 --------
async def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECCION_PAIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_pais)],
            EN_BUSQUEDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, ejecutar_busqueda)],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(conv)

    print("🚀 Radar VIP corriendo...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # Mantener vivo el bot
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
