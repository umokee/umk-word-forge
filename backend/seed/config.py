from pathlib import Path

SEED_DATA_DIR = Path(__file__).parent / "data"
SEED_DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_WORD_COUNT = 5000
IPA_DICT_URL = "https://raw.githubusercontent.com/open-dict-data/ipa-dict/master/data/en_US.txt"
TATOEBA_EN_RU_URL = "https://downloads.tatoeba.org/exports/sentences.tar.bz2"

CEFR_RANK_MAP = {
    500: "A1",
    1500: "A2",
    3000: "B1",
    5000: "B2",
    8000: "C1",
}


def rank_to_cefr(rank: int) -> str:
    for threshold, level in sorted(CEFR_RANK_MAP.items()):
        if rank <= threshold:
            return level
    return "C2"
