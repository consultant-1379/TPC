'''
Created on Jan 31, 2018

@author: xarjsin
'''
import EncryptionDecryption



class Encryption(object):
    ''' Module to Encrypt/Decrypt a tpi or universe package'''
    
    def encryptPackage(self,params,logger):
        packagePath = params['Package']
        ecrypt = EncryptionDecryption.EncryptDecrypt(logger)
        ecrypt.encryptTPI(packagePath)
    
    
    def decryptPackage(self,params,logger):
        packagePath = params['Package']
        decrypt = EncryptionDecryption.EncryptDecrypt(logger)
        decrypt.decryptTPI(packagePath)
        
