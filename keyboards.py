from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('◄ Назад', callback_data='menu')]])
to_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('◄ Перейти до меню', callback_data='menu')]])
close = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('❌ Закрити', callback_data="close")]])
whitelist_add_me = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('🙋🏾 Подати заявку', callback_data="whitelist_addme")]])
def whitelist(user):
    return InlineKeyboardMarkup(inline_keyboard=
        [
            [InlineKeyboardButton(f'✅ Прийняти {user.full_name}', callback_data=f"whitelist_accept_{user.id}_{user.full_name}_{user.username}")],
            [InlineKeyboardButton(f'⛔️ Відхилити', callback_data=f"whitelist_reject_{user.id}")],
        ])

menu = InlineKeyboardMarkup(inline_keyboard=
        [
            [InlineKeyboardButton('↓ Режими ↓', callback_data="blank")],
            [InlineKeyboardButton('🗃 Сортування слів', callback_data="start_sort")],
            [InlineKeyboardButton('👂🏻 "Чули слово ..?"', callback_data="start_heard")],
            # [InlineKeyboardButton('🤷🏼 Не відомі слова', callback_data="start_known")],
            [InlineKeyboardButton('↓ Інформація ↓', callback_data="blank")],
            [InlineKeyboardButton('📊 Статистика', callback_data="stats")],
            [InlineKeyboardButton('🛃 Останні дії користувачів', callback_data="last")],
            [InlineKeyboardButton('❔ Пояснення', callback_data="hints")]
        ])

def sort(word:str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(f'🟢 Легко', callback_data=f'sort_0_{word}'),
            InlineKeyboardButton('ㅤ', callback_data="blank"),
            InlineKeyboardButton(f'🔴 Складно', callback_data=f'sort_2_{word}')
        ],[
            InlineKeyboardButton('ㅤ', callback_data="blank"),
            InlineKeyboardButton(f'🟠 Нормально', callback_data=f'sort_1_{word}'),
            InlineKeyboardButton('ㅤ', callback_data="blank")
        ],[
            InlineKeyboardButton(f'🤷🏼‍♀️ Не знаю', callback_data=f'start_sort'),
            InlineKeyboardButton(f'❔ Про слово', callback_data=f'about_{word}')
        ],
        [InlineKeyboardButton('◄ Назад', callback_data="menu")]
    ])

def heard(word:str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(f'🟢 Так', callback_data=f'heard_y_{word}'),
            InlineKeyboardButton('ㅤ', callback_data="blank"),
            InlineKeyboardButton(f'🔴 Ні', callback_data=f'heard_n_{word}')
        ],[
            InlineKeyboardButton(f'🕵🏽‍♀️ Часто чую', callback_data=f'heard_o_{word}'),
            InlineKeyboardButton(f'🤷🏼‍♀️ Не знаю', callback_data=f'start_heard')
        ],
        [InlineKeyboardButton(f'❔ Про слово', callback_data=f'about_{word}')],
        [InlineKeyboardButton('◄ Назад', callback_data="menu")]
    ])

def known(words:list[str]):
    kb = ReplyKeyboardMarkup()
    for word in words: kb.add(KeyboardButton(word))
    kb.row(KeyboardButton('✅ Готово'))
    return kb

def reload(reload_data:str):
    return InlineKeyboardMarkup(inline_keyboard=
        [
            [
                InlineKeyboardButton('🔁 Оновити', callback_data=reload_data),
                InlineKeyboardButton('◄ Назад', callback_data="back")
            ]
        ])

last = InlineKeyboardMarkup(inline_keyboard=
        [
            [
                InlineKeyboardButton('🔁 Оновити', callback_data="last"),
                InlineKeyboardButton('↕️ Більше', callback_data="last_full")
            ],
            [InlineKeyboardButton('◄ Назад', callback_data="back")]
        ])
