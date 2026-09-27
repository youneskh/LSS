# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""GS1 identification key helpers.

This module contains pure functions only.  It has no dependency on the Odoo
ORM so that it can be unit tested in isolation and reused by other modules of
the Life Sciences Suite.

Implemented from the GS1 General Specifications:

* Standard modulo-10 check digit calculation, applicable to GTIN-8, GTIN-12,
  GTIN-13, GTIN-14 and SSCC-18.  Data digits are weighted alternately by 3
  and 1 starting from the right-most data digit; the check digit is the
  smallest value that brings the weighted sum to a multiple of ten.
* GS1 Application Identifier element strings in human-readable interpretation
  form, that is, with the Application Identifier enclosed in parentheses.

Sources
-------
* GS1, "How to Calculate a Check Digit Manually",
  https://documents.gs1us.org/adobe/assets/deliver/urn:aaid:aem:77c80eac-d4e2-41b1-a80d-97739060e8f4/How-to-Calculate-a-Check-Digit.pdf
* GS1 General Specifications, Section 3, "GS1 Application Identifier
  Definitions", https://www.gs1.org/standards/barcodes-epcrfid-id-keys/gs1-general-specifications

Not implemented
---------------
This module does not render barcode symbols.  Producing a GS1 DataMatrix or
GS1-128 symbol requires a symbology encoder, which is outside the scope of
this module.  The element strings produced here are the data content that
such an encoder consumes.
"""

import secrets
import string

from .constants import (
    AI_BATCH_LOT,
    AI_EXPIRY_DATE,
    AI_GTIN,
    AI_SERIAL,
    AI_SSCC,
    AI_VARIABLE_MAX_LENGTH,
    GTIN14_LENGTH,
    SERIAL_ALPHABET,
    SSCC_LENGTH,
)


class Gs1Error(ValueError):
    """Raised when a value does not satisfy a GS1 structural rule.

    A dedicated exception type is used so that callers inside the Odoo layer
    can translate the message before presenting it to a user.
    """


def compute_check_digit(digits):
    """Return the GS1 modulo-10 check digit for ``digits``.

    :param str digits: the identification key *without* its check digit.
        Only the characters ``0`` to ``9`` are accepted.
    :returns: the check digit.
    :rtype: int
    :raises Gs1Error: if ``digits`` is empty or contains a non-digit.
    """
    if not digits:
        raise Gs1Error("A GS1 check digit cannot be computed from an empty value.")
    if not all(character in string.digits for character in digits):
        raise Gs1Error(
            "A GS1 check digit can only be computed from decimal digits, "
            "received %r." % (digits,)
        )
    weighted_sum = 0
    # Position 1 is the right-most data digit and carries the weight 3.
    for position, character in enumerate(reversed(digits), start=1):
        weight = 3 if position % 2 else 1
        weighted_sum += int(character) * weight
    return (10 - (weighted_sum % 10)) % 10


def is_valid_key(key, length):
    """Return whether ``key`` is a structurally valid GS1 key of ``length``.

    The check covers the character set, the total length and the trailing
    modulo-10 check digit.

    :param str key: the complete key, check digit included.
    :param int length: the expected total length.
    :rtype: bool
    """
    if not isinstance(key, str):
        return False
    if len(key) != length:
        return False
    if not all(character in string.digits for character in key):
        return False
    return compute_check_digit(key[:-1]) == int(key[-1])


def is_valid_gtin14(gtin):
    """Return whether ``gtin`` is a structurally valid GTIN-14.

    :param str gtin: candidate GTIN-14.
    :rtype: bool
    """
    return is_valid_key(gtin, GTIN14_LENGTH)


def is_valid_sscc(sscc):
    """Return whether ``sscc`` is a structurally valid SSCC-18.

    :param str sscc: candidate SSCC-18.
    :rtype: bool
    """
    return is_valid_key(sscc, SSCC_LENGTH)


def build_sscc(company_prefix, extension_digit, serial_reference):
    """Assemble an SSCC-18 and append its check digit.

    An SSCC is composed of one extension digit, the GS1 Company Prefix, a
    serial reference and one check digit, for a total of eighteen digits.

    :param str company_prefix: the GS1 Company Prefix allocated to the
        company by its GS1 Member Organisation.
    :param str extension_digit: a single digit chosen by the company.
    :param str serial_reference: the serial reference; it is left-padded with
        zeroes so that the assembled key reaches eighteen digits.
    :rtype: str
    :raises Gs1Error: if the supplied parts cannot form a valid SSCC-18.
    """
    for name, value in (
        ("company prefix", company_prefix),
        ("extension digit", extension_digit),
        ("serial reference", serial_reference),
    ):
        if not value or not all(character in string.digits for character in value):
            raise Gs1Error(
                "The SSCC %s must consist of decimal digits, received %r."
                % (name, value)
            )
    if len(extension_digit) != 1:
        raise Gs1Error(
            "The SSCC extension digit must be exactly one digit, received %r."
            % (extension_digit,)
        )
    # Eighteen digits, minus the extension digit, minus the check digit.
    padding_length = SSCC_LENGTH - 2 - len(company_prefix)
    if padding_length < len(serial_reference):
        raise Gs1Error(
            "The GS1 Company Prefix and serial reference are too long to form "
            "an eighteen digit SSCC."
        )
    body = (
        extension_digit
        + company_prefix
        + serial_reference.rjust(padding_length, "0")
    )
    return body + str(compute_check_digit(body))


def format_expiry(value):
    """Return a date encoded in the GS1 ``YYMMDD`` format of AI (17).

    :param value: a :class:`datetime.date` or :class:`datetime.datetime`.
    :rtype: str
    :raises Gs1Error: if ``value`` is falsy.
    """
    if not value:
        raise Gs1Error(
            "An expiry date is required to build the AI (17) element string."
        )
    return value.strftime("%y%m%d")


def format_element_string(pairs):
    """Return the human-readable interpretation of a GS1 element string.

    :param pairs: an ordered iterable of ``(application identifier, value)``
        two-tuples.  Entries whose value is falsy are skipped so that optional
        data elements can be passed unconditionally.
    :rtype: str
    """
    return "".join(
        "(%s)%s" % (application_identifier, value)
        for application_identifier, value in pairs
        if value
    )


def build_unique_identifier(gtin, serial, batch, expiry):
    """Return the element string of a medicinal product unique identifier.

    Commission Delegated Regulation (EU) 2016/161 defines the unique
    identifier as the combination of a product code, a serial number, the
    batch number, the expiry date and, where the Member State requires one, a
    national reimbursement or identification number.  This helper builds the
    first four data elements using the GS1 Application Identifiers that are
    conventionally used to carry them.  A national reimbursement number, when
    required, is carried by a national healthcare reimbursement number
    Application Identifier that varies by Member State; it is therefore stored
    as a separate field by this module and is not appended here.

    :param str gtin: the product code, carried by AI (01).
    :param str serial: the serial number, carried by AI (21).
    :param str batch: the batch number, carried by AI (10).
    :param expiry: the expiry date, carried by AI (17).
    :rtype: str
    :raises Gs1Error: if a mandatory data element is missing or malformed.
    """
    if not is_valid_gtin14(gtin):
        raise Gs1Error("The product code %r is not a valid GTIN-14." % (gtin,))
    validate_variable_field(serial, "serial number")
    validate_variable_field(batch, "batch number")
    return format_element_string(
        [
            (AI_GTIN, gtin),
            (AI_SERIAL, serial),
            (AI_BATCH_LOT, batch),
            (AI_EXPIRY_DATE, format_expiry(expiry)),
        ]
    )


def build_sscc_element_string(sscc):
    """Return the element string of a logistics unit identified by an SSCC.

    :param str sscc: the SSCC-18.
    :rtype: str
    :raises Gs1Error: if ``sscc`` is not a valid SSCC-18.
    """
    if not is_valid_sscc(sscc):
        raise Gs1Error("The value %r is not a valid SSCC-18." % (sscc,))
    return format_element_string([(AI_SSCC, sscc)])


def validate_variable_field(value, label):
    """Validate a variable-length AI data field.

    AI (10) and AI (21) accept up to twenty characters.

    :param str value: the value to validate.
    :param str label: a human-readable name used in the error message.
    :raises Gs1Error: if ``value`` is empty or longer than twenty characters.
    """
    if not value:
        raise Gs1Error("The %s is required." % (label,))
    if len(value) > AI_VARIABLE_MAX_LENGTH:
        raise Gs1Error(
            "The %s may not exceed %d characters, received %d."
            % (label, AI_VARIABLE_MAX_LENGTH, len(value))
        )


def generate_random_serial(length):
    """Return a randomly generated serial number.

    Commission Delegated Regulation (EU) 2016/161 requires that the
    probability of a serial number being guessed is negligible.  This helper
    therefore draws every character from :mod:`secrets`, which uses the
    operating system source of cryptographically strong randomness, rather
    than from :mod:`random`.

    The caller remains responsible for verifying that the resulting serial
    number has not already been used for the same product code.

    :param int length: the number of characters to generate.
    :rtype: str
    :raises Gs1Error: if ``length`` is outside the range permitted by
        AI (21).
    """
    if length < 1 or length > AI_VARIABLE_MAX_LENGTH:
        raise Gs1Error(
            "A serial number must be between 1 and %d characters long, "
            "received %r." % (AI_VARIABLE_MAX_LENGTH, length)
        )
    return "".join(secrets.choice(SERIAL_ALPHABET) for _index in range(length))
