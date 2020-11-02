from utils import exec_as_student, register_test, register_build
from utils import TestResult, BuildResult, Panic, DEBUG
import os
import string


if DEBUG:
    os.environ['TOKEN'] = 'null'
    os.environ['SUBMISSION_ID'] = 'null'


def filter_printable(s: bytes) -> str:
    print('-->', s)
    return ''.join(chr(c) for c in s if c in set(ord(c) for c in string.printable))


@register_build
def build(build_result: BuildResult):
    stdout, retcode = exec_as_student('g++ -std=c++17 -Wall -o code code.cpp')
    build_result.passed = retcode == 0
    build_result.stdout = 'g++ -std=c++17 -Wall -o code code.cpp\n' + filter_printable(stdout)


@register_test('Sorted linked list')
def test_1(test_result: TestResult):
    stdout, retcode = exec_as_student('./code')
    stdout = filter_printable(stdout)
    passed = retcode == 0 and '3->5->7->7->8->9' in stdout
    message = 'Your submission passed this test!' if passed else 'This test did not pass...'

    test_result.stdout = stdout
    test_result.passed = passed
    test_result.message = message
