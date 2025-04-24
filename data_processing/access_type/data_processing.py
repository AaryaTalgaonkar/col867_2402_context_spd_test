import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import StratifiedKFold

class Model:
    def __init__(self, model=None):
        self.model = model if model else RandomForestClassifier(n_estimators=100, random_state=42)

    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)

    def predict(self, X):
        return self.model.predict(X)

    def evaluate(self, y_pred, y_gold):
        metrics = {
            "accuracy": accuracy_score(y_gold, y_pred),
            "precision_macro": precision_score(y_gold, y_pred, average="macro"),
            "f1_score_macro": f1_score(y_gold, y_pred, average="macro"),
        }
        return metrics
    
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


# def split_data(X, y):
#     """Perform an 80-20 train-validation split maintaining label distribution."""
#     return train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)


if __name__ == "__main__":
    CSV_FILE = "features.csv"  # Change this to your actual file path
    x, y = load_data(CSV_FILE)
    skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=True)
    for fold, (trainidx, testidx) in enumerate(skf.split(x,y), 1):
        xtrain, xtest = x[trainidx], x[testidx]
        ytrain, ytest = y[trainidx], y[testidx]
        model = Model()
        model.train(xtrain, ytrain)
        ypred = model.predict(xtest)
        metrics = model.evaluate(ypred, ytest)
        print("Evaluation Metrics:")
        for key, value in metrics.items():
            print(f"{key}: {value}")
        print(classification_report(ytest, ypred))   
        model.save_confusion_matrix(ypred, ytest, "confusion_matrix.png")
