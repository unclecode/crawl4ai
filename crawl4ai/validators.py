import re


class ValidationException(ValueError):
    def __init__(self, input, validator):
        ValueError.__init__(self, f"Input failed {validator} validation: {input}")

class BaseValidator:
    """
    Check the input against a regex and raise a ValidationException if it fails.
    """

    def __init__(self, regex, validator=None, flags=0):
        if isinstance(regex, str):
            self.match_object = re.compile(regex, flags)
        else:
            self.match_object = regex
        self.validator = validator

    def validate(self, value):
        """
        Validate the input against the regex. If it fails, raise a ValidationException.
        """
        if self.match_object.match(value) is None:
            raise ValidationException(value, self.validator)


class URLValidator(BaseValidator):
    """
    Check if the input is a valid URL.
    """

    def __init__(self):
        regex = (
            # {http,ftp}s:// (not required)
            r"^((?:http|ftp)s?://)?"
            # Domain
            r"(?:"
            r"(?:[A-Z0-9](?:[_A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
            r"(?:[A-Z]{2,6}\.?|[_A-Z0-9-]{2,}\.?)|"
            # Localhost
            r"localhost|"
            # IPv6 address
            r"\[[a-f0-9:]+\]|"
            # IPv4 address
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
            r")"
            # Optional port
            r"(?::\d+)?"
            # Path
            r"(?:/?|[/?#]\S+)$"
        )
        super(URLValidator, self).__init__(regex, "url", flags=re.IGNORECASE)

class SSLURLValidator(BaseValidator):
    """
    Check if the input is a valid SSL URL.
    """

    def __init__(self):
        regex = (
            # https:// (required)
            r"^(https?://)"
            # Domain
            r"(?:"
            r"(?:[A-Z0-9](?:[_A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
            r"(?:[A-Z]{2,6}\.?|[_A-Z0-9-]{2,}\.?)|"
            # Localhost
            r"localhost|"
            # IPv6 address
            r"\[[a-f0-9:]+\]|"
            # IPv4 address
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
            r")"
            # Optional port
            r"(?::\d+)?"
            # Path
            r"(?:/?|[/?#]\S+)$"
        )
        super(SSLURLValidator, self).__init__(regex, "ssl_url", flags=re.IGNORECASE)



class ProxyValidator(BaseValidator):
    """
    Check if the input is a valid proxy string.
    """

    def __init__(self):
        regex = (
            # proxy scheme
            r"^((?:https?|socks[45])://)"
            # Username and password
            r"(?:\S+(?::\S*)?@)?"
            # Domain
            r"(?:"
            r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
            r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
            # Localhost
            r"localhost|"
            # IPv6 address
            r"\[[a-f0-9:]+\]|"
            # IPv4 address
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
            r")"
            # port
            r"(?::\d+)$"
        )
        super(ProxyValidator, self).__init__(regex, "proxy", re.IGNORECASE)
