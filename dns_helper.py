import dpkt.dns as dns_lib

# white list domain
wl_domain = \
    (
        'facebook.com',
        'msn.com',
        'gmail.com',
        'hust.edu.vn',
        'microsoft.com',
        'yahoo.com',
        'g.doubleclick.net',
        'static.ak.fbcdn.net',
        'ibm.com',
        'google.com.vn',
        'msftspeechmodelsprod.azureedge.net',
        'sharepoint.com'
        'trafficmanager.net',
        'cdnjquery.com',
        'dasvision.vn',
        'twitter.com',
        'sublimetext.com',
        'ubuntu.com',
        'docker.com',
        'nodesource.com',
        'launchpad.net',
        'teamviewer.com'
        'local.hola'
        'nvidia.com'
        'cloudfront.net'
        'ubuntu.com.localdomain',
        'packagecloud.io',
        'rhcloud.com',
        'alibaba.com',
        'tendawifi.com',
        'local',
        'ip6.arpa',
        'stun.voxox.com',
        'data.wa.perf.overture.com',
        'in-addr.arpa',
        'footprintdns.com',
        'apache.org',
        'akamai.edu.vn',
        'lecturetek.vn',
        'akamaihd.net',
        'akamaihd.net.edgesuite.net',
        'duckduckgo.com',
        'id.amgdgt.com',
        'cloudfront.net'
    )


def is_nx_domain(split_response: list[str]):
    return \
            split_response[4] == 'no' and \
            split_response[5] == 'such' and \
            split_response[6] == 'name'


def is_serv_fail(split_query: list[str]):
    return \
            split_query[4] == 'server' and \
            split_query[5] == 'failure'


def is_nx_domain_with_whitelist(split_query: list[str]):
    return \
            split_query[4] == 'no' and \
            split_query[5] == 'such' and \
            split_query[6] == 'name' and \
            not split_query[8].endswith(wl_domain)


def is_serv_fail_with_whitelist(split_query: list[str]):
    return \
            split_query[4] == 'server' and \
            split_query[5] == 'failure' and \
            not split_query[7].endswith(wl_domain)


def should_domain_be_ignored(domain: str, whitelist: tuple[str] = wl_domain):
    domain = domain.strip()
    if not domain or '.' not in domain or domain.endswith(whitelist):
        return True

    return False


def get_record_type_in_int(record_type: str):
    match record_type:
        case 'A':
            return dns_lib.DNS_A
        case 'AAAA':
            return dns_lib.DNS_AAAA
        case 'NS':
            return dns_lib.DNS_NS
        case 'CNAME':
            return dns_lib.DNS_CNAME
        case 'SOA':
            return dns_lib.DNS_SOA
        case 'NULL':
            return dns_lib.DNS_NULL
        case 'PTR':
            return dns_lib.DNS_PTR
        case 'HINFO':
            return dns_lib.DNS_HINFO
        case 'MX':
            return dns_lib.DNS_MX
        case 'TXT':
            return dns_lib.DNS_TXT
        case 'SRV':
            return dns_lib.DNS_SRV
        case 'OPT':
            return dns_lib.DNS_OPT
        case _:
            return None


class DNS:
    """
    Represents a DNS query
    """

    def __init__(
            self,
            dns_id: str,
            domain: str,
            query_type: int,
            record_type: int,
            response_code: int,
            source_ip: str = '0.0.0.0',
            destination_ip: str = '0.0.0.0',
            timestamp: float = 0
    ):
        self.id = dns_id
        self.domain = domain
        self.query_type = query_type
        self.record_type = record_type
        self.response_code = response_code
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.timestamp = timestamp
