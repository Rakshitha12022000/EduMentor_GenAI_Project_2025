# login_page.py

import streamlit as st
from auth import login_user
from firestore_db import get_user_info

def show_login():
    st.subheader("🔑 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not email or not password:
            st.warning("Please fill in all fields.")
            return

        user = login_user(email, password)

        if isinstance(user, dict):
            st.success("✅ Logged in successfully!")

            st.session_state.logged_in = True
            st.session_state.user = user  

            profile_info = get_user_info(user['localId'])

            if profile_info:
                st.session_state.full_name = profile_info.get("full_name", "No Name")
                st.session_state.university_id = profile_info.get("university_id", "Unknown")
                st.session_state.department = profile_info.get("department", "Unknown")
                st.session_state.role = profile_info.get("role", "Unknown")
                st.session_state.phone = profile_info.get("phone", "Not Provided")
                st.session_state.bio = profile_info.get("bio", "No bio yet")
                st.session_state.user_role = profile_info.get("role", "Student")  
            else:
                st.warning("⚠️ Could not load profile information.")
            
            st.success("✅ Logged in successfully! Redirecting...")
            st.rerun()

        else:
            st.error("Login failed: " + user)