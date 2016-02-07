#!/usr/bin/python

import os
import subprocess

os.environ[ 'HTTP_COOKIE' ] = 'user=kmotilal@jccc.edu;' + \
                              'token=E2DF9C20-9892-11E5-8852-620F69064B53'

os.environ[ 'QUERY_STRING' ] = 'action=approve_user&email=jwmagnuson97@outlook.com&admin=false'
#os.environ[ 'QUERY_STRING' ] = 'action=load_vehicles'

subprocess.call( './admin.cgi', shell = True )
