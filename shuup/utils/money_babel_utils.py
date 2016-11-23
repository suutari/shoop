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

_precision_cache = None
_digits_cache = None


def get_precision(currency):
    """
    Get precisision for given currency from Babel.

    :type currency: str
    :param currency: Currency code as 3-letter string (ISO-4217)

    :rtype: decimal.Decimal
    :return: Precision value for given currency code
    """
    global _precision_cache
    if _precision_cache is None:
        _precision_cache = _generate_precision_cache()
    return _precision_cache[currency]


def _generate_precision_cache():
    currency_fractions = babel.core.get_global('currency_fractions')
    values = {
        currency: decimal.Decimal('0.1') ** data[0]
        for (currency, data) in currency_fractions.items()
    }
    default = values.pop('DEFAULT')
    cache = defaultdict(lambda: default)
    cache.update(values)
    return cache


def _generate_digits_cache():
    fractions = babel.core.get_global('currency_fractions')
    values = {currency: data[0] for (currency, data) in fractions.items()}
    default = values.pop('DEFAULT')
    cache = defaultdict(lambda: default)
    cache.update(values)
    return cache


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
    global _digits_cache
    if _digits_cache is None:
        _digits_cache = _generate_digits_cache()

    if not locale:
        loc = get_current_babel_locale()
    else:
        loc = get_babel_locale(locale)

    pattern = loc.currency_formats["standard"].pattern

    # pattern is a formatting string.  Couple examples:
    # '¤#,##0.00', '#,##0.00\xa0¤', '\u200e¤#,##0.00', and '¤#0.00'

    places = (_digits_cache[currency] if digits is None else digits) + widen
    pattern = pattern.replace(".00", "." + (places * "0"))

    return format_currency(value, currency, pattern, loc, currency_digits=False)

