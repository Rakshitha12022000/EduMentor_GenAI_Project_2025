# firestore_db.py
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "firebase/serviceAccountKey.json"))
    firebase_admin.initialize_app(cred)

db = firestore.client()

def save_user_info(uid, full_name, email, university_id, department, role, phone=None, bio=None):
    doc_ref = db.collection("users").document(uid)
    doc_ref.set({
        "full_name": full_name,
        "email": email,
        "university_id": university_id,
        "department": department,
        "role": role,
        "phone": phone,
        "bio": bio
    })

# firestore_db.py

def get_user_info(uid):
    try:
        doc_ref = db.collection("users").document(uid)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return None
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return None