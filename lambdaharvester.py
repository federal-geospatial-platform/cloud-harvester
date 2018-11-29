#!/home/ec2-user/environment/harvester/bin/python27
# -*- coding: latin-1 -*-
import globals
import os
import shutil
import time
import zipfile
import boto3

def zipdir(dirpath, zipfilename):
    os.chdir(dirpath)
    # ziph is zipfile handle
    ziph = zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('.'):
        for file in files:
            ziph.write(os.path.join(root, file))
    
    ziph.close()



def UploadFiletoS3Bucket(filepath, S3dir,bcopy = True):
    s3_resource= boto3.resource('s3')
    S3BUCKETNAME = globals.S3BUCKETNAME
    fileName = os.path.basename(filepath)
    if bcopy:
        shutil.copyfile(filepath, '/tmp/'+fileName)
        s3_resource.Object(S3BUCKETNAME, S3dir + fileName).put(Body=open('/tmp/'+fileName, 'rb'))
    else:
        s3_resource.Object(S3BUCKETNAME, S3dir + fileName).put(Body=open(filepath, 'rb'))
    return


def lambda_handler(event, context):
    import sys
    import json
    import commands
    import datetime
    import subprocess
    import logging


    LOCALBINPATH = globals.LOCALBINPATH
    CKANKEY = globals.CKANKEY
    PRODURL = globals.PRODURL
    STAGINGURL = globals.STAGINGURL
    LOCALBINPATH = globals.LOCALBINPATH
    RESOURCEFILEPATH = globals.RESOURCEFILEPATH
    DEVURL = globals.DEVURL
    S3BUCKETNAME = globals.S3BUCKETNAME
    S3RESOURCEFILENAME = globals.S3RESOURCEFILENAME
    OPERATION_ENV = globals.OPERATION_ENV
    LOGFILEPATH = globals.LOGFILEPATH
    LASTRUNTIME = globals.HARVESTSTART
    FORCEHARVESTSTART = globals.FORCEHARVESTSTART
    FORCEREMOVELOCKFILE = globals.FORCEREMOVELOCKFILE

    runlastfile = RESOURCEFILEPATH + "/run.last"

    #Check running instances
    if(FORCEREMOVELOCKFILE.upper() == 'YES' or FORCEREMOVELOCKFILE.upper() == 'TRUE'  ):
        if (os.path.isfile("/tmp/run.lock" ) ):
            os.remove("/tmp/run.lock")

    if (os.path.isfile("/tmp/run.lock" ) ):
        lockfileAge_In_Secs = time.time() - os.stat("/tmp/run.lock").st_mtime
        if ( lockfileAge_In_Secs < 10800 ):
		    print("Aborting: Lock file 'run.lock' found")
		    exit(0)

    #from shutil import copyfile
    fullpath = os.path.realpath(__file__)
    directory = os.path.dirname(fullpath)
    os.chdir(directory)

    #Set working environnement path
    os.environ['PYTHONPATH']=directory + ':' + LOCALBINPATH
    os.environ['PATH']= LOCALBINPATH + ':' + os.environ['PATH']

    #Config loggging file
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
       
    todaylogfile = LOGFILEPATH +"/" + today + "_harvester.log"

    ## Try to remove tree; if failed show an error using try...except on screen
    #try:
    #    shutil.rmtree('/tmp/bin')
    #except OSError as e:
    #    print ("Error: %s - %s." % (e.filename, e.strerror))
    #print directory

    #-------- S3 variables -----------
    #s3_resource= boto3.resource('s3')
    s3_client= boto3.client('s3')
    bucketName = S3BUCKETNAME #'fgp-s3-harvester'
    #bucket = s3_resource.Bucket(bucketName)

    #-------- zip variables -------
    tmpFolder = '/tmp/'
    zipFilename= S3RESOURCEFILENAME #'harvesterResources.zip'
    zipfilepath = tmpFolder+zipFilename
    s3_client.download_file(bucketName, zipFilename, zipfilepath)

    zip_ref = zipfile.ZipFile(zipfilepath, 'r')
    zip_ref.extractall(RESOURCEFILEPATH)
    zip_ref.close()

    if not os.path.exists(LOGFILEPATH):
        os.makedirs(LOGFILEPATH)

    # print subprocess.check_output('ls -la -R /tmp', shell = True)
    logging.basicConfig(filename= todaylogfile,level=logging.DEBUG)
    logging.debug('Logging Start :' + str(datetime.datetime.now()))
    logging.info('**********************')
    logging.warning('************************')
    #fileName = os.path.basename(todaylogfile)
    # Lockfile
    # 86400 — one day
    # 10800 - three hours
    # Jump into the Harvest user directory
    #_rc = subprocess.call(["source","/home/harvest/.bash_profile"])

    lockfileAge_In_Secs = 0
    _rc= subprocess.call("chmod -R 755 " + LOCALBINPATH,shell=True)
    now = datetime.datetime.now()

    if (os.path.isfile("/tmp/run.lock" ) ):
        lockfileAge_In_Secs = time.time() - os.stat("/tmp/run.lock").st_mtime
        if ( lockfileAge_In_Secs < 10800  ):
            logging.debug("Aborting: Lock file 'run.lock' found")
            print("Aborting: Lock file 'run.lock' found")
            exit(0)

    runlastfile = RESOURCEFILEPATH + "/run.last"

    OGS_HARVEST_LAST_RUN = None
    if FORCEHARVESTSTART.upper() == 'TRUE':
        print "forcing run time using: " + str(LASTRUNTIME)
        OGS_HARVEST_LAST_RUN = LASTRUNTIME.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        if os.path.isfile(runlastfile):
            f = open( runlastfile)
            OGS_HARVEST_LAST_RUN = str(f.read()).strip()
            print "using start time from last run: " + OGS_HARVEST_LAST_RUN 
            f.close()
        else:
            print "run.last not existant, using default start time: "+ str(LASTRUNTIME)
            OGS_HARVEST_LAST_RUN = LASTRUNTIME.strftime("%Y-%m-%dT%H:%M:%SZ")

    logging.info('***********************************')
    logging.info('Version 2.0.0')
    logging.info("Current time: " + datetime.datetime.now().strftime('%H:%M:%S'))
    logging.info("***********************************")
    logging.info("Run starting from:")
    logging.info(OGS_HARVEST_LAST_RUN)

    _output = subprocess.call("python ./harvest_hnap.py -f " + OGS_HARVEST_LAST_RUN + " > " +RESOURCEFILEPATH + "/harvested_records.xml", shell=True, stderr=subprocess.STDOUT )

    # Create the common core JSON file
    try:
        _output = subprocess.check_output("cat " + RESOURCEFILEPATH + "/harvested_records.xml  | python ./hnap2cc-json.py", shell=True, stderr=subprocess.STDOUT )
        print str(_output)
        logging.info(_output)
        pass
    except subprocess.CalledProcessError, e:
        logging.error("Subprocess error :\n"+ e.output)
        UploadFiletoS3Bucket(todaylogfile,'logs/')
        print "Subprocess error :\n", e.output

    # Convert csv errors to html
    try:
        _output = subprocess.check_output("python ./csv2html.py -f " + RESOURCEFILEPATH + "/harvested_record_errors.csv", shell=True, stderr=subprocess.STDOUT)
        print str(_output)
        logging.info(_output)
        pass
        # myfilesize=$(stat --format=%s "harvested_records.jl")
    except subprocess.CalledProcessError, e:
        logging.error("Subprocess error :\n" + e.output)
        UploadFiletoS3Bucket(todaylogfile,'logs/')
        print "Subprocess  output:\n", e.output 

    myfilesize = os.stat(RESOURCEFILEPATH + "/harvested_records.jl").st_size

    lockfile = open("/tmp/run.lock","w+")

    # for Linux
    #myfilesize=`stat -f %z harvested_records.jl` # for OSX
    if (myfilesize == 0  ):
        _output = "No new/updated records since last harvest, skipping load into CKAN"
        logging.info(_output)
        print(_output)

    else:
        _output = "Found new/updated records, loading into CKAN..."
        print(_output)
        #os.chdir("/var/www/html/open_gov/staging-portal/ckan")
        #_rc = subprocess.call(["python","ckanapi","load","datasets -I",os.path.expanduser("~/_harvester_OpenMaps/harvested_records.jl"),"-c","production.ini"])

        try:
            if OPERATION_ENV.upper() == 'STAGING':
                # STAGING
                _output =  "Loading to CKAN STAGING"
                logging.info(_output)
                print _output
                processCmd = "ckanapi load datasets -I " + RESOURCEFILEPATH + "/harvested_records.jl -r https://staging.open.canada.ca/data -a " + CKANKEY
                _output = subprocess.check_output(processCmd, shell=True, stderr=subprocess.STDOUT)
                logging.info(_output)
                print _output
                pass
            
            if OPERATION_ENV.upper() == 'PRODUCTION':
                # PRODUCTION
                _output = "Loading to CKAN Production"
                logging.info(_output)
                print _output
                processCmd = "ckanapi load datasets -I " + RESOURCEFILEPATH + "/harvested_records.jl -r https://open.canada.ca/data -a " + CKANKEY
                _output = subprocess.check_output(processCmd, shell=True, stderr=subprocess.STDOUT) 
                logging.info(" : \n" + str(_output))
                print " : \n" + _output
                pass

            if OPERATION_ENV.upper() == 'TESTING':
                # LOCAL TESTING
                _output = "Loading to CKAN TESTING"
                print _output
                logging.info(_output)
                processCmd = "ckanapi load datasets -I " + RESOURCEFILEPATH + "/harvested_records.jl -r https://dev.open.canada.ca/data -a " + CKANKEY
                _output = subprocess.check_output(processCmd, shell=True, stderr=subprocess.STDOUT) 
                logging.info(_output)
                print(_output)
                pass

        except subprocess.CalledProcessError, e:
            _output = "Cannot push data at this time please check the server and try again \n" + e.output
            logging.warning(_output)
            UploadFiletoS3Bucket(todaylogfile,'logs/')
            print _output

        lockfile.write(now.strftime("%Y-%m-%dT%H:%M:%SZ"))

    lockfile.close()
    _rc = os.remove("/tmp/run.lock")
    UploadFiletoS3Bucket(todaylogfile,'logs/')
    runlastfhdl = open(runlastfile,"w+")
    runlastfhdl.write(now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    runlastfhdl.close()
    
    #os.remove(zipfilepath)
    zipdir(RESOURCEFILEPATH,"../" + S3RESOURCEFILENAME)
 
    if os.path.isfile(zipfilepath) is not None:
        UploadFiletoS3Bucket(zipfilepath,'', False)
    # print "xxxxxxxxxxxxxxxxxxxxxx"
    # print subprocess.check_output('ls -la -R /tmp', shell = True)
    return {
        "statusCode": 200,
        "body": json.dumps("fgp-cloud-harvester job completed"),
        "time":  time.ctime()
        }
        
#lambda_handler(None, None)
