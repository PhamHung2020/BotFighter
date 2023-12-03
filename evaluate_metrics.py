import polars as pl
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, accuracy_score

import dga_helper
import constants


def process(source_path: str, result_by_threshold: dict, is_dga: bool):
    df = pl.read_csv(source_path, columns=["file_path", "infected", "dga_domain", "time", "threshold"])

    # iterate through each row of dataframe
    for (filepath, infected, dga_domain, time_query, threshold) in df.rows(named=False):
        if is_dga:
            detail_dga_name = dga_helper.get_dga_family(filepath, dga_helper.variant_dga_list)
        else:
            detail_dga_name = None

        threshold_str = str(threshold)

        if threshold_str not in result_by_threshold:
            result_by_threshold[threshold_str] = {
                constants.THRESHOLD: threshold,
                constants.TRUE_POSITIVE: 0,
                constants.TRUE_NEGATIVE: 0,
                constants.FALSE_POSITIVE: 0,
                constants.FALSE_NEGATIVE: 0,
                constants.ACCURACY: 0.0,
                constants.PRECISION: 0.0,
                constants.RECALL: 0.0,
                constants.F1_SCORE: 0.0,
                constants.TOTAL: 0,
                constants.TRUE_LABEL: [],
                constants.PREDICT_LABEL: []
            }

        result_by_threshold[threshold_str][constants.TOTAL] += 1
        result_by_threshold[threshold_str][constants.TRUE_LABEL].append(1 if is_dga else 0)

        if is_dga and infected and time_query < dga_helper.dga_start_active_time[detail_dga_name]:
            result_by_threshold[threshold_str][constants.PREDICT_LABEL].append(0)
        else:
            result_by_threshold[threshold_str][constants.PREDICT_LABEL].append(1 if infected else 0)


def calculate_result(data_path_list: dict):
    result_per_threshold = {}
    best_threshold = 0
    best_f1_score = 0
    best_recall = 0
    best_precision = 0
    best_accuracy = 0
    best_tp = 0
    best_fp = 0
    best_tn = 0
    best_fn = 0

    for data_path in data_path_list:
        process(data_path, result_per_threshold, data_path_list[data_path])

    # calculate accuracy, precision, recall, f1_score
    for threshold in result_per_threshold:

        metrics = result_per_threshold[threshold]
        confusion_matrix_by_threshold = confusion_matrix(
            metrics[constants.TRUE_LABEL],
            metrics[constants.PREDICT_LABEL],
            labels=[0, 1]
        )

        tn, fp, fn, tp = confusion_matrix_by_threshold.ravel()
        metrics[constants.TRUE_POSITIVE] = tp
        metrics[constants.TRUE_NEGATIVE] = tn
        metrics[constants.FALSE_POSITIVE] = fp
        metrics[constants.FALSE_NEGATIVE] = fn

        metrics[constants.ACCURACY] = accuracy_score(
            metrics[constants.TRUE_LABEL],
            metrics[constants.PREDICT_LABEL]
        )

        precision, recall, f1_score, _ = precision_recall_fscore_support(
            metrics[constants.TRUE_LABEL],
            metrics[constants.PREDICT_LABEL],
            pos_label=1
        )
        metrics[constants.PRECISION] = precision[1]
        metrics[constants.RECALL] = recall[1]
        metrics[constants.F1_SCORE] = f1_score[1]

        if metrics[constants.F1_SCORE] > best_f1_score:
            best_threshold = threshold
            best_f1_score = metrics[constants.F1_SCORE]
            best_recall = metrics[constants.RECALL]
            best_precision = metrics[constants.PRECISION]
            best_accuracy = metrics[constants.ACCURACY]
            best_tp = metrics[constants.TRUE_POSITIVE]
            best_fp = metrics[constants.FALSE_POSITIVE]
            best_tn = metrics[constants.TRUE_NEGATIVE]
            best_fn = metrics[constants.FALSE_NEGATIVE]

    print("Best result:")
    print("\t- Threshold: ", best_threshold)
    print("\t- F1 score: ", best_f1_score)
    print("\t- Recall: ", best_recall)
    print("\t- Precision: ", best_precision)
    print("\t- Accuracy: ", best_accuracy)
    print("\t- TP: ", best_tp)
    print("\t- FP: ", best_fp)
    print("\t- TN: ", best_tn)
    print("\t- FN: ", best_fn)

    return result_per_threshold


if __name__ == '__main__':
    result_file_list = {
        "./naive_result_22_28_42_03_12_23/result_22_28_42_03_12_23.csv": True,
        "./naive_result_22_50_28_03_12_23/result_22_50_28_03_12_23.csv": False,
    }

    metrics_result = calculate_result(result_file_list)

    metrics_val = [metrics_result[threshold] for threshold in metrics_result]

    result_df = pl.DataFrame(metrics_val)
    result_df = result_df.sort(by=constants.THRESHOLD)
    pl.Config.set_tbl_cols(15)
    pl.Config.set_tbl_hide_column_data_types(True)
    pl.Config.set_tbl_width_chars(200)

    print(result_df)
