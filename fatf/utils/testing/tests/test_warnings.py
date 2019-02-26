"""
Test helper functions for testing warning filters.
"""
# Author: Kacper Sokol <k.sokol@bristol.ac.uk>
# License: new BSD

import re
import warnings

import pytest

from fatf.utils.testing.warnings import (
    DEFAULT_WARNINGS, EMPTY_RE, EMPTY_RE_I, handle_warnings_filter_pattern,
    is_warning_class_displayed, set_default_warning_filters)


def test_handle_warnings_filter_pattern():
    """
    Test checking and conversion of message and module patterns in a warning
    filter.
    """

    def assert_correct_pattern(error, error_message, pattern, ignore_case):
        with pytest.raises(error) as value_error:
            handle_warnings_filter_pattern(pattern, ignore_case=ignore_case)
        assert str(value_error.value) == error_message

    # Test None
    assert EMPTY_RE == handle_warnings_filter_pattern(None, ignore_case=False)
    assert EMPTY_RE_I == handle_warnings_filter_pattern(None, ignore_case=True)

    # Test string
    my_str_pattern = 'my pattern'
    my_re_pattern = re.compile(my_str_pattern)
    my_re_pattern_i = re.compile(my_str_pattern, re.IGNORECASE)
    assert my_re_pattern == handle_warnings_filter_pattern(
        my_str_pattern, ignore_case=False)
    assert my_re_pattern_i == handle_warnings_filter_pattern(
        my_str_pattern, ignore_case=True)

    # Test re.compile return type
    assert my_re_pattern == \
        handle_warnings_filter_pattern(my_re_pattern, ignore_case=False)

    assert my_re_pattern_i == \
        handle_warnings_filter_pattern(my_re_pattern_i, ignore_case=True)
    value_error_message = (
        'The input regular expression should {neg} be compiled with '
        're.IGNORECASE flag -- it is imposed by the warning_filter_pattern '
        'input variable.')
    value_error_message_yes = value_error_message.format(neg='')
    value_error_message_no = value_error_message.format(neg='not')
    #
    assert_correct_pattern(ValueError, value_error_message_yes, my_re_pattern,
                           True)
    assert_correct_pattern(ValueError, value_error_message_no, my_re_pattern_i,
                           False)

    # Test other types: int, list, dict
    type_error_message = (
        'The warning filter module pattern should be either a string, a '
        'regular expression pattern or a None type.')
    assert_correct_pattern(TypeError, type_error_message, 4, False)
    assert_correct_pattern(TypeError, type_error_message, 2, True)
    assert_correct_pattern(TypeError, type_error_message, [4, 2], False)
    assert_correct_pattern(TypeError, type_error_message, [2, 4], True)
    assert_correct_pattern(TypeError, type_error_message, {1: '4', 2: '2'},
                           False)  # yapf: disable
    assert_correct_pattern(TypeError, type_error_message, {1: '2', 2: '4'},
                           True)  # yapf: disable

    # Test other regex flags
    flag_m = re.compile('', re.MULTILINE)
    assert flag_m == handle_warnings_filter_pattern(flag_m, ignore_case=False)
    assert_correct_pattern(ValueError, value_error_message_yes, flag_m, True)
    #
    flag_i = re.compile('', re.IGNORECASE)
    assert flag_i == handle_warnings_filter_pattern(flag_i, ignore_case=True)
    assert_correct_pattern(ValueError, value_error_message_no, flag_i, False)
    #
    flag_a = re.compile('', re.ASCII)
    assert flag_a == handle_warnings_filter_pattern(flag_a, ignore_case=False)
    assert_correct_pattern(ValueError, value_error_message_yes, flag_m, True)
    #
    flag_mi = re.compile('', re.MULTILINE | re.IGNORECASE)
    assert flag_mi == handle_warnings_filter_pattern(flag_mi, ignore_case=True)
    assert_correct_pattern(ValueError, value_error_message_no, flag_mi, False)
    #
    flag_ma = re.compile('', re.MULTILINE | re.ASCII)
    assert flag_ma == handle_warnings_filter_pattern(
        flag_ma, ignore_case=False)
    assert_correct_pattern(ValueError, value_error_message_yes, flag_ma, True)
    #
    flag_ai = re.compile('', re.ASCII | re.IGNORECASE)
    assert flag_ai == handle_warnings_filter_pattern(flag_ai, ignore_case=True)
    assert_correct_pattern(ValueError, value_error_message_no, flag_ai, False)


def test_set_default_warning_filters():
    """
    Test setting up default filters.
    """
    set_default_warning_filters()

    filters_number = len(DEFAULT_WARNINGS)
    assert len(warnings.filters) == filters_number

    for i in range(filters_number):
        builtin_filter = warnings.filters[i]
        default_filter = DEFAULT_WARNINGS[filters_number - 1 - i]

        # Compare warning action
        assert builtin_filter[0] == default_filter[0]
        # Compare message
        assert handle_warnings_filter_pattern(builtin_filter[1],
                                              ignore_case=True) == \
            handle_warnings_filter_pattern(default_filter[1],
                                           ignore_case=True)
        # Compare warning category
        assert builtin_filter[2] == default_filter[2]
        # Compare module
        assert handle_warnings_filter_pattern(builtin_filter[3],
                                              ignore_case=False) == \
            handle_warnings_filter_pattern(default_filter[3],
                                           ignore_case=False)
        # Compare lineno
        assert builtin_filter[4] == default_filter[4]


def test_is_warning_class_displayed():
    """
    Test a function that checks whether a particular warning class is displayed
    based on the available warning filters.
    """
    # No warning filters -> display
    warnings.resetwarnings()
    assert is_warning_class_displayed(DeprecationWarning)

    # No filter for this particular class -> display
    warnings.filterwarnings('default', category=ImportWarning, module='')
    assert is_warning_class_displayed(DeprecationWarning)

    # A filter that blocks -> do not display
    warnings.resetwarnings()
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='')
    assert not is_warning_class_displayed(DeprecationWarning)

    # A filter that allows -> display
    warnings.resetwarnings()
    warnings.filterwarnings('default', category=DeprecationWarning, module='')
    assert is_warning_class_displayed(DeprecationWarning)
    #
    warnings.resetwarnings()
    warnings.filterwarnings('error', category=DeprecationWarning, module='')
    assert is_warning_class_displayed(DeprecationWarning)
    #
    warnings.resetwarnings()
    warnings.filterwarnings('always', category=DeprecationWarning, module='')
    assert is_warning_class_displayed(DeprecationWarning)
    #
    warnings.resetwarnings()
    warnings.filterwarnings('module', category=DeprecationWarning, module='')
    assert is_warning_class_displayed(DeprecationWarning)
    #
    warnings.resetwarnings()
    warnings.filterwarnings('module', category=DeprecationWarning, module='')
    assert is_warning_class_displayed(DeprecationWarning)

    # A block filter that overwrites another (pass) filter -> do not display
    warnings.resetwarnings()
    warnings.filterwarnings('always', category=DeprecationWarning, module='')
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='')
    assert not is_warning_class_displayed(DeprecationWarning)

    # A pass filter that overwrites another (block) filter -> display
    warnings.resetwarnings()
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='')
    warnings.filterwarnings('always', category=DeprecationWarning, module='')
    assert is_warning_class_displayed(DeprecationWarning)

    # A filter with t namespace
    warnings.resetwarnings()
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='t')
    assert is_warning_class_displayed(DeprecationWarning, 'fatf.test.t')
    assert not is_warning_class_displayed(DeprecationWarning, 't.test')
    warnings.filterwarnings(
        'ignore', category=DeprecationWarning, module='fatf')
    assert not is_warning_class_displayed(DeprecationWarning, 'fatf.test.t')
    warnings.filterwarnings(
        'always', category=DeprecationWarning, module='fatf.test')
    assert not is_warning_class_displayed(DeprecationWarning, 'fatf.t')
    assert is_warning_class_displayed(DeprecationWarning, 'fatf.test.t')