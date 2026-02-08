from wordfreq import top_n_list


def get_top_words(count: int = 5000) -> list[str]:
    return top_n_list("en", count)
