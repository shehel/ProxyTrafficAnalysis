import requests
import time
import json
from difflib import SequenceMatcher

# OTX AlienVault API Key
API_KEY = "48542e042a3fe30cc2e7855f71279bf9d408454acefca1d536012b4f658fd927"
BASE_URL = "https://otx.alienvault.com/api/v1/indicators/"

# Headers for API requests
HEADERS = {
    "X-OTX-API-KEY": API_KEY
}

# Function to perform passive DNS lookup for a domain
def passive_dns_lookup(domain):
    url = f"{BASE_URL}domain/{domain}/passive_dns"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve passive DNS data for {domain}: {response.status_code}")
        return None

# Function to calculate similarity between two strings
def is_similar(domain1, domain2, threshold=0.5):
    print(domain1, domain2)
    similarity = SequenceMatcher(None, domain1, domain2).ratio()
    return similarity >= threshold

# Function to extract a limited number of related domains that are similar to the original domain
def extract_related_domains(domain_data, original_domain, limit=5):
    related_domains = set()
    if domain_data and "passive_dns" in domain_data:
        count = 0
        for entry in domain_data["passive_dns"]:
            hostname = entry.get("hostname")
            if hostname and is_similar(original_domain, hostname):
                related_domains.add(hostname)
                count += 1
                if count >= limit:
                    break
    return related_domains

# Function to perform reverse DNS lookup
def reverse_dns_lookup(ip):
    url = f"{BASE_URL}IPv4/{ip}/passive_dns"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve reverse DNS data for {ip}: {response.status_code}")
        return None

# Recursive discovery of related domains
def discover_related_domains(seed_domains, max_iterations=5, limit_per_domain=5):
    discovered_domains = set(seed_domains)
    new_domains = set(seed_domains)

    for _ in range(max_iterations):
        if not new_domains:
            break

        current_domains = new_domains.copy()
        new_domains.clear()

        for domain in current_domains:
            print(f"Processing domain: {domain}")

            # Step 1: Get passive DNS data for the domain
            domain_data = passive_dns_lookup(domain)
            ips = set()
            if domain_data and "passive_dns" in domain_data:
                for entry in domain_data["passive_dns"]:
                    ip = entry.get("address")
                    if ip:
                        ips.add(ip)

            # Step 2: Perform reverse DNS lookup for each IP
            for ip in ips:
                reverse_data = reverse_dns_lookup(ip)
                if reverse_data and "passive_dns" in reverse_data:
                    count = 0
                    for entry in reverse_data["passive_dns"]:
                        related_domain = entry.get("hostname")
                        if related_domain and related_domain not in discovered_domains and is_similar(domain, related_domain):
                            discovered_domains.add(related_domain)
                            new_domains.add(related_domain)
                            count += 1
                            if count >= limit_per_domain:
                                break

            # Pause to avoid API rate limits
            time.sleep(1)

    return discovered_domains

if __name__ == "__main__":
    # Seed domains to start with
    seed_domains = ["perr.l-err.biz", "perr.l-agent.me", "client.earnapp.com", "clientsdk.lum-sdk.io", 
                    "proxyjs.luminatinet.com", "earnapp.com", "lumtest.com", "perr.lum-sdk.io"]

    # Discover related domains
    related_domains = discover_related_domains(seed_domains, max_iterations=3, limit_per_domain=5)

    print("\nDiscovered Related Domains:")
    for domain in related_domains:
        print(domain)

    # Save discovered domains to a JSON file
    with open("discovered_domains.json", "w") as json_file:
        json.dump(list(related_domains), json_file, indent=4)

    print("\nDiscovered domains have been saved to 'discovered_domains.json'")
