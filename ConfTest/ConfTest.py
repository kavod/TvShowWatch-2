#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import sys
import datetime
import unittest
import JSAG3

from unittest.runner import TextTestResult
TextTestResult.getDescription = lambda _, test: test.shortDescription()

class ConfTest(JSAG3.JSAG3):
    def __init__(self,id="confTest",dataFile="tests.json",confFile=None,resultPath=None,verbosity=False):
        curPath = os.path.dirname(os.path.realpath(__file__))
        JSAG3.JSAG3.__init__(self,
            id=id,
            schemaFile=curPath+"/ConfTest.jschem",
            dataFile=dataFile,
            verbosity=verbosity
        )
        if "confFile" not in self.keys():
            if confFile is None:
                Exception("File is not initialized. confFile is missing")
            else:
                self['confFile'] = confFile
        if "resultPath" not in self.keys():
            if resultPath is None:
                Exception("File is not initialized. resultPath is missing")
            else:
                self['resultPath'] = resultPath
        if "suite" not in self.keys():
            self['suite'] = []
        self.save()

    def addTest(self,testCase):
        self.save_result(testCase)
        self.save()

    def runAll(self):
        for testClass in self['suite']:
            self.runOne(testClass['className'])

    def runOne(self,className):
        self.logger.debug("Running {0}".format(className))
        moduleName = '.'.join(className.split('.')[:-1])
        module = __import__(moduleName)
        className = className.split('.')[-1]
        testCase = getattr(module, className)
        testFile = os.path.join(self['resultPath'],moduleName)
        suite = unittest.TestSuite()
        for test in unittest.TestLoader().loadTestsFromTestCase(testCase):
            suite.addTest(testCase(test._testMethodName,confFile=self['confFile']))

        with open(testFile,"w") as fd:
            fd.write(datetime.datetime.now().strftime('%c')+"\n")
            result = unittest.TextTestRunner(stream=fd,failfast=True,verbosity=2).run(suite)
        self.save_result(
            ".".join([moduleName,className]),
            datetime.datetime.now(),
            result.wasSuccessful()
        )
        self.save()

    def save_result(self,className,lastRun="",success=False):
        resultEntry = {
            'className': className,
            'lastRun' : lastRun,
            'success' : success
        }
        index = self.getTestIndex(className)
        if index is None:
            self['suite'].append(resultEntry)
        else:
            self['suite'][index] = resultEntry

    def getTestIndex(self,className):
        print(className)
        try:
            index = next(index for (index,test) in enumerate(self['suite']) if test['className'] == className )
        except StopIteration:
            return None
        else:
            return index
