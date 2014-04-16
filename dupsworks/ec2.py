#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import boto.ec2



ctx = None
cfg = None
cfg_p = None
cfg_o = None

conn = None

def init(context, connection):
    global ctx, cfg, cfg_p, cfg_o
    global conn

    ctx = context
    cfg = ctx.cfg
    cfg_p = ctx.cfg_p
    cfg_o = ctx.cfg_o

    conn = connection

def set_name(resource, name):
    global conn
    conn.create_tags([resource.id], {"Name": name})

def check_security_groups_created():
    global ctx, cfg, cfg_p, cfg_o
    global conn

    # now + several seconds
    span = ctx.parser.getfloat("OptionalSettings", "ec2_timeout_check_sg")
    timeout = time.time() + span

    # get security groups name list like ["AWS-OpsWorks-Custom-Server", "AWS-OpsWorks-Default-Server"]
    necessary_names = cfg["OpsWorks"]["necessary_security_groups"]

    is_valid = False
    while True:
        # check timeout
        if time.time() > timeout:
            break

        # get all security groups
        sgs = conn.get_all_security_groups(filters={"vpc-id": ctx.vpc.id})
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
            time.sleep(1)               # sleep 1 second
            continue
        else:
            break

    if is_valid == False:
        raise Exception("couldn't confirm necessary security groups while at least 20 seconds.")

