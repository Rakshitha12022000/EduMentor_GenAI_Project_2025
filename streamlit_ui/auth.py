# auth.py
import pyrebase
from firebase_config import firebaseConfig

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

def register_user(email, password):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        uid = auth.get_account_info(user['idToken'])['users'][0]['localId']
        user['uid'] = uid  # Add UID to the returned object
        return user
    except Exception as e:
        return str(e)


def login_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return user
    except Exception as e:
        return str(e)
