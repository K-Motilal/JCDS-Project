#!/usr/bin/perl

use strict;
use warnings;
use feature "switch";
use DBI;
use XML::LibXML;
use POSIX qw/ strftime /;
use enum qw/ OK=0 AUTH=14 DB=15 /;

my @db_credentials = ('DBI:Pg:dbname=faffoos_test;host=faffoos.com', 'tim', 'sally664');

# parse out the cookies
# that are needed
my @rawCookies = split /; /, $ENV{'HTTP_COOKIE'};
my %cookies;
foreach (@rawCookies) {
	my ($key, $val) = split /\=/, $_;
	$cookies{$key} = $val;
}
$cookies{'user'} =~ s/%40/\@/;

# check identity of user
&validate_user ($cookies{'user'}, $cookies{'token'});

# parse out the URI
# parameters that are
# needed

my @queries = split /&/, $ENV{'QUERY_STRING'};
my %query;
foreach (@queries) {
	my ($key, $val) = split /\=/, $_;
	$query{$key} = $val;
}

if ($ENV{'REQUEST_METHOD'} eq 'POST') {

	# determine based on POST parameters
	# what action, if any, to take
	for ($query{'action'}) {
		when ('delete') {
			die unless $query{'r'};
			&delete_reservation ($query{'r'});
			# print the XML document with HTTP header
			print "Content-type: application/xml\n\n";
			print &load_schedule ($cookies{'user'}, $cookies{'token'});
		}
		when ('add') {
			die unless (
				$query{'v'} &&
				$query{'begin'} &&
				$query{'end'} );
			print "Content-type: application/xml\n\n";
			print &add_reservation($cookies{'user'}, $query{'v'}, $query{'begin'}, $query{'end'});
		}
	}
} elsif ($ENV{'REQUEST_METHOD'} eq 'GET') {

	# determine based on POST parameters
	# what action, if any, to take
	for ($query{'action'}) {
		when ('search') {
			# print the XML document with HTTP header
			print "Content-type: application/xml\n\n";
			print &load_availability ($query{'capacity'}, $query{'lift'}, $query{'begin'}, $query{'end'});
		}
		default {
			# print the XML document with HTTP header
			print "Content-type: application/xml\n\n";
			print &load_schedule ($cookies{'user'}, $cookies{'token'});
		}
	}
} else {

	# we don't know how to deal with this request
	die;
}

# load schedule information from
# the database and submit to
# build_table for processing
sub load_schedule {

	# in case of failure set failure reason
	$! = DB;

	my ($u, $c) = @_;
	my $dbh = DBI->connect (@db_credentials)
		or die DBI->errstr;
	my $sth = $dbh->prepare ('
		select s.reservation_id, s.pick_up, s.drop_off, s.vehicle_id,
			   f.capacity, f.lift, f.tie_down_no
		from schedule s
			inner join fleet f
			on s.vehicle_id = f.vehicle_id
		where s.user_id = (
			select user_id from users
			where email_address = ?)
		order by s.pick_up')
		or die $dbh->errstr;
	$sth->execute ($u)
		or die $sth->errstr;
	my @rows;
	while (my @row = $sth->fetchrow()) {
		push @rows, \@row;
	}

	$sth->finish;
	$dbh->disconnect;

	# reset
	$! = OK;

	&build_table (
		["Reservation", "Pick Up", "Drop Off", "Vehicle ID", "Capacity",
						"Lift", "Tie Downs", "Delete"],
		"Delete",
		"deleteReservation",
		@rows
	);
}

sub load_availability {

	# load user requirements and sanitize data
	my ($capacity, $lift, $begin, $end) = @_;
	$capacity = 0
		unless ($capacity);
	$lift = 'false' unless ($lift eq 'true');
	# convert Unix time to SQL time
	foreach ($begin, $end) {
		$_ = $_ ? $_ : time;
		$_ = strftime "%F %T", localtime ($_);
	}
	# in case of failure set failure reason
	$! = DB;

	my $dbh = DBI->connect (@db_credentials)
		or die DBI->errstr;
	my $sth = $dbh->prepare ('
		select vehicle_id, make, description, capacity, lift, tie_down_no
		from fleet
		where capacity >= ?
            and (location = \'Lackman Pool\')
			and (lift = ? or lift = true)
			and (vehicle_id not in (select vehicle_id
				from schedule
				where
					(pick_up between ? and ?)
					or
					(drop_off between ? and ?)
					or
					(? between pick_up and drop_off))
			)
		order by lift, capacity
		')
		or die $dbh->errstr;
	$sth->execute ($capacity, $lift, $begin, $end, $begin, $end, $begin)
		or die $sth->errstr;
	my @rows;
	while (my @row = $sth->fetchrow()) {
		push @rows, \@row;
	}

	$sth->finish;
	$dbh->disconnect;

	#reset
	$! = OK;

	&build_table (
		["Vehicle", "Make", "Description", "Capacity", "Lift", "Tie-Downs",
					"Add"],
		"Add",
		"addReservation",
		@rows
	);
}

# accepts a list of lists
# and builds the table
# returning an XML string
sub build_table {

	my $header_strings = shift @_;	# array reference containing table headers
	my $button_label = shift @_;	# string to label the action button with
	my $action = shift @_;			# ecmascript action to assign to the button
	my @rows = @_;					# table data as an array of array refs

	# tell libxml2 to skip the <?xml version="1.0"?> crap
	$XML::LibXML::skipXMLDeclaration = 1;

	# create an XML document with a
	# <table /> as it's root
	my $doc = XML::LibXML::Document->new ();
	my $root = $doc->createElement ('table');
	$doc->setDocumentElement ($root);

	# populate the table header and
	# attach it to the table
	my $header_container = $doc->createElement('thead');
	my $header_row = $doc->createElement ('tr');
	foreach (@$header_strings) {
	        my $element = $doc->createElement ('th');
	        $element->appendChild (XML::LibXML::Text->new ($_));
	        $header_row->appendChild ($element);
	}
	$header_container->appendChild ($header_row);
	$root->appendChild($header_container);

	# add rest of table
	my $body_container = $doc->createElement('tbody');
	foreach my $row (@rows) {
		my $row_element = $doc->createElement ('tr');
		foreach my $column (@$row) {
			my $data_element = $doc->createElement ('td');
			$data_element->appendChild (XML::LibXML::Text->new ($column));
			$row_element->appendChild ($data_element);
		}
		# add delete button
		my $button = $doc->createElement ('button');
		$button->{onclick} = $action . "($row->[0])";
		$button->appendChild (XML::LibXML::Text->new ($button_label));
		my $data_element = $doc->createElement ('td');
		$data_element->appendChild ($button);
		$row_element->appendChild ($data_element);

		$body_container->appendChild ($row_element);
	}
	$root->appendChild($body_container);

	$doc->toString;
}

sub delete_reservation {

	# in case of failure set failure reason
	$! = DB;

	my $r_id = pop;

        # remove reservation from database
        my $dbh = DBI->connect (@db_credentials)
                or die DBI->errstr;
        my $sth = $dbh->prepare ('
                delete from schedule
                where reservation_id = ?')
                or die $dbh->errstr;
        $sth->execute ($r_id)
                or die $sth->errstr;

	# reset
	$! = OK;

        # close database connection
        $sth->finish;
        $dbh->disconnect;
}

sub add_reservation {

	# in case of failure set failure reason
	$! = DB;

	my ($user, $vehicle_id, $begin, $end) = @_;
	if ($begin > $end) {
		print "Content-type: application/xml\n";
		print "Status: 400\n\n";
		die;
	}
	# sanitize the data
	foreach my $tm ($begin, $end) {
		my @tmp_time = localtime ($tm);
		$tmp_time[5] += 1900;
		++$tmp_time[4];
		$tm = "$tmp_time[5]-$tmp_time[4]-$tmp_time[3] $tmp_time[2]:$tmp_time[1]:$tmp_time[0]";
	}

        # add reservation to database
        my $dbh = DBI->connect (@db_credentials)
                or die DBI->errstr;
        my $sth = $dbh->prepare ('
                insert into schedule (
                user_id,
                vehicle_id,
                pick_up,
                drop_off
                ) values (
                (select user_id from users where email_address = ?),
                ?, ?, ? )')
                or die $dbh->errstr;
        $sth->execute ($user, $vehicle_id, $begin, $end)
                or die $sth->errstr;

	# reset
	$! = OK;

        # close database connection
        $sth->finish;
        $dbh->disconnect;

	&load_schedule;
}

# kill the program if the user
# is not authenticated
sub validate_user {

	# in case of failure set failure reason
	$! = DB;

        my($u, $c) = @_;

        # retrieve cookie from database
        my $dbh = DBI->connect (@db_credentials)
                or return 0;
        my $sth = $dbh->prepare ('
                select cookie from users
                where email_address = ?')
                or return 0;
        $sth->execute ($u)
                or return 0;
        my @real_cookie = $sth->fetchrow();

	# test authenticity of the token
	# and close database connection
        unless ($real_cookie[0] eq $c && $c ne "") {
		print "Status: 403 Forbidden\n\n";
		exit AUTH;
	}

	# reset
	$! = OK;

	$sth->finish;
        $dbh->disconnect;
}
