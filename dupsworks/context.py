#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Context:

    parser = None
    cfg = None
    cfg_p = None
    cfg_o = None

    vpc = None

    def __init__(self, parser):
        self.parser = parser
        self.cfg = parser._sections
        self.cfg_p = self.cfg["PersonalSettings"]
        self.cfg_o = self.cfg["OptionalSettings"]
