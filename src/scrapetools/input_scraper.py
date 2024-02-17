from bs4 import BeautifulSoup
from bs4.element import Tag


def scrape_inputs(
    source: str,
) -> tuple[list[Tag], list[Tag], list[Tag], list[Tag], list[Tag]]:
    """Searches html for various user input elements.

    Returns a tuple where each element is a list of BeautifulSoup Tag elements.

    The tuple elements are forms, inputs, buttons, select elements,
    and text_areas. If an element type was not found, it will be an empty list.

    The inputs, buttons, select elements, and text_areas are ones
    not already found in a form element."""
    soup = BeautifulSoup(source, "html.parser")
    forms = soup("form")
    for form in forms:
        form.extract()
    inputs = soup("input")
    buttons = soup("button")
    selects = soup("select")
    text_areas = soup("textAreas")

    return forms, inputs, buttons, selects, text_areas
