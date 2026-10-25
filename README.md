# **INNOVATRIX – Fake Job Detector**

###### About the Project

INNOVATRIX is a machine learning-based web application that analyzes job descriptions and identifies suspicious job postings. It helps users recognize possible job scams and provides safety tips for verifying job opportunities.

###### 

###### Problem Statement

Fake job postings can mislead job seekers through registration fees, false salary promises, and misleading recruitment processes. This project aims to help users identify potential warning signs before applying.



#### Objectives

* &#x20;Analyze job descriptions using Machine Learning.
* &#x20;Classify job postings as suspicious or lower risk.
* &#x20;Identify predefined suspicious phrases.
* &#x20;Provide job verification tips.
* &#x20;Store recent scan history.
* &#x20;Download an analysis report.

#### 

#### Technologies Used



###### Frontend

* React
* Vite
* HTML
* CSS
* JavaScript



###### Backend

* Python
* FastAPI
* SQLite



###### Machine Learning

* Scikit-learn
* TF-IDF Vectorization
* Logistic Regression
* Pandas
* Joblib



##### Dataset

The model was trained using the Fake Job Postings dataset from Kaggle.



**Dataset: https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction**

##### 

##### Key Features

1\. Job description analysis

2\. AI-based risk assessment

3\. Suspicious phrase detection

4\. Job safety recommendations

5\. Scan history management

6\. Downloadable analysis report



###### How to Run the Project



###### 1\. Start the Backend

Open a terminal and navigate to the backend folder:



```bash

cd backend

python -m uvicorn main:app --reload

```



Backend URL: http://127.0.0.1:8000



API Documentation: http://127.0.0.1:8000/docs



###### 2\. Start the Frontend

Open a second terminal:



```bash

cd frontend

npm run dev

```



Open the frontend URL shown in the terminal, usually:



http://localhost:5173/



###### Model Evaluation

On the current held-out test dataset, the model achieved approximately 98% accuracy. Performance on new, real-world job postings may differ.



###### Future Enhancements

* Improve model performance using additional datasets.
* Add more suspicious pattern detection.
* Develop user authentication.
* Improve the user interface and accessibility.
* Explore multilingual job description analysis.



###### Disclaimer

This application provides a preliminary machine learning assessment. It cannot prove whether a job posting is fraudulent. Users should independently verify employers and never pay money to obtain a job.



###### Developed By

INNOVATRIX Project Team



