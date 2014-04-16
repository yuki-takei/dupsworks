#!/usr/bin/env python
# -*- coding: utf-8 -*-

from boto.opsworks.layer1 import OpsWorksConnection

ctx = None
cfg = None
cfg_p = None
cfg_o = None

conn = None


def init(context):
    global ctx, cfg, cfg_p, cfg_o
    global conn

    ctx = context
    cfg = ctx.cfg
    cfg_p = ctx.cfg_p
    cfg_o = ctx.cfg_o

    conn = boto.opsworks.layer1.OpsWorkConnection()


def set_name(resource, name):
    global conn
    conn.create_tags([resource.id], {"Name": name})


def get_ec2id_from_opsid(opsid):
    global ctx, cfg, cfg_p, cfg_o
    global conn

    print("retrieving EC2 Instance ID... (this might take several minutes)")

    timeout = time.time() + ctx.cfg_o["ec2_timeout_retrieve_id"]          # now + several seconds later

    ec2id = None
    while True:
        # check timeout
        if time.time() > timeout:
            break

        # describe
        result = conn.describe_instances(instance_ids=[opsid])
        instance_info = result["Instances"][0]
        if "Ec2InstanceId" in instance_info:
            ec2id = instance_info["Ec2InstanceId"]
            break

        time.sleep(1)           # sleep 1 second

    if ec2id == None:
        raise Exception("couldn't retrieve EC2 Instance ID from OpsWorks Instance ID : " + opsid)

    print("retrieved. EC2 Instance ID is : " + ec2id)
    return ec2id
