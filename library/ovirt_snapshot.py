#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from datetime import datetime
from ovirtsdk.api import API
from ovirtsdk.xml import params
from time import sleep

DOCUMENTATION = '''
module: ovirt_snapshot
short_description: Creates/Delete/Restores snapshots
description:
    - Longer description of the module
version_added: "0.1"
author: "Karim Boumedhel, @karmab"
notes:
    - Details at https://github.com/karmab/iowa
requirements:
    - ovirt sdk'''

EXAMPLES = '''
- name: Create Ovirt snapshot with specific name
  ovirt_snapshot:
   state: present
   url: https://127.0.0.1
   user: admin@internal
   password: unix1234
   name: Weekly Snapshot
   vm: prout1
'''


def wait_ready(api, name):
    while True:
        jobs = [job for job in api.jobs.list() if job.get_status().get_state() == 'STARTED' and 'VM %s' % name in job.get_description()]
        if not jobs:
            break
        sleep(5)


def wait_up(api, name):
    while api.vms.get(name).status.state != "up":
        sleep(5)


def main():
    argument_spec = {
        "state": {
            "default": "present",
            "choices": ['present', 'absent', 'restored'],
            "type": 'str'
        },
        "url": {"default": 'https://127.0.0.1/ovirt-engine/api', "required": False, "type": "str"},
        "user": {"default": 'admin@internal', "required": False, "type": "str"},
        "password": {"required": True, "type": "str"},
        "vm": {"required": True, "type": "str"},
        "name": {"required": False, "type": "str"},
        "wait": {"default": True, "required": False, "type": "bool"},
        "force": {"default": False, "required": False, "type": "bool"},
        "start": {"default": True, "required": False, "type": "bool"},

    }
    module = AnsibleModule(argument_spec=argument_spec)
    url = module.params['url']
    user = module.params['user']
    password = module.params['password']
    vm = module.params['vm']
    state = module.params['state']
    name = module.params['name']
    wait = module.params['wait']
    force = module.params['force']
    start = module.params['start']
    api = API(url=url, username=user, password=password, insecure=True)
    vmname = vm
    vm = api.vms.get(name=vm)
    if not vm:
        module.fail_json(msg='Vm %s not found' % vmname)
    if state == 'present':
        if name is not None:
            snapshot = next((s for s in vm.snapshots.list() if s.description == name), None)
            if snapshot is not None:
                if not force:
                    module.fail_json(msg='Snapshot %s allready exists' % name)
                else:
                    wait_ready(api, vmname)
                    snapshot.delete()
            description = name
        else:
            now = datetime.now().strftime('%Y%m%d%H%M%S')
            description = "%s_%s" % (vmname, now)
        snapshot = params.Snapshot(description=description)
        wait_ready(api, vmname)
        vm.snapshots.add(snapshot)
        if wait:
            wait_ready(api, vmname)
        result = "%s created" % name
        meta = {'result': result}
        module.exit_json(changed=True, skipped=False, meta=meta)
    elif state == 'restored':
        if name is None:
            module.fail_json(msg='Snapshot name missing')
        else:
            snapshots = [s for s in vm.snapshots.list() if s.description == name]
            if not snapshots:
                module.fail_json(msg='No Snapshot with name %s found' % name)
            elif len(snapshots) > 1:
                module.fail_json(msg='Multiple Snapshots with name %s found' % name)
            else:
                if api.vms.get(vmname).status.state != 'down' and not force:
                    module.fail_json(msg='Cant Restore from snapshot while vm %s is up' % vmname)
                else:
                    api.vms.get(vmname).stop()
                    # api.vms.get(vmname).shutdown()
                    while api.vms.get(vmname).status.state != "down":
                        sleep(5)
                snapshot = snapshots[0]
                action = params.Action(snapshot=snapshot)
                wait_ready(api, vmname)
                vm.preview_snapshot(action)
                wait_ready(api, vmname)
                vm.commit_snapshot(action)
                wait_ready(api, vmname)
                if start:
                    api.vms.get(vmname).start()
                    wait_up(api, vmname)
                snapshot.delete()
                wait_ready(api, vmname)
            meta = {'result': '%s Restored' % name}
            module.exit_json(changed=True, skipped=False, meta=meta)
    elif state == 'absent':
        if name is None:
            module.fail_json(msg='Snapshot name missing')
        else:
            snapshotname = name
            snapshots = [s for s in vm.snapshots.list() if s.description == snapshotname]
            if snapshots:
                for snapshot in snapshots:
                    wait_ready(api, vmname)
                    snapshot.delete()
                    if wait:
                        wait_ready(api, vmname)
                meta = {'result': '%s deleted' % snapshotname}
                module.exit_json(changed=True, skipped=False, meta=meta)
            else:
                meta = {'result': '%s not found' % snapshotname}
                module.exit_json(changed=False, skipped=True, meta=meta)

if __name__ == '__main__':
    main()
