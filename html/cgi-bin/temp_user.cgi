#!/usr/bin/python
#=============================================================================
#
# temp_user.cgi
#
# Jacob Magnuson <jmagnus4@stumail.jccc.edu>
# 2015-24-11, version 0.0.0
#
# This script takes a query string of email=? and adds said email to the
# users_temp table in the database
#
#=============================================================================


"""
temp_user.cgi
=============

Takes a query string of email=? and adds the given email to the users_temp
table in the database. This allows an administrator to either approve or
decline the user. If the user is approved, a password reset will be initiated
and must be completed before the user can begin using their account.
"""


import cgi
import hashlib
import psycopg2
import sys


__version__ = '0.0.0'


#=============================================================================
def main():
    """
    Main entry point for the script. Ensures the new email address is not
    already present in the users table. If it is not present, adds the email
    to the users_temp table to await approval.

    @return True if the operation completed sucessfully, False otherwise
    """

    DB_CREDENTIALS = "dbname='faffoos_test' user='tim' " + \
                     "host='faffoos.com' password='sally664'"

    fields = cgi.FieldStorage()

    passwd = hashlib.sha256()

    passwd.update( fields.getvalue( 'password' ) )

    query_dict = {
                'email_address': fields.getvalue( 'email' ),
                'password': passwd.hexdigest()
            }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()
    query = 'SELECT email_address ' + \
            'FROM users ' + \
            'WHERE email_address = %(email_address)s'

    try:
        cur.execute( query, query_dict )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    if cur.fetchall():
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    query = 'INSERT INTO users_temp (email_address, password)' + \
            'VALUES (%(email_address)s, %(password)s)'

    try:
        cur.execute( query, query_dict )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    conn.commit()
    cur.close()
    conn.close()

    print 'Status: 200\n\n',

    return True


#=============================================================================
main()

