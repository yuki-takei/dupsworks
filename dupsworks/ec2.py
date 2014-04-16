#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto.ec2

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

    conn = boto.ec2.connect_to_region(cfg_p["region"])

def set_name(resource, name):
    global conn
    conn.create_tags([resource.id], {"Name": name})

