#!/usr/bin/python

# Nagios check for monitoring Pure-FTPd service
# Version 2.0
# Author: Trey Simmons
# Latest Script Version Tested: 2.0
# Lowest Python Version Tested: 2.6.6

import sys
import os
import getopt
import re
import ftplib
import textwrap
import ConfigParser

def main(argv):
  try:
    opts, args = getopt.getopt(argv, "hi:u:", ["help=", "ip=", "user="])
    validOpts = parse_args(opts)
    checkFTPConnection(validOpts)
  except getopt.GetoptError as e:
    return_response(2, "There was a problem with the arguments passed to this command: " + str(e).capitalize())

# Parse, validate, and group command line arguments
def parse_args(args):
  for opt, arg in args:
    if opt in ("-h", "--help"):
      # Display help message and immediately quit program
      helpMessage()
      sys.exit(0)
    elif opt in ("-i", "--ip-address"):
      ipAddress = arg
    elif opt in ("-u", "--user"):
      user = arg

  # Build standardized arrangement of FTP connection data
  # Verify that all required data is present
  try:
    parsedOptions = (ipAddress, user)
    return parsedOptions
  except UnboundLocalError as e:
    return_response(2, "A required flag was not set. Make sure that an IP address and user have been set for this command.")

# Construct help message trigged with "-h" or "--help" flag
def helpMessage():
  usage = "Usage: check_pure_ftpd.py [-h] -i I -u U" + "\n"
  desc = "Check that an FTP server is running and accessible." + "\n"
  argHeader = "Arguments:"
  helpInfo = "-h, --help      Show info about this command, optional"
  ipInfo   = "-i, --ip        IP address of FTP server, string, required"
  userInfo = "-u, --user      User name for FTP server, string, required"

  aboutPassHeader = "\nPasswords for Authentication:"
  passInfo = "\nThis script requires a separate file, 'ftp_passwords.cfg' be generated in the same working directory. This file will be used to store valid passwords for possible FTP users. The format of the file should be as follows:"
  passFormat = "\n[Host Name]\nuser_name: user_password\n"
  passInfo2 = "\nThe file should contain one 'Host' section for each host that will be monitored using this script. Each user and password combo should be saved as a 'key: value' pair under the appropriate 'Host' section header.\n"
  passNote = "\nPlease Note: Permissions for this file should be as restrictive as possible - Only give access to this file to users that must be able to read this file for script execution (programmtic users) and trusted admins."

  # Format long help text to terminal width (80 characters)
  passInfoText = formatHelpInfo(passInfo)
  passInfo2Text = formatHelpInfo(passInfo2)
  passNoteText = formatHelpInfo(passNote)

  display = (usage, desc, argHeader, helpInfo, ipInfo, userInfo, aboutPassHeader, passInfoText, passFormat, passInfo2Text, passNoteText)
  helpMessage = "\n".join(str(s) for s in display)
  print helpMessage

# Format string for use in help message
def formatHelpInfo(helpInfoString):
  return "\n".join(str(s) for s in re.findall(r'.{1,80}(?:\s+|$)', helpInfoString))

# Attempt to connect and interact with the desired FTP server
def checkFTPConnection(options):
  password = getPasswordFromFile(options)

  errorReplyMsg = "The FTP server sent an unexpected response: "
  errorOtherMsg = "The FTP server could not be reached or manipulated: "
  successMsg = "The FTP server is reachable, and is responsive."

  try:
    ftps = ftplib.FTP_TLS(options[0], options[1], password)
    ftps.prot_p()
    ftps.cwd('upload')
    ftps.quit()
  except ftplib.error_reply as e:
    return_response(3,  + str(e).capitalize())
  except (ftplib.error_temp, ftplib.error_perm, ftplib.error_proto) as e:
    return_response(2, errorOtherMsg + str(e).capitalize())
  else:
    return_response(0, successMsg)

# Load saved password for FTP user from "ftp_password" file
def getPasswordFromFile(options):
  passFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ftp_passwords.cfg")

  config = ConfigParser.SafeConfigParser()

  if not os.path.isfile(passFile):
    return_response(3, "There is no valid 'ftp_passwords.cfg' file present. Please create this file before running this script")

  try:
    config.read(passFile)
  except IOError as e:
    return_response(2, "The FTP password could not be retrieved. Please check the 'ftp_passwords.cfg' file.")
  else:
    try:
      # Get password value that matches the given host and user for CLI arguments
      password = config.get(options[0], options[1])
    except ConfigParser.NoSectionError as e:
      return_response(2, "There are no user credentials stored for this host. Please add the host to the 'ftp_passwords.cfg' file.")
    except ConfigParser.NoOptionError as e:
      return_response(2, "The user was not found in the 'ftp_passwords.cfg' file. Please check that the user is present in the correct host section.")
    else:
      return password

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
