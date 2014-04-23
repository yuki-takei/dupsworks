#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import boto.ec2
import boto.exception
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


def create_route_to_nat(rtb, cidr, nat_id):
    global conn
    
    print("creating route ... [%s : %s -> %s] (this might take several minutes)" % (rtb.id, cidr, nat_id))

    # now + several seconds later
    span = cfg_o.as_float("vpc_timeout_create_route_to_nat")
    timeout = time.time() + span

    ec2id = None
    while True:
        # check timeout
        if time.time() > timeout:
            print "[WARN] Timeout. Couldn't create route."
            print "Please create route at your own as follows : "
            print "  >> aws ec2 create-route --route-table-id %s --destination-cidr-block %s --instance-id %s" % (rtb.id, cidr, nat_id)
            break

        try:
            conn.create_route(rtb.id, cidr, instance_id=nat_id)
        except boto.exception.EC2ResponseError as e:
            print "[WARN] " + e.message + " (will retry after 5 sec...)"
        else:
            break

        # sleep 5 second
        time.sleep(5)

