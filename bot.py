from aiogram import Bot, Dispatcher, executor, types
import logging
logging.basicConfig(level=logging.INFO)

import config
import goroh
import database as db
import keyboards as kb

# Це для того, щоби бот працював у streamlit.io
import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Load bot
bot = Bot(token=config.API_KEY)
dp = Dispatcher(bot)
temp = {}

async def menu(user_id:int):
    msg = await bot.send_message(user_id, "Що хочете робити?", reply_markup=kb.menu)
    db.set_lm(user_id, msg.message_id)

async def next_sort(user_id:int):
    task = db.get_task_sort(user_id)
    if task is None:
        await bot.send_message(user_id, f'❌ Помилка!\nСхоже, що завдання закінчились.\nСпробуйте інший режим.', reply_markup=kb.to_menu)
        return
    msg = await bot.send_message(user_id, f'🗃 <i>Режим сортування </i>\n<b>Читайте уважно❗️</b>\n\nКуди відносити слово <b>"{task["word"]}"</b>?\n<i>(Частота: {task["rate"]})</i>', "HTML", reply_markup=kb.sort(task["word"]))
    db.set_lm(user_id, msg.message_id)

async def next_heard(user_id:int):
    task = db.get_task_heard(user_id)
    if task is None:
        await bot.send_message(user_id, f'❌ Помилка!\nСхоже, що завдання закінчились.\nСпробуйте інший режим.', reply_markup=kb.to_menu)
        return # ({len(db.heard_tasks)} слів)
    msg = await bot.send_message(user_id, f'👂🏻 <i>Режим "Чули слово ..?"</i>\n<b>Читайте уважно❗️</b>\n\nВи колись чули слово <b>"{task["word"]}"</b>?\n<i>(Частота: {task["rate"]})</i>', "HTML", reply_markup=kb.heard(task["word"]))
    db.set_lm(user_id, msg.message_id)

async def send_last_actions(user_id:int, full:bool=False):
    if full: keyboard = kb.last_full
    else: keyboard = kb.last
    msg = await bot.send_message(user_id, db.get_last_actions(full), reply_markup=keyboard)
    db.set_lm(user_id, msg.message_id)

async def send_stats(user_id:int):
    stats = db.get_stats()
    text = f"📊 <b>Статистика</b>\n\n📋 Кількість слів із завдань: <b>{stats['words']}</b>\n ➜ 🗃 Сортування слів: <b>{stats['sort']}</b>\n ➜ 👂🏻 \"Чули слово ..?\": <b>{stats['heard']}</b>\n ➜ 🤷🏼 Не відомі слова (закрито): <b>{stats['known']}</b>\n\n💾 Кількість записаних слів: <b>{stats['saved']}</b>\n⮩ <i>{stats['saved_split']}</i>\n\n  ➜ 🟢 У Легко: <b>{stats['easy']}</b>\n⮩ <i>{stats['easy_split']}</i>\n  ➜ 🟠 У Нормально: <b>{stats['normal']}</b>\n⮩ <i>{stats['normal_split']}</i>\n  ➜ 🔴 У Складно: <b>{stats['hard']}</b>\n⮩ <i>{stats['hard_split']}</i>\n\nКількість виконаних завдань: <b>{stats['complete']}</b>"

    for u in stats['users']: text += f"\n • {u[0]}: <b>{u[1]}</b>"

    msg = await bot.send_message(user_id, text, "HTML", reply_markup=kb.close)
    db.set_lm(user_id, msg.message_id)

@dp.message_handler(commands=['start'], commands_prefix='!/')
async def start_cmd(message: types.Message):
    await message.delete()
    if message.from_id in db.blacklist: await message.answer("❌ О НІ! ВАС ЗАБАНЕНО 😢🤯😳😡🫣\nта шож це творицця?🏳️‍🌈"); return
    elif message.from_id in db.whitelist:
        await del_last_msg(message.from_id)
        await menu(message.from_id)
    else: await message.answer("👋🏽 Привіт! Цей бот розроблений для того, щоби допомогти пану Ромчику створити гру зі словами.\nТут нічого складного немає. Вибираєш завдання і виконуєш його. Всі завдання ну дууже прості.\n\n❕ Але спочатку пан Романчик повинен додати вас у список користувачів.\nХочете приєднатися?", reply_markup=kb.whitelist_add_me)

@dp.message_handler(commands=['menu'], commands_prefix='!/')
async def menu_cmd(message: types.Message):
    await message.delete()
    if message.from_id not in db.whitelist or message.from_id in db.blacklist: await message.answer("/start", kb.close); return
    await del_last_msg(message.from_id)
    await menu(message.from_id)

@dp.callback_query_handler(lambda callback_query: True)
async def callback(call: types.CallbackQuery):
    if call.from_user.id in db.blacklist: return
    db.get_lm(call.from_user.id)
    match (call.data):
        case 'close': pass
        case 'blank': await call.answer('куда тикаєш', cache_time=0); return
        case 'menu': await menu(call.from_user.id); db.update_user(call.from_user)
        case 'stats': await send_stats(call.from_user.id); await call.answer(); return
        case 'last': await send_last_actions(call.from_user.id)
        case 'last_full': await send_last_actions(call.from_user.id, True)
        case 'hints':
            msg = await call.message.answer('❔ Пояснення\n\n• Що таке "Частота"?\n — Це частота вживання слова, взята із сайту goroh.pp.ua.\nЧастота слова "свято": 11737 - вживається часто;\nЧастота слова "слівце": 579 - вживається рідко.\n\n', reply_markup=kb.close)
            db.set_lm(call.from_user.id, msg.message_id)
            await call.answer(); return

        case "start_sort": await next_sort(call.from_user.id)
        case "start_heard": await next_heard(call.from_user.id)

        case _:
            data = call.data.split("_")
            match data[0]:
                case 'about':
                    await call.message.answer(goroh.about(data[1]), reply_markup=kb.close)
                    await call.answer()
                    return
                
                case 'sort':
                    await next_sort(call.from_user.id)
                    db.sort_word(data[2], data[1], call.from_user.id)
                    await call.answer(f'{data[2]} → {("🟢 Легко", "🟠 Нормально", "🔴 Складно")[int(data[1])]}')
                    db.add_action(f'🗃 {call.from_user.full_name} → "{data[2]}" до {("🟢 Легко", "🟠 Нормально", "🔴 Складно")[int(data[1])]}')

                case 'heard':
                    await next_heard(call.from_user.id)
                    rate = db.get_rate_word(data[2], 'heard')
                    match data[1]:
                        case 'y':
                            level = int(rate > 200)
                            db.heard_word(data[2], level, call.from_user.id)
                            await call.answer(f'{data[2]} → {("🔴 Складно", "🟠 Нормально")[level]}')
                            db.add_action(f'👂🏻 {call.from_user.full_name} чув "{data[2]}". До {("🔴 Складно", "🟠 Нормально")[level]}')
                        case 'n':
                            if rate > 180:
                                db.heard_word(data[2], 0, call.from_user.id)
                                db.add_action(f'👂🏻 {call.from_user.full_name} ніколи не чув "{data[2]}". До 🔴 Складно')
                                await call.answer(f'{data[2]} → 🔴 Складно')
                            else:
                                db.delete_task({'type': 'heard', 'word': data[2]})
                                db.add_action(f'👂🏻 {call.from_user.full_name} ніколи не чув "{data[2]}". ❌ Нікуди не записуємо')
                                await call.answer(f'{data[2]} → ❌ Нікуди не записуємо')
                        case 'o':
                            db.delete_task({'type': 'heard', 'word': data[2]})
                            db.new_task('heard', data[2], rate)
                            await call.answer(f'{data[2]} → 🗃 На сортування')
                            db.add_action(f'👂🏻 {call.from_user.full_name} часто чує "{data[2]}".  🗃 На сортування')

                case 'whitelist':
                    match data[1]:
                        case 'addme':
                            temp[call.from_user.id] = call.from_user.full_name
                            await call.message.answer('⌛️ Окей, пан Романчик перегляне Вашу заявку. Зачекайте...', reply_markup=kb.close)
                            await bot.send_message(1041234545, f'Ей! <i>{call.from_user.full_name}</i> хоче допомогти зі словами.\n - ID: <i>{call.from_user.id}</i>\n - Username: <i>@{call.from_user.username}</i>\n\nШо робити?', 'HTML', reply_markup=kb.whitelist(call.from_user))
                        case 'accept':
                            if call.from_user.id in temp: name = temp[call.from_user.id]; temp.pop(call.from_user.id)
                            else: name = "Невідомо"
                            db.new_user(int(data[2]), name, data[3])
                            await bot.send_message(int(data[2]), '🥳 Вітаю! Ви прийтяті.\nПан Ромчік довольний тим, що Ви бажаєте йому допомогти!💚\n\n/menu - Відкрити меню.\nНатиснувши на перші кнопки в меню, Ви почнете виконувати завдання.\nДалі розберетеся самі)\n\n❗️ Однак пам’ятайте, що за погану поведінку і погане виконання завдань пан Ромчич може Вас забанити. Тому не робіть дурниць.', reply_markup=kb.to_menu)
                        case 'reject':
                            await bot.send_message(int(data[2]), '⛔️ Вибачте, але Вашу заявку було відхилено(', reply_markup=kb.close)
                 
    try: await call.message.delete()
    except: pass

async def del_last_msg(user_id:int):
    msg = db.get_lm(user_id)
    if not msg is None:
        try: await bot.delete_message(user_id, msg)
        except: pass


""" Команди для мене """
@dp.message_handler(commands=['admin'], commands_prefix='!/')
async def admin_cmd(message: types.Message):
    await message.delete()
    if message.from_user.username != config.DEV_TG_NICKNAME: await message.answer("но-но, ше замалий", reply_markup=kb.close); return
    await message.answer("🃏 Спеціальні команди\n\n/admin → Всі спец. команди\n/ban (id) → Заблокувати користувача\n/unban (id) → Розблокувати користувача\n/blacklist → Список заблокованих користувачів\n/userlist → Список користувачів", reply_markup=kb.close)

@dp.message_handler(commands=['ban'], commands_prefix='!/')
async def ban_cmd(message: types.Message):
    await message.delete()
    if message.from_user.username != config.DEV_TG_NICKNAME: await message.answer("но-но, ше замалий", reply_markup=kb.close); return
    _id = message.get_args()
    if _id == '': await message.answer("❗️ Так кого банити? Де ID?\n/ban (id)", reply_markup=kb.close); return
    elif not _id.isdigit(): await message.answer("❗️ та напиши по-люцки.\n/ban (id)", reply_markup=kb.close); return

    _id = int(_id)
    user = db.get_user(_id)
    if user is None: await message.answer("❗️ У нас немає такого користувача.\n/userlist → Список користувачів", reply_markup=kb.close); return

    db.ban_user(_id)
    await message.answer(f"🔴 Користувача '<b>{user['name']}</b>' (@{user['username']}) Заблоковано!\nЩоб розблокувати → <code>/unban {_id}</code>", 'HTML', reply_markup=kb.close)
    await del_last_msg(_id)
    await bot.send_message(_id, '🔴 Будь ласка, відпочинте! Ви себе дуже добре проявили і тому вас ЗАБЛОКОВАНО!\nНе очікувано, правда?')
@dp.message_handler(commands=['unban'], commands_prefix='!/')
async def unban_cmd(message: types.Message):
    await message.delete()
    if message.from_user.username != config.DEV_TG_NICKNAME: await message.answer("но-но, ше замалий", reply_markup=kb.close); return
    _id = message.get_args()
    if _id == '': await message.answer("❗️ Так кого розбанити? Де ID?\n/unban (id)", reply_markup=kb.close); return
    elif not _id.isdigit(): await message.answer("❗️ та напиши по-люцки.\n/unban (id)", reply_markup=kb.close); return

    _id = int(_id)
    user = db.get_user(_id)
    if user is None: await message.answer("❗️ Цей користувач не заблокований.\n/blacklist → Список заблокованих користувачів", reply_markup=kb.close); return

    db.unban_user(_id)
    await message.answer(f"🟢 Користувача '<b>{user['name']}</b>' (@{user['username']}) Розблоковано!\nЩоб заблокувати → <code>/ban {_id}</code>", 'HTML', reply_markup=kb.close)
    await del_last_msg(_id)
    await bot.send_message(_id, '🟢 Вас розблоковано! Ви можете продовжити працювати!', reply_markup=kb.to_menu)

@dp.message_handler(commands=['blacklist'], commands_prefix='!/')
async def blacklist_cmd(message: types.Message):
    await message.delete()
    if message.from_user.username != config.DEV_TG_NICKNAME: await message.answer("но-но, ше замалий", reply_markup=kb.close); return
    text = '👿 Список заблокованих користувачів'
    for _id in db.blacklist:
        u = db.get_user(_id)
        text += f"\n — {u['name']} (@{u['username']}) → <code>{_id}</code>"
    text = text.replace('(@None)', '')
    await message.answer(text, 'HTML', reply_markup=kb.close)
@dp.message_handler(commands=['userlist'], commands_prefix='!/')
async def userlist_cmd(message: types.Message):
    await message.delete()
    if message.from_user.username != config.DEV_TG_NICKNAME: await message.answer("но-но, ше замалий", reply_markup=kb.close); return
    text = '👥 Список користувачів'
    for _id in db.whitelist:
        u = db.get_user(_id)
        text += f"\n — {u['name']} (@{u['username']}) → <code>{_id}</code>"
    text = text.replace('(@None)', '')
    await message.answer(text, 'HTML', reply_markup=kb.close)

if __name__ == "__main__":
    print("Bot is running")
    executor.start_polling(dp, skip_updates=True)
