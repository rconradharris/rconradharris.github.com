---
layout: post
title: Getting Cinder Up and Running
---

Lately I've been delving more-and-more into how Openstack handles block
storage. As part of that effort, I went through the process of setting up
Cinder, Openstack's block-storage API, wiring it up to Nova, and then using it
to dynamically attach a volume to a running Nova instance.

This blog entry is just a quick summary of what I learned in the process with
special attention paid to a few gotchas I ran into along the way.

What is Cinder?
===============

Cinder at its heart is an API which exposes commands to create and destroy
volumes within an Openstack installation. Originally this code lived in the
Nova compute service as `nova-volume`, but was extracted to become its own
component, complete with a separate API, language bindings and its own
command-line tool (`cinderclient`).

All this is relatively straightforward, but I think two points are worth
mentioning: 

First, Cinder is really just an API that happens to ship with a backend you
can use out of the box. This means you could use Cinder itself for storage
(using its LVM and ISCSI drivers) or you could write a *Cinder compliant*
storage-service to suit your own needs.  (If you're already familiar with
Openstack, you'll recognize this same plugin pattern used most across projects.)

Second, Cinder does not understand compute, but compute understands Cinder.
This means areas where volumes and compute intersect, like in the attaching
or detaching of volumes, are the responsibility of Nova:  to use Cinder with
Nova, you will have to use both `cinderclient` to create the volume, and then
`novaclient` to attach it.

Now that we have a basic understanding of Cinder, let's install and actually
use it. In particular, we're going to:

1. Install and configure Cinder using its LVM/ISCI backend

2. Provision a 1 GB volume using `cinderclient`.

3. Create a Nova instance and attach the volume using `novaclient`.

4. Log into the instance and setup the volume to be usable space.


Installation and Configuration
==============================

For this step, we're going to be installing Cinder from the perspective of a
developer, meaning we're going to fetch source code and run `cinder` directly
out of the git repository.


Install Cinder
--------------

1. Clone the repo from the Openstack repo on Github:

        $ git clone git://github.com/openstack/cinder.git

2. Copy the base configuration into `/etc/cinder`:

        $ cp -R etc/cinder /etc/

        $ mv /etc/cinder/cinder.conf.sample /etc/cinder.conf


3. Configure Cinder to use MySQL by adding this line to
   `/etc/cinder/cinder.conf`:

        sql_connection=mysql://root@127.0.0.1/cinder

4. Create database and load schema:

        $ mysqladmin -uroot create cinder
        $ ./bin/cinder-manage db sync

5. Configure LVM to manage the underlying block-storage. In my case, I'm using
   a second partition but you could also use a loopback device as well:

        $ apt-get install lvm2
        $ vgcreate cinder-volumes /dev/xvda2
        $ pvcreate /dev/xvda2
      
6. Install [tgt](http://stgt.sourceforge.net/) which will expose the
   block-storage over ISCSI:

        $ apt-get install tgt

7. Configure tgt by editing /etc/tgt/targets.conf to add this line. Make sure
   to modify that line to point the `volumes` directory in `cinder` git repo:

        include /home/rick/Documents/code/openstack/cinder/volumes/*

8. Start the `tgt` daemon. This may display some errors on startup. Those can
   be ignored for now (see
   http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=577925):

        $ /usr/sbin/tgtd

9. Start the cinder API and associated services:

        $ ./bin/cinder-all


Cinder now should be up and running but you still need a way to query and
manage it. To do this, we'll need to install `cinderclient`.


Install Cinderclient
--------------------


1. Clone python-cinderclient from the Openstack GitHub repo:

        $ git clone git://github.com/openstack/python-cinderclient.git

2. Now you need to install it

        $ python setup.py develop

3. Like other Openstack command-line tools, cinderclient uses environment
   variables for configuration, so you should create a config file and then
   source it, like:

        $ cat cinder.env 
        export OS_AUTH_URL=http://127.0.0.1:8776/v1/
        export OS_USERNAME=<YOUR_USERNAME>
        export OS_PASSWORD=<YOUR_PASSWORD>
        export OS_TENANT_NAME=openstack

        $ . cinder.env

4. Now you can test that it works by running

        $ cinder list  # <- should be emty since don't have any volumes yet


Configuring Nova to talk to Cinder
----------------------------------

In order to attach volumes created with Cinder, Nova needs to know where the
Cinder endpoint resides. To keep it simple, I'm not using
[Keystone](http://docs.openstack.org/developer/keystone/) (Openstack's
Identity Service), and instead hard-coding the endpoint with the
`cinder_endpoint_template` configuration:

1. Add the following to your `nova.conf`:

        volume_api_class=nova.volume.cinder.API
        cinder_endpoint_template=http://localhost:8776/v1/%(project_id)s

2. Restart nova-api and nova-compute


Provision a 1 GB Volume
=======================


With Cinder, Cinderclient and Nova configured, we can now create, attach and
use volumes.

1. Create a 1GB volume

        $ cinder create --display_name cindervol 1

2. Check to see that it exists:

        $ cinder list
        +--------------------------------------+-----------+-----------------+------+-------------+----------+-------------+
        |                  ID                  |   Status  |   Display Name  | Size | Volume Type | Bootable | Attached to |
        +--------------------------------------+-----------+-----------------+------+-------------+----------+-------------+
        | da6ae608-4673-4b24-acd4-75e527b5969a | available |    cindervol    |  1   |     None    |  false   |             |
        +--------------------------------------+-----------+-----------------+------+-------------+----------+-------------+


Attach Volume to Instance
=========================


1. Create the instance using whatever image and flavor combo you want:

        $ nova create --image <YOUR IMAGE> --flavor 1 myinstance

2. Attach the volume to the running instance. To do this, you'll need so
   specify what device identifier the volume should have within the instance.
   Make sure you don't accidentally use a device identifier that's already
   been used. In this case, I know that `/dev/xvdc` is being used for swap and
   that `/dev/xvdb` is free, so I'll use that:

         $ nova volume-attach myinstance da6ae608-4673-4b24-acd4-75e527b5969a /dev/xvdb


Use the Attached Volume
=======================

Now that the volume has been attached, you need to perform some setup within
the instance so that you can actually use it.

1. First ensure that the device is present:

        $ ls /dev/xvdb
        /dev/xvdb

2. Assuming it's present, you can now add a format it. If you want to use a
   specific filesystem, just add the appropriate options:

        $ mkfs /dev/xvdb

3. Mount the newly formatted disk

        $ mkdir /cindervol
        $ mount /dev/xvdb /cindervol

4. Verify that the newly mounted volume has the correct size.

        $ df -h
        Filesystem            Size  Used Avail Use% Mounted on
        /dev/xvda1             12G  738M   11G   7% /
        tmpfs                  28M     0   28M   0% /lib/init/rw
        udev                   15M   44K   15M   1% /dev
        tmpfs                  28M     0   28M   0% /dev/shm
        /dev/xvdb            1008M  1.3M  956M   1% /cindervol


We can see from the output, the newly-minted volume has the correct size so
the process has worked end-to-end.

Further Reading
================

The minimal Cinder setup we just created is great for learning the code and
see how things fit together but, as you become more familiar with it, you're
probably going to want to expand to a more complex setup to take advantage of
advanced features, for example Keystone integration. Your two best bets here
are diving into the code itself (daunting at first, but print/raise statements
are your friend) and checking out the online
[documentation](http://docs.openstack.org).
