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

import json
import time
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

def check_security_groups_created():
    timeout = time.time() + cfg_opt["ec2_timeout_check_sg"]		# now + several seconds

    # get security groups name list like ["AWS-OpsWorks-Custom-Server", "AWS-OpsWorks-Default-Server"]
    necessary_names = cfg["OpsWorks"]["necessary_security_groups"]

    is_valid = False
    while True:
        # check timeout
        if time.time() > timeout:
            break

        # get all security groups
        sgs = ec2_conn.get_all_security_groups(filters={"vpc-id": vpc.id})
        # create name list
        sg_names = []
        for sg in sgs:
            sg_names.append(sg.name)

        # set True temporary
        is_valid = True
        # check whethere necessary security groups are contained
        for name in necessary_names:
            if name not in sg_names:
                is_valid = False
                break

        # continue or break
        if is_valid == False:
            time.sleep(1)		# sleep 1 second
            continue
        else:
            break

    if is_valid == False:
        raise Exception("couldn't confirm necessary security groups while at least 20 seconds.")



def get_ec2id_from_opsid(opsid):
    print("retrieving EC2 Instance ID... (this might take several minutes)")

    timeout = time.time() + cfg_opt["ec2_timeout_retrieve_id"]		# now + several seconds later

    ec2id = None
    while True:
        # check timeout
        if time.time() > timeout:
            break
    
        # describe
        result = ow_conn.describe_instances(instance_ids=[opsid])
        instance_info = result["Instances"][0]
        if "Ec2InstanceId" in instance_info:
            ec2id = instance_info["Ec2InstanceId"]
            break

        time.sleep(1)		# sleep 1 second

    if ec2id == None:
        raise Exception("couldn't retrieve EC2 Instance ID from OpsWorks Instance ID : " + opsid)

    print("retrieved. EC2 Instance ID is : " + ec2id)
    return ec2id




# create a VPC
vpc = vpc_conn.create_vpc(cfg_psn["vpc_cidr"])
set_name(vpc, cfg_psn["vpc_name"])

# create subnets
subnet_a_pub = create_subnet(vpc.id, cfg_psn["vpc_subnetA_public_cidr"], cfg_psn["vpc_subnetA_az"],
    cfg["VPC"]["vpc_subnet_name_template"] % {"vpc_name": cfg_psn["vpc_name"], "layer": "public", "group": "A"})
rtb_main = vpc_conn.get_all_route_tables(filters=(("vpc-id", vpc.id),))[0]	# get main route table
subnet_a_pvt = create_subnet(vpc.id, cfg_psn["vpc_subnetA_private_cidr"], cfg_psn["vpc_subnetA_az"],
    cfg["VPC"]["vpc_subnet_name_template"] % {"vpc_name": cfg_psn["vpc_name"], "layer": "private", "group": "B"})
subnet_b_pub = create_subnet(vpc.id, cfg_psn["vpc_subnetA_public_cidr"], cfg_psn["vpc_subnetB_az"],
    cfg["VPC"]["vpc_subnet_name_template"] % {"vpc_name": cfg_psn["vpc_name"], "layer": "public", "group": "A"})
subnet_b_pvt = create_subnet(vpc.id, cfg_psn["vpc_subnetA_private_cidr"], cfg_psn["vpc_subnetB_az"],
    cfg["VPC"]["vpc_subnet_name_template"] % {"vpc_name": cfg_psn["vpc_name"], "layer": "private", "group": "B"})
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
print("OpsWorks Layer 'Admin Server' has been created : " + layer_id_admin)
result = ow_conn.create_layer(stack_id, 'custom', 'NAT Server', 'nat', auto_assign_public_ips=True, custom_recipes={"Setup": ["timezone", "vpcnat::disable-source-dest-check", "vpcnat::setup-heartbeat-script"]})
layer_id_nat = result["LayerId"]
print("OpsWorks Layer 'NAT Server' has been created : " + layer_id_nat)

# create an admin instance
result = ow_conn.create_instance(stack_id, [layer_id_admin], 't1.micro', subnet_id=subnet_a_pub.id)
instance_opsid_admin = result["InstanceId"]
print("1 admin instance has been created : " + instance_opsid_admin)

# create nat instances
result = ow_conn.create_instance(stack_id, [layer_id_nat], 't1.micro', subnet_id=subnet_a_pub.id)
instance_opsid_nat_a = result["InstanceId"]
result = ow_conn.create_instance(stack_id, [layer_id_nat], 't1.micro', subnet_id=subnet_b_pub.id)
instance_opsid_nat_b = result["InstanceId"]
print("2 nat instances has been created : " + instance_opsid_nat_a + ", " + instance_opsid_nat_b)



# check stack
print("checking whethere security groups had been created...")
try:
    check_security_groups_created()
except Exception as e:
    print "[WARN] " + e.message


# start nat instanceses and retrieve EC2 ID
print("starting instance : " + instance_opsid_nat_a)
ow_conn.start_instance(instance_opsid_nat_a)
print("starting instance : " + instance_opsid_nat_b)
ow_conn.start_instance(instance_opsid_nat_b)
sleep(cfg_opt["ops_instance_start_delay"])	# sleep a few seconds
instance_ec2id_nat_a = get_ec2id_from_opsid(instance_opsid_nat_a)
instance_ec2id_nat_b = get_ec2id_from_opsid(instance_opsid_nat_b)


# create route for private segments
vpc_conn.create_route(rtb_a_pvt, "0.0.0.0/0", instance_id=instance_ec2id_nat_a)
vpc_conn.create_route(rtb_b_pvt, "0.0.0.0/0", instance_id=instance_ec2id_nat_b)
# create route for heartbeat checking
vpc_conn.create_route(rtb_a_pub, "8.8.4.4/32", instance_id=instance_ec2id_nat_b)
vpc_conn.create_route(rtb_b_pub, "8.8.8.8/32", instance_id=instance_ec2id_nat_a)


# create and set Custom Json
json_obj = {
    "vpcnat": {
        "az": {
            "ap-northeast-1a": {
                "target_via_checking_nat": "8.8.4.4",
                "target_via_inetgw": "google.co.jp",
                "opposit_primary_nat_id": instance_ec2id_nat_b,
                "opposit_rtb": rtb_b_pvt.id,
                "enabled": 1
            },
            "ap-northeast-1c": {
                "target_via_checking_nat": "8.8.8.8",
                "target_via_inetgw": "google.co.jp",
                "opposit_primary_nat_id": instance_ec2id_nat_a,
                "opposit_rtb": rtb_a_pvt.id,
                "enabled": 1
            }
        }
    }
}
json_str = json.dumps(json_obj, sort_keys=True, indent=4)
ow_conn.update_stack(stack_id, custom_json=json_str)

print("installed custom_json to Stack : " + json_str)





# TODO print summary messages
