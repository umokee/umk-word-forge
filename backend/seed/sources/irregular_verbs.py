"""Loader for irregular verbs from GitHub dataset and local data."""

import asyncio
import aiohttp
from typing import Optional


# Core irregular verbs with translations (most common ~200)
IRREGULAR_VERBS_DATA: list[dict] = [
    # Pattern ABC (all different): go-went-gone
    {"base": "be", "past": "was/were", "participle": "been", "translations": ["быть"], "pattern": "ABC"},
    {"base": "go", "past": "went", "participle": "gone", "translations": ["идти", "ехать"], "pattern": "ABC"},
    {"base": "do", "past": "did", "participle": "done", "translations": ["делать"], "pattern": "ABC"},
    {"base": "see", "past": "saw", "participle": "seen", "translations": ["видеть"], "pattern": "ABC"},
    {"base": "take", "past": "took", "participle": "taken", "translations": ["брать", "взять"], "pattern": "ABC"},
    {"base": "give", "past": "gave", "participle": "given", "translations": ["давать"], "pattern": "ABC"},
    {"base": "know", "past": "knew", "participle": "known", "translations": ["знать"], "pattern": "ABC"},
    {"base": "come", "past": "came", "participle": "come", "translations": ["приходить"], "pattern": "ABA"},
    {"base": "eat", "past": "ate", "participle": "eaten", "translations": ["есть", "кушать"], "pattern": "ABC"},
    {"base": "drink", "past": "drank", "participle": "drunk", "translations": ["пить"], "pattern": "ABC"},
    {"base": "begin", "past": "began", "participle": "begun", "translations": ["начинать"], "pattern": "ABC"},
    {"base": "sing", "past": "sang", "participle": "sung", "translations": ["петь"], "pattern": "ABC"},
    {"base": "swim", "past": "swam", "participle": "swum", "translations": ["плавать"], "pattern": "ABC"},
    {"base": "ring", "past": "rang", "participle": "rung", "translations": ["звонить"], "pattern": "ABC"},
    {"base": "write", "past": "wrote", "participle": "written", "translations": ["писать"], "pattern": "ABC"},
    {"base": "drive", "past": "drove", "participle": "driven", "translations": ["водить", "ехать"], "pattern": "ABC"},
    {"base": "rise", "past": "rose", "participle": "risen", "translations": ["подниматься"], "pattern": "ABC"},
    {"base": "ride", "past": "rode", "participle": "ridden", "translations": ["ездить верхом"], "pattern": "ABC"},
    {"base": "speak", "past": "spoke", "participle": "spoken", "translations": ["говорить"], "pattern": "ABC"},
    {"base": "break", "past": "broke", "participle": "broken", "translations": ["ломать"], "pattern": "ABC"},
    {"base": "choose", "past": "chose", "participle": "chosen", "translations": ["выбирать"], "pattern": "ABC"},
    {"base": "freeze", "past": "froze", "participle": "frozen", "translations": ["замерзать"], "pattern": "ABC"},
    {"base": "steal", "past": "stole", "participle": "stolen", "translations": ["красть"], "pattern": "ABC"},
    {"base": "wake", "past": "woke", "participle": "woken", "translations": ["просыпаться"], "pattern": "ABC"},
    {"base": "wear", "past": "wore", "participle": "worn", "translations": ["носить (одежду)"], "pattern": "ABC"},
    {"base": "tear", "past": "tore", "participle": "torn", "translations": ["рвать"], "pattern": "ABC"},
    {"base": "bear", "past": "bore", "participle": "born/borne", "translations": ["нести", "рожать"], "pattern": "ABC"},
    {"base": "swear", "past": "swore", "participle": "sworn", "translations": ["клясться"], "pattern": "ABC"},
    {"base": "fly", "past": "flew", "participle": "flown", "translations": ["летать"], "pattern": "ABC"},
    {"base": "grow", "past": "grew", "participle": "grown", "translations": ["расти"], "pattern": "ABC"},
    {"base": "throw", "past": "threw", "participle": "thrown", "translations": ["бросать"], "pattern": "ABC"},
    {"base": "blow", "past": "blew", "participle": "blown", "translations": ["дуть"], "pattern": "ABC"},
    {"base": "draw", "past": "drew", "participle": "drawn", "translations": ["рисовать"], "pattern": "ABC"},
    {"base": "show", "past": "showed", "participle": "shown", "translations": ["показывать"], "pattern": "ABB"},
    {"base": "fall", "past": "fell", "participle": "fallen", "translations": ["падать"], "pattern": "ABC"},
    {"base": "forget", "past": "forgot", "participle": "forgotten", "translations": ["забывать"], "pattern": "ABC"},
    {"base": "hide", "past": "hid", "participle": "hidden", "translations": ["прятать"], "pattern": "ABC"},
    {"base": "bite", "past": "bit", "participle": "bitten", "translations": ["кусать"], "pattern": "ABC"},
    {"base": "shake", "past": "shook", "participle": "shaken", "translations": ["трясти"], "pattern": "ABC"},
    {"base": "mistake", "past": "mistook", "participle": "mistaken", "translations": ["ошибаться"], "pattern": "ABC"},
    {"base": "lie", "past": "lay", "participle": "lain", "translations": ["лежать"], "pattern": "ABC"},

    # Pattern ABB (past = participle): buy-bought-bought
    {"base": "have", "past": "had", "participle": "had", "translations": ["иметь"], "pattern": "ABB"},
    {"base": "make", "past": "made", "participle": "made", "translations": ["делать", "создавать"], "pattern": "ABB"},
    {"base": "say", "past": "said", "participle": "said", "translations": ["говорить", "сказать"], "pattern": "ABB"},
    {"base": "get", "past": "got", "participle": "got/gotten", "translations": ["получать"], "pattern": "ABB"},
    {"base": "find", "past": "found", "participle": "found", "translations": ["находить"], "pattern": "ABB"},
    {"base": "think", "past": "thought", "participle": "thought", "translations": ["думать"], "pattern": "ABB"},
    {"base": "tell", "past": "told", "participle": "told", "translations": ["рассказывать"], "pattern": "ABB"},
    {"base": "feel", "past": "felt", "participle": "felt", "translations": ["чувствовать"], "pattern": "ABB"},
    {"base": "leave", "past": "left", "participle": "left", "translations": ["уходить", "оставлять"], "pattern": "ABB"},
    {"base": "bring", "past": "brought", "participle": "brought", "translations": ["приносить"], "pattern": "ABB"},
    {"base": "buy", "past": "bought", "participle": "bought", "translations": ["покупать"], "pattern": "ABB"},
    {"base": "teach", "past": "taught", "participle": "taught", "translations": ["учить", "преподавать"], "pattern": "ABB"},
    {"base": "catch", "past": "caught", "participle": "caught", "translations": ["ловить"], "pattern": "ABB"},
    {"base": "fight", "past": "fought", "participle": "fought", "translations": ["бороться", "драться"], "pattern": "ABB"},
    {"base": "seek", "past": "sought", "participle": "sought", "translations": ["искать"], "pattern": "ABB"},
    {"base": "keep", "past": "kept", "participle": "kept", "translations": ["держать", "хранить"], "pattern": "ABB"},
    {"base": "sleep", "past": "slept", "participle": "slept", "translations": ["спать"], "pattern": "ABB"},
    {"base": "sweep", "past": "swept", "participle": "swept", "translations": ["подметать"], "pattern": "ABB"},
    {"base": "weep", "past": "wept", "participle": "wept", "translations": ["плакать"], "pattern": "ABB"},
    {"base": "creep", "past": "crept", "participle": "crept", "translations": ["ползти"], "pattern": "ABB"},
    {"base": "leap", "past": "leapt", "participle": "leapt", "translations": ["прыгать"], "pattern": "ABB"},
    {"base": "meet", "past": "met", "participle": "met", "translations": ["встречать"], "pattern": "ABB"},
    {"base": "lead", "past": "led", "participle": "led", "translations": ["вести"], "pattern": "ABB"},
    {"base": "feed", "past": "fed", "participle": "fed", "translations": ["кормить"], "pattern": "ABB"},
    {"base": "bleed", "past": "bled", "participle": "bled", "translations": ["кровоточить"], "pattern": "ABB"},
    {"base": "breed", "past": "bred", "participle": "bred", "translations": ["разводить"], "pattern": "ABB"},
    {"base": "speed", "past": "sped", "participle": "sped", "translations": ["мчаться"], "pattern": "ABB"},
    {"base": "read", "past": "read", "participle": "read", "translations": ["читать"], "pattern": "AAA"},
    {"base": "hear", "past": "heard", "participle": "heard", "translations": ["слышать"], "pattern": "ABB"},
    {"base": "hold", "past": "held", "participle": "held", "translations": ["держать"], "pattern": "ABB"},
    {"base": "stand", "past": "stood", "participle": "stood", "translations": ["стоять"], "pattern": "ABB"},
    {"base": "understand", "past": "understood", "participle": "understood", "translations": ["понимать"], "pattern": "ABB"},
    {"base": "lose", "past": "lost", "participle": "lost", "translations": ["терять"], "pattern": "ABB"},
    {"base": "shoot", "past": "shot", "participle": "shot", "translations": ["стрелять"], "pattern": "ABB"},
    {"base": "sell", "past": "sold", "participle": "sold", "translations": ["продавать"], "pattern": "ABB"},
    {"base": "win", "past": "won", "participle": "won", "translations": ["выигрывать"], "pattern": "ABB"},
    {"base": "spin", "past": "spun", "participle": "spun", "translations": ["крутить"], "pattern": "ABB"},
    {"base": "hang", "past": "hung", "participle": "hung", "translations": ["вешать"], "pattern": "ABB"},
    {"base": "dig", "past": "dug", "participle": "dug", "translations": ["копать"], "pattern": "ABB"},
    {"base": "stick", "past": "stuck", "participle": "stuck", "translations": ["приклеивать"], "pattern": "ABB"},
    {"base": "strike", "past": "struck", "participle": "struck", "translations": ["ударять"], "pattern": "ABB"},
    {"base": "swing", "past": "swung", "participle": "swung", "translations": ["качаться"], "pattern": "ABB"},
    {"base": "cling", "past": "clung", "participle": "clung", "translations": ["цепляться"], "pattern": "ABB"},
    {"base": "fling", "past": "flung", "participle": "flung", "translations": ["швырять"], "pattern": "ABB"},
    {"base": "sling", "past": "slung", "participle": "slung", "translations": ["бросать"], "pattern": "ABB"},
    {"base": "sting", "past": "stung", "participle": "stung", "translations": ["жалить"], "pattern": "ABB"},
    {"base": "wring", "past": "wrung", "participle": "wrung", "translations": ["выжимать"], "pattern": "ABB"},
    {"base": "sit", "past": "sat", "participle": "sat", "translations": ["сидеть"], "pattern": "ABB"},
    {"base": "spit", "past": "spat", "participle": "spat", "translations": ["плевать"], "pattern": "ABB"},
    {"base": "light", "past": "lit", "participle": "lit", "translations": ["зажигать"], "pattern": "ABB"},
    {"base": "slide", "past": "slid", "participle": "slid", "translations": ["скользить"], "pattern": "ABB"},
    {"base": "lay", "past": "laid", "participle": "laid", "translations": ["класть"], "pattern": "ABB"},
    {"base": "pay", "past": "paid", "participle": "paid", "translations": ["платить"], "pattern": "ABB"},
    {"base": "send", "past": "sent", "participle": "sent", "translations": ["отправлять"], "pattern": "ABB"},
    {"base": "spend", "past": "spent", "participle": "spent", "translations": ["тратить"], "pattern": "ABB"},
    {"base": "lend", "past": "lent", "participle": "lent", "translations": ["одалживать"], "pattern": "ABB"},
    {"base": "bend", "past": "bent", "participle": "bent", "translations": ["сгибать"], "pattern": "ABB"},
    {"base": "build", "past": "built", "participle": "built", "translations": ["строить"], "pattern": "ABB"},
    {"base": "burn", "past": "burnt", "participle": "burnt", "translations": ["гореть", "жечь"], "pattern": "ABB"},
    {"base": "learn", "past": "learnt", "participle": "learnt", "translations": ["учить", "узнавать"], "pattern": "ABB"},
    {"base": "smell", "past": "smelt", "participle": "smelt", "translations": ["пахнуть", "нюхать"], "pattern": "ABB"},
    {"base": "spell", "past": "spelt", "participle": "spelt", "translations": ["писать по буквам"], "pattern": "ABB"},
    {"base": "spill", "past": "spilt", "participle": "spilt", "translations": ["проливать"], "pattern": "ABB"},
    {"base": "spoil", "past": "spoilt", "participle": "spoilt", "translations": ["портить"], "pattern": "ABB"},
    {"base": "dream", "past": "dreamt", "participle": "dreamt", "translations": ["мечтать", "видеть сны"], "pattern": "ABB"},
    {"base": "mean", "past": "meant", "participle": "meant", "translations": ["значить", "иметь в виду"], "pattern": "ABB"},
    {"base": "deal", "past": "dealt", "participle": "dealt", "translations": ["иметь дело"], "pattern": "ABB"},
    {"base": "kneel", "past": "knelt", "participle": "knelt", "translations": ["становиться на колени"], "pattern": "ABB"},
    {"base": "shine", "past": "shone", "participle": "shone", "translations": ["светить"], "pattern": "ABB"},
    {"base": "bind", "past": "bound", "participle": "bound", "translations": ["связывать"], "pattern": "ABB"},
    {"base": "find", "past": "found", "participle": "found", "translations": ["находить"], "pattern": "ABB"},
    {"base": "grind", "past": "ground", "participle": "ground", "translations": ["молоть"], "pattern": "ABB"},
    {"base": "wind", "past": "wound", "participle": "wound", "translations": ["заводить (часы)"], "pattern": "ABB"},

    # Pattern AAA (all same): cut-cut-cut
    {"base": "cut", "past": "cut", "participle": "cut", "translations": ["резать"], "pattern": "AAA"},
    {"base": "put", "past": "put", "participle": "put", "translations": ["класть"], "pattern": "AAA"},
    {"base": "set", "past": "set", "participle": "set", "translations": ["устанавливать"], "pattern": "AAA"},
    {"base": "let", "past": "let", "participle": "let", "translations": ["позволять"], "pattern": "AAA"},
    {"base": "shut", "past": "shut", "participle": "shut", "translations": ["закрывать"], "pattern": "AAA"},
    {"base": "hit", "past": "hit", "participle": "hit", "translations": ["ударять"], "pattern": "AAA"},
    {"base": "hurt", "past": "hurt", "participle": "hurt", "translations": ["причинять боль"], "pattern": "AAA"},
    {"base": "cost", "past": "cost", "participle": "cost", "translations": ["стоить"], "pattern": "AAA"},
    {"base": "burst", "past": "burst", "participle": "burst", "translations": ["лопаться"], "pattern": "AAA"},
    {"base": "cast", "past": "cast", "participle": "cast", "translations": ["бросать"], "pattern": "AAA"},
    {"base": "split", "past": "split", "participle": "split", "translations": ["расщеплять"], "pattern": "AAA"},
    {"base": "quit", "past": "quit", "participle": "quit", "translations": ["бросать", "уходить"], "pattern": "AAA"},
    {"base": "rid", "past": "rid", "participle": "rid", "translations": ["избавлять"], "pattern": "AAA"},
    {"base": "spread", "past": "spread", "participle": "spread", "translations": ["распространять"], "pattern": "AAA"},
    {"base": "shed", "past": "shed", "participle": "shed", "translations": ["проливать (слёзы)"], "pattern": "AAA"},
    {"base": "bet", "past": "bet", "participle": "bet", "translations": ["делать ставку"], "pattern": "AAA"},

    # Pattern ABA (base = participle): come-came-come
    {"base": "become", "past": "became", "participle": "become", "translations": ["становиться"], "pattern": "ABA"},
    {"base": "run", "past": "ran", "participle": "run", "translations": ["бежать"], "pattern": "ABA"},
    {"base": "overcome", "past": "overcame", "participle": "overcome", "translations": ["преодолевать"], "pattern": "ABA"},
]


class IrregularVerbsLoader:
    """Loader for irregular verbs from local data and GitHub datasets."""

    GITHUB_URL = (
        "https://raw.githubusercontent.com/WithEnglishWeCan/"
        "generated-english-irregular-verbs/master/verbs.json"
    )

    def __init__(self):
        self._cache: Optional[list[dict]] = None

    def get_all_verbs(self) -> list[dict]:
        """Get all irregular verbs from local data.

        Returns list of dicts with keys:
        - base: base form (infinitive)
        - past: past simple form
        - participle: past participle
        - translations: list of Russian translations
        - pattern: verb pattern (ABC, ABB, AAA, ABA)
        """
        return IRREGULAR_VERBS_DATA.copy()

    async def fetch_from_github(self) -> list[dict]:
        """Fetch additional verbs from GitHub dataset.

        Note: GitHub data may not have translations, so we merge with local data.
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
                        result.append({
                            "base": item.get("base", ""),
                            "past": item.get("past", ""),
                            "participle": item.get("pastParticiple", ""),
                            "translations": [],
                            "pattern": self._detect_pattern(
                                item.get("base", ""),
                                item.get("past", ""),
                                item.get("pastParticiple", ""),
                            ),
                        })

                    self._cache = result
                    return result

        except (aiohttp.ClientError, asyncio.TimeoutError):
            return []

    def _detect_pattern(self, base: str, past: str, participle: str) -> str:
        """Detect verb pattern from forms."""
        base = base.lower()
        past = past.lower().split("/")[0]  # Handle "was/were"
        participle = participle.lower().split("/")[0]  # Handle "got/gotten"

        if base == past == participle:
            return "AAA"
        elif base == participle:
            return "ABA"
        elif past == participle:
            return "ABB"
        else:
            return "ABC"

    def get_verbs_by_pattern(self, pattern: str) -> list[dict]:
        """Get verbs matching a specific pattern."""
        return [v for v in self.get_all_verbs() if v["pattern"] == pattern]


# Synchronous wrapper
def get_irregular_verbs() -> list[dict]:
    """Get all irregular verbs synchronously."""
    loader = IrregularVerbsLoader()
    return loader.get_all_verbs()
