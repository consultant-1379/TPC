/*------------------------------------------------------------------------------
 *******************************************************************************
 * COPYRIGHT Ericsson 2012
 *
 * The copyright to the computer program(s) herein is the property of
 * Ericsson Inc. The programs may be used and/or copied only with written
 * permission from Ericsson Inc. or in accordance with the terms and
 * conditions stipulated in the agreement/contract under which the
 * program(s) have been supplied.
 *******************************************************************************
 *----------------------------------------------------------------------------*/

package com.ericsson.eniq.tpc;

import org.python.core.Py;
import org.python.core.PyObject;
import org.python.core.PySystemState;

/**
 * Jython Object Factory using PySystemState
 */
public class JythonObjectFactory {

 private Class interfaceType;
 private PyObject klass;

 // Constructor obtains a reference to the importer, module, and the class name
 public JythonObjectFactory(PySystemState state, Class interfaceType, String moduleName, String className) {
	 try{
     this.interfaceType = interfaceType;
     PyObject importer = state.getBuiltins().__getitem__(Py.newString("__import__"));
     PyObject module = importer.__call__(Py.newString(moduleName));
     klass = module.__getattr__(className);
     //System.err.println("module=" + module + ",class=" + klass);
	 }catch(Exception e){
		 e.printStackTrace();
	 }
 }

 // This constructor passes through to the other constructor
 public JythonObjectFactory(Class interfaceType, String moduleName, String className) {
     this(new PySystemState(), interfaceType, moduleName, className);
 }

 // All of the followng methods return
 // a coerced Jython object based upon the pieces of information
 // that were passed into the factory. The differences are
 // between them are the number of arguments that can be passed
 // in as arguents to the object.

 public Object createObject() {
     return klass.__call__().__tojava__(interfaceType);
 }


 public Object createObject(Object arg1) {
     return klass.__call__(Py.java2py(arg1)).__tojava__(interfaceType);
 }

 public Object createObject(Object arg1, Object arg2) {
     return klass.__call__(Py.java2py(arg1), Py.java2py(arg2)).__tojava__(interfaceType);
 }

 public Object createObject(Object arg1, Object arg2, Object arg3)
 {
     return klass.__call__(Py.java2py(arg1), Py.java2py(arg2),
         Py.java2py(arg3)).__tojava__(interfaceType);
 }

 public Object createObject(Object args[], String keywords[]) {
     PyObject convertedArgs[] = new PyObject[args.length];
     for (int i = 0; i < args.length; i++) {
         convertedArgs[i] = Py.java2py(args[i]);
     }

     return klass.__call__(convertedArgs, keywords).__tojava__(interfaceType);
 }

 public Object createObject(Object... args) {
     return createObject(args, Py.NoKeywords);
 }
}