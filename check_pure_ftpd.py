#!/usr/bin/python

# Nagios check for monitoring Pure-FTPd service
# Version 1.0
# Author: Trey Simmons
# Latest Script Version Tested: 1.0
# Lowest Python Version Tested: 2.6.6

import sys
import os
import getopt
import ftplib

def main(argv):
  try:
    opts, args = getopt.getopt(argv, "hi:u:s:", ["help=", "ip=", "user=", "with-ssl="])
    validOpts = parse_args(opts)
    checkFTPConnection(validOpts)
  except getopt.GetoptError as e:
    return_response(2, "There was a problem with the arguments passed to this command: " + str(e).capitalize())

# Parse, validate, and group command line arguments
def parse_args(args):
  withSSL = False

  for opt, arg in args:
    if opt in ("-h", "--help"):
      # Display help message and immediately quit program
      helpMessage()
      sys.exit(0)
    elif opt in ("-i", "--ip-address"):
      ipAddress = arg
    elif opt in ("-u", "--user"):
      user = arg
    elif opt in ("-s", "with-ssl"):
      if arg in ("true", "True"):
        withSSL = bool(arg)

  # Build standardized arrangement of FTP connection data
  # Verify that all required data is present
  try:
    parsedOptions = (ipAddress, user, withSSL)
    return parsedOptions
  except UnboundLocalError as e:
    return_response(2, "A required flag was not set. Make sure that an IP address and user have been set for this command.")

# Construct help message trigged with "-h" or "--help" flag
def helpMessage():
  usage = "Usage: check_pure_ftpd.py [-h] -i I -u U [-s S]" + "\n"
  desc = "Check that an FTP server is running and accessible." + "\n"
  argHeader = "Arguments:"
  helpInfo = "-h, --help      Show info about this command, optional"
  ipInfo   = "-i, --ip        IP address of FTP server, string, required"
  userInfo = "-u, --user      User name for FTP server, string, required"
  sslInfo  = "-s, --with-SSL  Connect with SSL, optional, boolean, defaults to false"
  display = (usage, desc, argHeader, helpInfo, ipInfo, userInfo, sslInfo)
  helpText = "\n".join(str(s) for s in display)
  print helpText

# Attempt to connect and interact with the desired FTP server
def checkFTPConnection(options):
  password = getPasswordFromFile()

  errorReplyMsg = "The FTP server sent an unexpected response: "
  errorOtherMsg = "The FTP server could not be reached or manipulated: "
  successMsg = "The FTP server is reachable, and is responsive."

  if options[2] == True:
    try:
      ftps = ftplib.FTP_TLS(options[0], options[1], password)
      ftps.prot_p()
      ftps.cwd('upload')
      ftps.quit()
    except ftplib.error_reply as e:
      return_response(3, errorReplyMsg + str(e).capitalize())
    except (ftplib.error_temp, ftplib.error_perm, ftplib.error_proto) as e:
      return_response(2, errorOtherMsg + str(e).capitalize())
    else:
      return_response(0, successMsg)
  else:
    try:
      ftp = ftplib.FTP(options[0], options[1], password)
      ftp.cwd('upload')
      ftp.quit()
    except ftplib.error_reply as e:
      return_response(3, errorReplyMsg + str(e).capitalize())
    except (ftplib.error_temp, ftplib.error_perm, ftplib.error_proto) as e:
      return_response(2, errorOtherMsg + str(e).capitalize())
    else:
      return_response(0, successMsg)

# Load saved password for FTP user from "ftp_password" file
def getPasswordFromFile():
  passFile =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "ftp_password")
  if os.path.isfile(passFile):
    try:
      loadedFile = open(passFile, 'rb')
    except IOError as e:
      return_response(2, "The FTP password could not be retrieved. Please check the 'ftp_password' file.")
    else:
      with loadedFile:
        password = loadedFile.read()
      return password.rstrip()
  else:
    return_response(3, "There is no valid 'ftp_password' file present. Please create this file before running this script")

# Send response and exit program based on exit code needed
def return_response(response_type, message):
  if response_type == 0:
    print "OK - " + message
    sys.exit(0)
  elif response_type == 1:
    print "WARNING - " + message
    sys.exit(1)
  elif response_type == 2:
    print "CRITICAL - " + message
    sys.exit(2)
  elif response_type == 3:
    print "UNKNOWN - " + message
    sys.exit(3)
  else:
    print "This is not a valid Nagios exit status."
    sys.exit(3)

# Initialize Python module
if __name__ == "__main__":
  main(sys.argv[1:])
