"""Loader for phrasal verbs from local data and GitHub datasets."""

import asyncio
import aiohttp
from typing import Optional


# Core phrasal verbs with translations and definitions (~300)
PHRASAL_VERBS_DATA: list[dict] = [
    # GET phrasal verbs
    {"phrase": "get up", "base_verb": "get", "particle": "up", "translations": ["вставать", "просыпаться"],
     "definitions": [{"en": "to rise from bed", "ru": "вставать с кровати"}], "is_separable": False},
    {"phrase": "get out", "base_verb": "get", "particle": "out", "translations": ["выходить", "выбираться"],
     "definitions": [{"en": "to leave a place", "ru": "покидать место"}], "is_separable": False},
    {"phrase": "get in", "base_verb": "get", "particle": "in", "translations": ["входить", "садиться"],
     "definitions": [{"en": "to enter", "ru": "входить"}], "is_separable": False},
    {"phrase": "get on", "base_verb": "get", "particle": "on", "translations": ["садиться (на транспорт)", "ладить"],
     "definitions": [{"en": "to board transport", "ru": "садиться на транспорт"}, {"en": "to have good relations", "ru": "ладить"}], "is_separable": False},
    {"phrase": "get off", "base_verb": "get", "particle": "off", "translations": ["выходить (из транспорта)", "слезать"],
     "definitions": [{"en": "to leave transport", "ru": "выходить из транспорта"}], "is_separable": False},
    {"phrase": "get back", "base_verb": "get", "particle": "back", "translations": ["возвращаться", "вернуть"],
     "definitions": [{"en": "to return", "ru": "возвращаться"}], "is_separable": True},
    {"phrase": "get over", "base_verb": "get", "particle": "over", "translations": ["преодолеть", "оправиться"],
     "definitions": [{"en": "to recover from", "ru": "оправиться от чего-либо"}], "is_separable": False},
    {"phrase": "get along", "base_verb": "get", "particle": "along", "translations": ["ладить", "уживаться"],
     "definitions": [{"en": "to have good relations with someone", "ru": "ладить с кем-то"}], "is_separable": False},
    {"phrase": "get away", "base_verb": "get", "particle": "away", "translations": ["убежать", "уехать"],
     "definitions": [{"en": "to escape or leave", "ru": "убежать, уехать"}], "is_separable": False},
    {"phrase": "get through", "base_verb": "get", "particle": "through", "translations": ["дозвониться", "пройти через"],
     "definitions": [{"en": "to reach by phone", "ru": "дозвониться"}, {"en": "to finish", "ru": "закончить"}], "is_separable": False},
    {"phrase": "get together", "base_verb": "get", "particle": "together", "translations": ["собираться", "встречаться"],
     "definitions": [{"en": "to meet socially", "ru": "собираться вместе"}], "is_separable": False},
    {"phrase": "get rid of", "base_verb": "get", "particle": "rid of", "translations": ["избавиться от"],
     "definitions": [{"en": "to eliminate or dispose of", "ru": "избавиться от чего-либо"}], "is_separable": False},

    # LOOK phrasal verbs
    {"phrase": "look up", "base_verb": "look", "particle": "up", "translations": ["искать (в справочнике)", "смотреть вверх"],
     "definitions": [{"en": "to search for information", "ru": "искать информацию"}], "is_separable": True},
    {"phrase": "look for", "base_verb": "look", "particle": "for", "translations": ["искать"],
     "definitions": [{"en": "to try to find", "ru": "пытаться найти"}], "is_separable": False},
    {"phrase": "look after", "base_verb": "look", "particle": "after", "translations": ["заботиться", "присматривать"],
     "definitions": [{"en": "to take care of", "ru": "заботиться о ком-то"}], "is_separable": False},
    {"phrase": "look at", "base_verb": "look", "particle": "at", "translations": ["смотреть на"],
     "definitions": [{"en": "to direct eyes towards", "ru": "смотреть на что-то"}], "is_separable": False},
    {"phrase": "look out", "base_verb": "look", "particle": "out", "translations": ["быть осторожным", "смотреть наружу"],
     "definitions": [{"en": "to be careful", "ru": "быть осторожным"}], "is_separable": False},
    {"phrase": "look forward to", "base_verb": "look", "particle": "forward to", "translations": ["с нетерпением ждать"],
     "definitions": [{"en": "to anticipate with pleasure", "ru": "предвкушать"}], "is_separable": False},
    {"phrase": "look into", "base_verb": "look", "particle": "into", "translations": ["изучать", "расследовать"],
     "definitions": [{"en": "to investigate", "ru": "расследовать"}], "is_separable": False},
    {"phrase": "look down on", "base_verb": "look", "particle": "down on", "translations": ["смотреть свысока"],
     "definitions": [{"en": "to consider inferior", "ru": "презирать"}], "is_separable": False},
    {"phrase": "look over", "base_verb": "look", "particle": "over", "translations": ["просматривать", "проверять"],
     "definitions": [{"en": "to examine", "ru": "просматривать"}], "is_separable": True},
    {"phrase": "look through", "base_verb": "look", "particle": "through", "translations": ["просматривать", "пролистывать"],
     "definitions": [{"en": "to examine quickly", "ru": "быстро просмотреть"}], "is_separable": False},

    # TAKE phrasal verbs
    {"phrase": "take off", "base_verb": "take", "particle": "off", "translations": ["снимать", "взлетать"],
     "definitions": [{"en": "to remove clothing", "ru": "снимать одежду"}, {"en": "to leave the ground (plane)", "ru": "взлетать"}], "is_separable": True},
    {"phrase": "take on", "base_verb": "take", "particle": "on", "translations": ["брать на себя", "нанимать"],
     "definitions": [{"en": "to accept responsibility", "ru": "брать на себя"}], "is_separable": True},
    {"phrase": "take out", "base_verb": "take", "particle": "out", "translations": ["выносить", "вынимать"],
     "definitions": [{"en": "to remove from a place", "ru": "вынимать"}], "is_separable": True},
    {"phrase": "take up", "base_verb": "take", "particle": "up", "translations": ["начать заниматься", "занимать (место)"],
     "definitions": [{"en": "to start a hobby", "ru": "начать заниматься чем-то"}], "is_separable": True},
    {"phrase": "take over", "base_verb": "take", "particle": "over", "translations": ["брать под контроль", "принимать управление"],
     "definitions": [{"en": "to assume control", "ru": "взять под контроль"}], "is_separable": True},
    {"phrase": "take back", "base_verb": "take", "particle": "back", "translations": ["возвращать", "брать назад"],
     "definitions": [{"en": "to return", "ru": "вернуть"}], "is_separable": True},
    {"phrase": "take down", "base_verb": "take", "particle": "down", "translations": ["записывать", "снимать"],
     "definitions": [{"en": "to write down", "ru": "записывать"}, {"en": "to remove from a high place", "ru": "снимать"}], "is_separable": True},
    {"phrase": "take in", "base_verb": "take", "particle": "in", "translations": ["впускать", "понимать"],
     "definitions": [{"en": "to understand", "ru": "понимать"}, {"en": "to accept as a guest", "ru": "принимать гостя"}], "is_separable": True},
    {"phrase": "take after", "base_verb": "take", "particle": "after", "translations": ["быть похожим на"],
     "definitions": [{"en": "to resemble a family member", "ru": "быть похожим на родственника"}], "is_separable": False},
    {"phrase": "take apart", "base_verb": "take", "particle": "apart", "translations": ["разбирать"],
     "definitions": [{"en": "to disassemble", "ru": "разбирать на части"}], "is_separable": True},

    # TURN phrasal verbs
    {"phrase": "turn on", "base_verb": "turn", "particle": "on", "translations": ["включать"],
     "definitions": [{"en": "to start a device", "ru": "включить устройство"}], "is_separable": True},
    {"phrase": "turn off", "base_verb": "turn", "particle": "off", "translations": ["выключать"],
     "definitions": [{"en": "to stop a device", "ru": "выключить устройство"}], "is_separable": True},
    {"phrase": "turn up", "base_verb": "turn", "particle": "up", "translations": ["прибавлять", "появляться"],
     "definitions": [{"en": "to increase volume", "ru": "прибавить громкость"}, {"en": "to arrive", "ru": "появиться"}], "is_separable": True},
    {"phrase": "turn down", "base_verb": "turn", "particle": "down", "translations": ["убавлять", "отклонять"],
     "definitions": [{"en": "to decrease volume", "ru": "убавить"}, {"en": "to reject", "ru": "отклонить"}], "is_separable": True},
    {"phrase": "turn out", "base_verb": "turn", "particle": "out", "translations": ["оказываться", "выключать"],
     "definitions": [{"en": "to prove to be", "ru": "оказаться"}], "is_separable": True},
    {"phrase": "turn around", "base_verb": "turn", "particle": "around", "translations": ["разворачиваться", "оборачиваться"],
     "definitions": [{"en": "to face opposite direction", "ru": "развернуться"}], "is_separable": True},
    {"phrase": "turn into", "base_verb": "turn", "particle": "into", "translations": ["превращаться в"],
     "definitions": [{"en": "to become", "ru": "превратиться во что-то"}], "is_separable": False},
    {"phrase": "turn back", "base_verb": "turn", "particle": "back", "translations": ["возвращаться", "поворачивать назад"],
     "definitions": [{"en": "to return", "ru": "повернуть назад"}], "is_separable": False},
    {"phrase": "turn over", "base_verb": "turn", "particle": "over", "translations": ["переворачивать"],
     "definitions": [{"en": "to flip to other side", "ru": "перевернуть"}], "is_separable": True},

    # GIVE phrasal verbs
    {"phrase": "give up", "base_verb": "give", "particle": "up", "translations": ["сдаваться", "бросать"],
     "definitions": [{"en": "to stop trying", "ru": "сдаться"}, {"en": "to quit a habit", "ru": "бросить привычку"}], "is_separable": True},
    {"phrase": "give in", "base_verb": "give", "particle": "in", "translations": ["уступать", "сдаваться"],
     "definitions": [{"en": "to yield", "ru": "уступить"}], "is_separable": False},
    {"phrase": "give out", "base_verb": "give", "particle": "out", "translations": ["раздавать", "заканчиваться"],
     "definitions": [{"en": "to distribute", "ru": "раздавать"}], "is_separable": True},
    {"phrase": "give away", "base_verb": "give", "particle": "away", "translations": ["отдавать", "выдавать (секрет)"],
     "definitions": [{"en": "to donate", "ru": "отдать даром"}, {"en": "to reveal", "ru": "выдать секрет"}], "is_separable": True},
    {"phrase": "give back", "base_verb": "give", "particle": "back", "translations": ["возвращать"],
     "definitions": [{"en": "to return something", "ru": "вернуть что-то"}], "is_separable": True},
    {"phrase": "give off", "base_verb": "give", "particle": "off", "translations": ["испускать", "излучать"],
     "definitions": [{"en": "to emit", "ru": "испускать, излучать"}], "is_separable": False},

    # PUT phrasal verbs
    {"phrase": "put on", "base_verb": "put", "particle": "on", "translations": ["надевать", "включать"],
     "definitions": [{"en": "to wear", "ru": "надеть одежду"}], "is_separable": True},
    {"phrase": "put off", "base_verb": "put", "particle": "off", "translations": ["откладывать", "отталкивать"],
     "definitions": [{"en": "to postpone", "ru": "откладывать"}], "is_separable": True},
    {"phrase": "put up", "base_verb": "put", "particle": "up", "translations": ["вешать", "размещать"],
     "definitions": [{"en": "to hang or display", "ru": "повесить"}], "is_separable": True},
    {"phrase": "put down", "base_verb": "put", "particle": "down", "translations": ["класть", "записывать"],
     "definitions": [{"en": "to place something down", "ru": "положить"}], "is_separable": True},
    {"phrase": "put away", "base_verb": "put", "particle": "away", "translations": ["убирать"],
     "definitions": [{"en": "to store in proper place", "ru": "убрать на место"}], "is_separable": True},
    {"phrase": "put out", "base_verb": "put", "particle": "out", "translations": ["тушить", "выставлять"],
     "definitions": [{"en": "to extinguish", "ru": "потушить"}], "is_separable": True},
    {"phrase": "put up with", "base_verb": "put", "particle": "up with", "translations": ["мириться с", "терпеть"],
     "definitions": [{"en": "to tolerate", "ru": "терпеть"}], "is_separable": False},
    {"phrase": "put together", "base_verb": "put", "particle": "together", "translations": ["собирать"],
     "definitions": [{"en": "to assemble", "ru": "собрать"}], "is_separable": True},

    # COME phrasal verbs
    {"phrase": "come in", "base_verb": "come", "particle": "in", "translations": ["входить"],
     "definitions": [{"en": "to enter", "ru": "войти"}], "is_separable": False},
    {"phrase": "come out", "base_verb": "come", "particle": "out", "translations": ["выходить", "появляться"],
     "definitions": [{"en": "to exit", "ru": "выйти"}, {"en": "to be released", "ru": "выйти в свет"}], "is_separable": False},
    {"phrase": "come back", "base_verb": "come", "particle": "back", "translations": ["возвращаться"],
     "definitions": [{"en": "to return", "ru": "вернуться"}], "is_separable": False},
    {"phrase": "come up", "base_verb": "come", "particle": "up", "translations": ["подниматься", "возникать"],
     "definitions": [{"en": "to arise", "ru": "возникнуть"}], "is_separable": False},
    {"phrase": "come down", "base_verb": "come", "particle": "down", "translations": ["спускаться", "снижаться"],
     "definitions": [{"en": "to descend", "ru": "спуститься"}], "is_separable": False},
    {"phrase": "come on", "base_verb": "come", "particle": "on", "translations": ["давай!", "начинаться"],
     "definitions": [{"en": "hurry up (informal)", "ru": "давай!"}, {"en": "to start", "ru": "начаться"}], "is_separable": False},
    {"phrase": "come over", "base_verb": "come", "particle": "over", "translations": ["заходить в гости"],
     "definitions": [{"en": "to visit someone", "ru": "зайти в гости"}], "is_separable": False},
    {"phrase": "come across", "base_verb": "come", "particle": "across", "translations": ["наткнуться на", "производить впечатление"],
     "definitions": [{"en": "to find by chance", "ru": "случайно найти"}], "is_separable": False},
    {"phrase": "come up with", "base_verb": "come", "particle": "up with", "translations": ["придумать"],
     "definitions": [{"en": "to think of an idea", "ru": "придумать идею"}], "is_separable": False},

    # GO phrasal verbs
    {"phrase": "go on", "base_verb": "go", "particle": "on", "translations": ["продолжать", "происходить"],
     "definitions": [{"en": "to continue", "ru": "продолжать"}], "is_separable": False},
    {"phrase": "go out", "base_verb": "go", "particle": "out", "translations": ["выходить", "встречаться"],
     "definitions": [{"en": "to leave home for entertainment", "ru": "выйти погулять"}], "is_separable": False},
    {"phrase": "go back", "base_verb": "go", "particle": "back", "translations": ["возвращаться"],
     "definitions": [{"en": "to return", "ru": "вернуться"}], "is_separable": False},
    {"phrase": "go up", "base_verb": "go", "particle": "up", "translations": ["подниматься", "расти"],
     "definitions": [{"en": "to increase", "ru": "подняться, вырасти"}], "is_separable": False},
    {"phrase": "go down", "base_verb": "go", "particle": "down", "translations": ["снижаться", "спускаться"],
     "definitions": [{"en": "to decrease", "ru": "снизиться"}], "is_separable": False},
    {"phrase": "go off", "base_verb": "go", "particle": "off", "translations": ["срабатывать", "взрываться"],
     "definitions": [{"en": "to explode or sound (alarm)", "ru": "сработать, взорваться"}], "is_separable": False},
    {"phrase": "go away", "base_verb": "go", "particle": "away", "translations": ["уходить", "уезжать"],
     "definitions": [{"en": "to leave", "ru": "уйти"}], "is_separable": False},
    {"phrase": "go through", "base_verb": "go", "particle": "through", "translations": ["проходить через", "просматривать"],
     "definitions": [{"en": "to experience", "ru": "пережить"}, {"en": "to examine", "ru": "просмотреть"}], "is_separable": False},
    {"phrase": "go over", "base_verb": "go", "particle": "over", "translations": ["просматривать", "повторять"],
     "definitions": [{"en": "to review", "ru": "просмотреть, повторить"}], "is_separable": False},
    {"phrase": "go ahead", "base_verb": "go", "particle": "ahead", "translations": ["продолжать", "начинать"],
     "definitions": [{"en": "to proceed", "ru": "продолжайте"}], "is_separable": False},

    # MAKE phrasal verbs
    {"phrase": "make up", "base_verb": "make", "particle": "up", "translations": ["придумывать", "мириться", "краситься"],
     "definitions": [{"en": "to invent", "ru": "придумать"}, {"en": "to reconcile", "ru": "помириться"}], "is_separable": True},
    {"phrase": "make out", "base_verb": "make", "particle": "out", "translations": ["разобрать", "понять"],
     "definitions": [{"en": "to understand", "ru": "разобрать, понять"}], "is_separable": True},
    {"phrase": "make up for", "base_verb": "make", "particle": "up for", "translations": ["компенсировать"],
     "definitions": [{"en": "to compensate", "ru": "компенсировать"}], "is_separable": False},

    # BREAK phrasal verbs
    {"phrase": "break down", "base_verb": "break", "particle": "down", "translations": ["ломаться", "разрушать"],
     "definitions": [{"en": "to stop working", "ru": "сломаться"}, {"en": "to lose control emotionally", "ru": "сорваться"}], "is_separable": True},
    {"phrase": "break up", "base_verb": "break", "particle": "up", "translations": ["расставаться", "разбивать"],
     "definitions": [{"en": "to end a relationship", "ru": "расстаться"}], "is_separable": True},
    {"phrase": "break in", "base_verb": "break", "particle": "in", "translations": ["вламываться", "разнашивать"],
     "definitions": [{"en": "to enter by force", "ru": "вломиться"}], "is_separable": True},
    {"phrase": "break out", "base_verb": "break", "particle": "out", "translations": ["вспыхивать", "сбегать"],
     "definitions": [{"en": "to start suddenly", "ru": "вспыхнуть"}, {"en": "to escape", "ru": "сбежать"}], "is_separable": False},
    {"phrase": "break into", "base_verb": "break", "particle": "into", "translations": ["вламываться"],
     "definitions": [{"en": "to enter by force", "ru": "вломиться"}], "is_separable": False},

    # WORK phrasal verbs
    {"phrase": "work out", "base_verb": "work", "particle": "out", "translations": ["тренироваться", "решать"],
     "definitions": [{"en": "to exercise", "ru": "тренироваться"}, {"en": "to solve", "ru": "решить"}], "is_separable": True},
    {"phrase": "work on", "base_verb": "work", "particle": "on", "translations": ["работать над"],
     "definitions": [{"en": "to spend time improving", "ru": "работать над чем-то"}], "is_separable": False},
    {"phrase": "work up", "base_verb": "work", "particle": "up", "translations": ["вызывать", "возбуждать"],
     "definitions": [{"en": "to develop gradually", "ru": "развить"}], "is_separable": True},

    # PICK phrasal verbs
    {"phrase": "pick up", "base_verb": "pick", "particle": "up", "translations": ["поднимать", "забирать", "выучить"],
     "definitions": [{"en": "to lift", "ru": "поднять"}, {"en": "to collect someone", "ru": "забрать"}], "is_separable": True},
    {"phrase": "pick out", "base_verb": "pick", "particle": "out", "translations": ["выбирать"],
     "definitions": [{"en": "to choose", "ru": "выбрать"}], "is_separable": True},
    {"phrase": "pick on", "base_verb": "pick", "particle": "on", "translations": ["придираться"],
     "definitions": [{"en": "to criticize unfairly", "ru": "придираться к кому-то"}], "is_separable": False},

    # SET phrasal verbs
    {"phrase": "set up", "base_verb": "set", "particle": "up", "translations": ["устанавливать", "организовывать"],
     "definitions": [{"en": "to establish", "ru": "установить, организовать"}], "is_separable": True},
    {"phrase": "set off", "base_verb": "set", "particle": "off", "translations": ["отправляться", "вызывать"],
     "definitions": [{"en": "to start a journey", "ru": "отправиться в путь"}], "is_separable": True},
    {"phrase": "set out", "base_verb": "set", "particle": "out", "translations": ["отправляться", "излагать"],
     "definitions": [{"en": "to begin a journey", "ru": "отправиться"}], "is_separable": False},
    {"phrase": "set down", "base_verb": "set", "particle": "down", "translations": ["записывать", "высаживать"],
     "definitions": [{"en": "to write down", "ru": "записать"}], "is_separable": True},

    # RUN phrasal verbs
    {"phrase": "run out", "base_verb": "run", "particle": "out", "translations": ["заканчиваться"],
     "definitions": [{"en": "to be exhausted (supply)", "ru": "закончиться (о запасах)"}], "is_separable": False},
    {"phrase": "run into", "base_verb": "run", "particle": "into", "translations": ["столкнуться с", "наткнуться на"],
     "definitions": [{"en": "to meet by chance", "ru": "случайно встретить"}], "is_separable": False},
    {"phrase": "run away", "base_verb": "run", "particle": "away", "translations": ["убегать"],
     "definitions": [{"en": "to escape by running", "ru": "убежать"}], "is_separable": False},
    {"phrase": "run over", "base_verb": "run", "particle": "over", "translations": ["переехать", "просмотреть"],
     "definitions": [{"en": "to hit with a vehicle", "ru": "переехать"}], "is_separable": True},

    # BRING phrasal verbs
    {"phrase": "bring up", "base_verb": "bring", "particle": "up", "translations": ["воспитывать", "поднимать (тему)"],
     "definitions": [{"en": "to raise a child", "ru": "воспитать"}, {"en": "to mention", "ru": "упомянуть"}], "is_separable": True},
    {"phrase": "bring back", "base_verb": "bring", "particle": "back", "translations": ["возвращать", "напоминать"],
     "definitions": [{"en": "to return", "ru": "вернуть"}], "is_separable": True},
    {"phrase": "bring out", "base_verb": "bring", "particle": "out", "translations": ["выпускать", "выявлять"],
     "definitions": [{"en": "to release", "ru": "выпустить"}], "is_separable": True},
    {"phrase": "bring down", "base_verb": "bring", "particle": "down", "translations": ["снижать", "свергать"],
     "definitions": [{"en": "to reduce", "ru": "снизить"}], "is_separable": True},

    # CALL phrasal verbs
    {"phrase": "call off", "base_verb": "call", "particle": "off", "translations": ["отменять"],
     "definitions": [{"en": "to cancel", "ru": "отменить"}], "is_separable": True},
    {"phrase": "call back", "base_verb": "call", "particle": "back", "translations": ["перезвонить"],
     "definitions": [{"en": "to return a phone call", "ru": "перезвонить"}], "is_separable": True},
    {"phrase": "call up", "base_verb": "call", "particle": "up", "translations": ["звонить", "призывать"],
     "definitions": [{"en": "to telephone", "ru": "позвонить"}], "is_separable": True},
    {"phrase": "call on", "base_verb": "call", "particle": "on", "translations": ["посещать", "призывать"],
     "definitions": [{"en": "to visit", "ru": "посетить"}], "is_separable": False},
    {"phrase": "call for", "base_verb": "call", "particle": "for", "translations": ["требовать", "заходить за"],
     "definitions": [{"en": "to require", "ru": "требовать"}], "is_separable": False},

    # HOLD phrasal verbs
    {"phrase": "hold on", "base_verb": "hold", "particle": "on", "translations": ["подождать", "держаться"],
     "definitions": [{"en": "to wait", "ru": "подождать"}], "is_separable": False},
    {"phrase": "hold up", "base_verb": "hold", "particle": "up", "translations": ["задерживать", "грабить"],
     "definitions": [{"en": "to delay", "ru": "задержать"}], "is_separable": True},
    {"phrase": "hold back", "base_verb": "hold", "particle": "back", "translations": ["сдерживать"],
     "definitions": [{"en": "to restrain", "ru": "сдержать"}], "is_separable": True},
    {"phrase": "hold out", "base_verb": "hold", "particle": "out", "translations": ["протягивать", "продержаться"],
     "definitions": [{"en": "to extend", "ru": "протянуть"}, {"en": "to resist", "ru": "продержаться"}], "is_separable": True},

    # KEEP phrasal verbs
    {"phrase": "keep on", "base_verb": "keep", "particle": "on", "translations": ["продолжать"],
     "definitions": [{"en": "to continue", "ru": "продолжать"}], "is_separable": False},
    {"phrase": "keep up", "base_verb": "keep", "particle": "up", "translations": ["поддерживать", "не отставать"],
     "definitions": [{"en": "to maintain", "ru": "поддерживать"}, {"en": "to stay at same level", "ru": "не отставать"}], "is_separable": True},
    {"phrase": "keep out", "base_verb": "keep", "particle": "out", "translations": ["не впускать"],
     "definitions": [{"en": "to prevent from entering", "ru": "не впускать"}], "is_separable": True},
    {"phrase": "keep away", "base_verb": "keep", "particle": "away", "translations": ["держаться подальше"],
     "definitions": [{"en": "to stay at a distance", "ru": "держаться подальше"}], "is_separable": True},
    {"phrase": "keep up with", "base_verb": "keep", "particle": "up with", "translations": ["не отставать от"],
     "definitions": [{"en": "to stay at same level as", "ru": "не отставать от"}], "is_separable": False},

    # CARRY phrasal verbs
    {"phrase": "carry on", "base_verb": "carry", "particle": "on", "translations": ["продолжать"],
     "definitions": [{"en": "to continue", "ru": "продолжать"}], "is_separable": False},
    {"phrase": "carry out", "base_verb": "carry", "particle": "out", "translations": ["выполнять", "проводить"],
     "definitions": [{"en": "to perform", "ru": "выполнить"}], "is_separable": True},
    {"phrase": "carry away", "base_verb": "carry", "particle": "away", "translations": ["уносить", "увлекать"],
     "definitions": [{"en": "to take away", "ru": "унести"}], "is_separable": True},

    # FILL phrasal verbs
    {"phrase": "fill in", "base_verb": "fill", "particle": "in", "translations": ["заполнять", "замещать"],
     "definitions": [{"en": "to complete a form", "ru": "заполнить форму"}], "is_separable": True},
    {"phrase": "fill out", "base_verb": "fill", "particle": "out", "translations": ["заполнять"],
     "definitions": [{"en": "to complete a form", "ru": "заполнить форму"}], "is_separable": True},
    {"phrase": "fill up", "base_verb": "fill", "particle": "up", "translations": ["наполнять", "заправлять"],
     "definitions": [{"en": "to make full", "ru": "наполнить"}], "is_separable": True},

    # FIGURE phrasal verbs
    {"phrase": "figure out", "base_verb": "figure", "particle": "out", "translations": ["понять", "разобраться"],
     "definitions": [{"en": "to understand", "ru": "понять, разобраться"}], "is_separable": True},

    # FIND phrasal verbs
    {"phrase": "find out", "base_verb": "find", "particle": "out", "translations": ["узнать", "выяснить"],
     "definitions": [{"en": "to discover", "ru": "узнать, выяснить"}], "is_separable": True},

    # POINT phrasal verbs
    {"phrase": "point out", "base_verb": "point", "particle": "out", "translations": ["указывать", "отмечать"],
     "definitions": [{"en": "to indicate", "ru": "указать на что-то"}], "is_separable": True},

    # SHOW phrasal verbs
    {"phrase": "show up", "base_verb": "show", "particle": "up", "translations": ["появляться", "приходить"],
     "definitions": [{"en": "to arrive", "ru": "появиться, прийти"}], "is_separable": False},
    {"phrase": "show off", "base_verb": "show", "particle": "off", "translations": ["хвастаться", "выставлять напоказ"],
     "definitions": [{"en": "to display proudly", "ru": "хвастаться"}], "is_separable": True},

    # HANG phrasal verbs
    {"phrase": "hang up", "base_verb": "hang", "particle": "up", "translations": ["вешать трубку", "вешать"],
     "definitions": [{"en": "to end phone call", "ru": "повесить трубку"}], "is_separable": True},
    {"phrase": "hang out", "base_verb": "hang", "particle": "out", "translations": ["проводить время", "тусоваться"],
     "definitions": [{"en": "to spend time casually", "ru": "проводить время"}], "is_separable": False},
    {"phrase": "hang on", "base_verb": "hang", "particle": "on", "translations": ["подождать", "держаться"],
     "definitions": [{"en": "to wait", "ru": "подождать"}], "is_separable": False},

    # THROW phrasal verbs
    {"phrase": "throw away", "base_verb": "throw", "particle": "away", "translations": ["выбрасывать"],
     "definitions": [{"en": "to discard", "ru": "выбросить"}], "is_separable": True},
    {"phrase": "throw out", "base_verb": "throw", "particle": "out", "translations": ["выбрасывать", "выгонять"],
     "definitions": [{"en": "to discard", "ru": "выбросить"}], "is_separable": True},
    {"phrase": "throw up", "base_verb": "throw", "particle": "up", "translations": ["рвать", "блевать"],
     "definitions": [{"en": "to vomit", "ru": "тошнить"}], "is_separable": False},

    # SORT phrasal verbs
    {"phrase": "sort out", "base_verb": "sort", "particle": "out", "translations": ["разбираться", "решать"],
     "definitions": [{"en": "to organize or resolve", "ru": "разобраться, решить"}], "is_separable": True},

    # STAND phrasal verbs
    {"phrase": "stand up", "base_verb": "stand", "particle": "up", "translations": ["вставать"],
     "definitions": [{"en": "to rise to standing position", "ru": "встать"}], "is_separable": False},
    {"phrase": "stand out", "base_verb": "stand", "particle": "out", "translations": ["выделяться"],
     "definitions": [{"en": "to be noticeable", "ru": "выделяться"}], "is_separable": False},
    {"phrase": "stand for", "base_verb": "stand", "particle": "for", "translations": ["означать", "отстаивать"],
     "definitions": [{"en": "to represent", "ru": "означать"}], "is_separable": False},

    # SIT phrasal verbs
    {"phrase": "sit down", "base_verb": "sit", "particle": "down", "translations": ["садиться"],
     "definitions": [{"en": "to take a seat", "ru": "сесть"}], "is_separable": False},
    {"phrase": "sit up", "base_verb": "sit", "particle": "up", "translations": ["садиться прямо", "не ложиться"],
     "definitions": [{"en": "to sit in upright position", "ru": "сесть прямо"}], "is_separable": False},

    # WAKE phrasal verbs
    {"phrase": "wake up", "base_verb": "wake", "particle": "up", "translations": ["просыпаться", "будить"],
     "definitions": [{"en": "to stop sleeping", "ru": "проснуться"}], "is_separable": True},

    # SHUT phrasal verbs
    {"phrase": "shut up", "base_verb": "shut", "particle": "up", "translations": ["замолчать", "заткнуться"],
     "definitions": [{"en": "to stop talking", "ru": "замолчать"}], "is_separable": False},
    {"phrase": "shut down", "base_verb": "shut", "particle": "down", "translations": ["закрывать", "выключать"],
     "definitions": [{"en": "to close permanently", "ru": "закрыть"}], "is_separable": True},

    # END phrasal verbs
    {"phrase": "end up", "base_verb": "end", "particle": "up", "translations": ["оказаться", "в итоге"],
     "definitions": [{"en": "to finally be in a situation", "ru": "в конце концов оказаться"}], "is_separable": False},

    # SLOW phrasal verbs
    {"phrase": "slow down", "base_verb": "slow", "particle": "down", "translations": ["замедлять"],
     "definitions": [{"en": "to reduce speed", "ru": "замедлиться"}], "is_separable": True},

    # SPEED phrasal verbs
    {"phrase": "speed up", "base_verb": "speed", "particle": "up", "translations": ["ускорять"],
     "definitions": [{"en": "to increase speed", "ru": "ускориться"}], "is_separable": True},

    # CLEAN phrasal verbs
    {"phrase": "clean up", "base_verb": "clean", "particle": "up", "translations": ["убирать", "приводить в порядок"],
     "definitions": [{"en": "to make tidy", "ru": "убрать, привести в порядок"}], "is_separable": True},

    # CHECK phrasal verbs
    {"phrase": "check in", "base_verb": "check", "particle": "in", "translations": ["регистрироваться"],
     "definitions": [{"en": "to register at hotel or airport", "ru": "зарегистрироваться"}], "is_separable": False},
    {"phrase": "check out", "base_verb": "check", "particle": "out", "translations": ["выписываться", "проверять"],
     "definitions": [{"en": "to leave hotel", "ru": "выписаться"}, {"en": "to examine", "ru": "проверить"}], "is_separable": True},

    # CALM phrasal verbs
    {"phrase": "calm down", "base_verb": "calm", "particle": "down", "translations": ["успокаиваться"],
     "definitions": [{"en": "to become less upset", "ru": "успокоиться"}], "is_separable": True},

    # CHEER phrasal verbs
    {"phrase": "cheer up", "base_verb": "cheer", "particle": "up", "translations": ["приободриться", "подбадривать"],
     "definitions": [{"en": "to become happier", "ru": "приободриться"}], "is_separable": True},

    # DRESS phrasal verbs
    {"phrase": "dress up", "base_verb": "dress", "particle": "up", "translations": ["наряжаться"],
     "definitions": [{"en": "to wear formal clothes", "ru": "нарядиться"}], "is_separable": False},

    # EAT phrasal verbs
    {"phrase": "eat out", "base_verb": "eat", "particle": "out", "translations": ["есть в ресторане"],
     "definitions": [{"en": "to eat at a restaurant", "ru": "есть в ресторане"}], "is_separable": False},

    # GROW phrasal verbs
    {"phrase": "grow up", "base_verb": "grow", "particle": "up", "translations": ["вырастать", "взрослеть"],
     "definitions": [{"en": "to become an adult", "ru": "вырасти, повзрослеть"}], "is_separable": False},

    # LOG phrasal verbs
    {"phrase": "log in", "base_verb": "log", "particle": "in", "translations": ["входить в систему"],
     "definitions": [{"en": "to enter a computer system", "ru": "войти в систему"}], "is_separable": False},
    {"phrase": "log out", "base_verb": "log", "particle": "out", "translations": ["выходить из системы"],
     "definitions": [{"en": "to exit a computer system", "ru": "выйти из системы"}], "is_separable": False},

    # PASS phrasal verbs
    {"phrase": "pass away", "base_verb": "pass", "particle": "away", "translations": ["умереть", "скончаться"],
     "definitions": [{"en": "to die (euphemism)", "ru": "умереть"}], "is_separable": False},
    {"phrase": "pass out", "base_verb": "pass", "particle": "out", "translations": ["терять сознание", "раздавать"],
     "definitions": [{"en": "to faint", "ru": "потерять сознание"}], "is_separable": True},

    # PAY phrasal verbs
    {"phrase": "pay back", "base_verb": "pay", "particle": "back", "translations": ["возвращать долг"],
     "definitions": [{"en": "to return money owed", "ru": "вернуть долг"}], "is_separable": True},
    {"phrase": "pay off", "base_verb": "pay", "particle": "off", "translations": ["выплачивать", "окупаться"],
     "definitions": [{"en": "to pay in full", "ru": "выплатить полностью"}], "is_separable": True},

    # PULL phrasal verbs
    {"phrase": "pull over", "base_verb": "pull", "particle": "over", "translations": ["остановиться (на обочине)"],
     "definitions": [{"en": "to stop vehicle at roadside", "ru": "остановиться на обочине"}], "is_separable": False},

    # WRITE phrasal verbs
    {"phrase": "write down", "base_verb": "write", "particle": "down", "translations": ["записывать"],
     "definitions": [{"en": "to write on paper", "ru": "записать"}], "is_separable": True},

    # CUT phrasal verbs
    {"phrase": "cut off", "base_verb": "cut", "particle": "off", "translations": ["отрезать", "прерывать"],
     "definitions": [{"en": "to remove by cutting", "ru": "отрезать"}], "is_separable": True},
    {"phrase": "cut down", "base_verb": "cut", "particle": "down", "translations": ["сокращать", "рубить"],
     "definitions": [{"en": "to reduce", "ru": "сократить"}], "is_separable": True},
    {"phrase": "cut out", "base_verb": "cut", "particle": "out", "translations": ["вырезать", "прекращать"],
     "definitions": [{"en": "to remove", "ru": "вырезать"}], "is_separable": True},

    # DROP phrasal verbs
    {"phrase": "drop off", "base_verb": "drop", "particle": "off", "translations": ["высаживать", "засыпать"],
     "definitions": [{"en": "to leave someone somewhere", "ru": "высадить"}], "is_separable": True},
    {"phrase": "drop by", "base_verb": "drop", "particle": "by", "translations": ["заходить"],
     "definitions": [{"en": "to visit informally", "ru": "зайти ненадолго"}], "is_separable": False},
    {"phrase": "drop out", "base_verb": "drop", "particle": "out", "translations": ["бросать (учёбу)"],
     "definitions": [{"en": "to quit school", "ru": "бросить учёбу"}], "is_separable": False},

    # BACK phrasal verbs
    {"phrase": "back up", "base_verb": "back", "particle": "up", "translations": ["поддерживать", "создавать резервную копию"],
     "definitions": [{"en": "to support", "ru": "поддержать"}, {"en": "to make a copy", "ru": "сделать резервную копию"}], "is_separable": True},

    # THINK phrasal verbs
    {"phrase": "think over", "base_verb": "think", "particle": "over", "translations": ["обдумывать"],
     "definitions": [{"en": "to consider carefully", "ru": "обдумать"}], "is_separable": True},
    {"phrase": "think up", "base_verb": "think", "particle": "up", "translations": ["придумывать"],
     "definitions": [{"en": "to invent", "ru": "придумать"}], "is_separable": True},

    # TRY phrasal verbs
    {"phrase": "try on", "base_verb": "try", "particle": "on", "translations": ["примерять"],
     "definitions": [{"en": "to test clothing", "ru": "примерить"}], "is_separable": True},
    {"phrase": "try out", "base_verb": "try", "particle": "out", "translations": ["пробовать", "испытывать"],
     "definitions": [{"en": "to test", "ru": "испробовать"}], "is_separable": True},

    # WIPE phrasal verbs
    {"phrase": "wipe out", "base_verb": "wipe", "particle": "out", "translations": ["уничтожать", "стирать"],
     "definitions": [{"en": "to destroy completely", "ru": "уничтожить"}], "is_separable": True},

    # WEAR phrasal verbs
    {"phrase": "wear out", "base_verb": "wear", "particle": "out", "translations": ["изнашивать", "утомлять"],
     "definitions": [{"en": "to damage by use", "ru": "износить"}], "is_separable": True},
]


class PhrasalVerbsLoader:
    """Loader for phrasal verbs from local data and GitHub datasets."""

    GITHUB_URL = (
        "https://raw.githubusercontent.com/Semigradsky/"
        "phrasal-verbs/master/src/phrasal-verbs.json"
    )

    def __init__(self):
        self._cache: Optional[list[dict]] = None

    def get_all_phrasal_verbs(self) -> list[dict]:
        """Get all phrasal verbs from local data.

        Returns list of dicts with keys:
        - phrase: full phrasal verb ("look up")
        - base_verb: base verb ("look")
        - particle: particle ("up")
        - translations: list of Russian translations
        - definitions: list of {en, ru} dicts
        - is_separable: bool
        """
        return PHRASAL_VERBS_DATA.copy()

    async def fetch_from_github(self) -> list[dict]:
        """Fetch additional phrasal verbs from GitHub dataset.

        Note: GitHub data may have different format, so we normalize.
        """
        if self._cache is not None:
            return self._cache

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.GITHUB_URL, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()
                    result = []

                    for item in data:
                        phrase = item.get("phrasal_verb", "")
                        parts = phrase.split()
                        base_verb = parts[0] if parts else ""
                        particle = " ".join(parts[1:]) if len(parts) > 1 else ""

                        result.append({
                            "phrase": phrase,
                            "base_verb": base_verb,
                            "particle": particle,
                            "translations": [],
                            "definitions": [
                                {"en": defn, "ru": ""} for defn in item.get("definitions", [])
                            ],
                            "is_separable": True,  # Default, would need manual verification
                        })

                    self._cache = result
                    return result

        except (aiohttp.ClientError, asyncio.TimeoutError):
            return []

    def get_phrasal_verbs_by_verb(self, base_verb: str) -> list[dict]:
        """Get all phrasal verbs with a specific base verb."""
        return [
            pv for pv in self.get_all_phrasal_verbs()
            if pv["base_verb"].lower() == base_verb.lower()
        ]

    def get_separable_phrasal_verbs(self) -> list[dict]:
        """Get only separable phrasal verbs."""
        return [pv for pv in self.get_all_phrasal_verbs() if pv["is_separable"]]

    def get_inseparable_phrasal_verbs(self) -> list[dict]:
        """Get only inseparable phrasal verbs."""
        return [pv for pv in self.get_all_phrasal_verbs() if not pv["is_separable"]]


# Synchronous wrapper
def get_phrasal_verbs() -> list[dict]:
    """Get all phrasal verbs synchronously."""
    loader = PhrasalVerbsLoader()
    return loader.get_all_phrasal_verbs()
