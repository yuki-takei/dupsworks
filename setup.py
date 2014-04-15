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

import uuid
import subprocess

# Import the SDK
import boto, boto.ec2, boto.opsworks
from boto.vpc import VPCConnection
from boto.opsworks.layer1 import OpsWorksConnection



# create connections
ec2region = boto.ec2.get_region("ap-northeast-1")
ec2_conn = boto.ec2.connect_to_region("ap-northeast-1")
vpc_conn = boto.vpc.VPCConnection(region=ec2region)
ow_conn = boto.opsworks.layer1.OpsWorksConnection()


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




# create a Stack
result = ow_conn.create_stack('Test', 'ap-northeast-1',
    'arn:aws:iam::259692501178:role/aws-opsworks-service-role',
    'arn:aws:iam::259692501178:instance-profile/aws-opsworks-ec2-role',
    vpc.id, default_subnet_id=subnet_a_pvt.id,
    default_root_device_type="ebs",
    use_custom_cookbooks=True,
    custom_cookbooks_source={
        "Type": "git",
        "Url": "https://github.com/yuki-takei/dupsworks-tmplate-cc.git"
    })
stack_id = result["StackId"]

print "OpsWorks Stack has been created : " + stack_id




# Chef settings
# !! using awscli because boto(at least 2.27.0) doesn't support the "chef-configuration" argument !!
subprocess.check_output("aws --region us-east-1 \
    opsworks update-stack --stack-id %s \
        --configuration-manager Name=Chef,Version=11.10 \
        --chef-configuration ManageBerkshelf=true,BerkshelfVersion=2.0.14" % stack_id,
    shell=True)




# create layers
result = ow_conn.create_layer(stack_id, 'custom', 'Admin Server', 'admin', auto_assign_elastic_ips=True, custom_recipes={"Setup": ["timezone"]})
layer_id_admin = result["LayerId"]
print("'Admin Server' layer has been created : " + layer_id_admin)
result = ow_conn.create_layer(stack_id, 'custom', 'NAT Server', 'nat', auto_assign_public_ips=True, custom_recipes={"Setup": ["timezone", "vpcnat::disable-source-dest-check", "vpcnat::setup-heartbeat-script"]})
layer_id_nat = result["LayerId"]
print("'NAT Server' layer has been created : " + layer_id_nat)

# create an admin instance
result = ow_conn.create_instance(stack_id, [layer_id_admin], 't1.micro', subnet_id=subnet_a_pub.id)
instance_id_admin = result["InstanceId"]
print("an admin instance has been created : " + instance_id_admin)

# create nat instances
result = ow_conn.create_instance(stack_id, [layer_id_nat], 't1.micro', subnet_id=subnet_a_pub.id)
instance_id_nat1 = result["InstanceId"]
result = ow_conn.create_instance(stack_id, [layer_id_nat], 't1.micro', subnet_id=subnet_b_pub.id)
instance_id_nat2 = result["InstanceId"]
print("nat instances has been created : " + instance_id_nat1 + ", " + instance_id_nat2)




# TODO setup route tables

# TODO create and set Custom Json

# TODO start nat instances

