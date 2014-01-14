#!/usr/bin/python

#
# sessionCtrl.py - manage vCenter connections
#

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl

import argparse
import ConfigParser
import atexit
import os
import datetime
import dateutil.parser
from collections import OrderedDict
import pprint

pp = pprint.PrettyPrinter()

# set up command line options
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(title='subcommands')
parser_view = subparsers.add_parser('view', help='View session(s)')
parser_view.set_defaults(which='view')
parser_view.add_argument('--session', dest='session_key', action='store', help="View this session's details")
parser_view.add_argument('--sort', dest='sortdir', choices=['asc', 'desc'], default='desc', action='store', help="Sort direction for last activity time")
parser_nuke = subparsers.add_parser('nuke', help='Log out session(s)')
parser_nuke.set_defaults(which='nuke')
parser_nuke.add_argument('--session', dest='session_key', action='store', help='Log out this session')
parser_nuke.add_argument('-d', '--noop', dest='noop', action='store_true', help='Dry run, take no action')
args = parser.parse_args()

# load configuration
SCRIPTPATH = os.path.dirname(os.path.abspath(__file__))
config = ConfigParser.ConfigParser()
config.read(SCRIPTPATH + '/config.yml')
HOSTNAME = config.get('vcenter', 'host')
PORT = config.get('vcenter', 'port')
USERNAME = config.get('vcenter', 'username')
PASSWORD = config.get('vcenter', 'password')
MAXIDLEHOURS = config.get('sessionCtrl', 'max_idle_hours')

# time considerations
datefmt = '%Y-%m-%d %H:%M:%S %Z%z'
now = datetime.datetime.now(dateutil.tz.tzutc())
#print now.strftime(datefmt)
maxidletime = 60*60*int(MAXIDLEHOURS)

def format_as_local(dt):
    return dt.astimezone(dateutil.tz.tzlocal()).strftime(datefmt)

def main():
    try:
        si = None
        try:
            si = SmartConnect(host=HOSTNAME, user=USERNAME, pwd=PASSWORD, port=int(PORT))
        except IOError, e:
            pass
        if not si:
            print "Could not connect to host: " + HOSTNAME
            return -1

        atexit.register(Disconnect, si)
        content = si.RetrieveContent()
        sm = content.sessionManager
        try:
            sessions = sm.sessionList
        except IndexError:
            print "No sessions found"
            return -1

        session_store = {}
        for sesh in sessions:
            session_store[sesh.key] = { 'userName': sesh.userName, 'lastActiveTime': sesh.lastActiveTime, 'fullName': sesh.fullName, 'loginTime': sesh.loginTime, 
                    'locale': sesh.locale, 'messageLocale': sesh.messageLocale, 'extensionSession': sesh.extensionSession, 'ipAddress': sesh.ipAddress, 
                    'userAgent': sesh.userAgent, 'callCount': sesh.callCount }

        if args.which == 'view':
            if args.session_key is None:
                tmp = {}
                for key, lat in session_store.iteritems():
                    tmp[key] = lat['lastActiveTime']
                sorted_sessions = OrderedDict(sorted(tmp.items(), key=lambda t: t[1], reverse=True if args.sortdir == 'desc' else False))
                for i in sorted_sessions.items():
                    key = i[0]
                    print "%-20s %-40s %s" % (session_store[key]['userName'], key, format_as_local(session_store[key]['lastActiveTime']))
            else:
                print 'userName: ' + session_store[args.session_key]['userName']
                print 'fullName: ' + session_store[args.session_key]['fullName']
                print 'loginTime: ' + format_as_local(session_store[args.session_key]['loginTime'])
                print 'lastActiveTime: ' + format_as_local(session_store[args.session_key]['lastActiveTime'])
                print 'ipAddress: ' + session_store[args.session_key]['ipAddress']
                print 'userAgent: ' + session_store[args.session_key]['userAgent']
                print 'locale: ' + session_store[args.session_key]['locale']
                print 'messageLocale: ' + session_store[args.session_key]['messageLocale']
                print 'extensionSession: ' + str(session_store[args.session_key]['extensionSession'])
                print 'callCount: ' + str(session_store[args.session_key]['callCount'])
        elif args.which == 'nuke':
            if args.session_key is None:
                # find all expired sessions
                tmp = []
                for key, s in session_store.iteritems():
                    lastActiveDelta = now - s['lastActiveTime']
                    if lastActiveDelta.total_seconds() > maxidletime:
                        tmp.append(key)
                # if dryrun, just print the sessions found
                if args.noop:
                    for key in tmp:
                        print "%-20s %-40s %s IS EXPIRED" % (session_store[key]['userName'], key, format_as_local(session_store[key]['lastActiveTime']))
                # terminate the sessions
                else:
                    sm.TerminateSession(tmp)
                    print 'Sessions terminated'
            else:
                # terminate the given session key
                if args.noop:
                    print 'Would terminate session ' + args.session_key
                else:
                    print 'Terminating session ' + args.session_key
                    sm.TerminateSession(args.session_key)
                    print 'Session terminated'

    except vmodl.MethodFault, e:
        print "Caught vmodl fault: " + e.msg
        return -1
    except Exception, e:
        print "Caught exception: " + str(e)
        return -1
    return 0

if __name__ == "__main__":
    main()
