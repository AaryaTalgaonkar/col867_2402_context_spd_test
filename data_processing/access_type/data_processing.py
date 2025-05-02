import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import StratifiedKFold

class Model:
    def __init__(self, model=None):
        self.model = model if model else RandomForestClassifier(n_estimators=100, max_depth=10, criterion='entropy', random_state=42)

    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)

    def predict(self, X):
        return self.model.predict(X)
    
    def save_confusion_matrix(self, y_pred, y_gold, file_name):
        cm = confusion_matrix(y_gold, y_pred)
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=np.unique(y_gold), yticklabels=np.unique(y_gold))
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.title('Confusion Matrix')
        plt.savefig(file_name)
        plt.close()


def load_data(csv_file):
    """Load CSV and extract features and labels."""
    df = pd.read_csv(csv_file)
    X = df.iloc[:, :-1].values  # All columns except last as features
    y = df.iloc[:, -1].values   # Last column as labels
    return X, y


def printValidationSummary(accuracy, f1_Score): 
    print("\n10 Cross-Validation Summary :")
    print(f"Mean Accuracy: {np.mean(accuracy):.4f}")
    print(f"Mean F1 Score: {np.mean(f1_Score):.4f}")

def extractFeatureImportance(importances, feature_names):

    if isinstance(feature_names, set):
        feature_names = list(feature_names)
    
    feature_importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    })
    feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False)
    print(feature_importance_df)

if __name__ == "__main__":
    CSV_FILE = "features02.csv"  # Change this to your actual file path
    x, y = load_data(CSV_FILE)
    skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=True)
    accuracy, prec, f1_Score, ypred_all, roc_auc, ytest_all, importances = [], [], [], [], [], [], []
    selected_columns = [0, 1, 2, 3, 8, 9, 10, 11, 12, 13]
    x_selected = x[:, selected_columns]

    for fold, (trainidx, testidx) in enumerate(skf.split(x,y), 1):
        xtrain, xtest = x_selected[trainidx], x_selected[testidx]
        ytrain, ytest = y[trainidx], y[testidx]
        model = Model()
        model.train(xtrain, ytrain)
        ypred = model.predict(xtest)
        acc = accuracy_score(ytest, ypred)
        f1 = f1_score(ytest, ypred, average='macro')
        pre = precision_score(ytest, ypred, average='macro')

        accuracy.append(acc)
        f1_Score.append(f1)
        ytest_all.extend(ytest)
        ypred_all.extend(ypred)
        importances.append(model.model.feature_importances_)

        # print("Training Accuracy", accuracy_score(ytrain, model.predict(xtrain)))
        print(f"Accuracy: {round(acc, 5)}, Precision: {round(pre, 5)}, f1-score: {round(f1, 5)}")

    for fold, imp in enumerate(importances, 1):
        print(f"Fold {fold} importances: {imp}")
    mean_importance = np.mean(importances, axis=0)
    printValidationSummary(accuracy, f1_Score)
    cm = confusion_matrix(ytest_all, ypred_all)
    print("Overall Confusion Matrix \n", cm)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=np.unique(ytest_all), yticklabels=np.unique(ytest_all))
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.title('Confusion Matrix')
    plt.savefig("cm.png")
    cr = classification_report(ytest_all, ypred_all)
    print("Overall Classification Report \n", cr)
    f_names = {"burst_ratio_to_443","burst_ratio_from_443","throughput_to_443","throughput_from_443","IAT_mean_to_443",
               "IAT_mean_from_443","IAT_variance_to_443","IAT_variance_from_443","packet_count_to_443","packet_count_from_443"}
    extractFeatureImportance(mean_importance, f_names)
