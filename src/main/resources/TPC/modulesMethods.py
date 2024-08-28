'''
Created on 26 Jul 2016

@author: econcia
'''
import os, sys, inspect
import CLI

#projectLocation = os.path.dirname(os.getcwd())
#projectLocation = 'C:\Users\ebrifol\Documents\Projects\TPC_V4\Project_Code'
unwantedPackages = {'CLI'}

modules = {}
methods = []
arguments = {}

def loadModules():
    ''' Populates the modules and arguments dictionaries, as well as the methods list '''
    
    for name, obj in inspect.getmembers(sys.modules[CLI.__name__]):
            if inspect.isclass(obj):
                modules[obj] = obj()

    for moduleName in modules:
        for className, classLocation in inspect.getmembers(modules[moduleName], inspect.isclass):
            for methodName, methodLocation in inspect.getmembers(classLocation, inspect.ismethod):
                if not methodName.startswith('_'):
                    methods.append(methodName)
                    functionArguments = inspect.getargspec(getattr(classLocation, methodName))[0]
                    for functionArgument in functionArguments:
                        arguments[methodName] = []
                        try:
                            arguments[methodName].append(functionArgument)
                        except:
                            arguments[methodName] = [functionArgument]   
    
def modulesMethods():
    ''' Return a string containing all modules and methods '''
    
    modulesMethods = ''        
            
    for moduleName in sorted(modules):
        modulesMethods += '\n\n' + moduleName.__name__
        for className, classLocation in inspect.getmembers(modules[moduleName], inspect.isclass):
            for methodName, methodLocation in inspect.getmembers(classLocation, inspect.ismethod):
                if not methodName.startswith('_'):
                    modulesMethods += '\n   ' + methodName + '\n        Description:' 
                    try:
                        modulesMethods += getattr(classLocation, methodName).__doc__ 
                    except:
                        modulesMethods += ''
                    modulesMethods += '\n        Arguments: ' + ', '.join(inspect.getargspec(getattr(classLocation, methodName))[0][1:])
               
    return modulesMethods
          
def runMethod(inputMethod, inputArguments = None):
    ''' Find and run requested method '''
    
    methodArguments = []
    
    if inputMethod in methods:
        for moduleName in modules:
            for className, classLocation in inspect.getmembers(modules[moduleName], inspect.isclass):
                for methodName, methodLocation in inspect.getmembers(classLocation, inspect.ismethod):
                    if methodName == inputMethod:
                        for arg in arguments[methodName]:
                            if arg in vars(inputArguments):
                                methodArguments.append(vars(inputArguments)[arg])
                            
                        getattr(classLocation(), inputMethod)(*methodArguments)
    else:
        print 'Invalid method', inputMethod, '\n', \
              'Type \'tpc -h\' or \'tpc --help\' to bring up a list of available methods and their arguments.\n'
              
              
              
              
              
              
              
              
              
              
              
              
              