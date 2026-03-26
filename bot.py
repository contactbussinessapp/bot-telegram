import logging, random, os, requests, csv
from io import StringIO
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# -------- CONFIG --------
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU00GJR_bjeMwu_2SdaU_Lrym18DZYQKYA0-uW7mzw_2KMbcNYfCAD34mLjHZpKRZH3oOviud0agl3/pub?gid=0&single=true&output=csv"
TOKEN = os.getenv("TELEGRAM_TOKEN")

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

# -------- BOT --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [['🇦🇷 AR', '🇨🇱 CL'], ['🇺🇾 UY', '🌎 GLOBAL']]
    await update.message.reply_text(
        "RADAR VIP GLOBAL\n¿Desde dónde nos visitas?",
        reply_markup=ReplyKeyboardMarkup(botones, resize_keyboard=True)
    )
    return SELECCION_PAIS

async def seleccionar_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['p'] = update.message.text
    await update.message.reply_text("OK. ¿Qué estás buscando?")
    return EN_BUSQUEDA

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_datos()
    query = update.message.text.lower()

    resultados = []
    for d in datos:
        texto = (d.get('Producto','') + d.get('Keywords','')).lower()
        if query in texto:
            resultados.append(d)

    if resultados:
        for r in resultados[:5]:
            await update.message.reply_text(f"{r['Producto']}\n{r['Link']}")
    else:
        await update.message.reply_text("No encontré resultados.")

    return EN_BUSQUEDA

# -------- MAIN --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECCION_PAIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_pais)],
            EN_BUSQUEDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, buscar)],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(conv)

    print("BOT FUNCIONANDO")
    app.run_polling()

if __name__ == '__main__':
    main()
