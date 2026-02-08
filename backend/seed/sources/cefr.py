from backend.seed.config import rank_to_cefr


def assign_cefr_levels(words: list[str]) -> dict[str, str]:
    return {word: rank_to_cefr(rank) for rank, word in enumerate(words, 1)}
