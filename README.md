# vmware-pyscripts

A collection of python scripts to automate and extract reporting information from vCenter

**TOC**
- [Requirements](#requirements)
- [Install](#install)
- [Script Index](#script-index)
    - [snapshot.py](#snapshotpy) - list and manage VM snapshots
    - [sessionCtrl.py](#sessionctrlpy-deprecated) [**DEPRECATED**] - manage vCenter sessions

## Requirements

* Python 3.8+

pip packages:

- [pyvmomi](https://github.com/vmware/pyvmomi)
- [pendulum](https://pendulum.eustace.io/)
- [docopt-ng](https://github.com/jazzband/docopt-ng)

Full tested package requirements are defined in `requirements.txt`

These scripts have been tested on VMware vSphere 7.0.3 using Python 3.11.

## Install

Using a virtualenv is highly recommended.

1. Install packages in `requirements.txt`.
1. Clone this repo.

## Configuration

1. Copy `vmware-pyscripts.conf-dist` to `vmware-pyscripts.conf` and edit as needed:

```
[main]
# Enable debugging output (yes|no)
EnableDebugging = yes
# Timezone for output (format: America/Los_Angeles)
Timezone = America/Los_Angeles
# vSphere hostname
VSphereHost = changeme
# vSphere port
VSpherePort = 443
# Enable verification of vSphere SSL certificate (yes|no)
VSphereVerifySSL = yes
```

2. Set vSphere API credentials as environment variables:
- `VSPHERE_USERNAME`
- `VSPHERE_PASSWORD`

## Script Index

### snapshot.py

```
Usage:
    snapshot.py list [VM_NAME ...] [--older-than=DAYS_AGO] [--output-width=CHARS]
    snapshot.py create VM_NAME SNAP_NAME [SNAP_DESC] [--snap-mem] [--quiesce]
    snapshot.py delete VM_NAME (SNAP_NAME | --all)
```

### sessionCtrl.py (DEPRECATED)

A script for managing vCenter sessions: view current sessions, terminate a session, or terminate sessions idle longer than a given amount of time.
