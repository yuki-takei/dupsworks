DupsWorks
=========

Scripts which build an OpsWorks Stack with HA-NAT Layer


Summary
--------

### Application environments need High-Availability

Amazon VPC and OpsWorks are amazing solution for publish applications.  
Suppose we are constructing such a structure:

<table>
  <tr>
    <td>
      <img width="320px" style="max-width:100%;" alt="03_heartbeat.png" src="/docs/images/02_working_correctly.png" />
    </td>
  </tr>
</table>

that has **4 subnets**

* public subnet 1
* private subnet 1 (connectable to the Internet due to nat1)
* public subnet 2
* private subnet 2 (connectable to the Internet due to nat2)


To avoid to enclose Single Point Of Failure, it is preffered to have such a mechanism.

<table>
  <tr>
    <td>
      <img width="320px" style="max-width:100%;" alt="03_heartbeat.png" src="/docs/images/03_heartbeat.png" />
    </td>
    <td>
      <img width="320px" style="max-width:100%;" alt="04_nat1_failure.png" src="/docs/images/05_nat2_failure.png" />
    </td>
  </tr>
  <tr>
    <th>checking heartbeat each other</th>
    <th>automatic failovering and recovering</th>
  </tr>
</table>

But constructing as above is hard a little bit.


### What does DupsWorks do?

DupsWorks makes it easy to build a VPC sutructure as above, OpsWorks Stack, NAT Layer and instances, and install some scripts to NAT instances that provides High-Availability.

All processes are below:

1. create VPC
1. create 4 subnets
1. create an OpsWorks stack
1. create OpsWorks layers
  1. admin layer (for gateway instances)
  1. nat layer
1. set permissions (optional)
2. create OpsWorks instances
  1. 1 admin instance
  1. 2 NAT instances
1. start NAT instances
1. configure route
  1. public subnets -> internet gateway
  1. private subnets -> nat instances
  1. checking heartbeat route
1. configure NAT instances
  1. disable Source/dest. check.
  1. set '1' to net.ipv4.ip_forward using sysctl
  1. configure iptables and enable IP Masquerading
1. install scripts(check heartbeat and failover) to NAT instances.


Requirements
-------------

Dupsworks depends on Python 2.7 and some packages. You can install them using pip:

    pip install -r requirements.txt


Usage
-----

### Script Settings

1. Copy ``settings.cfg.example`` to ``settings.cfg``.
1. Edit params in ``[PersonalSettings]`` section.

#### Example:

```ini:settings.cfg
[PersonalSettings]
vpc_name = MyVPC
vpc_cidr                    = 10.0.0.0/16
vpc_subnet_az1_public_cidr  = 10.0.0.0/24
vpc_subnet_az1_private_cidr = 10.0.128.0/24
vpc_subnet_az2_public_cidr  = 10.0.1.0/24
vpc_subnet_az2_private_cidr = 10.0.129.0/24
region                      = us-east-1
vpc_subnet_az1              = us-east-1a
vpc_subnet_az2              = us-east-1b
stack_name = MyStack
stack_service_role_arn = arn:aws:iam::111111111111:role/aws-opsworks-service-role
stack_default_instance_profile_arn = arn:aws:iam::111111111111:instance-profile/aws-opsworks-ec2-role

    [[stack_permissions]]
        [[[hoge]]]
            iam_user_arn = arn:aws:iam::111111111111:user/hoge
            allow_ssh = True
            allow_sudo = True

```

### Security Credentials

Dupsworks use [boto](http://aws.amazon.com/sdkforpython/) and [awscli](http://aws.amazon.com/jp/cli/).

You need to set your AWS security credentials before the script is able to
connect to AWS. The SDK will automatically pick up credentials in environment
variables:

    export AWS_ACCESS_KEY_ID="Your AWS Access Key ID"
    export AWS_SECRET_ACCESS_KEY="Your AWS Secret Access Key"

See the [Security Credentials](http://aws.amazon.com/security-credentials) page
for more information on getting your keys.

### Execute

    python build_stack.py


Contributing
------------

1. Fork the repository on Github
1. Write your change (and fix my poor English!)
1. Submit a Pull Request using Github


License and Authors
-------------------
- Author:: Yuki Takei (<yuki@weseek.co.jp>)

Copyright 2014 WESEEK, Inc.

Licensed under the Apache License, Version 2.0 (the "License");  
you may not use this file except in compliance with the License.  
You may obtain a copy of the License at  

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  
distributed under the License is distributed on an "AS IS" BASIS,  
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  
See the License for the specific language governing permissions and  
limitations under the License.  

