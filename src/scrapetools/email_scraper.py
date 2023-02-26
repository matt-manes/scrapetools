import re
from string import printable
from urllib.parse import unquote


def validate(email: str) -> bool:
    """Checks string to see if it's likely an email address.

    Returns True or False.

    Some emails violating some of these rules
    may technically be valid, but are practically
    never seen in use out in the wild."""
    if email.count("@") != 1 or email.count(".") == 0:
        return False
    atdex = email.find("@")
    last_dot = email.rfind(".")
    local, domain = email.split("@")
    # RULES:
    #'@' comes before the last '.'
    # local part is 64 characters or less
    # domain part doesn't contain any '_'
    # at least 1 character in local is alphabetical
    # 1st character is not '@' or '.'
    # last character is not '@' or '.'
    # character after '@' is not '.'
    # doesn't start with 'www.'
    # local is two or more characters
    # domain is more than 3 characters
    # domain doesn't consist of only numbers
    # local doesn't consist of only numbers
    # no consecutive '.' in email
    # email doesn't contain a listed file ext
    if all(
        [
            atdex < last_dot,
            len(local) <= 64,
            domain.count("_") == 0,
            any(ch.isalpha() for ch in local),
            email[0] not in ["@", "."],
            email[-1] not in ["@", "."],
            email[email.find("@") + 1] != ".",
            not email.startswith("www."),
            len(local) >= 2,
            len(domain) > 3,
            not all(ch.isnumeric() for ch in domain.replace(".", "")),
            not all(ch.isnumeric() for ch in local.replace(".", "")),
            all(email[i - 1] != "." for i, ch in enumerate(email) if ch == "."),
            all(
                ext not in domain
                for ext in [
                    ".png",
                    ".jpg",
                    ".js",
                    ".html",
                    ".svg",
                    ".jpeg",
                    ".mp4",
                    ".mpeg",
                    ".css",
                    ".pdf",
                    ".wav",
                    ".docx",
                    ".txt",
                    ".rtf",
                    ".gif",
                    ".webp",
                    ".x.x",
                ]
            ),
        ]
    ):
        return True
    else:
        return False


def find_last_valid_character_offset(text: str) -> int:
    """Iterates through a string to find the index of the last valid character,
    assuming that string either starts or ends with '@'.

    If the string doesn't start or end with '@', an Exception is raised.

    Returns the number of valid characters between '@' and first invalid character.
    e.g. '@abcde%' will return 5 and '#123@' will return 3.

    If no invalid characters are found, the function will return
    'len(text)-1'."""

    """ Technically some of these characters are valid in an email string,
    but the ratio of how often they're used to how often they produce
    false positives makes them worth disregarding. """
    invalid_characters = " <>[]{},\"':;\\/#$%^&*()=+`?|\n\t\r"
    if text[-1] == "@" and text[0] != "@":
        # reverse the string
        text = text[::-1]
    elif text[0] != "@":
        raise ValueError(
            'First or last character of text arg needs to be "@"\n',
            f"Argument {text} is invalid.",
        )
    i = 1
    while i < len(text):
        if text[i] in invalid_characters or text[i] not in printable:
            return i - 1
        else:
            i += 1
    return len(text) - 1


def strip_unicode(emails: list[str]) -> list[str]:
    """Removes unicode text that often gets picked
    up at the front of email addresses and returns the list."""
    stripped_emails = []
    for email in emails:
        for text in ["u003e", "u00a0"]:
            if text in email:
                email = email[len(text) :]
        stripped_emails.append(email)
    return stripped_emails


def scrape_emails_noregex(text: str) -> list[str]:
    """Extracts potential emails from given text
    and returns as a list of strings."""
    if "%" in text:
        # decode percent encoding
        text = unquote(text)
    for ch in ["\n", "\t", "\r"]:
        text = text.replace(ch, " ")
    at_count = text.count("@")
    emails = []
    if at_count > 0:
        last_stopdex = 0
        for i in range(at_count):
            atdex = text.find("@", last_stopdex)
            next_atdex = text.find("@", atdex + 1)
            try:
                chunk = (
                    text[last_stopdex:next_atdex]
                    if next_atdex != -1
                    else text[last_stopdex:]
                )
                chunk_atdex = chunk.find("@")
                startdex = find_last_valid_character_offset(chunk[: chunk_atdex + 1])
                stopdex = find_last_valid_character_offset(chunk[chunk_atdex:])
                email = chunk[chunk_atdex - startdex : stopdex + chunk_atdex + 1]
                while email[-1].isnumeric() or not email[-1].isalpha():
                    email = email[:-1]
                if validate(email):
                    emails.append(email.lower())
                """ The extra '+ 1' is to ensure last_stopdex increments
                if 'len(email.split('@')[1])' is 0."""
                last_stopdex = atdex + len(email.split("@")[1]) + 1
            except Exception as e:
                last_stopdex = atdex + 1
        emails = sorted(list(set(strip_unicode(emails))))
    return emails


def filter_out_files(
    emails: list[str], additional_extensions: list[str] = None
) -> list[str]:
    """Filter out emails with file extensions
    instead of domains.

    :param additional_extensions: Extra file extensions to filter out."""
    ext = [
        "png",
        "jpg",
        "js",
        "html",
        "svg",
        "jpeg",
        "mp4",
        "mpeg",
        "css",
        "pdf",
        "wav",
        "docx",
        "txt",
        "rtf",
        "gif",
        "webp",
        "x",
    ]
    if additional_extensions:
        ext.extend([extension.strip(".") for extension in additional_extensions])
    ignore = "$|".join(ext) + "$"
    pattern = r".*[.](?!" + ignore + r")[^.]*$"
    # Lazy evaluation means we can skip the regex overhead for common domains
    return [
        email
        for email in emails
        if email[email.rfind(".") + 1 :]
        in ["com", "org", "net", "us", "io", "edu", "gov", "biz"]
        or re.search(pattern, email.lower())
    ]


def replace_unicodehex(text: str) -> str:
    """Replace unicode hex strings (u003e etc.) with a space."""
    return re.sub(r"u00[a-zA-Z0-9]{2}", " ", text)


def scrape_emails(text: str, extra_extensions: list[str] = None) -> list[str]:
    """Extract emails from text using regex.

    :param text: The text to scrape.

    :param extra_extensions: Extra file extensions to filter out."""
    # Remove chunks with no "@" in them to reduce processing
    text = unquote(" ".join(chunk.lower() for chunk in text.split() if "@" in chunk))

    # Replace any % encoding or unicode hex strings with spaces
    text = replace_unicodehex(text)

    # Validation:
    # Starts with an alphanumeric character.
    # Local part consists of 1-63 alphanumeric + '._-' characters.
    # Contains a single '@' character not at the beginning or end of a string.
    # Domain consists of one or more alphanumeric + '_-' characters
    # followed by a '.' and one or more alphanumeric + '._-' characters
    # and ending in an alphabetical character.
    pattern = (
        r"[a-zA-Z0-9]{1}[a-zA-Z0-9._-]{1,63}@[a-zA-Z0-9_-]+\.[a-zA-Z0-9._-]+[a-zA-Z]{1}"
    )

    # Match pattern but throw out duplicates and anything that has only numbers in the local part of the address.
    emails = [
        email.lower()
        for email in set(re.findall(pattern, text))
        if not email.split("@")[0].isnumeric()
    ]
    # Remove anything that looks like a file and sort the final results
    return sorted(filter_out_files(emails))
