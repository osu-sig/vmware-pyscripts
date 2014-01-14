# vmware-pyscripts

A collection of python scripts to automate and extract reporting information from vCenter.

**TOC**
- [Requirements](#requirements)
- [Install](#install)
- [Script Index](#script-index)
    - [sessionCtrl.py](#sessionctrlpy) - manage vCenter sessions

## Requirements

These scripts have been tested on VMware vSphere 5.1.

```
pyvmomi==5.5.0
python-dateutil==2.2
```

## Install

1. Install [pyVmomi](https://github.com/vmware/pyvmomi).
1. Clone this repo.
1. Copy `config.yml-dist` to `config.yml` and edit as necessary.

## Script Index

### sessionCtrl.py

A script for managing vCenter sessions: view current sessions, terminate a session, or terminate sessions idle longer than a given amount of time.
