import sqlite3
import requests
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

# 🔐 TOKEN desde variables de entorno (Render)
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Falta BOT_TOKEN en variables de entorno")

# 💰 AFILIADOS
AMAZON_ID = "radarvip01-20"
ALI_ID = "default"

# 🇦🇷 PRODUCTOS
PRODUCTOS_AR = [
    {"nombre": "🎣 Caña Kunnan Horizon", "link": "https://articulo.mercadolibre.com.ar/MLA-1714239051-cana-de-pesca-mosca-kunnan-horizon-_JM"},
    {"nombre": "🚗 Peugeot 207 Sedan", "link": "https://auto.mercadolibre.com.ar/MLA-3076197834-peugeot-207-14-sedan-active-75cv-_JM"},
]

# 🌎 PAÍSES
PAISES = {
    "AR": "MLA",
    "CL": "MLC",
    "MX": "MLM",
    "CO": "MCO",
    "PE": "MPE",
    "BR": "MLB",
    "UY": "MLU",
    "OTRO": "MLM"
}

# 🧠 DB
def db():
    return sqlite3.connect("bot.db")

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, pais TEXT, consultas INT)")
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data

def save_user(user_id, pais):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (user_id, pais, 10))
    conn.commit()
    conn.close()

def update_consultas(user_id, n):
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET consultas=? WHERE id=?", (n, user_id))
    conn.commit()
    conn.close()

# 🔗 LINKS
def amazon(q):
    return f"https://www.amazon.com/s?k={q}&tag={AMAZON_ID}"

def ali(q):
    return f"https://www.aliexpress.com/wholesale?SearchText={q}"

def buscar_ml(site, q):
    url = f"https://api.mercadolibre.com/sites/{site}/search?q={q}"
    r = requests.get(url).json()
    if r.get("results"):
        item = r["results"][0]
        return f"{item['title']}\n💲 {item['price']}\n{item['permalink']}"
    return "No encontré resultados"

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [
        [InlineKeyboardButton("🇦🇷 Argentina", callback_data="AR")],
        [InlineKeyboardButton("🇨🇱 Chile", callback_data="CL")],
        [InlineKeyboardButton("🇲🇽 México", callback_data="MX")],
        [InlineKeyboardButton("🌎 Otro", callback_data="OTRO")]
    ]

    await update.message.reply_text(
        "🔥 Bienvenido!\n¿Desde qué país comprás?",
        reply_markup=InlineKeyboardMarkup(botones)
    )

# 🌎 SET PAÍS
async def set_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    pais = query.data

    save_user(user_id, pais)

    await query.answer()
    await query.message.reply_text("Perfecto 👍 ahora escribí qué buscás")

# 🔎 BUSCAR
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)

    if not user:
        await update.message.reply_text("👉 Escribí /start primero")
        return

    consultas = user[2]

    if consultas <= 0:
        await update.message.reply_text("🚫 Sin búsquedas. Escribí /pagar")
        return

    texto = update.message.text
    q = texto.replace(" ", "+")

    update_consultas(user_id, consultas - 1)

    site = PAISES[user[1]]

    mensaje = "🔥 Resultados:\n\n"

    if user[1] == "AR":
        mensaje += "🔥 Productos recomendados:\n"
        for p in PRODUCTOS_AR:
            mensaje += f"{p['nombre']}\n{p['link']}\n\n"

    mensaje += "🛒 MercadoLibre:\n"
    mensaje += buscar_ml(site, q) + "\n\n"

    mensaje += f"🟡 Amazon:\n{amazon(q)}\n\n"
    mensaje += f"🔴 AliExpress:\n{ali(q)}"

    await update.message.reply_text(mensaje)

# 💳 PAGO
async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💳 Pago: USD 5 = 20 búsquedas")

# 📊 STATS
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db()
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()

    await update.message.reply_text(f"Usuarios: {total}")

# 🚀 MAIN
init_db()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("pagar", pagar))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CallbackQueryHandler(set_pais))
app.add_handler(MessageHandler(filters.TEXT, buscar))

print("BOT FUNCIONANDO")
app.run_polling()
