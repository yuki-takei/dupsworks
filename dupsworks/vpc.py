#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto.ec2
from boto.vpc import VPCConnection

import dupsworks.ec2


ctx = None
cfg = None
cfg_p = None
cfg_o = None

conn = None
vpc = None

def init(context, connection):
    global ctx, cfg, cfg_p, cfg_o
    global conn

    ctx = context
    cfg = ctx.cfg
    cfg_p = ctx.cfg_p
    cfg_o = ctx.cfg_o

    conn = connection

def create_subnet(cidr_block, availability_zone, name=""):
    global ctx
    global conn

    subnet = conn.create_subnet(ctx.vpc.id, cidr_block, availability_zone)
    dupsworks.ec2.set_name(subnet, name)
    return subnet

def create_and_associate_route_table(subnet, name=""):
    global ctx
    global conn

    # create new route table
    rtb = conn.create_route_table(ctx.vpc.id)
    dupsworks.ec2.set_name(rtb, name)

    # replace
    conn.associate_route_table(rtb.id, subnet.id)

    return rtb


def setup_internet_gateway(rtbs, name=""):
    global ctx
    global conn

    # create
    igw = conn.create_internet_gateway()
    dupsworks.ec2.set_name(igw, name)
    conn.attach_internet_gateway(igw.id, ctx.vpc.id)

    #set
    for rtb in rtbs:
        conn.create_route(rtb.id, "0.0.0.0/0", gateway_id=igw.id)
        conn.create_route(rtb.id, "0.0.0.0/0", gateway_id=igw.id)



