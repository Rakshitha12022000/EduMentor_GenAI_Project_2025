# register_page.py
import streamlit as st
from auth import register_user
from firestore_db import save_user_info


def show_register():
    st.subheader("📝 Register for EduMentor")

    with st.form(key="registration_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email (use your student/teacher institutional email)")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        # Extra Info
        university_id = st.text_input("University ID / Employee ID")
        department = st.text_input("Department (e.g., Computer Science, Business Analytics)")
        phone = st.text_input("Phone Number (optional)")
        bio = st.text_area("Short Bio (optional)", max_chars=300)

        submit_button = st.form_submit_button(label="Register")

    if submit_button:
        # Basic validation
        if not email or not password or not confirm_password or not full_name or not university_id or not department:
            st.warning("⚠️ Please fill in all required fields.")
            return

        if password != confirm_password:
            st.warning("⚠️ Passwords do not match.")
            return

        # Role detection
        if email.endswith("@student.gsu.edu"):
            role = "Student"
        elif email.endswith("@faculty.gsu.edu"):
            role = "Teacher"
        else:
            st.error("❌ Invalid email domain. Please use your institutional email.")
            return

        user = register_user(email, password)
        if isinstance(user, dict):
            st.success("✅ Registered successfully! You can now log in.")

            uid = user.get('uid')
            st.session_state.user_role = role
            st.session_state.full_name = full_name
            st.session_state.university_id = university_id
            st.session_state.department = department
            st.session_state.phone = phone
            st.session_state.bio = bio

            # ✅ Save user profile into Firestore
            save_user_info(
                uid=uid,
                full_name=full_name,
                email=email,
                university_id=university_id,
                department=department,
                role=role,
                phone=phone,
                bio=bio
            )

        else:
            st.error("❌ Registration failed: " + user)
