/**
 *  @author Jacob Magnuson
 *
 *  @module admin.js
 *
 *  @version 0.0.0
 *
 *  @file Contains functions specific to the admin page
 */


//============================================================================
function adminToggleVisible (id, butId) {
    /**
     *  @function
     *
     *  @name adminToggleVisible
     *
     *  @param {String} id - the id of the element to make visible
     *
     *  @param {String} butId - the id of the sidebar button that corresponds
     *  to the given id
     *
     *  @description Hides all visible content windows and sets their buttons
     *  to the normal button color. This function then makes the desired
     *  content window visible and sets the corresponding button's color to
     *  the highlight color
     */

    var resId       = document.getElementById('reservations');
    var vehId       = document.getElementById('vehicles');
    var useId       = document.getElementById('users');

    var resButId    = document.getElementById('reservations-button');
    var vehButId    = document.getElementById('vehicles-button');
    var useButId    = document.getElementById('users-button');

    var ele         = document.getElementById(id);
    var eleBut      = document.getElementById(butId);
    var a           = document.getElementById('download-button');

    // Make all elements invisible
    if  (resId.style.visibility == 'visible') {
        resId.style.visibility          = 'hidden';
        resButId.className              = 'unselected-button';
    }
    if  (vehId.style.visibility == 'visible') {
        vehId.style.visibility          = 'hidden';
        vehButId.className              = 'unselected-button';
    }
   if  (useId.style.visibility == 'visible') {
        useId.style.visibility          = 'hidden';
        useButId.className              = 'unselected-button';
    }

    // Set wanted element to visible
    ele.style.visibility = 'visible';
    eleBut.className     = 'selected-button';

    // Adjust the download button's link
    if (ele == vehId || ele == resId) {
        a.style.visibility = 'visible';
        a.href = 'cgi-bin/csv?' + id;
    }
    else {
        a.style.visibility = 'hidden';
        a.href = '';
    }
}


//============================================================================
function toggleModal() {
    /**
     *  @function
     *
     *  @name toggleModal
     *
     *  @description Similarly to toggleVisible, this function hides all modal
     *  windows, then shows the correct modal window based on which content
     *  window is currently visible
     */

    var resId       = document.getElementById('reservations');
    var vehId       = document.getElementById('vehicles');
    var useId       = document.getElementById('users');

    var modId       = document.getElementById('modal-window');

    var ele         = '';

    if      (resId.style.visibility == 'visible') {
        ele = document.getElementById('add-reservations');
        generateDates(60);
        generateTimes();
        fillId('capacity-select');
        loadSelectAdmin('user-select');
    }
    else if (vehId.style.visibility == 'visible') {
        ele = document.getElementById('add-vehicles');
        loadSelectAdmin('location-select');
        loadSelectAdmin('make-select');
        loadSelectAdmin('class-select');
    }
    else if (useId.style.visibility == 'visible') {
        ele = document.getElementById('add-users');
    }
    else {
        return;
    }

    modId.style.visibility =
        modId.style.visibility == 'visible' ? 'hidden' : 'visible';

    ele.style.visibility =
        ele.style.visibility   == 'visible' ? 'hidden' : 'visible';

}


//============================================================================
function loadReservationsTableAdmin() {
    /**
     * @function
     *
     * @name loadReservationsTableAdmin
     *
     * @description Ajax function that calls admin.cgi with the query string
     * 'action=load_reservations' and places the response text in the
     * 'reservations' div
     */

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('GET',
                    '/cgi-bin/admin.cgi?action=load_reservations' +
                    '&random=' + randString(10),
                    true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('reservations', xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function loadAvailableTableAdmin() {
    /**
     * @function
     *
     * @name loadAvailableTableAdmin
     *
     * @description Ajax function that calls reservations.cgi, which returns
     * a list of available vehicles based on values scraped from the html
     */

    // Scrape necessary data from select boxes
    var startDate   = getDateFromId('start-date-select');
    var startTime   = getDateFromId('start-time-select');
    var endDate     = getDateFromId('end-date-select');
    var endTime     = getDateFromId('end-time-select');
    var capacity    = document.getElementById('capacity-select').value;
    var lift        = document.getElementById('lift-select').checked;

    // Convert the date objects to Unix Timestamps
    var begin       = getTimestamp(startDate, startTime);
    var end         = getTimestamp(endDate, endTime);

    var queryString = '/cgi-bin/admin.cgi?action=load_available' +
                      '&capacity=' + capacity +
                      '&lift=' + lift +
                      '&begin=' + begin +
                      '&end=' + end;

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('GET', queryString + '&random=' + randString(10), true);
    xmlRequest.send();

    // Display the ajax response
    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('available', xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function deleteReservationAdmin(resNumber) {
    /**
     *  @function
     *
     *  @name deleteReservationAdmin
     *
     *  @param {Number} resNumber - The id number of the reservation to delete
     *
     *  @description Ajax function that calls reservations.cgi with a
     *  queryString of 'action=delete_reservation&r={resNumber}',
     *  where resNumber is the reservation id to be deleted
     */

    // Ask for confirmation
    if(!window.confirm('Are you sure you want to delete reservation ' +
                       resNumber + '?')) return;

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST',
                    '/cgi-bin/admin.cgi?action=delete_reservation' +
                    '&reservation_id=' +
                    resNumber,
                    true);
    xmlRequest.send();

    // Update the reservation table on successful delete
    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('reservations', xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function addReservationAdmin(vehicleId) {
    /**
     * @function
     *
     * @name addReservationAdmin
     *
     * @param {Number} vehicleId - The id number of the vehicle to reserve
     *
     * @description Calls the admin.cgi with a query string containing the data
     * necessary to create a reservation (user, start date/time, end date/time)
     */

    // Scrape necessary data from html
    var user_id     = document.getElementById('user-select').value;
    var startDate   = getDateFromId('start-date-select');
    var startTime   = getDateFromId('start-time-select');
    var endDate     = getDateFromId('end-date-select');
    var endTime     = getDateFromId('end-time-select');

    // Convert dates to Unix Timestamps
    var begin       = getTimestamp(startDate, startTime);
    var end         = getTimestamp(endDate, endTime);

    // Make sure the begin time comes before the end time
    if (begin >= end) {
        alert('Error: Start Time must be before End Time');
        return;
    }

    // Build the query string
    var queryString ='/cgi-bin/admin.cgi?action=add_reservation' +
                     '&vehicle_id=' + vehicleId + '&user_id=' + user_id +
                     '&begin=' + begin + '&end=' + end;

    alert( queryString );
    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST', queryString, true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    toggleModal();
                    setInner('reservations', xmlRequest.responseText);
                    break;
                case 400:
                    alert('Error: Bad Input');
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };

}


//============================================================================
function loadVehiclesTableAdmin() {
    /**
     * @function
     *
     * @name loadVehiclesTableAdmin
     *
     * @description Ajax function that calls admin.cgi with the query string
     * 'action=load_vehicles' and places the response text in the 'vehicles' div
     */

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('GET',
                    '/cgi-bin/admin.cgi?action=load_vehicles' +
                    '&random=' + randString(10), true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('vehicles', xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function deleteVehicleAdmin(id) {
    /**
     * @function
     *
     * @name deleteVehicleAdmin
     *
     * @param {Number} id - The id of the vehicle to delete
     *
     * @description Calls the admin.cgi with the query string 'action=
     * delete_vehicle&vehicle_id={id}', which deletes the vehicle with the
     * given id
     */

    // Ask for confirmation
    if(!window.confirm('Deleting this vehicle will also delete all active ' +
                       'reservations associated with this vehicle. Are you ' +
                       'sure you want to delete vehicle ' +
                       id + '?')) return;

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST',
                    '/cgi-bin/admin.cgi?action=delete_vehicle&vehicle_id=' + id,
                    true);
    xmlRequest.send();
    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('vehicles', xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function addVehicleAdmin() {
    /**
     * @function
     *
     * @name addVehicleAdmin
     *
     * @description Ajax function that scrapes the necessary data from the
     * html and sends it in a query string to the admin.cgi, which adds the
     * vehicle to the database
     */
    var vehicle_id      = document.getElementById('vehicle-id').value;
    var capacity        = document.getElementById('vehicle-capacity').value;
    var location        = document.getElementById('location-select').value;
    var year            = document.getElementById('vehicle-year').value;
    var make            = document.getElementById('make-select').value;
    var vehicle_class   = document.getElementById('class-select').value;
    var description     = document.getElementById('vehicle-description').value;
    var lift            = document.getElementById('vehicle-lift').checked;
    var ties            = document.getElementById('vehicle-ties').value;
    var license         = document.getElementById('vehicle-license').value;
    var vin             = document.getElementById('vehicle-vin').value;

    queryString = '/cgi-bin/admin.cgi?action=add_vehicle'+
                  '&vehicle_id=' + vehicle_id +
                  '&capacity=' + capacity +
                  '&location=' + location +
                  '&year=' + year +
                  '&make=' + make +
                  '&class=' + vehicle_class +
                  '&description=' + description +
                  '&lift=' + lift +
                  '&ties=' + ties +
                  '&license=' + license +
                  '&vin=' + vin;

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST', queryString, true);
    xmlRequest.send();
    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('vehicles', xmlRequest.responseText);
                    toggleModal();
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function setMaintenanceAdmin(id) {
    /**
     * @function
     *
     * @name setMaintenanceAdmin
     *
     * @param {Number} id - The id of the vehicle to move to maintenance
     *
     * @description Makes an ajax call that changes the location of the given
     * vehicle to 'Maintenance'
     */

    // Build the query string
    queryString = '/cgi-bin/admin.cgi?action=update_location' +
                  '&vehicle_id=' + id +
                  '&new_location=Maintenance';

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST', queryString, true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('vehicles', xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function unsetMaintenanceAdmin(id) {
    /**
     * @function
     *
     * @name unsetMaintenanceAdmin
     *
     * @param {Number} id - The id of the vehicle to move to maintenance
     *
     * @description Makes an ajax call that changes the location of the given
     * vehicle to 'Lackman Pool'
     */

    // Build the query string
    queryString = '/cgi-bin/admin.cgi?action=update_location' +
                  '&vehicle_id=' + id +
                  '&new_location=Lackman Pool';

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST', queryString, true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('vehicles', xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function updateVehicleAdmin(DOM_id) {
    /**
     * @function
     *
     * @name updateVehicleAdmin
     *
     * @param {String} DOM_id - The row's DOM id
     *
     * @description Scrapes all data from the selected row and sends it to
     * the cgi, where the database is updated.
     */

    // Scrape data from the html
    row = document.getElementById(DOM_id);
    data = row.getElementsByTagName('td');

    vehicle_id          = data[0].innerHTML;
    vehicle_capacity    = data[1].innerHTML;
    vehicle_location    = data[2].innerHTML;
    vehicle_year        = data[3].innerHTML;
    vehicle_make        = data[4].innerHTML;
    vehicle_class       = data[5].innerHTML;
    vehicle_description = data[6].innerHTML;
    vehicle_lift        = data[7].innerHTML;
    vehicle_ties        = data[8].innerHTML;
    vehicle_license     = data[9].innerHTML;
    vehicle_vin         = data[10].innerHTML;

    queryString = '/cgi-bin/admin.cgi?action=update_vehicle'+
                  '&vehicle_id=' + vehicle_id +
                  '&capacity=' + vehicle_capacity +
                  '&location=' + vehicle_location +
                  '&year=' + vehicle_year +
                  '&make=' + vehicle_make +
                  '&class=' + vehicle_class +
                  '&description=' + vehicle_description +
                  '&lift=' + vehicle_lift +
                  '&ties=' + vehicle_ties +
                  '&license=' + vehicle_license +
                  '&vin=' + vehicle_vin;

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST', queryString, true);
    xmlRequest.send();
    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('vehicles', xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}
//============================================================================
function loadUsersTableAdmin() {
    /**
     * @function
     *
     * @name loadUsersTableAdmin
     *
     * @description Ajax function that calls admin.cgi with the query string
     * 'action=load_users' and places the response text in the 'users' div
     */

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('GET',
                    '/cgi-bin/admin.cgi?action=load_users' +
                    '&random=' + randString(10), true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('users', xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function deleteUserAdmin(id) {
    /**
     * @function
     *
     * @name deleteUserAdmin
     *
     * @param {Number} id - The id of the user to be deleted
     *
     * @description Ajax function that calls admin.cgi with the query string
     * 'action=delete_user&user_id={id}', which deletes the specified user
     * from the database
     */

    // Ask for confirmation
    if(!window.confirm('Deleting this user will also delete all active ' +
                       'reservations associated with this user. ' +
                       'Are you sure you want to delete user ' +
                       id + '?')) return;

    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST',
                    '/cgi-bin/admin.cgi?action=delete_user&user_id=' + id,
                    true);
    xmlRequest.send();
    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('users', xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function addUserAdmin() {
    /**
     * @function
     *
     * @name addUserAdmin
     *
     * @description Ajax function that calls admin.cgi which adds a user based
     * on data that has been scraped from the html
     */

    var email = document.getElementById('email').value;
    var password = document.getElementById('password').value;
    var passwordConfirm = document.getElementById('password-confirm').value;
    var admin = document.getElementById('admin-select').checked;

    if (password != passwordConfirm) {
        alert('Password fields must match');
        return;
    }

    if (admin === true) {
        if (!window.confirm('You are attempting to add a user with ' +
                            'administrator privileges, are you sure ' +
                            'you want to do this?')) return;
    }

    queryString = '/cgi-bin/admin.cgi?action=add_user&email=' + email +
                  '&password=' + password + '&admin=' + admin;

    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST', queryString, true);
    xmlRequest.send();
    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('users', xmlRequest.responseText);
                    toggleModal();
                    break;
                case 400:
                    alert('There is already a user registered with that' +
                          ' email address');
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


//============================================================================
function approveUserAdmin(email) {
    /**
     * @function
     *
     * @name approveUserAdmin
     *
     * @param {String} email - A string containing the email address to
     * approve
     *
     * @description Ajax function that calls the admin cgi and transfers a
     * user from the temp_users table to the users table
     */

    var xmlRequest = new XMLHttpRequest();

    queryString = '/cgi-bin/admin.cgi?action=approve_user' +
        '&admin=false&email=' + email;
    xmlRequest.open('POST', queryString, true);
    xmlRequest.send();
    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('users', xmlRequest.responseText);
                    break;
                case 400:
                    alert('There is already a user registered with that' +
                          ' email address');
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };

}


//============================================================================
function loadSelectAdmin(id) {
    /**
     * @function
     *
     * @name loadSelectAdmin
     *
     * @param {Number} id - The id of the html element to load
     *
     * @description Calls the admin.cgi with the query string
     * 'action=load_select' and places the response in the given id, currently
     * only handles the id's of user-select and locations
     */

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('GET',
                    '/cgi-bin/admin.cgi?action=load_select' +
                    '&id=' + id + '&random=' + randString(10),
                    true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner(id, xmlRequest.responseText);
                    if (id == 'user-select')
                        loadAvailableTableAdmin();
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }
    };
}


