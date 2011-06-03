---
layout: default
title: SSH with Pseudo-terminal
---

It's pretty common for me to execute the same commands on a remote machine
everyday. I usually do something like:

    $ ssh <machine.domain.com>
    screen -x   # reattach to irssi screen session

The most obvious optimization to make is to edit the `~/.ssh/config` file to
alias `machine.domain.com` to something easier to type, like just `machine`.
Now I can just type:

    $ ssh machine
    screen -x   # reattach to irssi screen session

Of course, it would be nice if I didn't have to type `screen -x` each time as
well. We can solve this by passing the commands to run on the remote maching
as arguments to the ssh command. So we try:

    $ ssh machine 'screen -x '
    Must be connected to a terminal.

Uh oh. The remote machine is unable to start screen because, by default, a tty
(a pseudoterminal), isn't created when we execute remote commands. To work
around this we need to pass the magic `-t` option. This forces the remote
machine to create a tty for us.

    $ ssh machine -t 'screen -x '

Voila! Worked like a charm. And this is useful for a bunch of typical commands
you'd like to run on a remote server, for example:

    $ ssh machine -t 'top'  # grab stats

    $ ssh machine -t 'watch ps -eaf | grep <blah>'

The final optimization we can make is to alias the whole command to something
easy to type. Since I like to keep my aliases in a separate ~/.bash_aliases
file, I run:

    $ echo alias irc='ssh machine -t "screen -x"' >> ~/.bash_aliases

Now, all I have to do is type `irc` everyday and I'm right back into my IRC
session.
