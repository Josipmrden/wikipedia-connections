from typing import List


def find_begin(context, current_index) -> int:
    try:
        for i in range(current_index - 1, -1, -1):
            child = context[i]
            if isinstance(child, str) and is_end_of_sentence(child):
                return i
    except Exception as e:
        return 0

    return 0


def find_end(context, current_index) -> int:
    try:
        for i in range(current_index + 1, len(context)):
            child = context[i]
            if isinstance(child, str) and is_end_of_sentence(child):
                return i
    except Exception as e:
        return len(context) - 1

    return len(context) - 1


def is_end_of_sentence(context: str) -> bool:
    return "." in context or "?" in context or "!" in context


def form_sentence(context: List[str], begin: int, end: int) -> str:
    begin_part = context[begin]
    end_part = context[end]

    begin_idx = find_index_of_ending_delimiter(begin_part)
    begin_idx = 0 if begin_idx == -1 else begin_idx + 1
    begin_str = begin_part[begin_idx:]

    end_idx = find_index_of_ending_delimiter(end_part)
    end_idx = len(end_part) - 2 if end_idx == -1 else end_idx
    end_str = end_part[: end_idx + 1]

    stripped_context = context[begin + 1 : end]

    sentence = begin_str + "".join(stripped_context) + end_str
    return clean_text(sentence)


def find_index_of_ending_delimiter(text: str) -> int:
    for i, c in enumerate(text):
        if is_end_of_sentence(c):
            return i

    return -1

def clean_text(text: str) -> str:
    result = text.replace("\n", "").strip()
    return result