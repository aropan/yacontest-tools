#!/usr/bin/env python

import simplejson as json
from sys import stdin, stderr, stdout
import traceback


def main():
    test_data = json.load(stdin)['tests']
    with open('scoring.json', 'r') as fd:
        scoring_data = json.load(fd)

    important = ['testName', 'verdict', 'message', 'runningTime', 'memoryUsed']
    tests = [{field: test.get(field) for field in important} for test in test_data]
    tests.sort(key=lambda x: int(x['testName'].split('/')[-1]))
    passed = [test['verdict'] == 'ok' for test in tests]
    seen = [False] * len(tests)

    total_points = 0
    for scoring in scoring_data['scoring']:
        points = scoring['points']
        required_passed = True
        for_each_test = bool(scoring.get('each'))

        for required_test in scoring.get('required', {}).get('tests'):
            if isinstance(required_test, int):
                tests = [required_test]
            elif isinstance(required_test, str) and '..' in required_test:
                a, b = map(int, required_test.split('..'))
                tests = range(a, b + 1)
            else:
                raise NotImplementedError('Unknown required_test="%s" format' % required_test)

            for t in tests:
                seen[t - 1] = True
                if not passed[t - 1]:
                    required_passed = False
                elif for_each_test:
                    total_points += points

        if required_passed and not for_each_test:
            total_points += points

    assert all(seen)

    if abs(round(total_points) - total_points) < 1e-9:
        stdout.write('%.0f\n' % total_points)
    else:
        stdout.write('%.2f\n' % total_points)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        stdout.write('-0\n')
        traceback.print_exc(file=stderr)
