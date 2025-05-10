from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import random

BOT_TOKEN = '8013008405:AAE1SfOYciRHY626Wr0hoyUiIzK44rkkfEI'

DOMINOES = [(i, j) for i in range(7) for j in range(i, 7)]
games = {}

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    games[update.effective_chat.id] = {
        "players": [],
        "hands": {},
        "board": [],
        "turn": None,
        "deck": [],
        "ids": {},
        "last_drawn": {}  # Əlavə etdik
    }
    await update.message.reply_text("Oyun yaradıldı! /qosul yaz.")

async def joingame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = str(update.effective_user.id)
    uname = update.effective_user.username or update.effective_user.first_name
    g = games.get(cid)
    if not g:
        return await update.message.reply_text("Əvvəlcə /basla yaz.")
    if uid in g["players"]:
        return await update.message.reply_text("Artıq qoşulmusan.")
    if len(g["players"]) >= 2:
        return await update.message.reply_text("4 nəfər kifayətdir.")
    g["players"].append(uid)
    g["ids"][uid] = uname
    if len(g["players"]) == 2:
        s = random.sample(DOMINOES, len(DOMINOES))
        g["hands"] = {g["players"][0]: s[:7], g["players"][1]: s[7:14]}
        g["deck"], g["turn"] = s[14:], g["players"][0]
        p1, p2 = g["ids"][g["players"][0]], g["ids"][g["players"][1]]
        await update.message.reply_text(f"Oyun başladı: {p1} vs {p2}\nNövbə: {p1}\n/daslar yaz.")
    else:
        await update.message.reply_text(f"{uname} qoşuldu. Başqa oyunçu gözlənilir.")

async def hand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = str(update.effective_user.id)
    g = games.get(cid)
    if not g or uid not in g["players"]: return
    button = InlineKeyboardButton("Daşlarını göstər", callback_data="showhand")
    await update.message.reply_text("Daşlarını görmək üçün kliklə:", reply_markup=InlineKeyboardMarkup([[button]]))

async def showhand_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    cid = query.message.chat.id
    g = games.get(cid)
    if not g or uid not in g["hands"]:
        return await query.answer("Daş tapılmadı", show_alert=True)
    tiles = g["hands"][uid]
    text = " • ".join([f"{a}:{b}" for a, b in tiles])
    await query.answer(text=f"Sənin daşların:\n{text}", show_alert=True)

async def showdrawn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    cid = query.message.chat.id
    g = games.get(cid)
    if not g or uid not in g["last_drawn"]:
        return await query.answer("Daş tapılmadı", show_alert=True)
    a, b = g["last_drawn"][uid]
    await query.answer(text=f"Çəkdiyin daş: {a}:{b}", show_alert=True)

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = str(update.effective_user.id)
    g = games.get(cid)
    if not g or g["turn"] != uid: return
    try:
        a, b = map(int, context.args)
        t = (a, b)
    except:
        return
    h, b = g["hands"][uid], g["board"]
    if t not in h and t[::-1] not in h: return
    t = t if t in h else t[::-1]
    if not b:
        b.append(t)
    elif t[0] == b[-1][1]:
        b.append(t)
    elif t[1] == b[-1][1]:
        b.append(t[::-1])
    elif t[1] == b[0][0]:
        b.insert(0, t)
    elif t[0] == b[0][0]:
        b.insert(0, t[::-1])
    else:
        return
    h.remove(t)
    if not h:
        winner = g["ids"][uid]
        del games[cid]
        return await update.message.reply_text(f"{winner} qalib oldu təbrikler👏🏻")

    g["turn"] = [p for p in g["players"] if p != uid][0]
    await update.message.reply_text(f"{g['ids'][uid]} oynadı {t[0]}:{t[1]} — Növbə: {g['ids'][g['turn']]}")

    board_str = " → ".join([f"{a}:{b}" for a, b in g["board"]])
    left = g["board"][0][0]
    right = g["board"][-1][1]
    await update.message.reply_text(
        f"Taxta: {board_str}\nSol ucu: {left} | Sağ ucu: {right}"
    )

async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = str(update.effective_user.id)
    g = games.get(cid)
    if not g or g["turn"] != uid or not g["deck"]:
        return await update.message.reply_text("Növbən deyil sebrli ol.")
    
    t = g["deck"].pop()
    g["hands"][uid].append(t)
    g["last_drawn"][uid] = t  # son çəkilən daşı yadda saxla

    button = InlineKeyboardButton("Çəkdiyim daşı göstər", callback_data="showdrawn")
    await update.message.reply_text(
        "Çəkdiyin daşı görmək üçün kliklə:",
        reply_markup=InlineKeyboardMarkup([[button]])
    )

async def stopgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in games:
        del games[cid]
        await update.message.reply_text("Oyun dayandırıldı.")
    else:
        await update.message.reply_text("Aktiv oyun yoxdur.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
for cmd, func in [
    ("baslat", startgame), ("qosul", joingame), ("daslar", hand),
    ("oyna", play), ("cek", draw), ("dayandirr", stopgame)
]:
    app.add_handler(CommandHandler(cmd, func))

app.add_handler(CallbackQueryHandler(showhand_callback, pattern="^showhand"))
app.add_handler(CallbackQueryHandler(showdrawn_callback, pattern="^showdrawn"))
app.run_polling()
