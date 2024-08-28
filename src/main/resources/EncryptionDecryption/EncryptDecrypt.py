'''
Created on 29 Jan 2018

@author: xarjsin
'''
from com.ericsson.eniq.tpc.encryption import ZipCrypter

class EncryptDecrypt(object):
    
    def __init__(self,logger):
        self.log = logger
    
    def encryptTPI(self,outputFile):
        cryptMode = 'encrypt'
        ISPUBLICKEY = 'false'
        keymodulate='123355219375882378192369770441285939191353866566017497282747046709534536708757928527167390021388683110840288891057176815668475724440731714035455547579744783774075008195670576737607241438665521837871490309744873315551646300131908174140715653425601662203921855253249615512397376967139410627761058910648132466577'
        keyexponent='56150463164644751914716495900093720157414415481292002669315194431219529412326876784449358059082155035515624734089410543128644396470938683386571095646717819191489425302090971582044719505456351962678152676022843274039720191188252080851399964166276217240881859709097082858039511039553656980967803072308827430913'    
        if outputFile:
            self.log.info('** Encryption Start **')
            zipCrypter = ZipCrypter()
            zipCrypter.setFile(outputFile)
            zipCrypter.setCryptType(cryptMode)
            zipCrypter.setIsPublicKey(ISPUBLICKEY)
            zipCrypter.setKeyModulate(keymodulate)
            zipCrypter.setKeyExponent(keyexponent)
            zipCrypter.execute()
        
        self.log.info('** Encryption End **')
            
    def decryptTPI(self,filePath):
        cryptMode = 'decrypt'
        ISPUBLICKEY = 'true'
        if filePath:
            self.log.info('** Decryption Start **')
            zipCrypterExtract = ZipCrypter()
            zipCrypterExtract.setFile(filePath)
            zipCrypterExtract.setCryptType(cryptMode)
            zipCrypterExtract.setIsPublicKey(ISPUBLICKEY)
            zipCrypterExtract.execute()
            
        self.log.info('** Decryption End **')
        
