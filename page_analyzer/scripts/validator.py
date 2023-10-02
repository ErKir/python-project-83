import validators


def is_valid_url(url):
    errors = []
    valid_url = validators.url(url)
    valid_len_url = validators.length(url, max=255)
    if isinstance(valid_url, validators.ValidationFailure):
        errors.append('Invalid URL!')
    if isinstance(valid_len_url, validators.ValidationFailure):
        errors.append('Maximum address length exceeded!')
    return errors
