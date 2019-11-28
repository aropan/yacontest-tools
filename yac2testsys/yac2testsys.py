#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import xml.etree.ElementTree as ET
import argparse


def get_time(submit):
    return (int(submit.get('contestTime')) + 999) // 1000


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-i', '--input', nargs='+', type=str, required=True)
    argparser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout)
    args = argparser.parse_args()

    g_teams = {}
    g_submits = []
    titles = []

    set_problems = set()
    set_length = set()
    for idx, inp in enumerate(args.input):
        tree = ET.parse(inp)
        root = tree.getroot()
        settings = root.find('settings')
        h, m, s = map(int, settings.find('duration').text.split(':'))
        length = 60 * h + m

        set_length.add(length)

        problems = root.find('problems').getchildren()
        teams = root.find('users').getchildren()
        submits = root.find('events').findall('submit')

        problems_tuple = tuple((p.get('title'), p.get('longName')) for p in problems)
        set_problems.add(problems_tuple)
        titles.append(settings.find('contestName').text)

        submits = [s for s in submits if get_time(s) <= length * 60]

        has_submit = set()
        for s in submits:
            t = int(s.get('userId'))
            has_submit.add(t)

        teams = [
            t for t in teams
            if t.get('participationType') != 'HIDDEN'
            and int(t.get('id')) in has_submit
            and int(t.get('id')) not in g_teams
        ]
        d_teams = {int(t.get('id')): t for t in teams}

        submits = [s for s in submits if int(s.get('userId')) in d_teams]

        g_teams.update(d_teams)
        g_submits.extend(submits)

    assert len(set_problems) == 1
    problems = list(set_problems)[0]

    assert len(set_length) == 1
    length = list(set_length)[0]

    args.output.write(chr(26) + '\n')
    args.output.write('@contest "%s"\n' % ', '.join(titles))
    args.output.write('@contlen %d\n' % length)
    args.output.write('@problems %d\n' % len(problems))
    args.output.write('@teams %d\n' % len(g_teams))
    args.output.write('@submissions %d\n' % len(g_submits))

    for title, name in problems:
        args.output.write('@p %s,"%s",20,0\n' % (title, name))

    for t in g_teams.values():
        args.output.write('@t %s,0,1,"%s"\n' % (t.get('id'), t.get('displayedName')))

    a = {}
    for s in g_submits:
        t = int(s.get('userId'))
        p = s.get('problemTitle')
        k = (t, p)
        a.setdefault(k, 0)
        a[k] += 1
        time = get_time(s)
        assert time <= length * 60
        verdict = s.get('verdict')
        if verdict == 'RE':
            verdict = 'RT'
        elif verdict not in ['WA', 'TL', 'OK', 'CE']:
            verdict = 'WA'
        args.output.write('@s %d,%s,%d,%d,%s\n' % (t, p, a[k], time, verdict))
    print(f'n_problems = {len(problems)}, n_teams = {len(g_teams)}, n_submissions = {len(g_submits)}')


if __name__ == '__main__':
    main()
