#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pycket.config import get_dummy_config
from pycket.entry_point import make_entry_point, target

from rpython.jit.metainterp.test.support import LLJitMixin
from rpython.jit.metainterp.warmspot import get_stats
from pycket.racket_entry import dev_mode_metainterp

# 1

from pycket.env import w_global_config as glob
glob.set_pycketconfig(get_dummy_config())

LLJitMixin().meta_interp(dev_mode_metainterp, [], listcomp=True, listops=True, backendopt=True)

# 2
from rpython.translator.driver import TranslationDriver
from rpython.config.translationoption import get_combined_translation_config

# pypy targetpycket.py --linklets --verbose 2 -I racket/kernel/init -e "1"
entry_flags_1 = ['--linklets', '--verbose', '2', '-I', 'racket/kernel/init', '-e', '1']

def interp_w_1():
    make_entry_point(get_dummy_config())(entry_flags_1)

## LLJitMixin().meta_interp(interp_w_1, [], listcomp=True, listops=True, backendopt=True)


# 3
# pypy targetpycket.py --linklets --dev
entry_flags_2 = ['--linklets', '--dev']

def interp_w_2():
    make_entry_point(get_dummy_config())(entry_flags_2)

## LLJitMixin().meta_interp(interp_w_2, [], listcomp=True, listops=True, backendopt=True)


# 4 - META-INTERP OLD PYCKET
from pycket.expand import JsonLoader, expand
from pycket.interpreter import interpret_one
from pycket.test.jit import TestLLtype

# TestLLtype().run_file("use-fasl.rkt", run_untranslated=False)
