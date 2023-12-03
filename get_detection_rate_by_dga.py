import polars as pl
from sklearn.metrics import confusion_matrix

import constants
import dga_helper


# ======================== DEFINE SOME HELPER FUNCTIONS ============================


def find_dga_name_from_file_path(file_path: str, dga_list: list) -> str | None:
    for dga_name in dga_list:
        if dga_name in file_path.lower():
            return dga_name
    return None


# ======================== START PROCESSING =========================================


def processing(data_file_path, result_by_dga_threshold, dga_list: list):
    df = pl.read_csv(data_file_path, columns=["file_path", "infected", "dga_domain", "time", "threshold"])

    # iterate through each row of dataframe
    for (filepath, infected, dga_domain, time_query, threshold) in df.rows(named=False):
        dga_name = find_dga_name_from_file_path(filepath, dga_list)
        if dga_name is None:
            continue

        if dga_name not in result_by_dga_threshold:
            result_by_dga_threshold[dga_name] = {
                constants.DGA: dga_name,
                constants.TOTAL: 0,
                constants.RESULT_BY_THRESHOLD: {}
            }

        detail_dga_name = dga_helper.get_dga_family(filepath, dga_helper.variant_dga_list)
        if detail_dga_name is None:
            continue

        result_by_dga_threshold[dga_name][constants.TOTAL] += 1
        result_by_threshold = result_by_dga_threshold[dga_name][constants.RESULT_BY_THRESHOLD]

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
                constants.TCD: -1,
                constants.TRUE_LABEL: [],
                constants.PREDICT_LABEL: []
            }

        result_by_threshold[threshold_str][constants.TOTAL] += 1
        result_by_threshold[threshold_str][constants.TRUE_LABEL].append(1)
        if infected:
            detection_time = time_query - dga_helper.dga_start_active_time[detail_dga_name]
            if detection_time < 0:
                result_by_threshold[threshold_str][constants.PREDICT_LABEL].append(0)
            else:
                result_by_threshold[threshold_str][constants.PREDICT_LABEL].append(1)
                if detection_time > result_by_threshold[threshold_str][constants.TCD]:
                    result_by_threshold[threshold_str][constants.TCD] = detection_time
        else:
            result_by_threshold[threshold_str][constants.PREDICT_LABEL].append(0)


def calculate(data_file_list, dga_list, best_threshold=None):
    result_by_dga_threshold = {}
    for data_file_path in data_file_list:
        processing(data_file_path, result_by_dga_threshold, dga_list)

    best_threshold_result = []
    # calculate true positive rate
    count = 0
    for dga in result_by_dga_threshold:
        count += result_by_dga_threshold[dga][constants.TOTAL]
        result_by_threshold = result_by_dga_threshold[dga][constants.RESULT_BY_THRESHOLD]

        for threshold in result_by_threshold:
            metrics = result_by_threshold[threshold]

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
            metrics[constants.TPR] = metrics[constants.TRUE_POSITIVE] / metrics[constants.TOTAL]

            if best_threshold is not None and abs(float(threshold) - best_threshold) < 0.001:
                best_threshold_result.append({
                    constants.DGA: dga,
                    constants.TRUE_POSITIVE: metrics[constants.TRUE_POSITIVE],
                    constants.TOTAL: metrics[constants.TOTAL],
                    constants.TCD: metrics[constants.TCD],
                    constants.TPR: metrics[constants.TPR]
                })

    print("Total DGA samples: ", count)

    if best_threshold is not None and best_threshold_result:
        best_threshold_df = pl.DataFrame(best_threshold_result)
        best_threshold_df = best_threshold_df.sort(by=constants.DGA)
        pl.Config.set_tbl_hide_column_data_types(True)
        pl.Config.set_tbl_cols(15)
        pl.Config.set_tbl_width_chars(200)

        print("Best threshold result:")
        print(best_threshold_df)

    export_result = []
    for dga in result_by_dga_threshold:
        new_obj = {
            constants.DGA: dga
        }
        result_by_threshold = result_by_dga_threshold[dga][constants.RESULT_BY_THRESHOLD]
        for threshold in result_by_threshold:
            new_obj[threshold] = result_by_threshold[threshold][constants.TPR]
        export_result.append(new_obj)

    export_result_df = pl.DataFrame(export_result)
    export_result_df.sort(by=constants.DGA)

    print("TPR for each DGA family and threshold:")
    print(export_result_df)


if __name__ == "__main__":
    result_file_list = [
        "naive_result_22_28_42_03_12_23/result_22_28_42_03_12_23.csv"
    ]

    calculate(result_file_list, dga_helper.dga_families, 0.43)
