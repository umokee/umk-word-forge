import httpx
from pathlib import Path
from backend.seed.config import SEED_DATA_DIR, IPA_DICT_URL


def load_ipa_dict() -> dict[str, str]:
    cache_file = SEED_DATA_DIR / "ipa_en_us.txt"

    if not cache_file.exists():
        print("Downloading IPA dictionary...")
        resp = httpx.get(IPA_DICT_URL, timeout=60)
        resp.raise_for_status()
        cache_file.write_text(resp.text, encoding="utf-8")
        print(f"Saved IPA dictionary to {cache_file}")

    ipa_dict = {}
    for line in cache_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "\t" not in line:
            continue
        parts = line.split("\t", 1)
        if len(parts) == 2:
            word = parts[0].strip().lower()
            ipa = parts[1].strip()
            if "," in ipa:
                ipa = ipa.split(",")[0].strip()
            ipa_dict[word] = ipa
    return ipa_dict
