import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def plot_simplified_confusion_matrix(tp, fp, fn, tn=0):
    """
    Plot a simplified confusion matrix as an image.

    Parameters:
    tp (int): True Positives.
    fp (int): False Positives.
    fn (int): False Negatives.
    tn (int): True Negatives (default=0).
    """
    cm = np.array([[tp, fn], [fp, tn]])
    labels = ['Positive', 'Negative']
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.xlabel('Predicted Labels')
    plt.ylabel('True Labels')
    plt.title('Confusion Matrix')
    plt.show()

# Example usage
tp = 40886
fp = 2865
fn = 12622

plot_simplified_confusion_matrix(tp, fp, fn)

