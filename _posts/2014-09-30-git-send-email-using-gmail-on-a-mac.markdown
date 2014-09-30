---
layout: post
title: git send-email using Gmail on a Mac
---


Some open source projects, most famously the Linux kernel, require patches to
be submitted by way of an email to their mailing list.

If you're used to submitting patches using [GitHub](https://github.com)
Pull-Requests or [Gerrit](https://code.google.com/p/gerrit/) reviews, the idea
of sending a patch by email can be a bit daunting at first.

Luckily, it's actually pretty simple! Here's how:


Assumptions
===========

...but first. Let's start with some assumptions.

* You're using a Mac
* You have Homebrew installed
* You're using Gmail


Configure System
================

Gmail requires email to be sent via TLS which the Homebrew package of `git`
doesn't support by default. So, the first thing we need to do is install the
SSL Perl module:

    brew install cpanm
    cpanm --sudo Net::SMTP::SSL


In general, `--sudo` is not a good idea with Homebrew, but in this case it
makes things easier by allowing `git` to find the Perl module in its default
search path. (If you want to avoid `sudo`, it's possible, just more work...)


Setup Google
============

If you're not using 2-factor authentication (2fa) for Gmail, go set that up first
(seriously!).

Now that you have 2fa setup, you need to generate an application-specific
password for `git send-email`.

Go to Gmail's "Account" Settings, and click the "Security" tab.

Follow the steps to generate a application-specific password and copy it into
your clipboard.


Setup .gitconfig
================

The next step is to add your Gmail settings to your `.gitconfig` file.

Open up your `.gitconfig` and add the following stanza filled in with your
personal information:

[sendemail]
    from = Your name <your-username@gmail.com>
    smtpserver = smtp.gmail.com
    smtpuser = your-name@gmail.com
    smtppass = your-application-specific-password
    smtpencryption = tls
    chainreplyto = false
    smtpserverport = 587


Format Patch
============

At tpis point, `git` should be configured to send email--you just need to
create your patch file and send it.

To create your patch, you use the `git format-patch` command which will
generate a patch in the `mbox` format,  appropriate for sending via email.

A common-case is to want to send the last commit. The command to do that would
be:

    git format-patch --to email@mailinglist.org HEAD^

This will create a file named something like `0001-name-of-my-patch.patch` in
your repo's base directory.


Send Email
==========

Now that you've created the patch file, you just need to send it to the
mailing list. To do that, use the `git send-email` command.

The command is:

    git send-email 0001-name-of-my-patch.patch


If everything worked properly, you should now see your patch show up on the
mailing-list.


Advanced - Multiple patch files
===============================

If you're submitting multiple patches to the ML, it's convenient to store the
patches in a separate directory so you can email and delete when you're done
all at once.

To do this, use the `-o` option to `git-format-patch` to specify the output
directory:

    # Create patch files for last 5 commits
    git format-patch -o outgoing HEAD~5

Now you can send these patches in one-shot using

    git send-email outgoing/*.patch

Once the email has been sent, you can clean up with,

    rm outgoing/*.patch
    rmdir outgoing
