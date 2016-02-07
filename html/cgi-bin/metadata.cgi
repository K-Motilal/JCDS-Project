#!/usr/bin/perl

use strict;
use warnings;
use feature "switch";
use DBI;
use XML::LibXML;
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

if ($ENV{'REQUEST_METHOD'} eq 'GET') {

	# determine based on GET parameters
	# what action, if any, to take
	for ($query{'id'}) {
		when ('capacity-select') {
			print "Content-type: application/xml\n\n";
			print &max_capacity;
		}
		default {
			die(); # do real HTTP error code later
		}
	}
} else {
	die (); # replace with real HTTP shit later
}

sub max_capacity {

	# in case of failure set failure reason
	$! = DB;

	my ($u, $c) = @_;
	my $dbh = DBI->connect (@db_credentials)
		or die DBI->errstr;
	my $sth = $dbh->prepare ('
		select distinct capacity
		from fleet
		order by capacity')
		or die $dbh->errstr;
	$sth->execute ()
		or die $sth->errstr;
	my @rows;
	while (my @row = $sth->fetchrow()) {
		push @rows, \@row;
	}

	$sth->finish;
	$dbh->disconnect;

	# reset
	$! = OK;

	&build_table (@rows);
}

# accepts a list of lists
# and builds the table
# returning an XML string
sub build_table {

	my @rows = @_;

	# tell libxml2 to skip the <?xml version="1.0"?> crap
	$XML::LibXML::skipXMLDeclaration = 1;

	# create an XML document with a
	# <select /> as it's root
	my $doc = XML::LibXML::Document->new ();
	my $root = $doc->createElement ('select');
	$doc->setDocumentElement ($root);

	# add <option /> list
	foreach my $row (@rows) {
		my $row_element = $doc->createElement ('option');
		foreach my $column (@$row) {
			$row_element->appendChild (XML::LibXML::Text->new($column));
		}

		$root->appendChild ($row_element);
		$root->appendChild (XML::LibXML::Text->new ("\n"));
	}

	$doc->toString;
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
