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



# create connections
ec2region = boto.ec2.get_region("ap-northeast-1")
ec2_conn = boto.ec2.connect_to_region("ap-northeast-1")
vpc_conn = boto.vpc.VPCConnection(region=ec2region)


def set_name(resource, name):
    ec2_conn.create_tags([resource.id], {"Name": name})

def create_subnet(vpc_id, cidr_block, availability_zone, name=""):
    subnet = vpc_conn.create_subnet(vpc_id, cidr_block, availability_zone)
    set_name(subnet, name)
    return subnet

def create_and_associate_route_table(subnet, name=""):
    # create new route table
    rtb = vpc_conn.create_route_table(vpc.id)
    set_name(rtb, name)

    # replace
    vpc_conn.associate_route_table(rtb.id, subnet.id)

    return rtb


def setup_internet_gateway(rtbs, name=""):
    # create
    igw = vpc_conn.create_internet_gateway()
    set_name(igw, name)
    vpc_conn.attach_internet_gateway(igw.id, vpc.id)

    #set
    for rtb in rtbs:
        vpc_conn.create_route(rtb.id, "0.0.0.0/0", gateway_id=igw.id)
        vpc_conn.create_route(rtb.id, "0.0.0.0/0", gateway_id=igw.id)

#s3 = boto.opsworks.connect_to_region('us-east-1')

#print boto.opsworks.regions()





# create a VPC
vpc = vpc_conn.create_vpc('10.27.0.0/16')
set_name(vpc, "TestVPC")

# create subnets
subnet_a_pub = create_subnet(vpc.id, "10.27.0.0/24", 'ap-northeast-1a', "TestVPC public segment A")
rtb_main = vpc_conn.get_all_route_tables(filters=(("vpc-id", vpc.id),))[0]	# get main route table
subnet_a_pvt = create_subnet(vpc.id, "10.27.128.0/24", 'ap-northeast-1a', "TestVPC private segment A")
subnet_b_pub = create_subnet(vpc.id, "10.27.1.0/24", 'ap-northeast-1c', "TestVPC public segment B")
subnet_b_pvt = create_subnet(vpc.id, "10.27.129.0/24", 'ap-northeast-1c', "TestVPC private segment B")
# get or create route tables
rtb_a_pub = rtb_main
vpc_conn.associate_route_table(rtb_a_pub.id, subnet_a_pub.id)			# set main route table
set_name(rtb_a_pub, "TestVPC public segment A")
rtb_a_pvt = create_and_associate_route_table(subnet_a_pvt, "TestVPC private segment A")
rtb_b_pub = create_and_associate_route_table(subnet_b_pub, "TestVPC public segment B")
rtb_b_pvt = create_and_associate_route_table(subnet_b_pvt, "TestVPC private segment B")
# set Internet Gateway
setup_internet_gateway([rtb_a_pub, rtb_b_pub], "TestVPC Internet Gateway")

print("VPC has been created : " + vpc.id)


# create OpsWorksConnection
ow_conn = boto.opsworks.layer1.OpsWorksConnection()
# create a Stack
result = ow_conn.create_stack('Test', 'ap-northeast-1', 'arn:aws:iam::259692501178:role/aws-opsworks-service-role', 'arn:aws:iam::259692501178:instance-profile/aws-opsworks-ec2-role', vpc.id, default_subnet_id=subnet_a_pvt.id)
stack_id = result["StackId"]

print "OpsWorks Stack has been created : " + stack_id

# TODO create nat instances

# TODO setup route tables

# TODO create and set Custom Json

# TODO start nat instances

