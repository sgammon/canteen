# -*- coding: utf-8 -*-

from __future__ import division
from jinja2.runtime import LoopContext, TemplateReference, Macro, Markup, TemplateRuntimeError, missing, concat, escape, markup_join, unicode_join, to_string, identity, TemplateNotFound
name = '/source/snippets/test.html'

def run(environment):

    def root(context):
        if 0: yield None
        yield u'<b></b>'

    blocks = {}
    debug_info = ''
    return (root, blocks, debug_info)
