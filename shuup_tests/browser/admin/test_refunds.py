# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import os
import time

import pytest
from django.core.urlresolvers import reverse

from shuup.testing.browser_utils import (
    click_element, wait_until_appeared, wait_until_condition
)
from shuup.testing.factories import (
    create_order_with_product, get_default_product, get_default_shop,
    get_default_supplier
)
from shuup.testing.utils import initialize_admin_browser_test
from shuup.utils.i18n import format_money

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_refunds(browser, admin_user, live_server, settings):
    order = create_order_with_product(
        get_default_product(), get_default_supplier(), 10, decimal.Decimal("10"), n_lines=10,
        shop=get_default_shop())
    order2 = create_order_with_product(
        get_default_product(), get_default_supplier(), 10, decimal.Decimal("10"), n_lines=10,
        shop=get_default_shop())
    order2.create_payment(order2.taxful_total_price)
    initialize_admin_browser_test(browser, live_server, settings)
    _test_toolbar_visibility(browser, live_server, order)
    _test_create_full_refund(browser, live_server, order)
    _test_refund_view(browser, live_server, order2)


def _check_create_refund_link(browser, order, present):
    url = reverse("shuup_admin:order.create-refund", kwargs={"pk": order.pk})
    wait_until_condition(browser, lambda x: (len(x.find_by_css("a[href='%s']" % url)) > 0) == present)


def _test_toolbar_visibility(browser, live_server, order):
    url = reverse("shuup_admin:order.detail", kwargs={"pk": order.pk})
    browser.visit("%s%s" % (live_server, url))
    wait_until_appeared(browser, "#order_details")
    _check_create_refund_link(browser, order, False)
    order.create_payment(order.taxful_total_price)
    browser.reload()
    wait_until_appeared(browser, "#order_details")
    _check_create_refund_link(browser, order, True)


def _test_create_full_refund(browser, live_server, order):
    url = reverse("shuup_admin:order.create-refund", kwargs={"pk": order.pk})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present("Refunded: %s" % format_money(order.shop.create_price("0.00"))))
    wait_until_condition(browser, lambda x: x.is_text_present("Remaining: %s" % format_money(order.taxful_total_price)))
    url = reverse("shuup_admin:order.create-full-refund", kwargs={"pk": order.pk})
    click_element(browser, "a[href='%s']" % url)
    wait_until_condition(browser, lambda x: x.is_text_present("Refund Amount: %s" % format_money(order.taxful_total_price)))
    click_element(browser, "#create-full-refund")
    wait_until_appeared(browser, "#order_details")
    _check_create_refund_link(browser, order, False)
    order.refresh_from_db()
    assert not order.taxful_total_price
    assert order.is_paid()
    assert order.is_fully_shipped()


def _test_refund_view(browser, live_server, order):
    url = reverse("shuup_admin:order.create-refund", kwargs={"pk": order.pk})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present("Refunded: %s" % format_money(order.shop.create_price("0.00"))))
    assert len(browser.find_by_css("#id_form-0-line_number option")) == 12 # blank + arbitrary amount + num lines
    click_element(browser, "#select2-id_form-0-line_number-container")
    wait_until_appeared(browser, "input.select2-search__field")
    browser.execute_script('$($(".select2-results__option")[1]).trigger({type: "mouseup"})') # select arbitrary amount
    wait_until_condition(browser, lambda x: len(x.find_by_css("#id_form-0-text")))
    wait_until_condition(browser, lambda x: len(x.find_by_css("#id_form-0-amount")))
    browser.find_by_css("#id_form-0-text").first.value = "test"
    browser.find_by_css("#id_form-0-amount").first.value = "900"
    click_element(browser, "#add-refund")
    click_element(browser, "#select2-id_form-1-line_number-container")
    wait_until_appeared(browser, "input.select2-search__field")
    browser.execute_script('$($(".select2-results__option")[2]).trigger({type: "mouseup"})') # select first line
    browser.find_by_css("#id_form-1-amount").first.value == "100"
    browser.find_by_css("#id_form-1-quantity").first.value == "10"
    click_element(browser, "button[form='create_refund']")
    _check_create_refund_link(browser, order, True) # can still refund quantity
    order.refresh_from_db()
    assert not order.taxful_total_price
    assert order.is_paid()
    assert not order.is_fully_shipped()
