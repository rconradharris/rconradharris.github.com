#!/usr/bin/python
import datetime
import os
import platform
import subprocess
import sys

PATH = "~/Documents/code/rconradharris.github.com/_posts"


def make_filename(title):
    date_str = datetime.date.today().strftime("%Y_%m_%d")
    filename_title = title.replace(' ', '_').replace('-', '_').lower()
    return "%(date_str)s_%(filename_title)s.markdown" % locals()


def write_template(title, filepath):
    with open(filepath, 'w') as f:
        body = """\
---
layout: post
title: %(title)s
---
        """ % locals()
        f.write(body)


def open_in_editor(filepath):
    # NOTE: Macs report 'posix' but don't have xdg-open
    if platform.platform().startswith('Darwin'):
        subprocess.call(('open', filepath))
    elif os.name == 'nt':
        subprocess.call(('start', filepath), shell=True)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', filepath))
    else:
        raise Exception('Unrecognized OS %s' % os.name)


if __name__ == "__main__":
    title_parts = sys.argv[1:]
    title = ' '.join(title_parts)

    filename = make_filename(title)
    base_path = os.path.expanduser(PATH)
    filepath = os.path.join(base_path, filename)

    write_template(title, filepath)
    open_in_editor(filepath)
