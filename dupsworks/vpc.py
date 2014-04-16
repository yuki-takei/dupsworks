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


def init(context):
    global ctx, cfg, cfg_p, cfg_o
    global conn

    ctx = context
    cfg = ctx.cfg
    cfg_p = ctx.cfg_p
    cfg_o = ctx.cfg_o

    # create connection
    ec2region = boto.ec2.get_region(cfg_p["region"])
    conn = boto.vpc.VPCConnection(region=ec2region)

def setup_vpc():
    global ctx, cfg, cfg_p, cfg_o
    global conn
    global subnet_az1_pub, sunet_a_pvt, subnet_az2_pub, subnet_az2_pvt
    global rtb_az1_pub, rtb_az1_pvt, rtb_az2_pub, rtb_az2_pvt


    # create a VPC
    vpc = conn.create_vpc(cfg_p["vpc_cidr"])
    dupsworks.ec2.set_name(vpc, cfg_p["vpc_name"])

    # create subnets
    tpl = cfg["VPC"]["vpc_subnet_name_template"]
    subnet_az1_pub = create_subnet(cfg_p["vpc_subnet_az1_public_cidr"], cfg_p["vpc_subnet_az1"],
        tpl % {"vpc_name": cfg_p["vpc_name"], "layer": "public", "group": "A"})
    rtb_main = conn.get_all_route_tables(filters=(("vpc-id", vpc.id),))[0]      # get main route table
    subnet_az1_pvt = create_subnet(cfg_p["vpc_subnet_az1_private_cidr"], cfg_p["vpc_subnet_az1"],
        tpl % {"vpc_name": cfg_p["vpc_name"], "layer": "private", "group": "B"})
    subnet_az2_pub = create_subnet(cfg_p["vpc_subnet_az2_public_cidr"], cfg_p["vpc_subnet_az2"],
        tpl % {"vpc_name": cfg_p["vpc_name"], "layer": "public", "group": "A"})
    subnet_az2_pvt = create_subnet(cfg_p["vpc_subnet_az2_private_cidr"], cfg_p["vpc_subnet_az2"],
        tpl % {"vpc_name": cfg_p["vpc_name"], "layer": "private", "group": "B"})
    # get or create route tables
    rtb_az1_pub = rtb_main
    tpl = cfg["VPC"]["vpc_rtb_name_template"]
    conn.associate_route_table(rtb_az1_pub.id, subnet_az1_pub.id)                   # set main route table
    dupsworks.ec2.set_name(rtb_az1_pub,
        tpl % {"vpc_name": cfg_p["vpc_name"], "layer": "public", "group": "A"})
    rtb_az1_pvt = create_and_associate_route_table(subnet_az1_pvt,
        tpl % {"vpc_name": cfg_p["vpc_name"], "layer": "private", "group": "A"})
    rtb_az2_pub = create_and_associate_route_table(subnet_az2_pub,
        tpl % {"vpc_name": cfg_p["vpc_name"], "layer": "public", "group": "B"})
    rtb_az2_pvt = create_and_associate_route_table(subnet_az2_pvt,
        tpl % {"vpc_name": cfg_p["vpc_name"], "layer": "private", "group": "B"})
    # set Internet Gateway
    tpl = cfg["VPC"]["vpc_igw_name_template"]
    setup_internet_gateway([rtb_az1_pub, rtb_az2_pub],
        tpl % {"vpc_name": cfg_p["vpc_name"]})

    print("VPC has been created : " + vpc.id)

    # set to context variable
    ctx.vpc = vpc
    ctx.subnet_az1_pub = subnet_az1_pub
    ctx.subnet_az1_prv = subnet_az1_prv
    ctx.subnet_az2_pub = subnet_az2_pub
    ctx.subnet_az2_prv = subnet_az2_priv
    ctx.rtb_az1_pub = rtb_az1_pub
    ctx.rtb_az1_pvt = rtb_az1_pvt
    ctx.rtb_az2_pub = rtb_az2_pub
    ctx.rtb_az2_pvt = rtb_az2_pvt



def create_subnet(cidr_block, availability_zone, name=""):
    global conn, vpc

    subnet = conn.create_subnet(vpc.id, cidr_block, availability_zone)
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



