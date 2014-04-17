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

import os
from ConfigParser import SafeConfigParser

import json
import time
import subprocess

# Import the SDK
import boto, boto.ec2, boto.opsworks
from boto.vpc import VPCConnection
from boto.opsworks.layer1 import OpsWorksConnection

import dupsworks.ec2
import dupsworks.vpc
import dupsworks.opsworks
from dupsworks.context import Context



def main():

    # create Context instance
    filepath = os.path.join(os.path.dirname(__file__), "setup.cfg")
    parser = SafeConfigParser()
    parser.read(filepath)

    ctx = Context(parser)
    cfg = ctx.cfg
    cfg_p = ctx.cfg_p
    cfg_o = ctx.cfg_o


    # create connections
    ec2region = boto.ec2.get_region("ap-northeast-1")
    ec2_conn = boto.ec2.connect_to_region("ap-northeast-1")
    vpc_conn = boto.vpc.VPCConnection(region=ec2region)
    ow_conn = boto.opsworks.layer1.OpsWorksConnection()
    
    # init modules
    dupsworks.ec2.init(ctx, ec2_conn)
    dupsworks.vpc.init(ctx, vpc_conn)
    dupsworks.opsworks.init(ctx, ow_conn)





    # create a VPC
    vpc = vpc_conn.create_vpc(cfg_p["vpc_cidr"])
    dupsworks.ec2.set_name(vpc, cfg_p["vpc_name"])
    # set to context
    ctx.vpc = vpc

    # create subnets
    subnet_a_pub = dupsworks.vpc.create_subnet(
        cfg_p["vpc_subnet_az1_public_cidr"],
        cfg_p["vpc_subnet_az1"],
        cfg["VPC"]["subnet_name_template"] % {"vpc_name": cfg_p["vpc_name"], "layer": "public", "group": "AZ1"})
    rtb_main = vpc_conn.get_all_route_tables(filters=(("vpc-id", vpc.id),))[0]  # get main route table
    
    subnet_a_pvt = dupsworks.vpc.create_subnet(
        cfg_p["vpc_subnet_az1_private_cidr"],
        cfg_p["vpc_subnet_az1"],
        cfg["VPC"]["subnet_name_template"] % {"vpc_name": cfg_p["vpc_name"], "layer": "private", "group": "AZ1"})
    
    subnet_b_pub = dupsworks.vpc.create_subnet(
        cfg_p["vpc_subnet_az2_public_cidr"],
        cfg_p["vpc_subnet_az2"],
        cfg["VPC"]["subnet_name_template"] % {"vpc_name": cfg_p["vpc_name"], "layer": "public", "group": "AZ2"})
    
    subnet_b_pvt = dupsworks.vpc.create_subnet(
        cfg_p["vpc_subnet_az2_private_cidr"],
        cfg_p["vpc_subnet_az2"],
        cfg["VPC"]["subnet_name_template"] % {"vpc_name": cfg_p["vpc_name"], "layer": "private", "group": "AZ2"})
    
    # get or create route tables
    rtb_a_pub = rtb_main
    vpc_conn.associate_route_table(rtb_a_pub.id, subnet_a_pub.id)		# set main route table
    dupsworks.ec2.set_name(rtb_a_pub, "TestVPC public segment A")
    
    rtb_a_pvt = dupsworks.vpc.create_and_associate_route_table(subnet_a_pvt, "TestVPC private segment A")
    rtb_b_pub = dupsworks.vpc.create_and_associate_route_table(subnet_b_pub, "TestVPC public segment B")
    rtb_b_pvt = dupsworks.vpc.create_and_associate_route_table(subnet_b_pvt, "TestVPC private segment B")
    
    # set Internet Gateway
    dupsworks.vpc.setup_internet_gateway([rtb_a_pub, rtb_b_pub], "TestVPC Internet Gateway")

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
        dupsworks.ec2.check_security_groups_created()
    except Exception as e:
        print "[WARN] " + e.message



    # start nat instanceses
    print("starting instance : " + instance_opsid_nat_a)
    ow_conn.start_instance(instance_opsid_nat_a)
    
    print("starting instance : " + instance_opsid_nat_b)
    ow_conn.start_instance(instance_opsid_nat_b)

    # sleep a few seconds
    delay = ctx.parser.getfloat("OpsWorks", "instance_start_delay")
    time.sleep(delay)
    
    # retrieve EC2 IDs
    instance_ec2id_nat_a = dupsworks.opsworks.get_ec2id_from_opsid(instance_opsid_nat_a)
    instance_ec2id_nat_b = dupsworks.opsworks.get_ec2id_from_opsid(instance_opsid_nat_b)



    # create route for private segments
    dupsworks.vpc.create_route_to_nat(rtb_a_pvt, "0.0.0.0/0", instance_ec2id_nat_a)
    dupsworks.vpc.create_route_to_nat(rtb_b_pvt, "0.0.0.0/0",instance_ec2id_nat_b)
    # create route for heartbeat checking
    dupsworks.vpc.create_route_to_nat(rtb_a_pub, "8.8.4.4/32", instance_ec2id_nat_b)
    dupsworks.vpc.create_route_to_nat(rtb_b_pub, "8.8.8.8/32", instance_ec2id_nat_a)


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





if __name__ == "__main__":
    main()
