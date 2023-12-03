# BotFighter

Continuous DGA-based bots detection tool using DNS traffic and LSTM network.

---
## Installation

1. Install Python 3.10
2. Install packages:

```commandline
pip install -r requirements
```

___
## Dataset

BotFighter's dataset can be downloaded from: [BotFighter's dataset](https://drive.google.com/file/d/1qh9jw3gSDeHNPDqkCxxFEqIHqMzEDXHu/view?usp=sharing)

The dataset has 3 folders:
- dga: DNS traffic of 20 DGA families
- normal: DNS traffic of benign hosts
- adversarial: DNS traffic of adversarial DGAs

DNS traffic is saved in CSV format. Each CSV file contains DNS traffic of a host in (average) 2 hours.


---
## Usage

---
### Classification

Run file *classify.py* with following options:
- *-dfp* or *--data-folder-path*: Path to folder containing data (csv) files need to be classified
- *-m* or *--method* (optional): Method to use to detect DGA (default: 'naive'). Supported methods are: *naive*, *temporal*, *botfighter* and *nxdomain_count*
- *-fp* or *--file-pattern* (optional): File's pattern used to filter files to classify (default: '**.csv')
- *-ofp* or *--out-folder-path* (optional): Path to folder saving classification result, (default: {method}_result_{current_date_time})
- *-o* or *--out* (optional): Name of result file (without .csv extension) (default: result_{current_date_time})

Following options are exclusive mutually:
- *-t* or *--threshold*: Threshold value
- *-tl* or *--threshold-list*:
  - Syntax: -tl/--threshold-list start stop step
  - Threshold list specified by start, stop and step. start value is inclusive and stop value is exclusive
- *-tv* or *--threshold-values*:
  - Syntax: -tv/--threshold-values VALUE_1 VALUE_2 ...
  - List of threshold values

Following options are for botfighter method only:
- *-l* or *--lambda-value* (optional): Lambda value required by botfighter method (default: 5)
- *--threshold-for-failed-response* (optional): Threshold for failed response, required by botfighter method (default: 0.7)

Following options are for temporal method only:
- *--window-time* (optional): Window time, required by temporal method (default: 600)

---
### Metrics calculation

For confusion matrix, precision, recall and F1-score, in file *evaluate_metrics.py* :
- Specify list of classification result files in *result_file_list* variable with following format:

```text
result_file_list = {
    '<file_name>': <is_dga_or_not> (True for DGA, False for normal)
}
```

- Run that file

For detection rate by DGA family, in file *get_detection_rate_by_dga* :
- Specify list of classification result files in *result_files* variable
- (optional) Specify threshold when calling *calculate* method (in the last line)
- Run that file