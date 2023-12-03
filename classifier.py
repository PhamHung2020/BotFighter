import dpkt.dns as dns_lib
import tqdm

from lstm_model import LSTMModel
from botfighter import BotFighter
import dns_helper


def classify_by_plain_lstm(dns_list: list[dns_helper.DNS], lstm_model: LSTMModel, threshold: float = None):
    infected = False
    dga_domain = None
    infected_time = None

    total_dns = len(dns_list)
    with tqdm.tqdm(total=total_dns, ncols=100) as p_bar:
        for dns_info in dns_list:
            p_bar.update(1)
            if dns_info.query_type != dns_lib.DNS_Q:
                continue
            if dns_info.domain.endswith(dns_helper.wl_domain):
                continue

            safe_probability, infected_probability = lstm_model.get_prediction_result(dns_info.domain)
            if threshold is not None and safe_probability < threshold:
                infected = True
                dga_domain = dns_info.domain
                infected_time = dns_info.timestamp

                break

        p_bar.update(total_dns - p_bar.n)

    return infected, dga_domain, infected_time


def classify_by_average_lstm(
        dns_list: list[dns_helper.DNS],
        lstm_model: LSTMModel,
        threshold: float = None,
        window_time_in_second: float = 600
):
    safe_probability_list = []
    time_list = []
    sum_probability = 0
    n_concern_domain = 0

    infected = False
    dga_domain = None
    infected_time = None

    total_dns = len(dns_list)
    with tqdm.tqdm(total=total_dns, ncols=100) as p_bar:
        for dns_info in dns_list:
            p_bar.update(1)

            if dns_info.query_type != dns_lib.DNS_Q:
                continue

            if dns_info.domain.endswith(dns_helper.wl_domain):
                continue

            safe_probability, infected_probability = lstm_model.get_prediction_result(dns_info.domain)
            n_concern_domain += 1
            time_list.append(dns_info.timestamp)
            safe_probability_list.append(safe_probability)
            sum_probability += safe_probability

            last_time = dns_info.timestamp - window_time_in_second
            idx = 0
            while time_list[idx] < last_time:
                sum_probability -= safe_probability_list[idx]
                n_concern_domain -= 1
                idx += 1

            time_list = time_list[idx:]
            safe_probability_list = safe_probability_list[idx:]

            average_probability = sum_probability / n_concern_domain
            if threshold is not None and average_probability < threshold:
                infected = True
                dga_domain = dns_info.domain
                infected_time = dns_info.timestamp
                break

        p_bar.update(total_dns - p_bar.n)

    return infected, dga_domain, infected_time


def classify_by_botfighter(dns_list: list[dns_helper.DNS], classifier: BotFighter, stop_if_infected: bool = True):
    total_dns = len(dns_list)
    with tqdm.tqdm(total=total_dns, ncols=100) as p_bar:
        for dns_info in dns_list:
            p_bar.update(1)

            if dns_info.query_type == dns_lib.DNS_Q:
                classifier.handle_request(dns_info.timestamp)
                continue

            is_failed_query = \
                dns_info.response_code == dns_lib.DNS_RCODE_NXDOMAIN or \
                dns_info.response_code == dns_lib.DNS_RCODE_SERVFAIL
            classifier.handle_response(dns_info.timestamp, dns_info.domain, is_failed_query)

            if classifier.infected and stop_if_infected:
                break

        p_bar.update(total_dns - p_bar.n)

    return classifier.infected, classifier.dga_domain, classifier.infected_time


def classify_by_counting_nxdomain(dns_list: list[dns_helper.DNS], threshold: int):
    nx_domain_time_list_in_one_hour = []
    is_infected = False
    detected_time = 0
    detected_domain = None

    total_dns = len(dns_list)
    with tqdm.tqdm(total=total_dns, ncols=100) as p_bar:
        for dns_info in dns_list:
            p_bar.update(1)

            if dns_info.query_type != dns_lib.DNS_R:
                continue
            if dns_info.response_code != dns_lib.DNS_RCODE_NXDOMAIN and \
                    dns_info.response_code != dns_lib.DNS_RCODE_SERVFAIL:
                continue
            if dns_info.domain.endswith(dns_helper.wl_domain):
                continue

            one_hour_before = dns_info.timestamp - 3600
            t_index = None
            for idx, t in enumerate(nx_domain_time_list_in_one_hour):
                if t >= one_hour_before:
                    t_index = idx
                    break

            if t_index is not None:
                nx_domain_time_list_in_one_hour = nx_domain_time_list_in_one_hour[t_index:]
            else:
                nx_domain_time_list_in_one_hour = []

            nx_domain_time_list_in_one_hour.append(dns_info.timestamp)

            if len(nx_domain_time_list_in_one_hour) >= threshold:
                is_infected = True
                detected_time = dns_info.timestamp
                detected_domain = dns_info.domain
                break

        p_bar.update(total_dns - p_bar.n)

    return is_infected, detected_domain, detected_time
