import re


def replace_all(text):
    # Replace all non word characters
    text = text.replace(" ", "")
    return re.sub("\\W|_", "-", text)


def remove_multiple_hyphens(string):
    # make sure no double hyphens, AWS won't allow
    cleaned = re.sub(r"-+", "-", string)
    return cleaned


def clean_name_string(raw_string, truncate_len=40):
    cleaned = replace_all(raw_string).lower()
    cleaned = cleaned.strip("-")
    cleaned = remove_multiple_hyphens(cleaned)

    if len(cleaned) > truncate_len:
        truncated = cleaned[:truncate_len].strip("-")
    else:
        truncated = cleaned

    return truncated
