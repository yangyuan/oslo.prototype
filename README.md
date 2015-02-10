README
======

http://www.yangyuan.info/post.php?id=1087

Prototype (oslo.prototype) is a simple template to create a new OpenStack project.

I try to use oslo libraries as much as possible, and keep it's coding style similar to Keystone, Nova, Glance and other OpenStack projects.

By replace the keywords 'prototype', 'Prototype' and 'PROTOTYPE', you can quickly create your own OpenStack project, there will be no relationship between your project and Prototype.

Main Functions
==============

### API: WSGI Service
Prototype contains a full WSGI API implementations, including request-context, version-control, keystone-authentication, fault-wrap and so on.

### Worker: RPC Service
Worker is a kind of service similar to nova-compute or nova-scheduler, it can do tasks periodicly or response to remote requests.

### SDK
Prototype Client contains not only a pythonclient, but also a CLI program.

### Installation
Like other OpenStack projects, you can install 'prototype' and 'python-prototypeclient' by run setup.py, You can also use devstack to do integrated installation.

## Usage
Please check usage.txt