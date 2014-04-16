#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Context:

    parser = None
    cfg = None
    cfg_p = None
    cfg_o = None

    def __init__(self, cfg_parser):
        self.parser = cfg_parser
        self.cfg = self.parser._sections
        self.cfg_p = self.cfg["PersonalSettings"]
        self.cfg_o = self.cfg["OptionalSettings"]
