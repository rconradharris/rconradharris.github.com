---
layout: post
title: Opening Files in an Editor from Python
---

For my latest attempt at a blog I'm using Github's built-in blogging system.
Using a git repo as the storage,
[Markdown](http://daringfireball.net/projects/markdown/) for the formatting,
and a text-editor for composition seems like a really nice combination. In
fact, I'm optimistic that I might make it past the three-post-wall, which up
until now, has been the most of I've ever posted to any of my ill-fated
proto-blogs.

Given this dubious record, I've decided to remove as many barriers to
posting as possible. And, as nice as Jekyll makes it&mdash;just create
a new file under the `_posts` directory&mdash;I wanted to be able to kick
off a new entry with a single command, something like:

    newpost My Snazzy New Blog Entry

I wanted this to:
* Create the properly named file under the `_posts` directory
* Drop in the heading text automatically
* Open the new file in my default text editor

Of these, only the third was interesting. It turns out opening a file in a
text-editor isn't as clear cut as I thought. There are really two routes you
can go:
* Use EDITOR and VISUAL environment variables to open up a
  command-line editor
* Invoke a system-specific command to choose the default-handler
  based on the file's type

The route I decided to go with was using the system's text-file handler, which
in my case is [MacVim](http://code.google.com/p/macvim/).  The one trick to
getting this right is to note that Macs and other UNIXes have two different
ways for accomplishing this: Macs use the
[open(1)](http://developer.apple.com/library/mac/#documentation/Darwin/Reference/ManPages/man1/open.1.html)
command whereas other POSIX OSes use
[xdg-open(1)](http://linux.die.net/man/1/xdg-open). The final code, taken from
[StackOverflow](http://stackoverflow.com/questions/434597/open-document-with-default-application-in-python)
with a small modification to handle the Mac case properly:

    def open_in_editor(filepath):
        # NOTE: Macs are 'posix' but don't have xdg-open
        if platform.platform().startswith('Darwin'):
            subprocess.call(('open', filepath))
        elif os.name == 'nt':
            subprocess.call(('start', filepath), shell=True)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', filepath))
        else:
            raise Exception('Unrecognized OS %s' % os.name)
