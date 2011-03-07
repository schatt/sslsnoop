#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

__author__ = "Loic Jaquemet loic.jaquemet+python@gmail.com"

import ctypes
from model import is_valid_address,getaddress,sstr,LoadableMembers
from ptrace.debugger.memory_mapping import readProcessMappings
import logging
log=logging.getLogger('openssl.model')

''' hmac.h:69 '''
HMAC_MAX_MD_CBLOCK=128
''' evp.h:91 '''
EVP_MAX_BLOCK_LENGTH=32
EVP_MAX_IV_LENGTH=16
AES_MAXNR=14 # aes.h:66

BN_ULONG=ctypes.c_ulong

#ok
class BIGNUM(LoadableMembers):
  _fields_ = [
  ("d",ctypes.POINTER(BN_ULONG) ),
  ('top',ctypes.c_int),
  ('dmax',ctypes.c_int),
  ('neg',ctypes.c_int),
  ('flags',ctypes.c_int)
  ]
  def loadMembers(self,process):
    ''' 
    isValid() should have been tested before, otherwise.. it's gonna fail...
    we copy memory from process for each pointer
    and assign it to a python object _here, then we assign 
    the member to be a pointer to _here'''
    if not self.valid:
      log.error('BigNUm tries to load members when its not validated')
      return False
    # Load and memcopy d / BN_ULONG *
    attr_obj_address=getaddress(self.d)
    self._d = process.readArray(attr_obj_address, ctypes.c_ulong, self.top) 
    ## or    
    #ulong_array= (ctypes.c_ulong * self.top)
    #self._d = process.readStruct(attr_obj_address, ulong_array) 
    self.d  = ctypes.cast(ctypes.pointer( self._d ), ctypes.POINTER(ctypes.c_ulong))
    self.loaded=True
    return True
  
  def isValid(self,mappings):
    if ( self.dmax < 0 or self.top < 0 or self.dmax < self.top ):
      return False
    if ( not (self.neg == 1 or self.neg == 0 ) ) :
      return False 
    #last test on memory address
    self.valid=is_valid_address( self.d, mappings)
    return self.valid
  
  def __str__(self):
    #return repr(self)
    d= getaddress(self.d)
    return ("BN { d=0x%lx, top=%d, dmax=%d, neg=%d, flags=%d }"%
                (d, self.top, self.dmax, self.neg, self.flags) )
#ok
class STACK(ctypes.Structure):
  _fields_ = [
  ("num",ctypes.c_int),
  ("data",ctypes.c_char_p),
  ("sorted",ctypes.c_int),
  ("num_alloc",ctypes.c_int),
  ("comp",ctypes.POINTER(ctypes.c_int) ) ]

#ok
class CRYPTO_EX_DATA(ctypes.Structure):
  _fields_ = [
  ("sk",ctypes.POINTER(STACK) ),
  ("dummy",ctypes.c_int)]
  
#ok
class BN_MONT_CTX(ctypes.Structure):
  _fields_ = [
  ("ri",ctypes.c_int),
  ("RR",BIGNUM),
  ("N",BIGNUM),
  ("Ni",BIGNUM),
  ("n0",ctypes.c_ulong),
  ("flags",ctypes.c_int)]

class EVP_PKEY(LoadableMembers):
	_fields_ = [
  ('type',ctypes.c_int),
  ('save_type',ctypes.c_int),
  ('references',ctypes.c_int),
  ('pkey',ctypes.c_void_p), ## union of struct really
  ('save_parameters',ctypes.c_int),
  ('attributes',ctypes.c_void_p) ## 	STACK_OF(X509_ATTRIBUTE) *attributes; /* [ 0 ] */
  ]


class ENGINE_CMD_DEFN(LoadableMembers):
	_fields_ = [
  ('cmd_num',ctypes.c_uint),
  ('cmd_name',ctypes.c_char_p),
  ('cmd_desc',ctypes.c_char_p),
  ('cmd_flags',ctypes.c_uint)
  ]  

class ENGINE(LoadableMembers):
  pass
ENGINE._fields_ = [
  ('id',ctypes.c_char_p),
  ('name',ctypes.c_char_p),
  ('rsa_meth',ctypes.POINTER(ctypes.c_int) ),
  ('dsa_meth',ctypes.POINTER(ctypes.c_int) ),
  ('dh_meth',ctypes.POINTER(ctypes.c_int) ),
  ('ecdh_meth',ctypes.POINTER(ctypes.c_int) ),
  ('ecdsa_meth',ctypes.POINTER(ctypes.c_int) ),
  ('rand_meth',ctypes.POINTER(ctypes.c_int) ),
  ('store_meth',ctypes.POINTER(ctypes.c_int) ),
  ('ciphers',ctypes.POINTER(ctypes.c_int) ), ## fn typedef int (*ENGINE_CIPHERS_PTR)(ENGINE *, const EVP_CIPHER **, const int **, int);
  ('digest',ctypes.POINTER(ctypes.c_int) ),  ## fn typedef int (*ENGINE_DIGESTS_PTR)(ENGINE *, const EVP_MD **, const int **, int);
  ('destroy',ctypes.POINTER(ctypes.c_int) ), ## fn typedef int (*ENGINE_GEN_INT_FUNC_PTR)(ENGINE *);
  ('init',ctypes.POINTER(ctypes.c_int) ),    ## fn typedef int (*ENGINE_GEN_INT_FUNC_PTR)(ENGINE *);
  ('finish',ctypes.POINTER(ctypes.c_int) ),  ## fn typedef int (*ENGINE_GEN_INT_FUNC_PTR)(ENGINE *);
  ('ctrl',ctypes.POINTER(ctypes.c_int) ),    ## fn typedef int (*ENGINE_CTRL_FUNC_PTR)(ENGINE *, int, long, void *, void (*f)(void));
  ('load_privkey',ctypes.POINTER(EVP_PKEY) ), ## fn EVP_PKEY *
  ('load_pubkey',ctypes.POINTER(EVP_PKEY) ),  ## fn EVP_PKEY *
  ('load_ssl_client_cert',ctypes.POINTER(ctypes.c_int) ), ## fn typedef int (*ENGINE_SSL_CLIENT_CERT_PTR)(ENGINE *, SSL *ssl,
  ('cmd_defns',ctypes.POINTER(ENGINE_CMD_DEFN) ), ##
  ('flags',ctypes.c_int),
  ('struct_ref',ctypes.c_int),
  ('funct_ref',ctypes.c_int),
  ('ex_data',CRYPTO_EX_DATA),
  ('prev',ctypes.POINTER(ENGINE) ),
  ('nex',ctypes.POINTER(ENGINE) )
  ]


#KO
class RSA(LoadableMembers):
  ''' rsa/rsa.h '''
  loaded=False
  _fields_ = [
  ("pad",  ctypes.c_int), 
  ("version",  ctypes.c_long),
  ("meth",ctypes.POINTER(BIGNUM)),#const RSA_METHOD *meth;
  ("engine",ctypes.POINTER(BIGNUM)),#ENGINE *engine;
  ('n', ctypes.POINTER(BIGNUM) ),
  ('e', ctypes.POINTER(BIGNUM) ),
  ('d', ctypes.POINTER(BIGNUM) ),
  ('p', ctypes.POINTER(BIGNUM) ),
  ('q', ctypes.POINTER(BIGNUM) ),
  ('dmp1', ctypes.POINTER(BIGNUM) ),
  ('dmq1', ctypes.POINTER(BIGNUM) ),
  ('iqmp', ctypes.POINTER(BIGNUM) ),
  ("ex_data", CRYPTO_EX_DATA ),
  ("references", ctypes.c_int),
  ("flags", ctypes.c_int),
  ("_method_mod_n", ctypes.POINTER(BN_MONT_CTX) ),
  ("_method_mod_p", ctypes.POINTER(BN_MONT_CTX) ),
  ("_method_mod_q", ctypes.POINTER(BN_MONT_CTX) ),
  ("bignum_data",ctypes.POINTER(ctypes.c_char)), ## moue c_char_p ou POINTER(c_char) ?
  ("blinding",ctypes.POINTER(BIGNUM)),#BN_BLINDING *blinding;
  ("mt_blinding",ctypes.POINTER(BIGNUM))#BN_BLINDING *mt_blinding;
  ]
  def printValid(self,mappings):
    print 'me',self.valid
    log.debug( '----------------------- LOADED: %s'%self.loaded)
    log.debug('pad: %d version %d ref %d'%(self.pad,self.version,self.references) )
    log.debug(is_valid_address( self.n, mappings)    )
    log.debug(is_valid_address( self.e, mappings)    )
    log.debug(is_valid_address( self.d, mappings)    )
    log.debug(is_valid_address( self.p, mappings)    )
    log.debug(is_valid_address( self.q, mappings)    )
    log.debug(is_valid_address( self.dmp1, mappings) ) 
    log.debug(is_valid_address( self.dmq1, mappings) )
    log.debug(is_valid_address( self.iqmp, mappings) )
    print 'me',self.valid
    return
  def loadMembers(self,process):
    # XXXX clean other structs
    self.meth=None
    self._method_mod_n = None
    self._method_mod_p = None
    self._method_mod_q = None
    self.bignum_data = None
    self.blinding = None

    if not LoadableMembers.loadMembers(self,process):
      log.debug('RSA not loaded')
      return False
    #
    #for e in [self.n, self.e, self.d, self.p, self.q, self.dmp1, self.dmq1 , self.iqmp]:
    #  print e.contents
    self.loaded=True
    return True
    
  def isValid(self,mappings):
    ''' struct is valid when :
    '''
    self.valid=(self.pad ==0 and self.version ==0 and
          (0 <= self.references <= 0xfff)  and
        is_valid_address( self.n, mappings)    and 
        is_valid_address( self.e, mappings)    and
        is_valid_address( self.d, mappings)    and
        is_valid_address( self.p, mappings)    and
        is_valid_address( self.q, mappings)    and
        is_valid_address( self.dmp1, mappings) and
        is_valid_address( self.dmq1, mappings) and
        is_valid_address( self.iqmp, mappings) )
    return self.valid

    
#KO
class DSA(LoadableMembers):
  _fields_ = [
  ("pad",  ctypes.c_int), 
  ("version",  ctypes.c_long),
  ("write_params",ctypes.c_int),
  ('p', ctypes.POINTER(BIGNUM) ),
  ('q', ctypes.POINTER(BIGNUM) ),
  ('g', ctypes.POINTER(BIGNUM) ),
  ('pub_key', ctypes.POINTER(BIGNUM) ),
  ('priv_key', ctypes.POINTER(BIGNUM) ),
  ('kinv', ctypes.POINTER(BIGNUM) ),
  ('r', ctypes.POINTER(BIGNUM) ),
  ("flags", ctypes.c_int),
  ("_method_mod_p", ctypes.POINTER(BN_MONT_CTX) ),
  ("references", ctypes.c_int),
  ("ex_data", CRYPTO_EX_DATA ),
  ("meth",ctypes.POINTER(ctypes.c_int)),#  const DSA_METHOD *meth;
  ("engine",ctypes.POINTER(ENGINE))
  ]
  def printValid(self,mappings):
    log.debug( '----------------------- \npad: %d version %d ref %d'%(self.pad,self.version,self.write_params) )
    log.debug(is_valid_address( self.p, mappings)    )
    log.debug(is_valid_address( self.q, mappings)    )
    log.debug(is_valid_address( self.g, mappings)    )
    log.debug(is_valid_address( self.pub_key, mappings)    )
    log.debug(is_valid_address( self.priv_key, mappings)    )
    return
  def internalCheck(self):
    '''  pub_key = g^privKey mod p '''
    return

  def loadMembers(self,process):
    # clean other structs
    # r and kinv can be null
    self.meth=None
    self._method_mod_p = None
    self.engine = None
    
    if not LoadableMembers.loadMembers(self,process):
      log.debug('DSA not loaded')
      return False
    #
    self.loaded=True
    return True
    
  def isValid(self,mappings):
    self.valid= (
        self.pad ==0 and self.version ==0 and
        (0 <= self.references <= 0xfff)  and
        is_valid_address( self.p, mappings)        and
        is_valid_address( self.q, mappings)        and
        is_valid_address( self.g, mappings)        and
        is_valid_address( self.priv_key, mappings) and
        is_valid_address( self.pub_key, mappings)  and
        #is_valid_address( self.kinv, mappings) and  # kinv and r can be null
        #is_valid_address( self.r, mappings)  ) 
        True )
    return self.valid

#ok
class EVP_CIPHER(ctypes.Structure):
  ''' evp.h:332 '''	
  _fields_ = [
  ("nid",  ctypes.c_int), 
  ("block_size",  ctypes.c_int), 
  ("key_len",  ctypes.c_int), 
  ("iv_len",  ctypes.c_int), 
  ("flags",  ctypes.c_ulong), 
  ("init",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("do_cipher",  ctypes.POINTER(ctypes.c_int)), # function () ## crypt func.
  ("cleanup",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("ctx_size",  ctypes.c_int), 
  ("set_asn1_parameters",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("get_asn1_parameters",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("ctrl",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("app_data",  ctypes.c_void_p) 
  ]

#mok
class EVP_CIPHER_CTX(ctypes.Structure):
  ''' evp.h:332 '''	
  _fields_ = [
  ("cipher",  ctypes.POINTER(EVP_CIPHER)), 
  ("engine",  ctypes.POINTER(ctypes.c_int)), ## TODO ENGINE*
  ("encrypt",  ctypes.c_int), 
  ("buf_len",  ctypes.c_int), 
  ("oiv",  ctypes.c_char*EVP_MAX_IV_LENGTH),## unsigned char  oiv[EVP_MAX_IV_LENGTH];
  ("iv",  ctypes.c_char*EVP_MAX_IV_LENGTH), ##unsigned char  iv[EVP_MAX_IV_LENGTH];
  ("buf",  ctypes.c_char*EVP_MAX_BLOCK_LENGTH), ##unsigned char buf[EVP_MAX_BLOCK_LENGTH];
  ("num",  ctypes.c_int), 
  ("app_data",  ctypes.c_void_p), 
  ("key_len",  ctypes.c_int), 
  ("flags",  ctypes.c_ulong), 
  ("cipher_data",  ctypes.c_void_p), 
  ("final_used",  ctypes.c_int), 
  ("block_mask",  ctypes.c_int), 
  ("final",  ctypes.c_char*EVP_MAX_BLOCK_LENGTH) ###unsigned char final[EVP_MAX_BLOCK_LENGTH]
  ]

#mok
class EVP_MD(ctypes.Structure):
  ''' struct env_md_st evp.h:227 '''
  _fields_ = [
  ("type",  ctypes.c_int), 
  ("pkey_type",  ctypes.c_int), 
  ("md_size",  ctypes.c_int), 
  ("flags",  ctypes.c_ulong), 
  ("init",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("update",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("final",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("copy",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("cleanup",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("sign",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("verify",  ctypes.POINTER(ctypes.c_int)), # function () 
  ("required_pkey_type",  ctypes.c_int*5), #required_pkey_type[5]
  ("block_size",  ctypes.c_int), 
  ("ctx_size",  ctypes.c_int)
  ]

class EVP_MD_CTX(ctypes.Structure):
  ''' evp.h:304 '''
  _fields_ = [
  ("digest",  ctypes.POINTER(EVP_MD)),
  ("engine",  ctypes.POINTER(ENGINE) ), #
  ("flags",  ctypes.c_ulong),
  ("md_data",  ctypes.c_void_p)
  ]

class HMAC_CTX(ctypes.Structure):
  ''' hmac.h:75 '''
  _fields_ = [
  ("md",  ctypes.POINTER(EVP_MD)), 
  ("md_ctx",  EVP_MD_CTX), 
  ("i_ctx",  EVP_MD_CTX), 
  ("o_ctx",  EVP_MD_CTX), 
  ("key_length",  ctypes.c_uint), 
  ("key",  ctypes.c_char * HMAC_MAX_MD_CBLOCK)
  ] 

class AES_KEY(ctypes.Structure):
  ''' aes.h:78 '''
  _fields_ = [
  ("rd_key",  ctypes.c_ulong * 4 * (AES_MAXNR+1)), 
  ("rounds",  ctypes.c_int)
  ] 

def printSizeof():
  print 'BIGNUM:',ctypes.sizeof(BIGNUM)
  print 'STACK:',ctypes.sizeof(STACK)
  print 'CRYPTO_EX_DATA:',ctypes.sizeof(CRYPTO_EX_DATA)
  print 'BN_MONT_CTX:',ctypes.sizeof(BN_MONT_CTX)
  print 'EVP_PKEY:',ctypes.sizeof(EVP_PKEY)
  print 'ENGINE_CMD_DEFN:',ctypes.sizeof(ENGINE_CMD_DEFN)
  print 'ENGINE:', ctypes.sizeof(ENGINE)
  print 'RSA:',ctypes.sizeof(RSA)
  print 'DSA:',ctypes.sizeof(DSA)
  print 'EVP_CIPHER:',ctypes.sizeof(EVP_CIPHER)
  print 'EVP_CIPHER_CTX:',ctypes.sizeof(EVP_CIPHER_CTX)
  print 'EVP_MD:',ctypes.sizeof(EVP_MD)
  print 'EVP_MD_CTX:',ctypes.sizeof(EVP_MD_CTX)
  print 'HMAC_CTX:',ctypes.sizeof(HMAC_CTX)
  print 'AES_KEY:',ctypes.sizeof(AES_KEY)
  print 'HMAC_MAX_MD_CBLOCK:',HMAC_MAX_MD_CBLOCK
  print 'EVP_MAX_BLOCK_LENGTH:',EVP_MAX_BLOCK_LENGTH
  print 'EVP_MAX_IV_LENGTH:',EVP_MAX_IV_LENGTH
  print 'AES_MAXNR:',AES_MAXNR

