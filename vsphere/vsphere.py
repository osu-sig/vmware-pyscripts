import atexit
import os
import ssl
import sys

import pendulum
import pyVim.connect
from pyVmomi import vim, vmodl

from .exceptions import VMNotFoundException

import pprint
pp_ = pprint.PrettyPrinter(indent=2)
pp = pp_.pprint


class vSphere:
    def __init__(self, config):
        self._config = config

        # connect to vSphere
        try:
            self._si = pyVim.connect.SmartConnect(
                host=self._config.VSPHERE_HOST,
                user=self._config.VSPHERE_USERNAME,
                pwd=self._config.VSPHERE_PASSWORD,
                port=self._config.VSPHERE_PORT,
                sslContext=ssl.SSLContext(ssl.PROTOCOL_SSLv23))
        except Exception as e:
            print(f"Error connecting to vSphere host "
                  f"{self._config.VSPHERE_HOST}:\n{e}")
            sys.exit(1)

        atexit.register(pyVim.connect.Disconnect, self._si)

    def get_vms(self, vm_names=None, include_templates=False):
        if vm_names is None:
            is_get_all = True
        else:
            is_get_all = False

        obj_view = self._si.content.viewManager.CreateContainerView(
            self._si.content.rootFolder, [vim.VirtualMachine], True
        )
        all_vms = obj_view.view
        obj_view.Destroy()

        target_vms = set(vm_names)
        res = []
        for vm in all_vms:
            if not include_templates and vm.summary.config.template:
                continue

            if is_get_all:
                res.append(vm)
            elif vm.name in target_vms:
                res.append(vm)
                target_vms.remove(vm.name)
                if len(target_vms) == 0: break

        return res

    def get_vm(self, vm_name):
        res = self.get_vms([vm_name])
        if len(res) == 0:
            raise VMNotFoundException(f"{vm_name} not found")
        return res[0]

    def get_snapshots(self, vm_snaplist, snap_name=None, filter_by=None):
        filter_older_than = False
        if filter_by is not None:
            if 'created_older_than' in filter_by.keys():
                filter_older_than = True
                date_cutoff = pendulum.now().subtract(
                    days=filter_by['created_older_than'])

        res = []
        for snap in vm_snaplist:
            passed_filter_checks = True
            if snap_name is not None:
                if snap_name != snap.name:
                    passed_filter_checks = False
            if filter_older_than:
                if pendulum.instance(snap.createTime) > date_cutoff:
                    passed_filter_checks = False

            if passed_filter_checks:
                res.append(snap)

            res = res + self.get_snapshots(snap.childSnapshotList,
                                           snap_name, filter_by)

        return res
