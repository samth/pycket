#! /usr/bin/env python
# -*- coding: utf-8 -*-

# XXX: This whole module is wrong

import sys

from pycket              import values
from pycket.error        import SchemeException
from pycket.foreign      import W_CType, W_PrimitiveCType, W_DerivedCType, W_CStructType
from pycket.prims.expose import default, expose, expose_val, procedure
from rpython.rlib        import jit, unroll

if sys.maxint == 2147483647:    # 32-bit
    POINTER_SIZE = 4
else:                           # 64-bit
    POINTER_SIZE = 8

PRIMITIVE_CTYPES = [
    ("bool"          , 4           , 4 ) ,
    ("stdbool"       , 1           , 1 ) ,
    ("int8"          , 1           , 1 ) ,
    ("int16"         , 2           , 2 ) ,
    ("int32"         , 4           , 4 ) ,
    ("int64"         , 8           , 8 ) ,
    ("uint8"         , 1           , 1 ) ,
    ("uint16"        , 2           , 2 ) ,
    ("uint32"        , 4           , 4 ) ,
    ("uint64"        , 8           , 8 ) ,
    ("void"          , 0           , 1 ) ,
    ("bytes"         , POINTER_SIZE, POINTER_SIZE) ,
    ("path"          , POINTER_SIZE, POINTER_SIZE) ,
    ("pointer"       , POINTER_SIZE, POINTER_SIZE) ,
    ("fpointer"      , POINTER_SIZE, POINTER_SIZE) ,
    ("string/utf-16" , POINTER_SIZE, POINTER_SIZE) ,
    ("gcpointer"     , POINTER_SIZE, POINTER_SIZE) ,
    ("or-null"       , POINTER_SIZE, POINTER_SIZE) ,
    ("_gcable"       , POINTER_SIZE, POINTER_SIZE) ,
    ("scheme"        , POINTER_SIZE, POINTER_SIZE  , "racket") ,
    ]

sym = values.W_Symbol.make

# Best effort
COMPILER_SIZEOF = unroll.unrolling_iterable([
    (sym("int"    ) , POINTER_SIZE ) ,
    (sym("char"   ) , 1            ) ,
    (sym("short"  ) , 1            ) ,
    (sym("long"   ) , POINTER_SIZE ) ,
    (sym("*"      ) , POINTER_SIZE ) ,
    (sym("void"   ) , 0            ) ,
    (sym("float"  ) , 4            ) ,
    (sym("double" ) , 8            ) ,
    ])

del sym

def expose_ctype(name, size, alignment, *extra_names):
    basetype = values.W_Symbol.make(name)
    ctype    = W_PrimitiveCType(basetype, size, alignment)
    expose_val("_" + name, ctype)
    for name in extra_names:
        expose_val("_" + name, ctype)

for spec in PRIMITIVE_CTYPES:
    expose_ctype(*spec)

@expose("make-ctype", [W_CType, values.W_Object, values.W_Object])
def make_c_type(ctype, rtc, ctr):
    if rtc is not values.w_false and not rtc.iscallable():
        raise SchemeException("make-ctype: expected (or/c #f procedure) in argument 1 got %s" %
                              rtc.tostring())
    if ctr is not values.w_false and not ctr.iscallable():
        raise SchemeException("make-ctype: expected (or/c #f procedure) in argument 2 got %s" %
                              ctr.tostring())
    return W_DerivedCType(ctype, rtc, ctr)

def validate_alignment(ctx, arg, align):
    if align is values.w_false:
        return -1
    if isinstance(align, values.W_Fixnum) and align.value in (1, 2, 4, 8, 16):
        return align.value
    msg = ("%s: expected (or/c #f 1 2 4 8 16) in argument %d got %s" %
           (ctx, arg, align.tostring()))
    raise SchemeException(msg)

@expose("make-cstruct-type",
        [values.W_List,
         default(values.W_Object, values.w_false),
         default(values.W_Object, values.w_false)])
def make_cstruct_type(types, abi, _alignment):
    alignment = validate_alignment("make-cstruct-type", 2, _alignment)

    if types.is_proper_list():
        types_list = []
        for ctype in values.from_list_iter(types):
            if not isinstance(ctype, W_CType):
                break
            types_list.append(ctype)
        else:
            return W_CStructType(types_list[:], abi, alignment)

    msg = "make-cstruct-type: expected (listof ctype?) in argument 0 got %s" % types.tostring()
    raise SchemeException(msg)

@jit.elidable
def _compiler_sizeof(ctype):
    if ctype.is_proper_list():
        acc = 0
        for type in values.from_list_iter(ctype):
            if not isinstance(type, values.W_Symbol):
                break
            size = _compiler_sizeof(type)
            acc = max(size, acc)
        else:
            return acc

    if not isinstance(ctype, values.W_Symbol):
        msg = ("compiler-sizeof: expected (or/c symbol? (listof symbol?)) in argument 0 got %s" %
               ctype.tostring())
        raise SchemeException(msg)

    for sym, size in COMPILER_SIZEOF:
        if ctype is sym:
            return size
    raise SchemeException("compiler-sizeof: %s is not a valid C type" % ctype.tostring())

@expose("compiler-sizeof", [values.W_Object])
def compiler_sizeof(obj):
    return values.W_Fixnum(_compiler_sizeof(obj))

@expose("make-stubborn-will-executor", [])
def make_stub_will_executor():
    return values.w_false

@expose("ctype-sizeof", [W_CType])
def ctype_sizeof(ctype):
    return values.W_Fixnum(ctype.sizeof())

@expose("ctype-alignof", [W_CType])
def ctype_alignof(ctype):
    return values.W_Fixnum(ctype.alignof())

@expose("ctype?", [W_CType])
def ctype(c):
    return values.W_Bool.make(isinstance(c, W_CType))

@expose("ffi-lib?", [values.W_Object])
def ffi_lib(o):
    # Naturally, since we don't have ffi values
    return values.w_false

@expose("ffi-lib")
def ffi_lib(args):
    return values.w_false

@expose("malloc")
def malloc(args):
    return values.W_CPointer()

@expose("ptr-ref")
def ptr_ref(args):
    return values.w_void

@expose("ptr-set!")
def ptr_set(args):
    return values.w_void

@expose("cpointer-gcable?")
def cp_gcable(args):
    return values.w_false

@expose("ffi-obj")
def ffi_obj(args):
    return values.W_CPointer()

@expose("ctype-basetype", [values.W_Object])
def ctype_basetype(ctype):
    if ctype is values.w_false:
        return values.w_false
    if not isinstance(ctype, W_CType):
        msg = ("ctype-basetype: expected (or/c ctype? #f) in argument 0 got %s" %
               ctype.tostring())
        raise SchemeException(msg)
    return ctype.basetype()

@expose("ctype-scheme->c", [W_CType])
def ctype_scheme_to_c(ctype):
    return ctype.scheme_to_c()

@expose("ctype-c->scheme", [W_CType])
def ctype_c_to_scheme(ctype):
    return ctype.c_to_scheme()

