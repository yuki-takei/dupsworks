#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Context:

    cfg = None
    cfg_p = None
    cfg_o = None

    vpc = None

    def __init__(self, cfg):
        self.cfg = cfg
        self.cfg_p = cfg["PersonalSettings"]
        self.cfg_o = cfg["OptionalSettings"]
