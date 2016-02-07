#!/usr/bin/python
#=============================================================================
#
# admin.cgi
#
# Kaleb Motilal <kmotilal@jccc.edu>,
# Jacob Magnuson <jmagnus4@stumail.jccc.edu>
# 2015-30-11, version 0.0.0
#
# This script acts on query strings passed to it through AJAX. It is capable
# of performing all administrator actions need for the VROOMS web-app. This
# script always requires a query string to include an 'action' value, as well
# as be sent by an authorized user (something that is determined using the
# browser's cookies).
#
#=============================================================================


"""
admin.cgi
=========

Interprets and acts upon query strings passed to it from the admin front-end.
All query strings must be sent by an authorized user and contain an 'action'
value.
"""


import cgi
import Cookie
import datetime
import hashlib
from lxml import etree
import os
import psycopg2
import random
import string


__version__ = '0.0.0'


#=============================================================================
# Module Constants
#=============================================================================
DB_CREDENTIALS = "dbname='faffoos_test' user='tim' " + \
                 "host='faffoos.com' password='sally664'"

INPUT_DATA = cgi.FieldStorage()


#=============================================================================
def main():
    """
    Primary entry point for the script. Validates the user, then calls a
    corresponding function based on the value of the 'action' parameter in
    the query string

    @return False if user is not valid
    """

    if not validate_user():
        return False

    action = INPUT_DATA.getvalue( 'action' )

    if action == 'load_reservations':
        load_reservations()

    elif action == 'load_select':
        load_select()

    elif action == 'load_available':
        load_available()

    elif action == 'delete_reservation':
        delete_reservation()

    elif action == 'add_reservation':
        add_reservation()

    elif action == 'load_vehicles':
        load_vehicles()

    elif action == 'delete_vehicle':
        delete_vehicle()

    elif action == 'add_vehicle':
        add_vehicle()

    elif action == 'update_vehicle':
        update_vehicle()

    elif action == 'update_location':
        update_location()

    elif action == 'load_users':
        load_users()

    elif action == 'delete_user':
        delete_user()

    elif action == 'add_user':
        add_user()

    elif action == 'approve_user':
        approve_user(True)

    elif action == 'decline_user':
        approve_user(False)


#=============================================================================
def validate_user():
    """
    Reads the environment cookies and compares the user's email and token to
    the corresponding values in the database. If the cookie does not exist
    or does not match the database value, the function prints an http header
    indicating a status of 403 Forbidden.

    @return True if user is valid, False otherwise
    """
    try:
        cookie = Cookie.SimpleCookie( os.environ[ 'HTTP_COOKIE' ] )
    except:
        print 'Status: 403 Forbidden\n\n',
        return False

    query_dict = {
                'user' : cookie[ 'user' ].value,
                'token': cookie[ 'token' ].value
            }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()
    query = 'SELECT cookie, admin ' + \
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
    if real_token[ 0 ][ 0 ] != query_dict[ 'token' ] or\
       real_token[ 0 ][ 1 ] != True:
        print 'Status: 403 Forbidden\n\n',
        return False

    cur.close()
    conn.close()
    return True


#=============================================================================
def load_reservations():
    """
    Queries the database for all records in the schedule table and constructs
    a table out of the returned values

    @return True if the operation completed sucessfully, False otherwise
    """

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()
    query = 'SELECT s.reservation_id, u.email_address, ' + \
                   's.vehicle_id, s.pick_up, s.drop_off ' + \
            'FROM schedule as s ' + \
            'INNER JOIN users as u ' + \
            'ON u.user_id = s.user_id ' + \
            'ORDER BY pick_up ASC'

    try:
        cur.execute( query )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    reservation_data = cur.fetchall()
    header_data = [ 'Reservation ID', 'User', 'Vehicle ID',
                    'Pick Up', 'Drop Off', '' ]

    build_table( header_data, reservation_data, [ 'Delete' ],
                 [ 'deleteReservationAdmin' ] )

    cur.close()
    conn.close()
    return True


#=============================================================================
def load_select():
    """
    Queries the database and constructs a select menu based on the 'id'
    parameter of the query string

    @return True if the operation completed sucessfully, False otherwise
    """

    select_id = INPUT_DATA.getvalue( 'id' )

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()
    if select_id == 'user-select':
        query = 'SELECT email_address ' + \
                'FROM users ' + \
                'ORDER BY email_address'

    elif select_id == 'location-select':
        query = 'SELECT DISTINCT location ' + \
                'FROM fleet ' + \
                'WHERE location NOT LIKE \'%Auction%\' ' + \
                'ORDER BY location'

    elif select_id == 'class-select':
        query = 'SELECT DISTINCT vehicle_class ' + \
                'FROM fleet ' + \
                'ORDER BY vehicle_class'

    elif select_id == 'make-select':
        query = 'SELECT DISTINCT make ' + \
                'FROM fleet ' + \
                'ORDER BY make'

    try:
        cur.execute( query )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    select_data = cur.fetchall()

    build_select( select_data )

    cur.close()
    conn.close()

    return True


#=============================================================================
def load_available():
    """
    Queries the database for available vehicles at the given times and with
    the given requirements, constructs a table of the returned values

    @return True if the operation completed sucessfully, False otherwise
    """

    if INPUT_DATA.getvalue( 'capacity' ) == None:
        query_dict = {
                    'capacity' : int( 0 ),
                    'lift'     : INPUT_DATA.getvalue( 'lift' ),
                    'begin'    : datetime.datetime.fromtimestamp(
                                    int( INPUT_DATA.getvalue( 'begin' ) ) ),
                    'end'      : datetime.datetime.fromtimestamp(
                                    int( INPUT_DATA.getvalue( 'end' ) ) )
                }
    else:
        query_dict = {
                    'capacity' : int( INPUT_DATA.getvalue( 'capacity' ) ),
                    'lift'     : INPUT_DATA.getvalue( 'lift' ),
                    'begin'    : datetime.datetime.fromtimestamp(
                                    int( INPUT_DATA.getvalue( 'begin' ) ) ),
                    'end'      : datetime.datetime.fromtimestamp(
                                    int( INPUT_DATA.getvalue( 'end' ) ) )
                }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'SELECT vehicle_id, make, description, ' + \
            'capacity, lift, tie_down_no ' + \
            'FROM fleet ' + \
            'WHERE capacity >= %(capacity)s ' + \
                'AND (lift = %(lift)s OR lift = true) ' + \
                'AND (vehicle_id NOT IN (' + \
                    'SELECT vehicle_id ' + \
                    'FROM schedule ' + \
                    'WHERE ' + \
                    '(pick_up BETWEEN %(begin)s AND %(end)s) ' + \
                    'OR ' + \
                    '(drop_off BETWEEN %(begin)s AND %(end)s) ' + \
                    'OR ' + \
                    '(%(begin)s between pick_up AND drop_off))) ' + \
            'ORDER BY lift, capacity'

    try:
        cur.execute( query, query_dict )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    available_data = cur.fetchall()
    header_data = [ 'Vehicle ID', 'Make', 'Description', 'Capacity',
                    'Lift', 'Tie-Downs', '' ]

    build_table( header_data, available_data, [ 'Add' ],
                 [ 'addReservationAdmin' ] )

    cur.close()
    conn.close()
    return True


#=============================================================================
def delete_reservation():
    """
    Deletes a record from the schedule table using the given id number

    @return True if the operation completed sucessfully, False otherwise
    """

    query_dict = {
                'reservation_id': int(
                    INPUT_DATA.getvalue( 'reservation_id' ) )
            }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'DELETE FROM schedule ' + \
            'WHERE reservation_id = %(reservation_id)s'

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

    load_reservations()

    return True


#=============================================================================
def add_reservation():
    """
    Inserts a record into the schedule table containing the values passed via
    query string

    @return True if the operation completed sucessfully, False otherwise
    """

    query_dict = {
                # NOTE: user_id is NOT an integer, in this case it is a string
                # (it's the user's email, not their id number)
                'user_id'   : INPUT_DATA.getvalue( 'user_id' ),
                'vehicle_id': int( INPUT_DATA.getvalue( 'vehicle_id' ) ),
                'begin'     : datetime.datetime.fromtimestamp(
                                int( INPUT_DATA.getvalue( 'begin' ) ) ),
                'end'       : datetime.datetime.fromtimestamp(
                                int( INPUT_DATA.getvalue( 'end' ) ) )
            }

    if query_dict[ 'begin' ] >= query_dict[ 'end' ]:
        print 'Status: 400\n\n',
        return False

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'INSERT INTO schedule (user_id, vehicle_id, pick_up, drop_off)' + \
            'VALUES ((SELECT user_id FROM users ' + \
                     'WHERE email_address = %(user_id)s), ' + \
                     '%(vehicle_id)s, %(begin)s, %(end)s)'

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

    load_reservations()

    return True


#=============================================================================
def load_vehicles():
    """
    Queries the fleet table and constructs three tables based on vehicle
    location (Lackman Pool, Maintenance, and other locations)

    @return True if the operation completed sucessfully, False otherwise
    """

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'SELECT * ' + \
            'FROM fleet ' + \
            'WHERE location = \'Lackman Pool\' ' + \
            'ORDER BY vehicle_id'

    try:
        cur.execute( query )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    vehicle_data = cur.fetchall()
    header_data = [ 'Vehicle ID', 'Capacity', 'Location',
                    'Model Year', 'Make', 'Class',
                    'Description', 'Lift', 'Tie Downs',
                    'License', 'VIN', '', '', '' ]
    button_names = [ 'Set', 'Update', 'Delete' ]
    button_funcs = [ 'setMaintenanceAdmin', 'updateVehicleAdmin',
                     'deleteVehicleAdmin' ]

    build_table( header_data, vehicle_data, button_names, button_funcs,
                 DOM_id_prefix = 'lack' )

    query = 'SELECT * ' + \
            'FROM fleet ' + \
            'WHERE location = \'Maintenance\' ' + \
            'ORDER BY vehicle_id'

    try:
        cur.execute( query )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    vehicle_data = cur.fetchall()
    button_names = [ 'Unset', 'Update', 'Delete' ]
    button_funcs = [ 'unsetMaintenanceAdmin', 'updateVehicleAdmin',
                     'deleteVehicleAdmin' ]

    build_table( header_data, vehicle_data, button_names, button_funcs,
                 print_header = False, DOM_id_prefix = 'maint' )

    query = 'SELECT * ' + \
            'FROM fleet ' + \
            'WHERE location != \'Lackman Pool\' ' + \
                'AND location != \'Maintenance\' ' + \
                'AND location not like \'%Auction%\' ' + \
            'ORDER BY vehicle_id'

    try:
        cur.execute( query )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    vehicle_data = cur.fetchall()

    button_names = [ 'Update', 'Delete' ]
    button_funcs = [ 'updateVehicleAdmin', 'deleteVehicleAdmin' ]

    build_table( header_data, vehicle_data, button_names, button_funcs,
                 print_header = False, DOM_id_prefix = 'other' )

    cur.close()
    conn.close()

    return True


#=============================================================================
def delete_vehicle():
    """
    Deletes a vehicle from the fleet table based on the given id

    @return True if the operation completed sucessfully, False otherwise
    """

    query_dict = {
                'vehicle_id': int( INPUT_DATA.getvalue( 'vehicle_id' ) )
            }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'DELETE FROM schedule ' + \
            'WHERE vehicle_id = %(vehicle_id)s'

    try:
        cur.execute( query, query_dict )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    query = 'DELETE FROM fleet ' + \
            'WHERE vehicle_id = %(vehicle_id)s'

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

    load_vehicles()

    return True


#=============================================================================
def add_vehicle():
    """
    Inserts a record into the fleet table based on the parameters passed via
    query string

    @return True if the operation completed sucessfully, False otherwise
    """

    query_dict = {
                'vehicle_id'    : int( INPUT_DATA.getvalue( 'vehicle_id' ) ),
                'capacity'      : int( INPUT_DATA.getvalue( 'capacity' ) ),
                'location'      : INPUT_DATA.getvalue( 'location' ),
                'year'          : int( INPUT_DATA.getvalue( 'year' ) ),
                'make'          : INPUT_DATA.getvalue( 'make' ),
                'vehicle_class' : INPUT_DATA.getvalue( 'class' ),
                'description'   : INPUT_DATA.getvalue( 'description' ),
                'lift'          : INPUT_DATA.getvalue( 'lift' ),
                'tie_down_no'   : int( INPUT_DATA.getvalue( 'ties' ) ),
                'license_id'    : INPUT_DATA.getvalue( 'license' ),
                'vin_id'        : INPUT_DATA.getvalue( 'vin' )
            }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'INSERT INTO fleet (vehicle_id, capacity, location, year, ' + \
                        'make, vehicle_class, description, lift, ' + \
                        'tie_down_no, license_id, vin_id) ' + \
            'VALUES(%(vehicle_id)s, %(capacity)s, %(location)s, ' + \
                   '%(year)s, %(make)s, %(vehicle_class)s, ' + \
                   '%(description)s, %(lift)s, %(tie_down_no)s, ' + \
                   '%(license_id)s, %(vin_id)s)'

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

    load_vehicles()

    return True


#=============================================================================
def update_vehicle():
    """
    Inserts a record into the fleet table based on the parameters passed via
    query string

    @return True if the operation completed sucessfully, False otherwise
    """

    query_dict = {
                'vehicle_id'    : int( INPUT_DATA.getvalue( 'vehicle_id' ) ),
                'capacity'      : int( INPUT_DATA.getvalue( 'capacity' ) ),
                'location'      : INPUT_DATA.getvalue( 'location' ),
                'year'          : int( INPUT_DATA.getvalue( 'year' ) ),
                'make'          : INPUT_DATA.getvalue( 'make' ),
                'vehicle_class' : INPUT_DATA.getvalue( 'class' ),
                'description'   : INPUT_DATA.getvalue( 'description' ),
                'lift'          : INPUT_DATA.getvalue( 'lift' ),
                'tie_down_no'   : int( INPUT_DATA.getvalue( 'ties' ) ),
                'license_id'    : INPUT_DATA.getvalue( 'license' ),
                'vin_id'        : INPUT_DATA.getvalue( 'vin' )
            }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'UPDATE fleet ' + \
            'SET vehicle_id = %(vehicle_id)s, ' + \
                'capacity = %(capacity)s, ' + \
                'location = %(location)s, ' + \
                'year = %(year)s, ' + \
                'make = %(make)s, ' + \
                'vehicle_class = %(vehicle_class)s, ' + \
                'description = %(description)s, ' + \
                'lift = %(lift)s, ' + \
                'tie_down_no = %(tie_down_no)s, ' + \
                'license_id = %(license_id)s, ' + \
                'vin_id = %(vin_id)s ' + \
            'WHERE vehicle_id = %(vehicle_id)s'

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

    load_vehicles()

    return True


#=============================================================================
def update_location():
    """
    Updates the location of the vehicle with the given id, primarily used to
    move vehicles to and from maintenance

    @return True if the operation completed sucessfully, False otherwise
    """

    query_dict = {
                'vehicle_id': int( INPUT_DATA.getvalue( 'vehicle_id' ) ),
                'new_location': INPUT_DATA.getvalue( 'new_location' )
            }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'UPDATE fleet ' + \
            'SET location = %(new_location)s ' + \
            'WHERE vehicle_id = %(vehicle_id)s'

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

    load_vehicles()

    return True


#============================================================================
def load_users():
    """
    Queries the users table for all records and creates a table containing
    all non-critical information (excludes passwords and tokens)

    @return True if the operation completed sucessfully, False otherwise
    """

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'SELECT email_address ' + \
            'FROM users_temp ' + \
            'ORDER BY email_address'

    try:
        cur.execute( query )
    except:
        print 'Status: 400\n\n'
        cur.close()
        conn.close()
        return False

    temp_data = cur.fetchall()
    header_data = [ 'Email Address', '', '' ]
    button_names = [ 'Approve', 'Decline' ]
    button_funcs = [ 'approveUserAdmin', 'declineUserAdmin' ]

    not_printed = True
    if temp_data:
        build_table( header_data, temp_data, button_names, button_funcs )
        not_printed = False

    query = 'SELECT user_id, email_address, admin ' + \
            'FROM users ' + \
            'ORDER BY user_id'

    try:
        cur.execute( query )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    user_data = cur.fetchall()
    header_data = [ 'User ID', 'Email Address', 'Administrator', '' ]

    build_table( header_data, user_data, [ 'Delete' ], [ 'deleteUserAdmin' ],
                 print_header = not_printed )

    cur.close()
    conn.close()

    return True


#=============================================================================
def delete_user():
    """
    Deletes the record corresponding to the given id from the users table

    @return True if the operation completed sucessfully, False otherwise
    """

    query_dict = {
                'user_id' : int( INPUT_DATA.getvalue( 'user_id' ) )
            }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'DELETE FROM schedule ' + \
            'WHERE user_id = %(user_id)s'

    try:
        cur.execute( query, query_dict )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    query = 'DELETE FROM users ' + \
            'WHERE user_id = %(user_id)s'

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

    load_users()

    return True


#=============================================================================
def add_user( hashed = False ):
    """
    Adds a record to the users table with the given values. If no password is
    specified, a random 50 character string is generated and substituted.
    Passwords are appropriately hashed before being inserted.

    @return True if the operation completed sucessfully, False otherwise
    """

    passwd = hashlib.sha256()

    # If no password is given, generate a random password
    if INPUT_DATA.getvalue( 'password' ) == None:
        passwd.update(''.join(random.SystemRandom().choice(\
                string.ascii_uppercase + string.digits) for _ in range(50)))
    else:
        passwd.update( INPUT_DATA.getvalue( 'password' ) )

    query_dict = {
                'email_address': INPUT_DATA.getvalue( 'email' ),
                'admin': INPUT_DATA.getvalue( 'admin' ),
                'password': passwd.hexdigest()
            }

    if hashed:
        query_dict [ 'password' ] = INPUT_DATA.getvalue( 'password' )

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'INSERT INTO users (email_address, password, admin) ' + \
            'VALUES (%(email_address)s, %(password)s, %(admin)s)'

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

    load_users()

    return True


#=============================================================================
def approve_user(approved):
    """
    Deletes the corresponding record from the users_temp table and, depending
    on the value of approved, adds a new record to the users table

    @param approved Boolean value indicating whether or not a record should
                    be added to the main users table

    @return         True if the operation completed sucessfully,
                    False otherwise
    """

    query_dict = {
                'email': INPUT_DATA.getvalue( 'email' )
            }

    try:
        conn = psycopg2.connect( DB_CREDENTIALS )
    except:
        print 'Status: 503\n\n',
        return False

    cur = conn.cursor()

    query = 'SELECT password FROM users_temp ' + \
            'WHERE email_address = %(email)s'

    try:
        cur.execute( query, query_dict )
    except:
        print 'Status: 400\n\n',
        cur.close()
        conn.close()
        return False

    os.environ[ 'QUERY_STRING' ] += '&password=' + cur.fetchall()[ 0 ][ 0 ]
    global INPUT_DATA
    INPUT_DATA = cgi.FieldStorage() # I'm sorry

    query = 'DELETE FROM users_temp ' + \
            'WHERE email_address = %(email)s'

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

    if approved:
        add_user( hashed = True )
    else:
        load_users()

    return True


#=============================================================================
def build_table( header_data, body_data, button_text, button_action,
                 print_header = True, DOM_id_prefix = '' ):
    """
    Constructs an html table out of the given parameters and prints it, along
    with a html header indicating a status of 200 (sucessful)

    @param header_data   A list containing values for each cell in the table
                         header row

    @param body_data     A list of tuples containing data for the body of the
                         table, the list should preferably be the data
                         returned by psycopg2

    @param button_text   A list of strings containing the desired text for
                         each button (each button is appended as a new cell at
                         the end of each row of the table)

    @param button_action A list of strings containing the name of the
                         javascript function each button will call

    @param print_header  A boolean value that indicates whether the function
                         should print the html header or not, defaults to
                         true

    @return              True if the table was sucessfully created, otherwise
                         False
    """

    if print_header:
        print 'Content-Type: text/html'
        print 'Status: 200\n\n',

    root = etree.Element( 'table' )
    head = etree.Element( 'thead' )
    row  = etree.Element( 'tr' )
    for data in header_data:
        child = etree.Element( 'th' )
        child.text = str( data )
        row.append( child )

    head.append( row )
    root.append( head )

    body = etree.Element( 'tbody' )
    for data_row in body_data:
        row = etree.Element( 'tr' )
        for data_cell in data_row:
            child      = etree.Element( 'td' )
            child.text = str( data_cell )
            child.set( 'contenteditable', 'true' )
            row.append( child )


        for pos in range( len( button_text ) ):
            child       = etree.Element( 'td' )
            button      = etree.Element( 'button' )
            button.text = str( button_text[pos] )
            if button.text == 'Update':
                button.set( 'onclick', button_action[pos] + '(\'' + \
                        DOM_id_prefix + str( data_row[ 0 ] ) + '\')' )
            else:
                button.set( 'onclick', button_action[pos] + '(\'' + \
                        str( data_row[ 0 ] ) + '\')' )
            child.append( button )
            row.append( child )

        row.set( 'id', DOM_id_prefix + str( data_row[ 0 ] ) )
        body.append( row )

    root.append( body )

    print etree.tostring( root ),

    return True


#=============================================================================
def build_select( body_data ):
    """
    Constructs an html select element based on the given data

    @param body_data A list of tuples containing the desired data, preferably
                     data returned by psycopg2

    @return          True if the element was sucessfully created, otherwise
                     False
    """

    print 'Content-Type: text/html'
    print 'Status: 200\n\n',

    root = etree.Element( 'select' )

    for data in body_data:
        child = etree.Element( 'option' )
        child.text = str( data[0] )
        root.append( child )

    print etree.tostring( root, pretty_print = True ),

    return True


#=============================================================================
main()

