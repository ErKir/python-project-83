import validators


def is_valid_url(url):
    valid_url = validators.url(url)
    valid_len_url = validators.length(url, max=255)
    if (valid_len_url and valid_url):
        return True
    return False
