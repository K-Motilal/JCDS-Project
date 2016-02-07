#!/usr/bin/python
#==============================================================================
#
# redirect.cgi
#
# Jacob Magnuson <jmagnus4@stumail.jccc.edu>
# 2015-03-12, version 0.0.0
#
# This script checks the user's administrator status and redirects them to the
# admin page if necessary.
#
#==============================================================================


"""
redirect.cgi
============

Redirects the user to the admin page if they meet qualifications
"""


import cgi
import Cookie
import os

import psycopg2


__version__ = '0.0.0'


#==============================================================================
# Module Constants
#==============================================================================
DB_CREDENTIALS = "dbname='faffoos_test' user='tim' " + \
                 "host='faffoos.com' password='sally664'"


#==============================================================================
def admin_redirect():
    """
    Reads the environment cookies and uses them to retrieve the user's admin
    status. Assumes the user is logged in because reservations.cgi should run
    before this.

    @return True if admin, False otherwise
    """

    try:
        cookie = Cookie.SimpleCookie( os.environ[ 'HTTP_COOKIE' ] )
    except:
        print 'Status: 403 Forbidden\n\n',
        return False

    query_dict = {
                'user' : cookie[ 'user' ].value,
            }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()
    query = 'SELECT admin ' + \
            'FROM users ' + \
            'WHERE email_address = %(user)s'

    try:
        cur.execute( query, query_dict )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    real_token = cur.fetchall()

    if real_token[ 0 ][ 0 ] == True:
        print 'Status: 200\n\n'
    else:
        print 'Status: 403 Forbidden\n\n'

    cur.close()
    conn.close()
    return True


#==============================================================================
admin_redirect()
