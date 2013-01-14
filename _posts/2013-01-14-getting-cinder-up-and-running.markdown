---
layout: post
title: Getting Cinder Up and Running
---

Lately I've been delving more-and-more into how Openstack handles block
storage in the cloud. As part of that effort, I went through the process of
setting up Cinder, Openstack's block-stroage API, wiring it up to Nova, and
then using it to dynamically attach a volume to a running instance.

This blog entry is just a quick summary of what I've learned in the process
with special attention paid to a few gotchas I ran into along the way.


What is Cinder?
===============

Cinder at its heart is an API which exposes commands to create and destroy
volumes within an Openstack installation. Originally this code lived in the
Nova compute-service as `nova-volume`, but was extracted to become its own
component, complete with a separate API, language bindings and its own
command-line tool (`cinderclient`).

All this is relatively straightforward, but I think two points are worth
mentioning: 

First, Cinder is really just an API that happens to ship with a backend you
can use out of the gate. This means you could use Cinder itself for storage
(using its LVM and ISCSI drivers) or you could write a *Cinder compliant*
storage-service to suit your own needs and then use that instead. (If you're
already familiar with Openstack, you'll recognize this same quality in the
virt and network layers as well.)

Second, Cinder does not understand compute, but compute does understand
Cinder. This means, areas where volumes and compute interesect, like in the
attaching or detaching of volumes, are the responsibility of Nova.  This
means, to use Cinder with Nova, you will have to use both `cinderclient` to
create the volume, and then `novaclient` to attach it.

Now that we have a high-level understanding of what Cinder is and isn't, let's
go ahead install and actually use it. In particular, we're going to:

1. Install and configure Cinder using it's LVM+ISCI backend

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


2. Copy the base configuration into /etc/cinder

    $ cp -R etc/cinder /etc/

    $ mv /etc/cinder/cinder.conf.sample /etc/cinder.conf


3. Configure Cinder to use MySQL by adding this line to
   /etc/cinder/cinder.conf

    sql_connection=mysql://root@127.0.0.1/cinder

4. Create database and load schema:

    $ mysqladmin -uroot create cinder

    $ ./bin/cinder-manage db sync

5. Configure LVM to manage the underlying block-storage. In my case, I'm using
   a second partition but you could also use a loopback device as well:

    $ apt-get install lvm2

    $ vgcreate cinder-volumes /dev/xvda2

    $ pvcreate /dev/xvda2
      

6. Install TGT which will expose the block-storage over ISCSI:

    $ apt-get install tgt

7. Configure tgt by editing /etc/tgt/targets.conf to add this line. Make sure
   to modify that line to point the `volumes` directory in `cinder` git repo:

    include /home/rick/Documents/code/openstack/cinder/volumes/*

8. Start the `tgt` daemon. This may display some errors, you can ignore those
   for now. (see http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=577925)

    $ /usr/sbin/tgtd

9. Start the cinder API and associated services

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
Cinder endpoint resides. To keep it simple, I'm not using Keystone
(Openstack's Identity Service), and instead hard-coding the endpoint with the
`cinder_endpoint_template` configuration:

1. Add the following to your nova.conf

  volume_api_class=nova.volume.cinder.API
  cinder_endpoint_template=http://localhost:8776/v1/%(project_id)s

2. Restart nova-api and nova-compute


Provision a 1 GB Volume
=======================


With Cinder, Cinderclient and Nova properly configured, we can now create, attach and
use our volumes.

1. Create a 1GB volume

    $ cinder create --display_name cindervol 1

2. Check to see it exists:

    $ cinder list
    +--------------------------------------+-----------+-----------------+------+-------------+----------+-------------+
    |                  ID                  |   Status  |   Display Name  | Size | Volume Type | Bootable | Attached to |
    +--------------------------------------+-----------+-----------------+------+-------------+----------+-------------+
    | da6ae608-4673-4b24-acd4-75e527b5969a | available |    cindervol    |  1   |     None    |  false   |             |
    +--------------------------------------+-----------+-----------------+------+-------------+----------+-------------+



Create an Instance and Attach the Volume
========================================


1. Create the instance using whatever image and flavor combo you want.

    $ nova create --image <YOUR IMAGE> --flavor 1 myinstance


2. Attach the volume to the running instance. To do this, you'll need so
   specify what device indentifier the volume should have within the instance.
   Make sure you don't accidentally use a device identifier that's already
   been used. In this case, I know that `/dev/xvdc` is being used for swap and
   that `/dev/xvdb` is free, so I'll use that:


  nova volume-attach myinstance da6ae608-4673-4b24-acd4-75e527b5969a /dev/xvdb


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
  root@myinstance:~# df -h
  Filesystem            Size  Used Avail Use% Mounted on
  /dev/xvda1             12G  738M   11G   7% /
  tmpfs                  28M     0   28M   0% /lib/init/rw
  udev                   15M   44K   15M   1% /dev
  tmpfs                  28M     0   28M   0% /dev/shm
  /dev/xvdb            1008M  1.3M  956M   1% /cindervol


We can see from the output, it has the correct size, so we're good to go.




OOOOOOOOLLLLLLLDDDDD



Setting up Cinder
=================


Lately I've been looking into how Openstack handles block-storage in the
cloud and as part of that effort I've spent some time setting up Cinder,
Openstack's block-storage API, and getting that to talk to my existing Nova
installation. This blog-entry details some of the hang-ups I ran into in this
process, both conceptually and technically, so hopefully others don't make the
same mistakes.

First of all...


What Is Cinder?
===============

Cinder is a service that lets users create and manage block-storage devices
('volumes') that can then be connected ('attached') to other Openstack
services. In this case, we're interested in:

1. Creating a Cinder volume, say, 1GB in size

2. Creating a Nova instance

3. Attaching the volume to the instance

4. Formatting and mounting the volume within the instance so we can use it.


To do this, we first need to install Cinder and then wire it up to Nova so the
two can communicate with each other.


Installing Cinder
=================

We'll be installing Cinder from the perspective a developer not an operator,
meaning we'll be running Cinder directly out of a git repository. (Running this
way was immensely helpful in getting things setup, since I could sprinkle
debug statements throughout the code until I could figure out which
configuration was missing.)


1. Clone the repo from the Openstack repo on Github:

    git clone git://github.com/openstack/cinder.git


2. Copy base configuration into /etc/cinder

    cp -R etc/cinder /etc/

    # Use the sample config as a starting point
    mv /etc/cinder/cinder.conf.sample /etc/cinder.conf


3. Configure Cinder to use MySQL by adding this line to
   /etc/cinder/cinder.conf

    sql_connection=mysql://root@127.0.0.1/cinder

4. Create database and load schema:

      mysqladmin -uroot create cinder
      ./bin/cinder-manage db sync

5. We will be using LVM to manage the volumes, so we need to install LVM if we
   haven't already and then create a `cinder-volumes` volume group.
      apt-get install lvm2
      vgcreate cinder-volumes /dev/xvda2
      pvcreate /dev/xvda2
      

6. We will be exposing the LVM volumes over ISCSI which is handled via the
   `tgt` program:

      apt-get install tgt

7. Configure tgt by editing /etc/tgt/targets.conf to add this line:

    include /home/rick/Documents/code/openstack/cinder/volumes/*

    Where you use your path to source.


8. Start the tgt daemon. This may display some errors, you can ignore those
   for now. (see http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=577925)

    /usr/sbin/tgtd

9. Start the cinder API and associated services

    ./bin/cinder-all


Cinder now should be up and running but you still need a way to query and
manage it. To do this, we'll need to install cinderclient.


Installing Cinderclient
=======================

Luckily this is much simpler than installing Cinder itself.

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

    $ cinder list


Since we haven't created any volumes yet, that should be empty.


Create Cinder Volume
====================

Now that we have Cinderclient talking to Cinder, we can use that to create a
1GB volume

1. Run

    $ cinder create --display_name cindervol 1

2. Check to see it exists:

    $ cinder list
    +--------------------------------------+-----------+-----------------+------+-------------+----------+-------------+
    |                  ID                  |   Status  |   Display Name  | Size | Volume Type | Bootable | Attached to |
    +--------------------------------------+-----------+-----------------+------+-------------+----------+-------------+
    | da6ae608-4673-4b24-acd4-75e527b5969a | available |    cindervol    |  1   |     None    |  false   |             |
    +--------------------------------------+-----------+-----------------+------+-------------+----------+-------------+


Configuring Nova
================

We now have a volume but we still need to attach it to a Nova compute
instance. To do this, we need to tell Nova to use the Cinder API and where to
find it.


1. Add the following to your nova.conf

  volume_api_class=nova.volume.cinder.API
  cinder_endpoint_template=http://localhost:8776/v1/%(project_id)s

2. Restart nova-api and nova-compute



Create an Instance
==================

1. Run

  nova create --image <YOUR IMAGE> --flavor 1 myinstance


Attach the Volume
=================

1. Attach the volume to the instance as /dev/xvdb:

  nova volume-attach myinstance da6ae608-4673-4b24-acd4-75e527b5969a /dev/xvdb


Use the Attached Volume
=======================

Now that the volume has been attached, you need to perform some setup within
the instance so that you can use it.

1. First ensure that the device is present:

  $ ls /dev/xvdb
  /dev/xvdb

2. Assuming it's present, you can now add a format it

  $ mkfs /dev/xvdb

3. Mount the newly formatted disk

  $ mkdir /cindervol
  $ mount /dev/xvdb /cindervol

4. Verify correct size:

  $ df -h
  root@myinstance:~# df -h
  Filesystem            Size  Used Avail Use% Mounted on
  /dev/xvda1             12G  738M   11G   7% /
  tmpfs                  28M     0   28M   0% /lib/init/rw
  udev                   15M   44K   15M   1% /dev
  tmpfs                  28M     0   28M   0% /dev/shm
  /dev/xvdb            1008M  1.3M  956M   1% /cindervol
