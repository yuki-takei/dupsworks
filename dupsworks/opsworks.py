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


def setup_stack():
    global ctx, cfg, cfg_p, cfg_o
    global conn

    # create a Stack
    result = conn.create_stack('Test', 'ap-northeast-1',
        'arn:aws:iam::259692501178:role/aws-opsworks-service-role',
        'arn:aws:iam::259692501178:instance-profile/aws-opsworks-ec2-role',
        ctx.vpc.id, default_subnet_id=ctx.subnet_a_pvt.id,
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
    
    # create admin layer
    result = conn.create_layer(stack_id, 'custom', 'Admin Server', 'admin',
        auto_assign_elastic_ips=True, custom_recipes={"Setup": ["timezone"]})
    layer_id_admin = result["LayerId"]
    print("OpsWorks Layer 'Admin Server' has been created : " + layer_id_admin)
    # create nat layer
    result = ow_conn.create_layer(stack_id, 'custom', 'NAT Server', 'nat',
        auto_assign_public_ips=True, custom_recipes={
            "Setup": [
                "timezone",
                "vpcnat::disable-source-dest-check", "vpcnat::setup-heartbeat-script"
            ]
        })
    layer_id_nat = result["LayerId"]
    print("OpsWorks Layer 'NAT Server' has been created : " + layer_id_nat)


    # create an admin instance
    result = conn.create_instance(stack_id, [layer_id_admin], 't1.micro', subnet_id=ctx.subnet_a_pub.id)
    instance_opsid_admin = result["InstanceId"]
    print("1 admin instance has been created : " + instance_opsid_admin)
    
    # create nat instances
    result = conn.create_instance(stack_id, [layer_id_nat], 't1.micro', subnet_id=ctx.subnet_a_pub.id)
    instance_opsid_nat_az1 = result["InstanceId"]
    result = conn.create_instance(stack_id, [layer_id_nat], 't1.micro', subnet_id=ctx.subnet_b_pub.id)
    instance_opsid_nat_az2 = result["InstanceId"]
    print("2 nat instances has been created : " + instance_opsid_nat_a + ", " + instance_opsid_nat_b)
    
    # set to context variable
    ctx.stack_id = stack_id
    ctx.instance_opsid_admin = instance_opsid_admin
    ctx.instance_opsid_nat_az1 = instance_opsid_nat_az1
    ctx.instance_opsid_nat_az2 = instance_opsid_nat_az2


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
