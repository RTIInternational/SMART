README

SECTION 1: FILES

This readme contains information about how to use the files downloaded in this folder. The folder should contain:
*  This README
*  #.pkl file – this is the TFIDF (see section 2) matrix of the uploaded data.
*  project_#_training_#.pkl file – this is the model itself (see section 3), trained on the most recent labeled data
*  project_#_labels.xlsx – this file contains all labeled data, with the original text, unique ID, and assigned label. It also contains a second sheet with the mapping between label name and ID.
NOTE: All models and TFIDF files use Scikit-Learn version 0.19.0. If you are using a different version, be careful!

SECTION 2: TFIDF

A.  What is TFIDF?
Term Frequency Inverse Document Frequency is a way of quantifying text data. For each document (piece of text, in this case one tweet, news article, etc.) a count is created for the number of times each term (word) appears. This count is then scaled down by the amount of times the word appears in all of the documents (so common words like “the” are given a lower score). The result is a set of numerical features representing each document by the words in it. 

Note that this method of quantifying text is a bag of words approach, and does not take the location or co-occurrence of words or phrases within a document into account.

B.  File format
The text data loaded into SMART is preprocessed with Scikit-Learn’s TFIDFVectorizer (http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html) with the parameters:
* max_df: 0.95 (only keep those terms with document frequency lower than this value)
* min_df: 0.05 (only keep those terms with document frequency higher than this value)
* stop_words= English (Automatically remove words like “the”, “at”, “and”, etc.)

The data is then placed into a dictionary of unique id to values (ex: { “tweet1” : [0, 0.5, 0.8, …. ], “tweet2”: [0.56, 0.0, 0.99, …..] } ). It is saved as a pickle file with the .pkl ending.

SECTION 3: THE MODEL

A. Source

The models used in this application are build using Scikit-Learn libraries. The four options are:
* Logistic Regression (http://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)
   *  Parameters: class_weight: balanced, solver: lbfgs, multi_class: multinomial
* Support Vector Machine (http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html)
   *  Parameters: default
* Random Forest (http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
   *  Parameters: default
* Gaussian Naïve Bayes (http://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.GaussianNB.html)
   *  Parameters: default

B. File Format

All models are saved as pickle (.pkl) files through Scikit-Learn’s joblib library.

SECTION 4: HOW TO RUN

The following sample code can be used to read in the zipped files and get predictions for the unlabeled data.

NOTE: the model will predict labels as a number. The second sheet in the labels excel file gives the mapping between label text and ID.


```
import pandas as pd
import pickle
from sklearn.externals import joblib
import xlrd

#read in the TFIDF matrix and the labeled data
labeled_frame = pd.read_excel(<<path to unzipped labels excel>>, sheet_name=“Labeled Data”)
with open(<<path to #.pkl file>>,”rb") as tfidf_file:
    tfidf_dict = pickle.load(tfidf_file)

#Subset the TFIDF matrix by the unlabeled data and get as 2D list
labeled_ids = labeled_frame["ID"].tolist()
unlabeled = [tfidf_dict[key] for key in tfidf_dict if key not in labeled_ids]
#read in the model from the pickle file
model = joblib.load(<<path to training .pkl file>>)
#apply the model to the unlabeled data
predictions = model.predict(unlabeled)
#print the results
print(predictions)
```