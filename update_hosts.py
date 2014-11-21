#!/usr/bin/env python
import boto, os, re, sys, getopt
from collections import defaultdict

class HostsFile:
	def __init__(self, hosts_text):
		self.lines = []
		for row in hosts_text.strip("\n").split("\n"):
			row = row.strip("\n")
			if self.marker_comment_for(None) in row:
				match = re.search(r"(\S+)\s+([^#]+)[\s#]+(.+)", row)
				script_generated_entry = dict()
				script_generated_entry["ip_addr"] = match.group(1)
				script_generated_entry["host"] = match.group(2).strip()
				script_generated_entry["comment"] = match.group(3).strip()
				self.lines.append(script_generated_entry)
			else:
				self.lines.append(row)

	def marker_comment_for(self, zone_fqdn):
		if zone_fqdn != None:
			return "Updated by script for %s" % zone_fqdn
		else:
			return "Updated by script"

	def update_with_records(self, zone_fqdn, records):
		"""
		zone_fqdn: name of zone to manipulate
		records: a dictionary[string] -> list(string) from ip_addr to hostnames
		"""
		result = []
		for entry in self.lines:
			if type(entry) is str:
				result.append(entry)
			elif type(entry) is dict:
				mutated_entry = entry
				if (self.marker_comment_for(zone_fqdn)) in entry["comment"]:
					if mutated_entry["ip_addr"] in records:
						# Update existing records in place
						mutated_entry["host"] = " ".join(records[mutated_entry["ip_addr"]])
						del records[mutated_entry["ip_addr"]]
					else:
						# Ensure deleted records are deleted
						mutated_entry = None
				if mutated_entry != None:
					result.append(mutated_entry)
			else:
				raise Exception("unexpected type %s" % type(entry))
		# Append zone records that haven"t been updated
		for record in records:
			entry = {}
			entry["ip_addr"] = record
			entry["host"] = " ".join(records[record])
			entry["comment"] = self.marker_comment_for(zone_fqdn)
			result.append(entry)
		self.lines = result

	def to_str(self):
		result = []
		for entry in self.lines:
			if type(entry) is str:
				result.append(entry)
			elif type(entry) is dict:
				result.append("%s\t%s\t# %s" % (entry["ip_addr"], entry["host"], entry["comment"]))
			else:
				raise Exception("unexpected type %s" % type(entry))
		return "\n".join(result)


def get_records(zone_fqdn, entry_types=["A"]):
	route53 = boto.connect_route53()
	hosts_entries = defaultdict(list)
	warnings = []

	zone = route53.get_zone(zone_fqdn)
	records = zone.get_records()
	for record in records:
		if record.type in entry_types:
			if record.alias_dns_name:
				warnings.append("# WARN: Ignoring Route53 alias record %s." % record)
				continue
			else:
				for ip_addr in record.resource_records:
					hosts_entries[ip_addr].append(record.name)
	if warnings:
		print >> sys.stderr, "\nWARN: ".join(warnings) + "\n"
	return hosts_entries

def check_prereqs():
	env_req = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
	missing_env_req = filter(lambda x: os.getenv(x) == None, env_req)
	if len(missing_env_req) > 0:
		print "Missing environment variables: %s" % (", ".join(missing_env_req))
		sys.exit(1)

def main(argv):
	check_prereqs()
	domain_name = None
	hosts_in_file = "/etc/hosts"
	hosts_out_file = "-"
	USAGE_STRING = "%s -d <domain> -i <inputfile> [-o <outputfile>]" % argv[0]
	try:
		opts, args = getopt.getopt(argv[1:],"d:i:o:",["domain=", "in=","out="])
	except getopt.GetoptError:
		print USAGE_STRING
		sys.exit(1)
	for opt, arg in opts:
   		if opt in ("-d", "--domain"):
			domain_name = arg
		elif opt in ("-i", "--ifile"):
			hosts_in_file = arg
		elif opt in ("-o", "--ofile"):
			hosts_out_file = arg
	if domain_name == None:
		print USAGE_STRING
		sys.exit(1)
	new_hosts_content = None
	with open(hosts_in_file, "r") as in_file:
		hosts_text = in_file.read()
		hosts = HostsFile(hosts_text)
		hosts.update_with_records(domain_name, get_records(domain_name))
		new_hosts_content = hosts.to_str()
	if hosts_out_file != "-":
		with open(hosts_out_file, "w") as out_file:
			out_file.write(new_hosts_content + "\n")
	else:
		print new_hosts_content

if __name__ == "__main__":
   main(sys.argv)
