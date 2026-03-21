```python
import sqlite3
import requests
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

# 🔐 TOKEN desde variable de entorno (Render)
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ Falta BOT_TOKEN en variables de entorno")

# 💰 AFILIADOS
AMAZON_ID = "radarvip01-20"
ALI_ID = "default"

# 🇦🇷 TUS PRODUCTOS (PRIORIDAD)
PRODUCTOS_AR = [
    {"nombre": "🎣 Caña Kunnan Horizon", "link": "https://articulo.mercadolibre.com.ar/MLA-1714239051-cana-de-pesca-mosca-kunnan-horizon-_JM"},
    {"nombre": "🚗 Peugeot 207 Sedan", "link": "https://auto.mercadolibre.com.ar/MLA-3076197834-peugeot-207-14-sedan-active-75cv-_JM"},
    {"nombre": "🔊 Amplificador SS Pro 30W", "link": "https://articulo.mercadolibre.com.ar/MLA-3082496808-amplificador-ss-pro-ss-30st-multiproposito-de-30w-_JM"},
    {"nombre": "🎸 Amplificador Fender Stage", "link": "https://articulo.mercadolibre.com.ar/MLA-3082510664-amplificador-fender-stage-112-se-_JM"},
    {"nombre": "🚴 Bicicleta Oxea Hunter", "link": "https://articulo.mercadolibre.com.ar/MLA-3082608454-bicicleta-mountain-bike-oxea-hunter-_JM"},
    {"nombre": "🎣 Caña Ranger Fiber", "link": "https://articulo.mercadolibre.com.ar/MLA-3082612028-cana-de-pesca-ranger-fiber-glass-ran-1952-195m-_JM"},
    {"nombre": "🚴 MTB Motomel Maxam", "link": "https://articulo.mercadolibre.com.ar/MLA-3082645566-mountain-bike-motomel-maxam-_JM"}
]

# 🌎 MERCADOS ML
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

# 🧠 BASE DE DATOS
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

# 🔗 LINKS AFILIADOS
def amazon(q):
    return f"https://www.amazon.com/s?k={q}&tag={AMAZON_ID}"

def ali(q):
    return f"https://www.aliexpress.com/wholesale?SearchText={q}&aff_fcid={ALI_ID}"

def buscar_ml(site, q):
    url = f"https://api.mercadolibre.com/sites/{site}/search?q={q}"
    r = requests.get(url).json()
    if r.get("results"):
        item = r["results"][0]
        return f"{item['title']}\n💲 {item['price']}\n{item['permalink']}"
    return "No encontré resultados en MercadoLibre"

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [
        [InlineKeyboardButton("🇦🇷 Argentina", callback_data="AR")],
        [InlineKeyboardButton("🇨🇱 Chile", callback_data="CL")],
        [InlineKeyboardButton("🇲🇽 México", callback_data="MX")],
        [InlineKeyboardButton("🌎 Otro", callback_data="OTRO")]
    ]
    await update.message.reply_text(
        "🔥 Bienvenido! Te ayudo a encontrar las mejores ofertas.\n\n¿Desde qué país comprás?",
        reply_markup=InlineKeyboardMarkup(botones)
    )

# 🌎 SET PAÍS
async def set_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    pais = query.data

    save_user(user_id, pais)

    await query.answer()
    await query.message.reply_text("Perfecto 👍\n\n¿Qué estás buscando?")

# 🔎 BUSCAR
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)

    if not user:
        await update.message.reply_text("👉 Escribí /start primero")
        return

    consultas = user[2]

    if consultas <= 0:
        await update.message.reply_text(
            "🚫 Te quedaste sin búsquedas\n\n💳 USD 5 = 20 búsquedas\n👉 Escribí /pagar"
        )
        return

    texto = update.message.text
    q = texto.replace(" ", "+")

    update_consultas(user_id, consultas - 1)

    site = PAISES[user[1]]

    mensaje = "🔥 Encontré esto para vos 👇\n\n"

    # 🇦🇷 OPORTUNIDADES PROPIAS
    if user[1] == "AR":
        mensaje += "🔥 OPORTUNIDADES (RECOMENDADO)\n"
        for p in PRODUCTOS_AR[:3]:
            mensaje += f"{p['nombre']}\n{p['link']}\n\n"

    # 🛒 ML
    mensaje += "🛒 MercadoLibre\n"
    mensaje += buscar_ml(site, q) + "\n\n"

    # 🟡 AMAZON
    mensaje += f"🟡 Amazon\n{amazon(q)}\n\n"

    # 🔴 ALIEXPRESS
    mensaje += f"🔴 AliExpress\n{ali(q)}\n"

    if consultas <= 2:
        mensaje += "\n\n⚠️ Te quedan pocas búsquedas"

    await update.message.reply_text(mensaje)

# 💳 PAGO
async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💳 Pago de acceso\n\nUSD 5 = 20 búsquedas\n\n(Después integramos MercadoPago o Stripe)"
    )

# 📊 STATS
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db()
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()

    await update.message.reply_text(f"📊 Usuarios registrados: {total}")

# 🚀 INICIO
init_db()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("pagar", pagar))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CallbackQueryHandler(set_pais))
app.add_handler(MessageHandler(filters.TEXT, buscar))

print("🔥 BOT FUNCIONANDO...")
app.run_polling()
```
