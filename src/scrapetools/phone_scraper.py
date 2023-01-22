import phonenumbers


def get_num_consecutive_numbers(text: str, reverse: bool = False) -> int:
    """Finds the number of consecutive numeric characters in a string."""
    # limit search to 10 characters
    text[:10]
    if reverse:
        text = text[::-1]
    for i, ch in enumerate(text):
        if not ch.isnumeric():
            return i
    return len(text)


def find_by_separator(text: str, separator: str) -> list[str]:
    """Attempts to detect phone numbers according to these
    patterns by scanning for separators (typically '-.')
    and how many consecutive numbers follow or precede them:

    (xxx)xxx{separator}xxxx

    (xxx) xxx{separator}xxxx

    (xxx){separator}xxx{separator}xxxx

    xxx{separator}xxx{separator}xxxx"""
    count = text.count(separator)
    numbers = []
    if count > 0:
        last_stopdex = 0
        for _ in range(count):
            number = ""
            sepdex = text.find(separator, last_stopdex)
            if sepdex != -1:
                next_sepdex = text.find(separator, sepdex + 1)
                # consecutive numbers preceding sepdex
                start_offset = get_num_consecutive_numbers(
                    text[last_stopdex:sepdex], reverse=True
                )
                # consecutive numbers between sepdex and next_sepdex
                first_stop_offset = get_num_consecutive_numbers(
                    text[sepdex + 1 : next_sepdex + 1]
                )
                # consecutive numbers after next_sepdex
                second_stop_offset = get_num_consecutive_numbers(
                    text[next_sepdex + 1 :]
                )

                if (
                    start_offset == 3
                    and first_stop_offset == 3
                    and second_stop_offset == 4
                ):
                    # xxx{separator}xxx{separator}xxxx
                    number = text[
                        sepdex - start_offset : next_sepdex + second_stop_offset + 1
                    ]
                elif (
                    start_offset == 0
                    and first_stop_offset == 3
                    and second_stop_offset == 4
                    and text[sepdex - 1] == ")"
                    and text[sepdex - 5] == "("
                ):
                    # (xxx){separator}xxx{separator}xxxx
                    number = text[
                        sepdex - 5 : sepdex + first_stop_offset + second_stop_offset + 2
                    ]
                elif start_offset == 3 and text[sepdex - 4] in [")", " "]:
                    # (xxx)xxx{separator}xxxx or (xxx) xxx{separator}xxxx
                    number = text[sepdex - 8 : sepdex + 5]
                last_stopdex = sepdex + 5
                for ch in [separator, "(", ")", " "]:
                    number = number.replace(ch, "")
                if len(number) == 10 and all(ch.isnumeric() for ch in number):
                    numbers.append(number)
    return numbers


def find_by_href(text: str) -> list[str]:
    """Scrapes phone numbers by href attribute."""
    indicator = 'href="'
    count = text.count(indicator)
    prefixes = ["tel:", "callto:"]
    index = 0
    numbers = []
    for _ in range(count):
        index = text.find(indicator, index + 1)
        number = text[index + len(indicator) : text.find('"', index + len(indicator))]
        if any(prefix in number for prefix in prefixes):
            number = "".join(
                [num for num in number[number.find(":") + 1 :] if num.isnumeric()]
            )
            if len(number) == 10:
                numbers.append(number)
    return numbers


def scrape_phone_numbers(text: str) -> list[str]:
    """Scrape for u.s. phone numbers."""
    numbers = []
    text = text.replace("+1", "")
    for separator in "-.":
        numbers.extend(find_by_separator(text, separator))
    numbers.extend(find_by_href(text))
    numbers = [
        number
        for number in numbers
        if phonenumbers.is_valid_number(phonenumbers.parse("+1" + number))
    ]
    numbers = sorted(list(set(numbers)))
    return numbers
