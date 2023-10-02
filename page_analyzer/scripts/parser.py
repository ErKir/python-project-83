from urllib.parse import urlparse, urlunsplit


def parse_url(data):
    url_obj = urlparse(data['url'])
    return urlunsplit((url_obj.scheme, url_obj.netloc, '', '', '',))
