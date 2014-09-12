# -*- coding: utf-8 -*-

from __future__ import division
from jinja2.runtime import LoopContext, TemplateReference, Macro, Markup, TemplateRuntimeError, missing, concat, escape, markup_join, unicode_join, to_string, identity, TemplateNotFound
name = '/source/base.html'

def run(environment):

    def root(context):
        if 0: yield None
        for event in context.blocks['root'][0](context):
            yield event

    def block_root(context):
        if 0: yield None
        yield u'<html></html>'

    blocks = {'root': block_root}
    debug_info = '1=11'
    return (root, blocks, debug_info)
