Dupsworks
=========

Scripts which build an OpsWorks Stack with HA-NAT Layer


Summary
--------



Requirements
-------------

Dupsworks depends on Python 2.7 and some packages. You can install them using pip:

    pip install -r requirements.txt


Usage
-----

### Script Settings

1. Copy ``settings.cfg.example`` to ``settings.cfg``.
1. Edit params of ``[PersonalSettings]`` section.

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

