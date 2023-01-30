from aiogram import Bot, Dispatcher, executor, types

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

async def menu(user_id:int):
    msg = await bot.send_message(user_id, "Що хочете робити?", reply_markup=kb.menu)
    db.set_lm(user_id, msg.message_id)

async def next_sort(user_id:int):
    task = db.get_task_sort(user_id)
    if task is None:
        await bot.send_message(user_id, f'❌ Помилка!\nСхоже, що завдання закінчились.\nСпробуйте інший режим.', reply_markup=kb.to_menu)
        return
    if task["rate"] < 800: maybe = 'складно'
    elif task["rate"] < 1150: maybe = 'нормально'
    else: maybe = 'легко'
    msg = await bot.send_message(user_id, f'🗃 <i>Режим сортування ({len(db.sort_tasks)} слів)</i>\n<b>Читайте уважно❗️</b>\n\nКуди відносити слово <b>"{task["word"]}"</b>?\n<i>(Частота: {task["rate"]} | <tg-spoiler>Може {maybe}?</tg-spoiler>)</i>', "HTML", reply_markup=kb.sort(task["word"]))
    db.set_lm(user_id, msg.message_id)

async def next_heard(user_id:int):
    task = db.get_task_heard(user_id)
    if task is None:
        await bot.send_message(user_id, f'❌ Помилка!\nСхоже, що завдання закінчились.\nСпробуйте інший режим.', reply_markup=kb.to_menu)
        return
    msg = await bot.send_message(user_id, f'👂🏻 <i>Режим "Чули слово ..?" ({len(db.heard_tasks)} слів)</i>\n<b>Читайте уважно❗️</b>\n\nВи колись чули слово <b>"{task["word"]}"</b>?\n<i>(Частота: {task["rate"]})</i>', "HTML", reply_markup=kb.heard(task["word"]))
    db.set_lm(user_id, msg.message_id)

async def send_last_actions(user_id:int, full:bool=False):
    if full: keyboard = kb.reload("last")
    else: keyboard = kb.last
    msg = await bot.send_message(user_id, db.get_last_actions(full), reply_markup=keyboard)
    db.set_lm(user_id, msg.message_id)

async def send_stats(user_id:int):
    stats = db.get_stats()
    text = f"📊 <b>Статистика</b>\n\n📋 Кількість слів із завдань: <i>{stats['words']}</i>\n — 🗃 Сортування слів: <i>{stats['sort']}</i>\n — 👂🏻 \"Чули слово ..?\": <i>{stats['heard']}</i>\n — 🤷🏼 Не відомі слова: <i>{stats['known']}</i>\n\nКількість виконаних завдань: <i>{stats['complete']}</i>"

    for u in stats['users']: text += f"\n — {u[0]}: <i>{u[1]}</i>"

    msg = await bot.send_message(user_id, text, "HTML", reply_markup=kb.reload("stats"))
    db.set_lm(user_id, msg.message_id)

@dp.message_handler(commands=['start'], commands_prefix='!/')
async def start_cmd(message: types.Message):
    await message.delete()
    if message.from_id in db.blacklist: return
    elif message.from_id in db.whitelist:
        await del_last_msg(message.from_id)
        await menu(message.from_id)
    else: await message.answer("👋🏽 Привіт! Цей бот розроблений для того, щоби допомогти пану Ромчику створити гру зі словами.\nТут нічого складного немає. Вибираєш завдання і виконуєш його. Всі завдання ну дууже прості.\n\n❕ Але спочатку пан Романчик повинен додати вас у список користувачів.\nХочете приєднатися?", reply_markup=kb.whitelist_add_me)

@dp.message_handler(commands=['menu'], commands_prefix='!/')
async def menu_cmd(message: types.Message):
    await message.delete()
    if message.from_id not in db.whitelist or message.from_id in db.blacklist: return
    await del_last_msg(message.from_id)
    await menu(message.from_id)


@dp.callback_query_handler(lambda callback_query: True)
async def callback(call: types.CallbackQuery):
    if call.from_user.id in db.blacklist: return
    db.get_lm(call.from_user.id)
    match (call.data):
        case 'close': pass
        case 'blank': await call.answer('куда тикаєш'); return
        case 'back': await menu(call.from_user.id)
        case 'menu': await menu(call.from_user.id)
        case 'stats': await send_stats(call.from_user.id)
        case 'last': await send_last_actions(call.from_user.id)
        case 'last_full': await send_last_actions(call.from_user.id, True)
        case 'hints':
            msg = await call.message.answer( '❔ Пояснення\n\n• Що таке "Частота"?\n — Це частота вживання слова, взята із сайту goroh.pp.ua.\nЧастота слова "свято": 11737 - вживається часто;\nЧастота слова "слівце": 579 - вживається рідко.\n\n', reply_markup=kb.back)
            db.set_lm(call.from_user.id, msg.message_id)

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
                            level = int(rate > 420)
                            db.heard_word(data[2], level, call.from_user.id)
                            await call.answer(f'{data[2]} → {("🔴 Складно", "🟠 Нормально")[level]}')
                            db.add_action(f'👂🏻 {call.from_user.full_name} чув "{data[2]}". До {("🔴 Складно", "🟠 Нормально")[level]}')
                        case 'n':
                            if rate > 420:
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
                            await call.message.answer('⌛️ Окей, пан Романчик перегляне Вашу заявку. Зачекайте...', reply_markup=kb.close)
                            await bot.send_message(1041234545, f'Ей! <i>{call.from_user.full_name}</i> хоче допомогти зі словами.\n - ID: <i>{call.from_user.id}</i>\n - Username: <i>@{call.from_user.username}</i>\n\nШо робити?', 'HTML', reply_markup=kb.whitelist(call.from_user))
                        case 'accept':
                            db.new_user(int(data[2]), data[3], data[4])
                            await bot.send_message(int(data[2]), '🥳 Вітаю! Ви прийтяті.\nПан Ромчік довольний тим, що Ви бажаєте йому допомогти!💚\n\n/menu - Відкрити меню.\nНатиснувши на перші кнопки в меню, Ви почнете виконувати завдання.\nДалі розберетеся самі)\n\n❗️ Однак пам’ятайте, що за погану поведінку і погане виконання завдань пан Ромчич може Вас забанити. Тому не робіть дурниць.', reply_markup=kb.to_menu)
                        case 'reject':
                            await bot.send_message(int(data[2]), '⛔️ Вибачте, але Вашу заявку було відхилено(', reply_markup=kb.close)
                 
    await call.message.delete()

async def del_last_msg(user_id:int):
    msg = db.get_lm(user_id)
    if not msg is None:
        try: await bot.delete_message(user_id, msg)
        except: pass

if __name__ == "__main__":
    print("Bot is running")
    executor.start_polling(dp, skip_updates=True)
