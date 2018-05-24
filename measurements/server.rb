#!/usr/bin/env ruby

require 'rubygems'
require 'rubydns'
require 'time'

Name = Resolv::DNS::Name
IN = Resolv::DNS::Resource::IN

RubyDNS.run_server() do
	match('dns-test.timwattenberg.de', IN::SOA) do |transaction|
		transaction.respond!(
			Name.create('ns.dns-test.timwattenberg.de.'),	# Master Name
			Name.create('admin.example.org.'),		# Responsible Name
			Time.parse("00:00", Time.now).to_i,		# Serial Number
			1200,						# Refresh Time
			900,						# Retry Time
			3_600_000,					# Maximum TTL / Expiry Time
			172_800,					# Minimum TTL
			#ttl: 4711					# TTL for SOA Record
		)
		
		transaction.append!(transaction.question, IN::NS, section: :authority)
	end

	match('01.dns-test.timwattenberg.de', IN::SOA) do |transaction|
		transaction.respond!(
			Name.create('ns.dns-test.timwattenberg.de.'),	# Master Name
			Name.create('mail.timwattenberg.de.'),		# Responsible Name
			Time.now.to_i,					# Serial Number
			86400,						# Refresh Time
			7200,						# Retry Time
			3_600_000,					# Maximum TTL / Expiry Time
			172_800,					# Minimum TTL
			#ttl: 4711					# TTL for SOA Record
		)
	end

	match('02.dns-test.timwattenberg.de', IN::SOA) do |transaction|
		transaction.respond!(
			Name.create('ns.dns-test.timwattenberg.de.'),	# Master Name
			Name.create('mail.timwattenberg.de.'),		# Responsible Name
			Time.now.to_i,					# Serial Number
			86400,						# Refresh Time
			7200,						# Retry Time
			3_600_000,					# Maximum TTL / Expiry Time
			172_800,					# Minimum TTL
			ttl: 0					# TTL for SOA Record
		)
	end

	match('03.dns-test.timwattenberg.de', IN::SOA) do |transaction|
		transaction.respond!(
			Name.create('ns.dns-test.timwattenberg.de.'),	# Master Name
			Name.create('mail.timwattenberg.de.'),		# Responsible Name
			Time.parse("00:00", Time.now).to_i,		# Serial Number
			86400,						# Refresh Time
			7200,						# Retry Time
			3_600_000,					# Maximum TTL / Expiry Time
			172_800,					# Minimum TTL
			#ttl: 4711					# TTL for SOA Record
		)
	end

	match('04.dns-test.timwattenberg.de', IN::SOA) do |transaction|
		transaction.respond!(
			Name.create('ns.dns-test.timwattenberg.de.'),	# Master Name
			Name.create('mail.timwattenberg.de.'),		# Responsible Name
			rand(0..1),					# Serial Number
			86400,						# Refresh Time
			7200,						# Retry Time
			3_600_000,					# Maximum TTL / Expiry Time
			172_800,					# Minimum TTL
			#ttl: 4711					# TTL for SOA Record
		)
	end

	match('dns-test.timwattenberg.de', IN::NS) do |t|
		t.respond!(Name.create('ns.dns-test.timwattenberg.de'))
	end

	match('ns.dns-test.timwattenberg.de', IN::A) do |t|
		t.respond!('188.166.166.75')
	end

	# Default DNS handler
	otherwise do |transaction|
		transaction.fail!(:NXDomain)
	end
end
