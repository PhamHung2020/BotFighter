import argparse
import glob
import os.path
import sys
from pathlib import Path
import datetime
import numpy as np

# sys.path.append(os.path.dirname(os.getcwd()))
from lstm_model import LSTMModel
from botfighter import BotFighter
from data_csv_parser import DataCSVParser
import constants
import classifier


def add_argument(argument_parser: argparse.ArgumentParser):
    argument_parser.add_argument(
        "-dfp",
        "--data-folder-path",
        action="store",
        type=str,
        required=True,
        help="Path to folder containing data (csv) files"
    )

    argument_parser.add_argument(
        "-m", "--method",
        action="store",
        choices=[
            constants.NAIVE_INTEGRATION_METHOD,
            constants.TEMPORAL_INTEGRATION_METHOD,
            constants.BOTFIGHTER_METHOD,
            constants.NXDOMAIN_COUNT_INTEGRATION_METHOD],
        default=constants.BOTFIGHTER_METHOD,
        type=str,
        help="Specify method to use to detect DGA (default: %(default)s)",
    )

    argument_parser.add_argument(
        "-fp",
        "--file-pattern",
        action="store",
        default="**.csv",
        type=str,
        help="File's pattern used to filter files to classify (default: %(default)s)"
    )

    argument_parser.add_argument(
        "-ofp",
        "--out-folder-path",
        action="store",
        type=str,
        help="Path to folder saving classification result, (default: {method}_result_{current_date_time})"
    )

    argument_parser.add_argument(
        "-o",
        "--out",
        action="store",
        type=str,
        help="Name of result file (without .csv extension) (default: result_{current_date_time}"
    )

    threshold_group_options = argument_parser.add_mutually_exclusive_group(required=True)

    threshold_group_options.add_argument(
        "-t",
        "--threshold",
        type=float,
        help="Threshold value"
    )

    threshold_group_options.add_argument(
        "-tl",
        "--threshold-list",
        nargs=3,
        type=float,
        metavar=("START", "STOP", "STEP"),
        help="Threshold list specified by start, stop and step. start value is inclusive and stop value is exclusive"
    )

    threshold_group_options.add_argument(
        "-tv",
        "--threshold-values",
        nargs='+',
        type=float,
        metavar=("VALUE_1", "VALUE_2", "VALUE_3", "..."),
        help="Threshold values"
    )

    botfighter_options = argument_parser.add_argument_group("For botfighter method only")
    botfighter_options.add_argument(
        "-l",
        "--lambda-value",
        default=5,
        type=int,
        help="Lambda value required by botfighter method (default: %(default)s)"
    )

    botfighter_options.add_argument(
        "--threshold-for-failed-response",
        default=0.7,
        type=float,
        help="Threshold for failed response, required by botfighter method (default: %(default)s)"
    )

    average_lstm_options = argument_parser.add_argument_group("For average_lstm only")
    average_lstm_options.add_argument(
        "--window-time",
        default=600,
        type=float,
        help="Window time, required by average_lstm method (default: %(default)s)"
    )


def validate_argument(argument_parser: argparse.ArgumentParser):
    current_time = datetime.datetime.now().strftime('%H_%M_%S_%d_%m_%y')

    args = argument_parser.parse_args()
    data_folder_path = Path(args.data_folder_path)
    if not data_folder_path.exists():
        argument_parser.exit(1, message="The data folder path doesn't exist")

    if args.out_folder_path is not None:
        out_folder_path = Path(args.out_folder_path)
        if not out_folder_path.exists():
            argument_parser.exit(1, message="The out folder path doesn't exist")
    else:
        args.out_folder_path = os.path.join('.', f"{args.method}_result_{current_time}")

    if args.out is None:
        args.out = f"result_{current_time}.csv"
    else:
        args.out = f"{args.out}.csv"

    if args.threshold_list is not None:
        start = args.threshold_list[0]
        stop = args.threshold_list[1]
        step = args.threshold_list[2]
        args.threshold_list = list(np.arange(start, stop, step))
    elif args.threshold is not None:
        args.threshold_list = [args.threshold]
    elif args.threshold_values is not None:
        args.threshold_list = args.threshold_values

    return args


def get_classifier_by_method(arguments: argparse.Namespace):
    dns_list = arguments.dns_list
    model = arguments.model
    method_value = arguments.method
    window_time_value = arguments.window_time
    lambda_value = arguments.lambda_value
    threshold_for_failed_response_value = arguments.threshold_for_failed_response

    match method_value:
        case constants.NAIVE_INTEGRATION_METHOD:
            return \
                lambda threshold: classifier.classify_by_plain_lstm(
                    dns_list,
                    model,
                    threshold
                )

        case constants.TEMPORAL_INTEGRATION_METHOD:
            return \
                lambda threshold: classifier.classify_by_average_lstm(
                    dns_list,
                    model,
                    threshold,
                    window_time_value
                )

        case constants.BOTFIGHTER_METHOD:
            return \
                lambda threshold: classifier.classify_by_botfighter(
                    dns_list,
                    BotFighter(model, lambda_value, threshold, threshold_for_failed_response_value)
                )

        case constants.NXDOMAIN_COUNT_INTEGRATION_METHOD:
            return \
                lambda threshold: classifier.classify_by_counting_nxdomain(
                    dns_list,
                    threshold
                )


def main(arguments: argparse.Namespace):
    data_folder_path_value = arguments.data_folder_path
    out_folder_path_value = arguments.out_folder_path
    out_file_name_value = arguments.out
    file_pattern_value = arguments.file_pattern
    threshold_list_value = arguments.threshold_list

    out_folder_path = Path(out_folder_path_value)
    if not out_folder_path.exists():
        out_folder_path.mkdir(exist_ok=True)

    file_list = glob.glob(file_pattern_value, root_dir=data_folder_path_value)
    if file_list is None or not file_list:
        return

    model = LSTMModel("./model_binary.h5")
    arguments.model = model

    out_file_path = Path(os.path.join(out_folder_path_value, out_file_name_value))
    if out_file_path.exists():
        out_file = open(os.path.join(out_folder_path_value, out_file_name_value), "a")
    else:
        out_file = open(os.path.join(out_folder_path_value, out_file_name_value), "w")
        out_file.write("file_path,infected,dga_domain,time,threshold\n")

    for file_name in file_list:
        print("Processing " + file_name)
        file_path = os.path.join(data_folder_path_value, file_name)
        data_parser = DataCSVParser()
        data_parser.parse(file_path)
        arguments.dns_list = data_parser.dns_list

        classify_function = get_classifier_by_method(arguments)
        for threshold in threshold_list_value:
            print("\t- Threshold: ", threshold)
            infected, dga_domain, detected_time = classify_function(threshold)

            out_file.write(
                f"{file_path},"
                f"{infected},"
                f"{dga_domain if dga_domain is not None else ''},"
                f"{detected_time if detected_time is not None else -1},"
                f"{threshold}\n"
            )

    out_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DGA Detection using LSTM model",
        allow_abbrev=False
    )

    add_argument(parser)
    validated_arguments = validate_argument(parser)
    main(validated_arguments)
