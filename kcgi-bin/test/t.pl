#!/usr/bin/perl

print "Content-type: text/html\r\n\r\n";
foreach $ksy (keys %ENV){
    print "Key: ".$ksy." => ".$ENV{$ksy}."\n<br>";
}
