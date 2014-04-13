#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013. Amazon Web Services, Inc. All Rights Reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import uuid

# Import the SDK
import boto, boto.ec2, boto.opsworks
from boto.vpc import VPCConnection
from boto.opsworks.layer1 import OpsWorksConnection

ec2region = boto.ec2.get_region("ap-northeast-1")

# create VPCConnection
vpc_conn = boto.vpc.VPCConnection(region=ec2region)
# create a VPC
vpc = vpc_conn.create_vpc('10.20.0.0/16')
subnet_a_pub = vpc_conn.create_subnet(vpc.id, "10.20.0.0/24", 'ap-northeast-1c')
subnet_a_pvt = vpc_conn.create_subnet(vpc.id, "10.20.128.0/24", 'ap-northeast-1c')
subnet_b_pub = vpc_conn.create_subnet(vpc.id, "10.20.1.0/24", 'ap-northeast-1c')
subnet_b_pvt = vpc_conn.create_subnet(vpc.id, "10.20.129.0/24", 'ap-northeast-1c')



# create OpsWorksConnection
ow_conn = boto.opsworks.layer1.OpsWorksConnection()
# create a Stack
result = ow_conn.create_stack('Test', 'ap-northeast-1', 'arn:aws:iam::259692501178:role/aws-opsworks-service-role', 'arn:aws:iam::259692501178:instance-profile/aws-opsworks-ec2-role', vpc.id, default_subnet_id=subnet_a_pvt.id)




def setup_vpc(conn):
    vpc = vpc_conn.create_vpc('10.20.0.0/16')

    # create the main subnet
    subnet_a_pub = conn.create_subnet(vpc.id, "10.20.0.0/24", 'ap-northeast-1c')
    # create an Internet Gateway
    igw = conn.create_internet_gateway()
    conn.attach_internet_gateway(igw.id, vpc.id)

    # get main route table (should have been created automatically)
    rtb_main = conn.get_all_route_tables(filters=(("vpc-id", vpc.id),))[0]
    conn.create_route(rtb_main.id, "0.0.0.0/0", gateway_id=igw.id)

    # create other subnets
    subnet_a_pvt = conn.create_subnet(vpc.id, "10.20.128.0/24", 'ap-northeast-1c')
#    rtb_a_pvt = conn.create_route_table(vpc.id)
    subnet_b_pub = conn.create_subnet(vpc.id, "10.20.1.0/24", 'ap-northeast-1c')
    subnet_b_pvt = conn.create_subnet(vpc.id, "10.20.129.0/24", 'ap-northeast-1c')



#setup_subnets(vpc, vpc_conn)


print("Created VPC " + vpc.id)
print(result)

#s3 = boto.opsworks.connect_to_region('us-east-1')

#print boto.opsworks.regions()
