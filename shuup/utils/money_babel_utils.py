# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

import decimal
from collections import defaultdict

import babel.core
from babel.numbers import format_currency


def get_precision(currency):
    """
    Get precisision for given currency from Babel.

    :type currency: str
    :param currency: Currency code as 3-letter string (ISO-4217)

    :rtype: decimal.Decimal
    :return: Precision value for given currency code
    """
    return _get_precision_from_cache(currency)


def format_money(value, currency, digits=None, widen=0, locale=None):
    """
    Format money amount in the given locale.

    If neither digits or widen is passed, the preferred number of digits for
    the amount's currency is used.

    :param amount: The Money object to format
    :type amount: shuup.utils.money.Money
    :param digits: How many digits to format the currency with.
    :type digits: int|None
    :param widen: How many digits to widen any existing decimal width with.
    :type widen: int|None
    :param locale: Locale object or locale identifier
    :type locale: Locale|str
    :return: Formatted string
    :rtype: str
    """
    if not locale:
        loc = get_current_babel_locale()
    else:
        loc = get_babel_locale(locale)

    pattern = loc.currency_formats["standard"].pattern

    # pattern is a formatting string.  Couple examples:
    # '¤#,##0.00', '#,##0.00\xa0¤', '\u200e¤#,##0.00', and '¤#0.00'

    d = digits if digits is not None else _get_digits_from_cache(currency)
    places = d + widen
    pattern = pattern.replace(".00", "." + (places * "0"))

    return format_currency(value, currency, pattern, loc, currency_digits=False)


def _get_digits_from_cache(currency):
    return _fill_caches_and_set_cache_getters()[0](currency)


def _get_precision_from_cache(currency):
    return _fill_caches_and_set_cache_getters()[1](currency)


def _fill_caches_and_set_cache_getters():
    global _get_digits_from_cache
    global _get_precision_from_cache

    (get_digits, get_precision) = _get_digit_and_precision_getters()

    _get_digits_from_cache = get_digits
    _get_precision_from_cache = get_precision

    return (get_digits, get_precision)


def _get_digit_and_precision_getters():
    fractions = babel.core.get_global('currency_fractions')
    digits = _make_defaultdict(
        (currency, data[0])
        for (currency, data) in fractions.items())
    precisions = _make_defaultdict(
        (currency, decimal.Decimal('0.1') ** data[0])
        for (currency, data) in fractions.items())
    return (digits.__getitem__, precisions.__getitem__)


def _make_defaultdict(iterable, default_key='DEFAULT'):
    values = {key: value for (key, value) in iterable}
    default = values.pop(default_key)
    return defaultdict(lambda: default, values)
