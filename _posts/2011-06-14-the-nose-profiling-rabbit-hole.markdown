---
layout: post
title: The Nose Profiling Rabbit Hole
---

Today I got the itch to try to speed up one of our slowest tests in the
[OpenStack Nova](https://launchpad.net/nova) project. Clocking in at 12
seconds, this one test is a major pain-point in a suite that is run on every
check-in.

To figure out why it was so slow, I decided to use
[`nose`'s](http://somethingaboutorange.com/mrl/projects/nose/1.0.0/)
buillt-in profiling plugin which, according to the man page, is invoked with
`--with-profile`. Unfortunately, this was the beginning of some serious pain:

    $ nosetests --with-profile nova/tests/test_vlan_network.py:VlanNetworkTestCase.test_too_many_addresses
    nosetests: error: no such option: --with-profile

So, apparently `nose` (which I suspected was using `optparse`), was not
parsing the profile option correctly.  Looking through the `nose` code, I
could see where it added the option for the profile plugin. 

My next step was to start tossing in `print` statements into the the `nose` code
to see how far it was getting in loading the module. 

ASIDE: debugging by modifying site-packages is a dangerous game;
but if you have to do it, I highly recommend you attach a grep'able expression
to each line so you can go back later and remove the lines. Something like:

    print "got here => ", plugin  # RCH

So, after some carefully placed `prints` and `raises`, I finally traced the
problem to the profile plugin's `is_available()` function which, oddly,
was returning `False`.

This is particularly strange since the availability is determined by trying to
import [`hotshot`](http://docs.python.org/library/hotshot.html) (a Python profiler) and [`pstats`](http://docs.python.org/library/profile.html) (a profile statistics
helper), and both of these are part of the standard library. Looking more
carefully, I noticed that the import was swallowing `ImportError` exceptions,
so I decided to add a print statement:

    # nose/plugins/prof.py
    try:
        import hotshot
        from hotshot import stats
    except ImportError as e:
        print e
        hotshot, stats = None, None


Running this once more, I hit the root of the problem:

    $ nosetests --with-profile nova/tests/test_vlan_network.py:VlanNetworkTestCase.test_too_many_addresses
    No module named profile; please install the python-profiler package

Apparently, the `pstats` module was missing. Alarmingly, this means
that Ubuntu isn't shipping with the full Python
standard-library. To fix this I ran:

    sudo apt-get install python-profiler

Of course, not having the complete Python standard library is broken behavior,
so there better be a good reason for this.  I tracked down the relevant issues
in the [Python issue-tracker](https://bugs.launchpad.net/ubuntu/+source/python-defaults/+bug/123755) and the
[Debian issue-tracker](http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=293932)

The TL;DR is: the `pstats` license includes some language that is incompatible
with Ubuntu and, since the company that originally wrote the software is
long-since defunct, having been absorbed into Disney, there is no way to get
the license updated. Essentially `pstats` is stuck in license purgatory,
available for install by request, but not part of main packages. AFAIK, this is the
only Python standard-library module like this.

Anyway, after getting that sorted out, I was able to successfully run the
nose-profiler.

Just one problem: it immediately raised an `AssertionError`. Turns out,
`hotshot` has a [bug](http://bugs.python.org/issue900092)
relating to how it deals with stack-frames when exceptions are
raised. Worse, `hotshot` is no longer maintained; in fact, it was removed from
Python 3000 entirely.  So, getting this fixed is not only difficult, it's
ultimately moot.

So, to summarize:

1. Ubuntu does not include the `pstats` module from the Python
   standard-library. You need to `apt-get python-profiler` to fetch it.
2. `nose` silently fails if `hotshot` or `pstats` isn't present, and then
   throws a completely unhelpful error regarding its options parsing.
3. `pstats` uses a bogus license that's more-or-less impossible to change
   because the people who created it are long gone.
4. `nose` uses a deprecated profiler, `hotshot`, that has a major bug in it
   that's not likely to be fixed.


Given the above, looks like I'll probably hand-roll a `cProfile` harness and
just be done with it.
