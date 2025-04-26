from auth import login_user
import streamlit as st
from firestore_db import get_user_info

def show_login():
    st.subheader("🔐 Login")

    email = st.text_input("Email (use your student/teacher institutional email)")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(email, password)
        if isinstance(user, dict):
            st.success("Login successful!")
            st.session_state.user = user
            st.session_state.logged_in = True

            # Get UID
            uid = user.get("localId")
            st.session_state.uid = uid

            # Fetch role and other info
            user_info = get_user_info(uid)
            if user_info:
                st.session_state.user_role = user_info.get("role", "Student")
                st.session_state.full_name = user_info.get("full_name")
                st.session_state.university_id = user_info.get("university_id")
                st.session_state.department = user_info.get("department")
                st.session_state.phone = user_info.get("phone")
                st.session_state.bio = user_info.get("bio")
            else:
                st.warning("User profile not found. Please complete registration.")
            st.rerun()

        else:
            st.error("Login failed. Please check your email and password.")

