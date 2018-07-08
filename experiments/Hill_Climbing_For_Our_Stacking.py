import pandas as pd
import numpy as np
import os
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import minmax_scale


def init_hillclimb():
    best_ensemble = {}
    for label in LABELS:
        best_ensemble[label] = []
    best_score = {}
    for label in LABELS:
        best_score[label] = 0

    return best_ensemble, best_score

def score_ensemble(ensemble, label):
    blend_preds = np.zeros(len(train))

    for model in ensemble:
        blend_preds += minmax_scale(files[model][label])

    blend_preds = blend_preds / len(subnums)
    score = roc_auc_score(train[label], blend_preds)

    return score


def find_best_improvement(ensemble, label):
    best_score = 0
    best_ensemble = []

    for i in range(0, len(files)):
        ensemble = ensemble + [i]

        score = score_ensemble(ensemble, label)

        if score > best_score:
            best_score = score
            best_ensemble = ensemble

        ensemble = ensemble[:-1]

    return best_ensemble, best_score



def climb(best_ensemble, best_score):
    for label in LABELS:
        best_ensemble[label], best_score[label] = find_best_improvement(best_ensemble[label], label)

    return best_ensemble, best_score

def get_optimal_weights(best_ensemble):
    weights = {}
    for label in LABELS:
        weights[label] = {}
        for num in set(best_ensemble[label]):
            weights[label][num] = best_ensemble[label].count(num) / len(best_ensemble[label])
    return weights

def get_optimal_blend(optimal_weights):
    sub = pd.read_csv(os.path.join(DATA_PATH, "sample_submission.csv"))
    blend = sub.copy()
    for label in LABELS:
        print(label)
        for key in optimal_weights[label]:
            blend[label] += optimal_weights[label][key] * minmax_scale(get_sub_file(key)[label])
            print(optimal_weights[label][key], filenames[key])
            blend[label] = minmax_scale(blend[label])

    return blend


def get_sub_file(num):
    filename = filenames[num]
    filename = filename.replace("oof", "sub")
    return pd.read_csv(os.path.join(SUB_PATH, filename))


if __name__ == "__main__":
    DATA_PATH = "/pan_data/"
    SUB_PATH = "/pan_outputs/"

    train = pd.read_csv(os.path.join(DATA_PATH, "train.csv")).fillna(' ')
    test = pd.read_csv(os.path.join(DATA_PATH, "test.csv")).fillna(' ')

    LABELS = train.columns[2:]

    # Get submissions and out-of-fold predictions
    subnums = [1,2,3,4,5,6,7,8,9,10] # for example :D
    filenames = ["oof" + str(num) + ".csv" for num in subnums]
    files = [pd.read_csv(os.path.join(SUB_PATH, filename)) for filename in filenames]

    best_ensemble, best_score = init_hillclimb()

    # Run hillclimb
    for i in range(250):
        print("-------------")
        print("Step", i)
        best_ensemble, best_score = climb(best_ensemble, best_score)
        print("Best ensemble:")
        print(best_ensemble)

    # Get optimal weights
    opt_w = get_optimal_weights(best_ensemble)
    print("Optimal weights:")
    print(opt_w)

    # Construct the blend
    blend = get_optimal_blend(opt_w)

    # Submit
    blend.to_csv("/output/hillclimb.csv", index=False)