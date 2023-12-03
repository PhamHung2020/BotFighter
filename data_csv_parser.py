import dpkt.dns as dns_lib
import polars as pl

import dns_helper


class DataCSVParser:
    def __init__(self):
        self.dns_list: list[dns_helper.DNS] = []

    def parse(self, file_path: str):
        df = pl.read_csv(
            file_path,
            columns=['No.', 'Time', 'Source', 'Destination', 'Info'],
            dtypes={'No.': pl.Int32, 'Time': pl.Float64}
        )

        for row in df.rows(named=True):
            time_query = row['Time']
            info = row['Info']

            split_query = info.lower().split(' ')
            if len(split_query) < 5 or (split_query[0] != 'standard' and split_query[1] != 'query'):
                continue
            elif split_query[2].startswith('0x'):
                self.handle_request(time_query, split_query)
            elif split_query[2] == 'response' and split_query[3].startswith('0x'):
                self.handle_response(time_query, split_query)

    def handle_request(self, timestamp: float, split_query: list[str]):
        dns_id = split_query[2]
        record_type = split_query[3]
        domain = split_query[4]

        record_type_int = dns_helper.get_record_type_in_int(record_type.upper())
        if record_type_int is None:
            return

        if "[malformed" in domain:
            domain = domain[:domain.rindex("[malformed")]

        self.dns_list.append(
            dns_helper.DNS(
                dns_id=dns_id,
                domain=domain,
                query_type=dns_lib.DNS_Q,
                record_type=record_type_int,
                response_code=dns_lib.DNS_RCODE_NOERR,
                timestamp=timestamp
            )
        )

    def handle_response(self, timestamp: float, split_query: list[str]):
        split_query_length = len(split_query)
        if split_query_length < 6:
            return

        dns_id = split_query[3]

        if split_query_length >= 9 and split_query[4] == 'no' and split_query[5] == 'such' and split_query[6] == 'name':
            record_type = split_query[7]
            domain = split_query[8]
            response_code = dns_lib.DNS_RCODE_NXDOMAIN
        elif split_query_length >= 8 and split_query[4] == 'server' and split_query[5] == 'failure':
            record_type = split_query[6]
            domain = split_query[7]
            response_code = dns_lib.DNS_RCODE_SERVFAIL
        else:
            record_type = split_query[4]
            domain = split_query[5]
            response_code = dns_lib.DNS_RCODE_NOERR

        record_type_int = dns_helper.get_record_type_in_int(record_type.upper())
        if record_type_int is None:
            return

        if "[malformed" in domain:
            domain = domain[:domain.rindex("[malformed")]

        self.dns_list.append(
            dns_helper.DNS(
                dns_id=dns_id,
                domain=domain,
                query_type=dns_lib.DNS_R,
                record_type=record_type_int,
                response_code=response_code,
                timestamp=timestamp
            )
        )
