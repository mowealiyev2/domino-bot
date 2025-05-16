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
        "last_drawn": {}
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
    if len(g["players"]) >= 4:
        return await update.message.reply_text("4 nəfər kifayətdir.")
    g["players"].append(uid)
    g["ids"][uid] = uname
    if len(g["players"]) >= 2:
        s = random.sample(DOMINOES, len(DOMINOES))
        g["hands"] = {p: s[i*7:(i+1)*7] for i, p in enumerate(g["players"])}
        g["deck"] = s[len(g["players"])*7:]
        g["turn"] = g["players"][0]
        players = " vs ".join([g["ids"][p] for p in g["players"]])
        await update.message.reply_text(f"Oyun başladı: {players}\nNövbə: {g['ids'][g['turn']]}\n/daslar yaz.")
    else:
        await update.message.reply_text(f"{uname} qoşuldu. Başqa oyunçu gözlənilir.")

async def hand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = str(update.effective_user.id)
    g = games.get(cid)
    if not g or uid not in g["players"]: return
    button = InlineKeyboardButton("Daşlar", callback_data="showhand")
    await update.message.reply_text("➤ /daslar — Daşlarını görmək üçün kliklə:", reply_markup=InlineKeyboardMarkup([[button]]))

async def showhand_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    cid = query.message.chat.id
    g = games.get(cid)
    if not g or uid not in g["hands"]:
        return await query.answer("Tələsmə Xaiş)", show_alert=True)
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

    # Növbəni növbəti oyunçuya ver
    i = g["players"].index(uid)
    g["turn"] = g["players"][(i + 1) % len(g["players"])]

    await update.message.reply_text(f"{g['ids'][uid]} oynadı {t[0]}:{t[1]} — Növbə: {g['ids'][g['turn']]}")

    board_str = " → ".join([f"{a}:{b}" for a, b in g["board"]])
    left = g["board"][0][0]
    right = g["board"][-1][1]
    await update.message.reply_text(f"Taxta: {board_str}\nSol ucu: {left} | Sağ ucu: {right}")

    button = InlineKeyboardButton("Daşlar", callback_data="showhand")
    await update.message.reply_text(
        "➤ Daşlarına baxmaq üçün kliklə:",
        reply_markup=InlineKeyboardMarkup([[button]])
    )

async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = str(update.effective_user.id)
    g = games.get(cid)
    if not g or g["turn"] != uid or not g["deck"]:
        return await update.message.reply_text("Növbən deyil səbrli ol.")
    
    t = g["deck"].pop()
    g["hands"][uid].append(t)
    g["last_drawn"][uid] = t

    button = InlineKeyboardButton("Çəkdiyin daşı göstər", callback_data="showdrawn")
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

async def leavegame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = str(update.effective_user.id)
    g = games.get(cid)

    if not g or uid not in g["players"]:
        return await update.message.reply_text("Sən oyunda deyilsən.")

    g["players"].remove(uid)
    g["ids"].pop(uid, None)
    g["hands"].pop(uid, None)
    g["last_drawn"].pop(uid, None)

    await update.message.reply_text(f"{update.effective_user.first_name} oyundan çıxdı.")

    if len(g["players"]) < 2:
        del games[cid]
        await update.message.reply_text("Oyunçu sayı azaldı. Oyun dayandırıldı.")

# ✅ PAS FUNKSİYASI
async def passturn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = str(update.effective_user.id)
    g = games.get(cid)

    if not g:
        return await update.message.reply_text("Aktiv oyun yoxdur.")
    if g["turn"] != uid:
        return await update.message.reply_text("Növbən deyil.")

    i = g["players"].index(uid)
    g["turn"] = g["players"][(i + 1) % len(g["players"])]

    await update.message.reply_text(f"{g['ids'][uid]} pas verdi. Növbə: {g['ids'][g['turn']]}")

# Komandaları qeydiyyat
app = ApplicationBuilder().token(BOT_TOKEN).build()
for cmd, func in [
    ("baslat", startgame), ("qosul", joingame), ("daslar", hand),
    ("oyna", play), ("cek", draw), ("dayandirr", stopgame),
    ("cixmaq", leavegame), ("pas", passturn)  # <- PAS ƏLAVƏ OLUNDU
]:
    app.add_handler(CommandHandler(cmd, func))

app.add_handler(CallbackQueryHandler(showhand_callback, pattern="^showhand"))
app.add_handler(CallbackQueryHandler(showdrawn_callback, pattern="^showdrawn"))
app.run_polling()
