---
layout: post
title: A Todo List Workflow That Works
---

Introduction
============

My work-life revolves around my TODO list. It's how I structure my day, it
gives me short-term goals to keep me motivated, and provides an easy way to
recall what I did the day before for the daily standup.

The problem I've run into is that todo list apps universally suck. They're
often slow, mouse-centric, low information density, and most importantly
completely inflexible. As a tool you use all day, your todo list needs to
completely match how you work or you'll end feeling miserable and eventually
abandon it (see Jeff Atwood's polemic
[Todon't](http://www.codinghorror.com/blog/2012/10/todont.html)).

The only solution I've found to work for me long-term (over 2 years and
counting) is to abandon the idea that a single *tool* can solve this problem,
and instead develop a *workflow* that helps manage your day. The rest of this
blog entry details my approach and may serve as inspriation as you develop
your own process for getting-things-done.

Design
======

The workflow I've adopted wasn't really designed, but evolved over the years
from trying a variety of approaches, finally settling on a relatively stable
set of repeatable steps. Looking back, though, the things I've found important
have been:

* **FREEFORM:** The TODO list should be a single text file with minimal structure.
  This means that if you have raw data, tracebacks, or anything else, just paste it
  directly into the TODO list. Almost always, this data will be much more
  useful to you then the short-description that todo-list apps require.

* **DAY-CENTRIC:** The list should be broken up into days. This allows you to see
  what you did yesterday at a glance (useful for standups). This also
  allows you to, upfront, set a *personal* goal for what you expect to get
  done that day. I find this motivating, not guilt-inducing.

* **REVERSE CHRON:** New entries should be at the top, older entries at the
  bottom. This means when you open the file up, you're immediately ready to
  add a new entry.

* **KEEP IT SIMPLE:** The temptation will arise to try to automate everything. Don't!
  The goal should be to have a process that stays out of your way, not one
  that minimizes the number of keystrokes. Trust me, a few extra keystrokes
  paired with a simple, repeatable workflow, will make you much happier than a
  workflow built around incantations and black-magic.

* **BACKUP:** Once you've developed a decent TODO list, you're going need a way to
  back it up. You could use TimeMachine or the like, but, I find `git`
  provides the extra benefit of giving you a change history for your TODO list.
  Personally, I use my own
  [homefiles](https://github.com/rconradharris/homefiles) tool for this
  purpose (along with backing up all my other documents).


My Workflow
===========


Probably the best way to describe this workflow is just to walk through some
of the basic steps and, where appropriate, describe the few customizations
I've done to `vim` to speed things up while also keeping-it-simple.


Pull Up The List
----------------

This is something you're going to do many, many times a day, so this needs to
be quick. To accomplish this, I've mapped a key sequence to horizontally split
the screen and open the TODO list file in the new pane:


    nmap ,td :new ~/Documents/TODO<CR>


Add Today's Entry
-----------------

Each day gets a date heading and a section devoted to PENDING and DONE tasks
and looks like:

    2012-11-29

    PENDING

    - Not started yet

    DONE

    - Finished this one


Rather than having to type this out each day, I've automated this part as
well:

    nmap ,nd :r! date +"\%Y-\%m-\%d"<CR>$"="\nPENDING\n\n\n\nDONE\n\n"<CR>pjjj"="- "<CR>pA

This creates the entry and drops you into insert mode on the first pending item for
the day.


Add a Pending Task
------------------

To add a task, just create a new line under the PENDING section. Remember,
this document is completely freeform, so put anything you want here:

    PENDING

    - Fix whatever's causing this:

    2012-11-29 21:47:59 TRACE nova   File "/opt/stack/nova/nova/compute/manager.py", line 3135, in update_available_resource
    2012-11-29 21:47:59 TRACE nova     nodenames = self.driver.get_available_nodes()
    2012-11-29 21:47:59 TRACE nova   File "/opt/stack/nova/nova/virt/driver.py", line 768, in get_available_nodes
    2012-11-29 21:47:59 TRACE nova     return [s['hypervisor_hostname'] for s in stats]
    2012-11-29 21:47:59 TRACE nova KeyError: 'hypervisor_hostname'
    2012-11-29 21:47:59 TRACE nova 


Mark a Task Done
----------------

Marking a task done is accomplished by cutting and pasting the item from the
PENDING into the DONE section for the day.

    DONE

    - Fix whatever's causing this:

    2012-11-29 21:47:59 TRACE nova   File "/opt/stack/nova/nova/compute/manager.py", line 3135, in update_available_resource
    2012-11-29 21:47:59 TRACE nova     nodenames = self.driver.get_available_nodes()
    2012-11-29 21:47:59 TRACE nova   File "/opt/stack/nova/nova/virt/driver.py", line 768, in get_available_nodes
    2012-11-29 21:47:59 TRACE nova     return [s['hypervisor_hostname'] for s in stats]
    2012-11-29 21:47:59 TRACE nova KeyError: 'hypervisor_hostname'
    2012-11-29 21:47:59 TRACE nova 

    - Something else I did earlier


Trust me, `ddjjjp` will eventually feel way more satifying than clicking a checkbox.


Moving Unfinished Work
----------------------

Invariably you're going to have tasks that span multiple days. In this case,
you just push forward any unfinished tasks by cutting them from the previous
day's PENDING section and pasting them into today's.

This means, ideally, the PENDING sections for previous days should be empty.
It's a good idea to periodically scan down the list to make sure that
condition is holding.


Handling Sub-Tasks
------------------

Subtasks are added by indenting them underneath the parent task, like so:

    PENDING

    - Main task
      - Subtask1
      - Subtask2

The key difference between sub-tasks and top-level tasks is that sub-tasks
are't moved into the DONE section when completed. Instead, a `[DONE]` tag is
added to the end of the line. When all of the sub-tasks are tagged as done,
I then cut-and-paste the top-level-task and its associated subtasks into the
DONE section to mark it completed:

    DONE

    - Main task
      - Subtask1 [DONE]
      - Subtask2 [DONE]


At the risk of over-auotmation, I also have a keybinding for this task:

    nmap ,dn A [DONE]<ESC>


That's It
=========

That's all there is to it. With these simple operations, I'm able to keep
track of what I have left to do, and see what I've done without having to futz
with a separate tool.

And as you can see, this workflow is simple, flexible, and most importantly, stays
out of your way. I find myself spending very little time actively thinking
about my TODO list, and instead, rely on habits I've built up using this on a
day-to-day basis to move quickly from task to task.

There's only enough structure to be useful and not a bit more.

It's with this in mind, that I challenge you to think about the TODO list app
that you use and ask yourself how well it matches up with how you *really*
work. And if you find it wanting, hopefully this blog post serves as an
inspriation for you to create a process that 100% works for you.

Postscript
==========

Here are some entries from my TODO file that show how it (and this process)
have evolved over time:


First Entry
-----------

    2010/10/13
    ==========

    #info {yesterday} Verified #T2164 for dabo, Fixed Python 2.6 compat bug in
    glance, inter-review call
    #info {yesterday} Troubleshot Iback issue w/ hinch, Drafted email explaining Iback enabling in Backstage
    #info {today} grabbing and working a  blueprint for glance, review mergeprops
    etc
    done

First Entry w/ PENDING and DONE Sections
----------------------------------------

    2011-06-02

    PENDING

    DONE

    - Writing blueprint for GlanceZones (pending feedback)
    - Work on jk0's bug - decided to punt that to next sprint
    - Fix 2b per B Waldons comments
    - Demo Prep
    - Looking at glance package issues with murkk, looks like ubuntu package is
      built incorrectly, call `glance manage db sync` instead `db_sync` 
    - Got comments from Jaypipes and Dubs on Glance Zones
    - Reviewed JayPipes S3 Patch


First Entry w/ Sub-Tasks Tagged with DONE
-----------------------------------------

    2012-07-09

    PENDING

    DONE

    - Fix migration
      - Refactor migration [DONE]
      - Make migration use import_vhd [DONE]
