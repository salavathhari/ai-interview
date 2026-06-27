import os, sys, json, re, time
import numpy as np
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score
from xgboost import XGBClassifier

start = time.time()

DATASETS_DIR = r'C:\Users\salav\OneDrive\Desktop\ai-interview-platform\backend\app\ml\datasets'
MODELS_DIR = r'C:\Users\salav\OneDrive\Desktop\ai-interview-platform\backend\app\ml\models\saved'

CATEGORY_MAP = {
    'INFORMATION-TECHNOLOGY': 'Software Engineer', 'ENGINEERING': 'Software Engineer',
    'BUSINESS-DEVELOPMENT': 'Business Analyst', 'ADVOCATE': 'Legal',
    'CHEF': 'Hospitality', 'FINANCE': 'Financial Analyst',
    'ACCOUNTANT': 'Accountant', 'FITNESS': 'Fitness Trainer',
    'AVIATION': 'Aviation', 'SALES': 'Sales Representative',
    'HEALTHCARE': 'Healthcare', 'CONSULTANT': 'Consultant',
    'BANKING': 'Banking', 'CONSTRUCTION': 'Construction',
    'PUBLIC-RELATIONS': 'Public Relations', 'HR': 'HR Manager',
    'DESIGNER': 'UI/UX Designer', 'ARTS': 'Arts', 'TEACHER': 'Teacher',
    'APPAREL': 'Fashion Designer', 'DIGITAL-MEDIA': 'Digital Media Specialist',
    'AGRICULTURE': 'Agriculture', 'AUTOMOBILE': 'Automotive', 'BPO': 'Customer Service',
}

print("Loading dataset...", flush=True)
df = pd.read_csv(os.path.join(DATASETS_DIR, 'kaggle_resume.csv'))
print(f'Dataset: {len(df)} rows', flush=True)

texts, labels = [], []
for _, row in df.iterrows():
    text = str(row.get('Resume_str', ''))
    cat = str(row.get('Category', ''))
    label = CATEGORY_MAP.get(cat)
    if text and len(text) >= 50 and label:
        texts.append(re.sub(r'\s+', ' ', text.lower()).strip())
        labels.append(label)

print(f'Processed: {len(texts)} resumes', flush=True)

print("Building TF-IDF...", flush=True)
tfidf = TfidfVectorizer(max_features=3000, ngram_range=(1,2), min_df=2, max_df=0.95, sublinear_tf=True)
X_tfidf = tfidf.fit_transform(texts).toarray().astype(np.float32)
print(f'TF-IDF shape: {X_tfidf.shape}, time: {time.time()-start:.1f}s', flush=True)

le = LabelEncoder()
y = le.fit_transform(labels)
class_names = le.classes_
print(f'Classes: {len(class_names)}', flush=True)

X_train, X_test, y_train, y_test = train_test_split(X_tfidf, y, test_size=0.15, random_state=42, stratify=y)
print(f'Train: {len(X_train)}, Test: {len(X_test)}', flush=True)

print('Training XGBoost (200 trees)...', flush=True)
model = XGBClassifier(
    n_estimators=200, max_depth=8, learning_rate=0.1,
    subsample=0.8, colsample_bytree=0.7,
    objective='multi:softprob', eval_metric='mlogloss',
    random_state=42, tree_method='hist',
)
model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
print(f'Training done: {time.time()-start:.1f}s', flush=True)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

y_proba = model.predict_proba(X_test)
top3 = sum(1 for i, t in enumerate(y_test) if t in np.argsort(y_proba[i])[-3:]) / len(y_test)
top5 = sum(1 for i, t in enumerate(y_test) if t in np.argsort(y_proba[i])[-5:]) / len(y_test)

print(f'\nACCURACY: {accuracy:.4f} ({accuracy*100:.1f}%)', flush=True)
print(f'TOP-3:    {top3:.4f} ({top3*100:.1f}%)', flush=True)
print(f'TOP-5:    {top5:.4f} ({top5*100:.1f}%)', flush=True)

report = classification_report(y_test, y_pred, target_names=class_names, zero_division=0)
print(f'\n{report}', flush=True)

model_data = {
    'model': model, 'tfidf': tfidf, 'label_encoder': le,
    'feature_names': [f'tfidf_{f}' for f in tfidf.get_feature_names_out()],
    'category_map': CATEGORY_MAP, 'class_names': list(class_names),
    'metrics': {
        'accuracy': float(accuracy), 'top3_accuracy': float(top3),
        'top5_accuracy': float(top5), 'n_samples': len(texts),
        'n_classes': len(class_names), 'n_features': int(X_tfidf.shape[1]),
    },
}
path = os.path.join(MODELS_DIR, 'job_recommender_model.joblib')
joblib.dump(model_data, path)
print(f'\nModel saved: {path} ({os.path.getsize(path)/1024:.0f} KB)', flush=True)
print(f'Total time: {time.time()-start:.1f}s', flush=True)
