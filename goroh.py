from requests_html import HTMLSession

session = HTMLSession()
headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}

def rate(word:str) -> int:
    r = session.get(f"https://goroh.pp.ua/%D0%A7%D0%B0%D1%81%D1%82%D0%BE%D1%82%D0%B0/{word}", headers=headers)
    table = r.html.find(".table", first=True)
    if table is None: return None

    res = table.find(".row")[1].find(".cell")[1].text
    if res == "дані відсутні": return None
    return int(res)

def about(word:str) -> str:
    r = session.get(f"https://slova.com.ua/word/{word}", headers=headers)
    defenition = r.html.find(".defenition", first=True)

    if defenition is not None:
        text = f'Визначення слова "{word}"\n'
        i = 0
        for el in defenition.find("p", first=False):
            if i == 3: break
            text += f"{el.text}\n\n"
            i += 1
        return text
    return f'Я не знаю що таке "{word}"'

# print(rate('авто'), about('авто'))