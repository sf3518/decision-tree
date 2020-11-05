import random
import sys

import numpy as np
# used for formatting the output, not in evaluation implementation.
from texttable import Texttable

import dt

FOLD_NUM = 10
CLASS_NUM = 4


def evaluate(test_db, trained_tree):
    """
    :param test_db: The test dataset
    :param trained_tree: The decision tree to evaluate
    :return: the accuracy of the confusion matrix generated by the decision tree
    """
    confusion_matrix = get_confusion_matrix(test_db, trained_tree)
    total_diagonal = 0
    for i in range(CLASS_NUM):
        total_diagonal += confusion_matrix[i][i]
    try:
        return total_diagonal / len(test_db)
    except ZeroDivisionError:
        print('the sum of values in the confusion matrix is 0, please check.')


def cross_validation(all_db_list):
    header_list = ["index", "accuracy", "precision", "recall", "f1",
                   "maximal depth"]  # set up heading for evaluation result table
    class_list = ["room1", "room2", "room3", "room4"]  # set up heading for the confusion matrix
    macro_table = Texttable()
    macro_table.header(header_list)

    for roomi in range(CLASS_NUM):  # validate for each class (room)
        # total accuracy, precision, recall, f1 scores and confusion matrix for all 10 folds of validation
        total_accuracy = 0
        total_precision = 0
        total_recall = 0
        total_f1 = 0
        total_matrix = np.zeros((CLASS_NUM, CLASS_NUM))
        # maximum depth of all decision trees generated
        max_depth = 0
        # calculate step size
        db_size = len(all_db_list)
        step = db_size // FOLD_NUM
        # initialise list for result output
        output = [header_list]

        for start in range(0, db_size, step):  # permute training data set and test data set
            # separate data into training data and test data
            end = start + step
            test_db, training_db = separate_data(all_db_list, start, end, db_size)
            d_tree, depth = dt.decision_tree_learning(training_db, 0)

            # update maximum depth
            if depth > max_depth:
                max_depth = depth

            # calculate metrics
            confusion_matrix = get_confusion_matrix(test_db, d_tree)
            precision = get_precision(roomi, confusion_matrix)
            recall = get_recall(roomi, confusion_matrix)
            f1 = get_f1(roomi, confusion_matrix)
            accuracy = get_accuracy(roomi, confusion_matrix)
            total_precision += precision
            total_recall += recall
            total_f1 += f1
            total_accuracy += accuracy

            total_matrix = np.array(confusion_matrix) + np.array(total_matrix)
            col = [str(start // step + 1), str(accuracy), str(precision), str(recall), str(f1), str(depth)]
            output.append(col)
        t = Texttable()
        t.add_rows(output)
        print('Evaluation result for room' + str(roomi + 1) + ' is: ')
        average_result = ["average of room " + str(roomi + 1), str(total_accuracy / FOLD_NUM),
                          str(total_precision / FOLD_NUM),
                          str(total_recall / FOLD_NUM), str(total_f1 / FOLD_NUM),
                          str(max_depth) + ' (Note: this is max depth rather than avg depth)']
        macro_table.add_row(average_result)
        t.add_row(average_result)
        print(t.draw())  # print "index", "accuracy", "precision", "recall", "f1" of each fold
        average_matrix = np.array(total_matrix) / FOLD_NUM
        m = Texttable()
        m.header(class_list)
        for i in range(CLASS_NUM):
            m.add_row(average_matrix[i])
        print('average confusion matrix for room ' + str(roomi + 1) + ' is: ')
        print(m.draw())  # print average confusion matrix
    print(macro_table.draw())


def separate_data(all_db_list, start, end, size):
    """
    Separates the data into (training + validation) set and test set / training set and test set
    :param all_db_list: all the data
    :param start: start index of test/validation set
    :param end: end index of test/validation set
    :param size: size of all data
    :return: a pair (test_set, training_set) or (test_set, training_validation_set)
    """
    test_set = all_db_list[start:end]  # test or validation set
    # training set or (training + validation) set
    if start == 0:
        training_set = all_db_list[end:]
    elif end == size:
        training_set = all_db_list[:start]
    else:
        training_set = np.concatenate((all_db_list[:start], all_db_list[end:]))
    return test_set, training_set


def predict(test_data_row, d_tree):
    """
    :param: test_data: one-dimensional, a row of test data
    :param: d_tree: trained tree
    :return: classified label (room)
    """
    # leaf (base case)
    if d_tree['leaf']:
        return d_tree['value']

    # node (recursion case)
    attr_number = int(d_tree['attribute'].split('_')[1])  # attribute (can be 1-7) at this node
    split_value = d_tree['value']  # split value at this node
    if test_data_row[attr_number - 1] > split_value:
        return predict(test_data_row, d_tree['left'])
    else:
        return predict(test_data_row, d_tree['right'])


def get_confusion_matrix(test_db, trained_tree):
    """
    :param: test_db: two-dimensional, all test data
    :param: trained_tree: a python dictionary {'attribute', 'value', 'left', 'right', 'leaf'}
    :return: confusion matrix generated by the decision tree and the test dataset
    """

    confusion_matrix = [[0] * CLASS_NUM for _ in range(CLASS_NUM)]  # 4*4 confusion matrix

    for rowi in test_db:
        actual_room = int(rowi[-1])  # class (room) value from test data
        predicted_room = int(predict(rowi, trained_tree))
        confusion_matrix[actual_room - 1][predicted_room - 1] += 1
    return confusion_matrix


def get_recall(class_num, confusion_matrix):
    attributes = get_tp_fp_tn_fn(class_num, confusion_matrix)
    tp = attributes[0]
    fn = attributes[3]
    try:
        return tp / (tp + fn)
    except ZeroDivisionError:
        print("tp + fn result in a sum of 0, please check the classifier:")


def get_precision(class_num, confusion_matrix):
    attributes = get_tp_fp_tn_fn(class_num, confusion_matrix)
    tp = attributes[0]
    fp = attributes[1]
    try:
        return tp / (tp + fp)
    except ZeroDivisionError:
        print("tp + fp result in a sum of 0, please check the classifier:")


def get_f1(class_num, confusion_matrix):
    precision = get_precision(class_num, confusion_matrix)
    recall = get_recall(class_num, confusion_matrix)
    try:
        return 2 * precision * recall / (precision + recall)
    except ZeroDivisionError:
        print("precision and recall are both 0, please check the classifier:")


def get_accuracy(class_num, confusion_matrix):
    metrics = get_tp_fp_tn_fn(class_num, confusion_matrix)
    tp = metrics[0]
    tn = metrics[2]
    try:
        return (tp + tn) / sum(metrics)
    except ZeroDivisionError:
        print("tp + tn + fp + fn result in a sum of 0, please check the classifier:")


def get_tp_fp_tn_fn(class_num, confusion_matrix):
    tp = confusion_matrix[class_num][class_num]
    fp = sum(confusion_matrix[i][class_num] for i in range(CLASS_NUM) if i != class_num)
    fn = sum(confusion_matrix[class_num][i] for i in range(CLASS_NUM) if i != class_num)
    tn = sum(confusion_matrix[i][i] for i in range(CLASS_NUM) if i != class_num)
    return [tp, fp, tn, fn]


if __name__ == '__main__':
    inputfile = sys.argv[1]
    all_db = np.loadtxt(inputfile)
    all_db_list = []
    for row in all_db:
        all_db_list.append(row)
    random.shuffle(all_db_list)
    cross_validation(all_db_list)