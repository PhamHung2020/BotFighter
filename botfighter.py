import dns_helper
from lstm_model import LSTMModel
from scipy.stats import poisson

DNS_REQUEST = 0
DNS_RESPONSE = 1


class BotFighter:

    def __init__(self, model: LSTMModel, lambda_value: int = 5, threshold: float = 0.001,
                 threshold_for_failed_response: float = 0.7, ip: str = '0.0.0.0'):
        self.model = model
        self.lambda_value = lambda_value
        self.threshold = threshold
        self.threshold_for_failed_response = threshold_for_failed_response
        self.ip = ip

        self.infected = False
        self.p_normal_machine = 1
        self.p_infected_machine = 0
        self.infected_time = None
        self.dga_domain = None
        self.list_nxdomain = {}
        self.predicted_domain = {}

    def predict(self, timestamp: float, domain: str, dns_type: int, is_failed_response: bool):
        if dns_type == DNS_REQUEST:
            self.handle_request(timestamp)
        elif dns_type == DNS_RESPONSE:
            self.handle_response(timestamp, domain, is_failed_response)
        else:
            pass

    def handle_request(self, timestamp: float):
        one_hour_before = timestamp - 3600
        del_list = []
        for d, t in self.list_nxdomain.items():
            if t < one_hour_before:
                del_list.append(d)
        for d in del_list:
            del self.list_nxdomain[d]

    def handle_response(self, timestamp: float, domain: str, is_failed_response: bool):
        domain = domain.strip()
        if not domain:
            return

        if "[malformed" in domain:
            domain = domain[:domain.rindex("[malformed")]

        if '.' not in domain:
            return

        if is_failed_response and not domain.endswith(dns_helper.wl_domain):
            self.list_nxdomain[f"{domain}_{timestamp}"] = timestamp
        else:
            is_failed_response = False

        if domain in self.predicted_domain:
            infected_probability = self.predicted_domain[domain]
            # safe_probability = 1 - infected_probability
        else:
            safe_probability, infected_probability = self.model.get_prediction_result(domain)
            self.predicted_domain[domain] = infected_probability

        # infected_probability = 1 - safe_probability
        if is_failed_response:
            p_dian = \
                infected_probability if infected_probability > self.threshold_for_failed_response \
                else self.threshold_for_failed_response
        else:
            p_dian = infected_probability

        p_din = 1 - p_dian
        p_state_changing = 1 - poisson.cdf(len(self.list_nxdomain), self.lambda_value)

        p_safe_t = p_din * p_state_changing * self.p_normal_machine
        p_infected_t = p_dian * ((1 - p_state_changing) * self.p_normal_machine + self.p_infected_machine)
        self.p_normal_machine = p_safe_t / (p_safe_t + p_infected_t)
        self.p_infected_machine = 1 - self.p_normal_machine

        if self.p_normal_machine < self.threshold:
            self.infected = True
            self.dga_domain = domain
            self.infected_time = timestamp
