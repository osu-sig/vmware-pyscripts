#!/usr/bin/env python
"""snapshot.py

Usage:
    snapshot.py list [VM_NAME ...] [--older-than=DAYS_AGO] [--output-width=CHARS]
    snapshot.py create VM_NAME SNAP_NAME [SNAP_DESC] [--snap-mem] [--quiesce]
    snapshot.py delete VM_NAME (SNAP_NAME | --all)

Options:
    -h --help   Show this screen
    --version   Show version
"""
import sqlite3
import sys
from collections import defaultdict

import pendulum
from docopt import docopt
from pyVim.task import WaitForTask

import config
import vsphere

import pprint
pp_ = pprint.PrettyPrinter(indent=2)
pp = pp_.pprint


class SnapshotControl:
    def __init__(self):
        self.config = config.GlobalConfig()
        self.vsapi = vsphere.vSphere(self.config)

    def list_snapshots(self, vm_names=None, older_than=None, output_width=None):
        """ List snapshots on VM(s)

        Optional:
          vm_names   - list of names of VMs to display snapshots for, defaults
                       to all VMs if None
          older_than - only show snapshots older than the given number of days

        Returns:
          printed report of snapshots for the given VM(s)
        """
        if vm_names is None:
            # get all VMs
            vms = self.vsapi.get_vms()
        else:
            # get specific VMs
            vms = self.vsapi.get_vms(vm_names)

        # setup in-memory sqlite datastore
        snapdb = sqlite3.connect(':memory:')
        cursor = snapdb.cursor()
        cursor.execute('CREATE TABLE snapshots '
                       '(vm_name TEXT, snap_name TEXT, created INTEGER)')

        # get snapshots for VMs
        for vm in vms:
            if vm.snapshot is None:
                continue

            if older_than is None:
                tmpsnaps = self.vsapi.get_snapshots(vm.snapshot.rootSnapshotList)
            else:
                tmpsnaps = self.vsapi.get_snapshots(
                    vm.snapshot.rootSnapshotList,
                    filter_by={'created_older_than': older_than})

            for snap in tmpsnaps:
                created = pendulum.instance(snap.createTime).int_timestamp
                cursor.execute(f"INSERT INTO snapshots VALUES (?,?,?)",
                               (vm.name, snap.name, created))

        # get snaps in sorted order
        if older_than is None:
            snaps = cursor.execute(
                "SELECT * FROM snapshots "
                "ORDER BY vm_name ASC, created ASC").fetchall()
        else:
            snaps = cursor.execute(
                "SELECT * FROM snapshots "
                "ORDER BY created ASC, vm_name ASC").fetchall()

        if len(snaps) == 0:
            print("No snapshots found.")
            return

        # calculate field widths for pretty output
        DATE_FORMAT_WIDTH = 23  # our chosen date format is 23 chars wide

        vmname_width = cursor.execute(
            "SELECT max(length(vm_name)) FROM snapshots").fetchone()[0] + 1
        if output_width is None:
            snapname_width = cursor.execute(
                "SELECT max(length(snap_name)) "
                "FROM snapshots").fetchone()[0] + 1
        else:
            # set minimum width of 80
            if output_width < 80:
                output_width = 80

            # calculate snapname column width dynamically
            snapname_width = output_width - vmname_width - DATE_FORMAT_WIDTH

            # enforce a sane minimum width if VM names get unruly
            if snapname_width < 10:
                snapname_width = 10
                vmname_width = vmname_width - 10

        # output to print is stored here
        output = ''

        # generate pretty header
        output = f"{'VM':<{vmname_width}}{'Snapshot':<{snapname_width}}Created On\n"
        total_width = vmname_width + snapname_width + DATE_FORMAT_WIDTH
        for x in range(0, total_width):
            output += '-'
        output += "\n"

        # generate report
        for snap in snaps:
            vm_name = snap[0][:vmname_width-1]
            snap_name = snap[1][:snapname_width-1]
            created = (
                pendulum.from_timestamp(snap[2])
                .in_tz(self.config.TIMEZONE)
                .format('YYYY-MM-DD HH:mm:ss zz')
            )
            output += f"{vm_name:<{vmname_width}}{snap_name:<{snapname_width}}{created}\n"

        print(output.rstrip())

    def create_snapshot(self, vm_name, snap_name, snap_desc=None,
                        snap_mem=False, snap_quiesce=False):
        """ Create a snapshot on a VM
        """
        try:
            vm = self.vsapi.get_vm(vm_name)
        except vsphere.VMNotFoundException:
            print(f"VM not found: {vm_name}")
            sys.exit(1)

        print(f"Creating snapshot for VM {vm.name}...")
        WaitForTask(vm.CreateSnapshot(name=snap_name,
                                      description=snap_desc,
                                      memory=snap_mem,
                                      quiesce=snap_quiesce))
        print("Done.")
        self.list_snapshots([vm_name])

    def delete_snapshot_by_name(self, vm_name, snap_name):
        vm = self.vsapi.get_vm(vm_name)
        if not vm:
            print(f"VM not found: {vm_name}")
            sys.exit(1)

        if vm.snapshot is None:
            print(f"No snapshots found for VM {vm.name}")
            sys.exit(0)

        snaps = self.vsapi.get_snapshots(vm.snapshot.rootSnapshotList, snap_name)

        if len(snaps) > 1:
            print(f"Found {len(snaps)} snapshots named '{snap_name}'")
            print("Use the vCenter UI to delete the correct one until this "
                  "feature is added in the future.")
            self.list_snapshots([vm_name])
            return
        elif len(snaps) == 0:
            print(f"Snapshot {snap_name} not found on VM {vm_name}")
            sys.exit(1)

        snap = snaps[0]
        print(f"Deleting snapshot '{snap.name}' from {vm.name}...")
        WaitForTask(snap.snapshot.RemoveSnapshot_Task(removeChildren=False))
        print("Done.")
        self.list_snapshots([vm_name])

    def delete_snapshots(self, vm_name):
        vm = self.vsapi.get_vm(vm_name)
        if not vm:
            print(f"VM not found: {vm_name}")
            sys.exit(1)

        if vm.snapshot is None:
            print(f"No snapshots found for VM {vm.name}")
            sys.exit(0)

        snaps = self.vsapi.get_snapshots(vm.snapshot.rootSnapshotList)

        for snap in snaps:
            print(f"Deleting snapshot '{snap.name}' from {vm.name}...")
            WaitForTask(snap.snapshot.RemoveSnapshot_Task(removeChildren=False))
        print("Done.")
        self.list_snapshots([vm_name])


if __name__ == '__main__':
    args = docopt(__doc__, version='snapshot.py 0.1')
    # pp(args)

    snapCtrl = SnapshotControl()

    if args['list']:
        if args['VM_NAME']:
            vm_names = args['VM_NAME']
        else:
            vm_names = None

        if args['--output-width'] is None:
            width = None
        else:
            width = int(args['--output-width'])

        if args['--older-than'] is None:
            snapCtrl.list_snapshots(vm_names, output_width=width)
        else:
            snapCtrl.list_snapshots(vm_names, int(args['--older-than']),
                                    output_width=width)
    elif args['create']:
        vm_name = args['VM_NAME'][0]  # arg always comes from docopt as a list

        snapCtrl.create_snapshot(vm_name, args['SNAP_NAME'], args['SNAP_DESC'],
                                 args['--snap-mem'], args['--quiesce'])
    elif args['delete']:
        vm_name = args['VM_NAME'][0]  # arg always comes from docopt as a list

        if args['--all'] is False:
            snapCtrl.delete_snapshot_by_name(vm_name, args['SNAP_NAME'])
        else:
            snapCtrl.delete_snapshots(vm_name)
