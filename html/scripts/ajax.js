/**
 *  @author Jacob Magnuson <jwmagnuson95@outlook.com>
 *
 *  @module ajax.js
 *
 *  @version 0.0.0
 *
 *  @file Contains all user functions that utilize AJAX
 */


//============================================================================
function checkAdminStatus() {
    /**
     * @function
     *
     * @name checkAdminStatus
     *
     * @description Calls the redirect.cgi and redirects the user to the admin
     * page if needed.
     */

    // Make the Ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('GET', '/cgi-bin/redirect.cgi?random=' +
                    randString(10), true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    window.location.assign('/admin.html');
                    break;
                case 403:
                    break;
                default:
                    break;
            }
        }
    };
}


//============================================================================
function loadReservationsTable() {
    /**
     *  @function
     *
     *  @name loadReservationsTable
     *
     *  @description Ajax function that calls reservations.cgi and places the
     *  response text in the 'reservations' div
     */

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('GET', '/cgi-bin/reservations.cgi?random=' +
                    randString(10), true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    checkAdminStatus();
                    setInner('reservations', xmlRequest.responseText);
                    formatReservations();
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
function deleteReservation(resNumber) {
    /**
     *  @function
     *
     *  @name deleteReservation
     *
     *  @param {Number} resNumber - The id number of the reservation to delete
     *
     *  @description Ajax function that calls reservations.cgi with a
     *  queryString of 'action=delete&r={resNumber}',
     *  where resNumber is the reservation id to be deleted
     */

    // Ask for confirmation
    if(!window.confirm('Are you sure you want to delete reservation ' +
                       resNumber + '?')) return;

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST', '/cgi-bin/reservations.cgi?action=delete&r=' +
                    resNumber, true);
    xmlRequest.send();

    // Update the reservation table on successful delete
    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner('reservations', xmlRequest.responseText);
                    formatReservations();
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
function fillId(id) {
    /**
     *  @function
     *
     *  @name fillId
     *
     *  @param {String} id - The id of the element to be filled
     *
     *  @description Ajax function that calls metadata.cgi with the query
     *  string ;id={id}', which requests the needed html for the given id,
     *  then places the html received from the server into the element
     *  associated with the given id
     */

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('GET', '/cgi-bin/metadata.cgi?id=' + id +
                    '&random=' + randString(10), true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        // Display the table from the backend
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    setInner(id, xmlRequest.responseText);
                    break;
                case 403:
                    loginRedirect();
                    break;
                default:
                    alert('Server Error: ' + xmlRequest.status);
                    break;
            }
        }

        // Add a default option 'Any'
        document.getElementById(id).add(new Option('Any', -1), 0);
        document.getElementById(id)[0].selected = true;
    };
}


//============================================================================
function getAvailable() {
    /**
     *  @function
     *
     *  @name getAvailable
     *
     *  @description Ajax function that calls reservations.cgi with the query
     *  string 'action=search&capacity={capacity}&begin={begin}&end={end]&
     *  lift={lift}', this retrieves a list of vehicles available within the
     *  given parameters. The function then places the returned html into the
     *  element associated with the id 'available'
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

    // Build the query string, ensuring each variable exists before appending
    var queryString = '/cgi-bin/reservations.cgi?action=search';
    if (capacity !== '-1') {
        queryString += '&capacity=' + capacity;
    }
    if (begin !== '-1') {
        queryString += '&begin=' + begin;
    }
    if (end !== '-1') {
        queryString += '&end=' + begin;
    }
    if (lift !== '-1') {
        queryString += '&lift=' + lift;
    }

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
                    formatAvailable();
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
function addReservation(vehicleId) {
    /**
     *  @function
     *
     *  @name addReservation
     *
     *  @param {Number} vehicleId - the id of the vehicle to which a
     *  reservation will be added
     *
     *  @description Ajax function that calls reservations.cgi with the query
     *  string 'action=add&v={vehicleId}&begin={begin}&end={end}',
     *  the cgi then uses the given data to add a reservation on the back end,
     *  then refreshes the reservations table to reflect the changes
     */

    // Scrape necessary data from select boxes
    var startDate   = getDateFromId('start-date-select');
    var startTime   = getDateFromId('start-time-select');
    var endDate     = getDateFromId('end-date-select');
    var endTime     = getDateFromId('end-time-select');

    // Convert to unix timestamp
    var begin       = getTimestamp(startDate, startTime);
    var end         = getTimestamp(endDate, endTime);

    // Build the query string
    var queryString = '/cgi-bin/reservations.cgi?action=add&v=' + vehicleId +
        '&begin=' + begin + '&end=' + end;

    // Make sure the start time is before the end time
    if (begin >= end) {
        alert('Error: Start Time must be before End Time');
        return;
    }

    // Make the ajax call
    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST', queryString, true);
    xmlRequest.send();

    // Update the reservations table after a reservation is added
    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    toggleVisible('add-modal');
                    setInner('reservations', xmlRequest.responseText);
                    formatReservations();
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
function logout() {
    /**
     *  @function
     *
     *  @name logout
     *
     *  @description Ajax function that calls auth with the queryString
     *  'logout'. The cgi then invalidates the current session cookie.
     *  After the cgi returns a successful status, this function deletes
     *  the user cookies from the browser and redirects the user to the
     *  login page
     */

    var xmlRequest = new XMLHttpRequest();
    xmlRequest.open('POST', '/cgi-bin/auth?logout', true);
    xmlRequest.send();

    xmlRequest.onreadystatechange = function() {
        if (xmlRequest.readyState == 4) {
            switch (xmlRequest.status) {
                case 200:
                    document.cookie = 'token=;' +
                        'expires=Thu, 01 Jan 1970 00:00:00 UTC;' +
                        'path=/cgi-bin/';
                    document.cookie = 'user=;' +
                        'expires=Thu, 01 Jan 1970 00:00:00 UTC;' +
                        'path=/cgi-bin/';
                    loginRedirect();
                    break;
                case 403:
                    document.cookie = 'token=;' +
                        'expires=Thu, 01 Jan 1970 00:00:00 UTC;' +
                        'path=/cgi-bin/';
                    document.cookie = 'user=;' +
                        'expires=Thu, 01 Jan 1970 00:00:00 UTC;' +
                        'path=/cgi-bin/';
                    loginRedirect();
                    break;
                default:
                    alert('Logout Failed: ' + xmlRequest.status);
                    break;
            }
        }
    };
}

