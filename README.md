# ovirt_snapshot repository

[![Build Status](https://travis-ci.org/karmab/ovirt_snapshot.svg?branch=master)](https://travis-ci.org/karmab/ovirt_snapshot)

Simple ovirt_snapshot using ovirtsdk3 and allowing:
 
 - snapshot creation
 - snapshot deletion
 - snapshot preview/commit on a single step


## REQUIREMENTS

ovirt-engine-sdk-python needs to exist on the target node so that would typically be your engine host


## BASIC TESTING

```
ansible-playbook test.yml
```

```
  - name: Create Ovirt snapshot
    ovirt_snapshot:
     state: present
     url: https://127.0.0.1
     user: admin@internal
     password: unix1234
     name: "{{ item }}"
     wait: True
     vm: prout1
     force: True
    with_items:
     - X1
     - X2
     - X3
```


##Problems?

Send me a mail at [karimboumedhel@gmail.com](mailto:karimboumedhel@gmail.com) !

Mac Fly!!!

karmab
