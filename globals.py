# -*- coding: latin-1 -*-
import os
import datetime

CKANKEY = None
PRODURL = None
STAGINGURL = None
LOCALBINPATH = None
RESOURCEFILEPATH = None
DEVURL = None
S3BUCKETNAME = None
S3RESOURCEFILENAME = None
OPERATION_ENV = None
LOGFILEPATH = "/tmp/harvester/logs"
FORCEREMOVELOCKFILE = None
FORCEHARVESTSTART = False

if os.environ.get('CKANKEY') is not None:
    CKANKEY=os.environ['CKANKEY']

if os.environ.get('DEVURL') is not None:
    DEVURL=os.environ['DEVURL']

if os.environ.get('PRODURL') is not None:
    PRODURL=os.environ['PRODURL']

if os.environ.get('STAGINGURL') is not None:
    STAGINGURL=os.environ['STAGINGURL']

if os.environ.get('S3BUCKETNAME') is not None:
    S3BUCKETNAME=os.environ['S3BUCKETNAME']

if os.environ.get('S3RESOURCEFILENAME') is not None:
    S3RESOURCEFILENAME=os.environ['S3RESOURCEFILENAME']

if os.environ.get('RESOURCEFILEPATH') is not None:
    RESOURCEFILEPATH=os.environ['RESOURCEFILEPATH']

if os.environ.get('LOCALBINPATH') is not None:
    LOCALBINPATH=os.environ['LOCALBINPATH']

if os.environ.get('OPERATION_ENV') is not None:
    OPERATION_ENV=os.environ['OPERATION_ENV']

if os.environ.get('LOGFILEPATH') is not None:
    LOGFILEPATH=os.environ['LOGFILEPATH']


FORCEREMOVELOCKFILE = os.getenv('FORCEREMOVELOCKFILE','FALSE')

FORCEHARVESTSTART = os.getenv('FORCEHARVESTSTART', 'FALSE')




HARVESTSTART = datetime.datetime.now() + datetime.timedelta(-30)
HARVESTSTART = HARVESTSTART.strftime("%Y-%m-%dT%H:%M:%SZ")

if os.environ.get('HARVESTSTART') is not None:
    temptime = os.environ.get('HARVESTSTART')
    if temptime is not None:
        ValidTimeInput = True
        try:
            HARVESTSTART = datetime.datetime.strptime(temptime + "T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            ValidTimeInput = False

    if ValidTimeInput == False:
        try:
            HARVESTSTART = datetime.datetime.strptime(temptime + "T00:00:00Z", "%d-%m-%YT%H:%M:%SZ")
        except ValueError:
            print "Validation Error!!!! HARVESTSTART value error please check the time format \"Year-Month-Day\" or \"Day-Month-Year\""
