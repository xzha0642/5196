# -*- coding: utf-8 -*-
"""Shared text functions for FIT5196 A1 Group050.

The six public functions implement the fixed Task 3 interface. This module
uses only the Python standard library and performs no file I/O, network access
or row-specific lookups.
"""

import html
import re
import unicodedata

__all__ = [
    "clean_narrative_text",
    "extract_order_reference",
    "extract_product_sku",
    "extract_promo_code",
    "build_latin_analysis",
    "contains_non_latin_script",
]


_LITERAL_NAN = "NaN"

# The code itself is ASCII-only, while the surrounding ``\w`` checks remain
# Unicode-aware. Including hyphens in both boundaries rejects malformed
# extensions instead of accepting a valid prefix from a longer token.
_ORDER_REFERENCE_RE = re.compile(r"(?<![\w-])(?ai:(?:HORD|CORD)[0-9]{6})(?![\w-])")

# Task 3, Step 2: SKU extraction (owner: Xingao Zhan / Evodia).
# Require SKU- followed by one or more ASCII letters/digits, with no fixed
# suffix length. (?ai:...) allows either case without Unicode lookalikes;
# the outer Unicode-aware boundaries reject embedded or hyphen-extended codes.
_PRODUCT_SKU_RE = re.compile(r"(?<![\w-])(?ai:SKU-[A-Z0-9]+)(?![\w-])")

# Task 3, Step 2: promotion extraction (owner: Xingao Zhan / Evodia).
# Only B1SAVE- to B5SAVE- followed by exactly two ASCII digits are valid.
# The right boundary prevents extracting B3SAVE-20 from B3SAVE-200 or
# B3SAVE-20-extra; the left boundary prevents matching inside a larger token.
_PROMO_CODE_RE = re.compile(r"(?<![\w-])(?ai:B[1-5]SAVE-[0-9]{2})(?![\w-])")

_EMOJI_RE = re.compile(
    r"[0-9#*]\ufe0f?\u20e3"
    r"|[\u00a9\u00ae\u203c\u2049\u2122\u2139\u3030\u303d\u3297\u3299]\ufe0f"
    r"|[\U0001F000-\U0001FAFF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF"
    r"\uFE00-\uFE0F\U000E0020-\U000E007F\u200D\u20E3]"
)


def _extract_upper(value, pattern):
    """Return the first bounded match in upper case, or literal ``NaN``."""

    if not isinstance(value, str):
        return _LITERAL_NAN

    match = pattern.search(value)
    return match.group(0).upper() if match else _LITERAL_NAN


def clean_narrative_text(value):
    """Accept None or a string; return cleaned text or the string 'NaN'."""
    # check for non-string input and the literal NaN string
    if not isinstance(value, str):
        return _LITERAL_NAN
    if value == _LITERAL_NAN:
        return _LITERAL_NAN
    # start cleaning the text in step order, as specified in the assignment instructions

    # step 3: convert HTML entities to Unicode
    text = html.unescape(value)
    # step 3:normalize to NFC
    text = unicodedata.normalize("NFC", text)
    # step 4: remove HTML tags
    text = re.sub(r"<[^<>]*>", " ", text)
    # step 5: remove system, catalogue, verified-purchase, source, and rating mentions
    text = re.sub(
        (
            r"\[(?:SYSTEM|CATALOGUE|VERIFIED_PURCHASE|"
            r"SOURCE:\s*[^\]]*|RATING:\s*[0-5]\s*/\s*5)\]"
        ),
        " ",
        text,
        flags=re.IGNORECASE,
    )
    # step 5: remove verified-buyer and store-support mentions
    text = re.sub(
        r"(?<![\w-])(?:#verified-buyer|@store_support)(?![\w-])",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    # step 5: remove URLs and emojis
    text = re.sub(
        r"\b(?:https?://|www\.)\S+",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = _EMOJI_RE.sub("", text)
    # step 6: remove promotional references, including the SKU and promo code
    text = re.sub(
        (
            r"(?<![\w-])Reference:\s*"
            r"(?a:(?:HORD|CORD)[0-9]{6})(?![\w-])"
            r"(?:\s*[|,;/]\s*|\s+)"
            r"SKU:\s*(?a:SKU-[A-Z0-9]+)(?![\w-])"
        ),
        " ",
        text,
        flags=re.IGNORECASE,
    )
    # step 7: remove promotional references, including the promo code
    text = re.sub(
        r"(?<![\w-])PROMO:\s*(?a:B[1-5]SAVE-[0-9]{2})(?![\w-])",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    # step 8: remove extra whitespace and convert to lowercase
    text = re.sub(r"\s+", " ", text).strip().lower()
    # step 9: return the cleaned text or the literal NaN string
    return text if text else _LITERAL_NAN


def extract_order_reference(value):
    """Accept None or a string; return the upper-case reference or 'NaN'."""

    return _extract_upper(value, _ORDER_REFERENCE_RE)


def extract_product_sku(value):
    """Extract a product SKU from raw narrative text (Task 3, Step 2).

    Owner: Xingao Zhan (Evodia).
    Input: a structurally parsed raw string or None. Call before narrative
    cleaning (Steps 3-9), while the reference/SKU wrapper is still present.
    Output: the first valid bounded SKU, in upper case, or the literal string
    "NaN" for non-string input, empty text or no valid match.

    The shared helper searches the whole input with _PRODUCT_SKU_RE and
    normalises only the matched code. This extracts a code; it does not check
    catalogue membership, clean the narrative or modify the source text.

    >>> extract_product_sku("Reference: HORD000001 | SKU: sku-a1B2")
    'SKU-A1B2'
    >>> extract_product_sku("SKU-ABC123-extra")
    'NaN'
    >>> extract_product_sku(None)
    'NaN'
    """

    return _extract_upper(value, _PRODUCT_SKU_RE)


def extract_promo_code(value):
    """Extract a promotion code from raw narrative text (Task 3, Step 2).

    Owner: Xingao Zhan (Evodia).
    Input: a structurally parsed raw string or None. Extract before narrative
    cleaning (Steps 3-9) removes the PROMO wrapper from the customer note.
    Output: the first valid bounded code, in upper case, or the literal string
    "NaN" for non-string input, empty text or no valid match.

    The shared helper searches with _PROMO_CODE_RE, so invalid prefixes,
    non-ASCII digits and malformed continuations cannot yield partial codes.
    This records a reference only; it does not apply a discount or change
    order amounts, and a PROMO label is not required for a valid match.

    >>> extract_promo_code("PROMO: b5save-99")
    'B5SAVE-99'
    >>> extract_promo_code("B3SAVE-200")
    'NaN'
    >>> extract_promo_code(None)
    'NaN'
    """

    return _extract_upper(value, _PROMO_CODE_RE)


def build_latin_analysis(value):
    """Accept cleaned multilingual text; return Latin analysis or 'NaN'."""

    # Step 1: Validate the input.
    # This function expects review_body_clean rather than the noisy raw review.
    # Non-string values and the published literal missing-value sentinel
    # cannot produce a Latin-script analysis.
    if not isinstance(value, str) or value == _LITERAL_NAN:
        return _LITERAL_NAN

    # Step 2: Apply Unicode NFC normalisation.
    # This gives canonically equivalent characters a consistent representation
    # while preserving valid multilingual Unicode text.
    text = unicodedata.normalize("NFC", value)

    # Step 3: Initialise the output and processing state.
    # output_characters stores characters retained for the Latin analysis.
    # contains_latin_letter records whether at least one Latin letter survives.
    # previous_character_was_latin allows combining marks to be retained only
    # when they belong to a retained Latin base letter.
    output_characters = []
    contains_latin_letter = False
    previous_character_was_latin = False

    # Step 4: Inspect every Unicode character in the cleaned review.
    for character in text:
        # Obtain the Unicode general category and official Unicode name.
        # Categories beginning with "L" are letters, while those beginning
        # with "M" are combining marks.
        category = unicodedata.category(character)
        unicode_name = unicodedata.name(character, "")

        # Step 4.1: Process Unicode letters.
        if category.startswith("L"):

            # Retain Latin-script letters, including precomposed European
            # letters with diacritics such as é, ü and ñ.
            if "LATIN" in unicode_name:
                output_characters.append(character)
                contains_latin_letter = True
                previous_character_was_latin = True

            # Remove letters from non-Latin scripts.
            # Insert a space so that Latin text on either side of removed
            # non-Latin writing does not become incorrectly joined.
            else:
                output_characters.append(" ")
                previous_character_was_latin = False

        # Step 4.2: Process Unicode combining marks.
        # Retain a combining mark only when it directly continues a retained
        # Latin base letter. Marks belonging to removed scripts are discarded.
        elif category.startswith("M"):
            if previous_character_was_latin:
                output_characters.append(character)

        # Step 4.3: Preserve applicable non-letter content.
        # Digits, punctuation, symbols and whitespace are retained because
        # the Latin-analysis field may keep these characters.
        else:
            output_characters.append(character)
            previous_character_was_latin = False

    # Step 5: Reconstruct the analysis string.
    # Collapse spaces, tabs and line breaks into one space, then remove
    # whitespace from the beginning and end of the result.
    result = re.sub(
        r"\s+",
        " ",
        "".join(output_characters),
    ).strip()

    # Step 6: Apply the published sentinel rule.
    # Return the result only when at least one Latin letter remains.
    # A result containing only digits or punctuation is not sufficient.
    return (
        result
        if contains_latin_letter and result
        else _LITERAL_NAN
    )


def contains_non_latin_script(value):
    """Accept cleaned multilingual text; return a Python bool."""

    # Step 1: Handle invalid or missing cleaned text.
    # Non-string values and the literal "NaN" sentinel do not contain
    # review text, so the required indicator is False.
    if not isinstance(value, str) or value == _LITERAL_NAN:
        return False

    # Step 2: Apply Unicode NFC normalisation before script detection.
    # This keeps canonically equivalent text consistent and prevents
    # non-ASCII Latin letters from being misclassified.
    text = unicodedata.normalize("NFC", value)

    # Step 3: Inspect Unicode letters and detect non-Latin script.
    # A character counts as non-Latin only when:
    #   1. its Unicode category identifies it as a letter; and
    #   2. its Unicode name does not identify it as Latin.
    #
    # Digits, punctuation, emoji, symbols and combining marks alone do not
    # trigger the indicator. any() stops as soon as one matching letter is
    # found and otherwise returns False after checking the complete text.
    return any(
        unicodedata.category(character).startswith("L")
        and "LATIN" not in unicodedata.name(character, "")
        for character in text
    )