'''
Created on Jul 6, 2016

@author: ebrifol
'''

class DataStorage(object):


    def __init__(self):
        self.dataStorage = {}
        
    def addDataToStore(self, storageKey, storageValue):
        self.dataStorage[storageKey] = storageValue
        
    def getDataFromStore(self, storageKey):
        if storageKey in self.dataStorage:
            return self.dataStorage[storageKey]
        else:
            dummyreturn = []
            return dummyreturn
    
    def removeDataFromStore(self, storageKey):
        self.dataStorage.pop(storageKey, None)
    
    def clearDataStore(self):
        self.dataStorage = {}

        