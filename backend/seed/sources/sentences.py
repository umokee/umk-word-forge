BASIC_SENTENCES: dict[str, list[dict]] = {
    "time": [
        {"en": "I don't have much time.", "ru": "У меня мало времени.", "difficulty": 1},
        {"en": "What time is it?", "ru": "Который час?", "difficulty": 1},
        {"en": "Time flies when you're having fun.", "ru": "Время летит, когда весело.", "difficulty": 2},
    ],
    "people": [
        {"en": "Many people live in this city.", "ru": "Много людей живёт в этом городе.", "difficulty": 1},
        {"en": "People often forget important things.", "ru": "Люди часто забывают важные вещи.", "difficulty": 2},
    ],
    "good": [
        {"en": "This is a good book.", "ru": "Это хорошая книга.", "difficulty": 1},
        {"en": "She is a good teacher.", "ru": "Она хороший учитель.", "difficulty": 1},
    ],
    "make": [
        {"en": "I want to make a cake.", "ru": "Я хочу сделать торт.", "difficulty": 1},
        {"en": "Don't make noise.", "ru": "Не шуми.", "difficulty": 1},
    ],
    "know": [
        {"en": "I know the answer.", "ru": "Я знаю ответ.", "difficulty": 1},
        {"en": "Do you know this person?", "ru": "Ты знаешь этого человека?", "difficulty": 1},
    ],
    "take": [
        {"en": "Please take a seat.", "ru": "Пожалуйста, садитесь.", "difficulty": 1},
        {"en": "I need to take the bus.", "ru": "Мне нужно сесть на автобус.", "difficulty": 1},
    ],
    "work": [
        {"en": "I work in an office.", "ru": "Я работаю в офисе.", "difficulty": 1},
        {"en": "Hard work always pays off.", "ru": "Тяжёлый труд всегда окупается.", "difficulty": 2},
    ],
    "think": [
        {"en": "I think you are right.", "ru": "Я думаю, ты прав.", "difficulty": 1},
        {"en": "Think before you speak.", "ru": "Думай, прежде чем говоришь.", "difficulty": 1},
    ],
    "come": [
        {"en": "Come here, please.", "ru": "Иди сюда, пожалуйста.", "difficulty": 1},
        {"en": "Spring has come.", "ru": "Пришла весна.", "difficulty": 1},
    ],
    "look": [
        {"en": "Look at this picture.", "ru": "Посмотри на эту картину.", "difficulty": 1},
        {"en": "You look happy today.", "ru": "Ты выглядишь счастливым сегодня.", "difficulty": 1},
    ],
    "want": [
        {"en": "I want to learn English.", "ru": "Я хочу выучить английский.", "difficulty": 1},
        {"en": "What do you want for dinner?", "ru": "Что ты хочешь на ужин?", "difficulty": 1},
    ],
    "give": [
        {"en": "Give me a moment.", "ru": "Дай мне минутку.", "difficulty": 1},
        {"en": "She gave him a gift.", "ru": "Она подарила ему подарок.", "difficulty": 1},
    ],
    "use": [
        {"en": "I use this app every day.", "ru": "Я использую это приложение каждый день.", "difficulty": 1},
        {"en": "Can I use your phone?", "ru": "Можно мне использовать твой телефон?", "difficulty": 1},
    ],
    "find": [
        {"en": "I can't find my keys.", "ru": "Я не могу найти свои ключи.", "difficulty": 1},
        {"en": "Did you find the answer?", "ru": "Ты нашёл ответ?", "difficulty": 1},
    ],
    "tell": [
        {"en": "Tell me the truth.", "ru": "Скажи мне правду.", "difficulty": 1},
        {"en": "Can you tell me the way?", "ru": "Можешь подсказать дорогу?", "difficulty": 1},
    ],
    "help": [
        {"en": "Can you help me?", "ru": "Можешь мне помочь?", "difficulty": 1},
        {"en": "I need your help.", "ru": "Мне нужна твоя помощь.", "difficulty": 1},
    ],
    "learn": [
        {"en": "I want to learn new words.", "ru": "Я хочу учить новые слова.", "difficulty": 1},
        {"en": "We learn from our mistakes.", "ru": "Мы учимся на своих ошибках.", "difficulty": 2},
    ],
    "solve": [
        {"en": "I need to solve this problem.", "ru": "Мне нужно решить эту проблему.", "difficulty": 1},
        {"en": "Can you solve this puzzle?", "ru": "Можешь решить эту головоломку?", "difficulty": 2},
    ],
    "love": [
        {"en": "I love my family.", "ru": "Я люблю свою семью.", "difficulty": 1},
        {"en": "She loves reading books.", "ru": "Она любит читать книги.", "difficulty": 1},
    ],
    "play": [
        {"en": "Children love to play outside.", "ru": "Дети любят играть на улице.", "difficulty": 1},
        {"en": "Do you play the guitar?", "ru": "Ты играешь на гитаре?", "difficulty": 1},
    ],
}


def _generate_template_sentences(word: str, pos: str = "noun") -> list[dict]:
    """Generate template sentences - DISABLED, AI should generate contexts instead.

    Returns empty list so words without predefined contexts will get AI-generated ones.
    """
    # Don't generate awful templates like "This is a to."
    # AI will generate proper contexts when the word is shown
    return []


def get_sentences_for_word(word: str, pos: str = "noun") -> list[dict]:
    """Get example sentences for a word, with fallback to templates."""
    sentences = BASIC_SENTENCES.get(word.lower(), [])
    if not sentences:
        # Generate template sentences if no predefined ones
        sentences = _generate_template_sentences(word, pos)
    return sentences


def get_all_sentences() -> dict[str, list[dict]]:
    return BASIC_SENTENCES
