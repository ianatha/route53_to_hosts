#!/usr/bin/env py.test
import update_hosts

hosts_fixture_basis = ("##\n"
			"# Host Database\n"
			"#\n"
			"# localhost is used to configure the loopback interface\n"
			"# when the system is booting.  Do not change this entry.\n"
			"##\n"
			"127.0.0.1   localhost\n"
			"255.255.255.255 broadcasthost\n"
			"::1             localhost\n")

hosts_fixture = hosts_fixture_basis + (
			"\n"
			"1.2.3.4\tatha.io.\t# Updated by script for atha.io.\n"
			"1.1.1.1\ttest.atha.io.\t# Updated by script for atha.io")

def test_parse_and_out():
	hosts_file = update_hosts.HostsFile(hosts_fixture)
	assert hosts_fixture == hosts_file.to_str()

def test_add_record():
	hosts_file = update_hosts.HostsFile(hosts_fixture)
	hosts_file.update_with_records("test.com", { "2.2.2.2": ["example.test.com."] })
	assert (hosts_fixture + "\n2.2.2.2\texample.test.com.\t# Updated by script for test.com") == hosts_file.to_str()

def test_add_record_with_multi_hosts():
	hosts_file = update_hosts.HostsFile(hosts_fixture)
	hosts_file.update_with_records("test.com", { "2.2.2.2": ["example.test.com.", "example2.test.com."] })
	correct_output = hosts_fixture + "\n2.2.2.2\texample.test.com. example2.test.com.\t# Updated by script for test.com"
	assert correct_output == hosts_file.to_str()

def test_add_record_with_multi_hosts_with_existing_multi_host():
	hosts_file = update_hosts.HostsFile(hosts_fixture)
	hosts_file.update_with_records("test.com", { "2.2.2.2": ["example.test.com.", "example2.test.com."] })
	correct_output = hosts_fixture + "\n2.2.2.2\texample.test.com. example2.test.com.\t# Updated by script for test.com"
	assert correct_output == hosts_file.to_str()
	hosts2_file = update_hosts.HostsFile(correct_output)
	assert correct_output == hosts2_file.to_str()

def test_delete_records():
	hosts_file = update_hosts.HostsFile(hosts_fixture)
	hosts_file.update_with_records("atha.io", { })
	assert hosts_fixture_basis == hosts_file.to_str()

def test_mutate_records():
	hosts_file = update_hosts.HostsFile(hosts_fixture)
	hosts_file.update_with_records("atha.io", { "1.2.3.4": ["atha.io."], "2.2.2.2": ["test.atha.io."] })
	assert hosts_fixture.replace("1.1.1.1", "2.2.2.2") == hosts_file.to_str()

if __name__ == '__main__':
	unittest.main()
