"""
Login & Signup Page.
"""
import streamlit as st
from utils.api_client import get_api_client
import time

st.set_page_config(page_title="Login - Personal Stock Screener", page_icon="🔑", layout="centered")

client = get_api_client()

st.title("🔑 Login")

# Tabs for Login and Signup
tab1, tab2 = st.tabs(["Log In", "Sign Up"])

with tab1:
    st.header("Welcome Back")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log In", use_container_width=True)
        
        if submit:
            if not email or not password:
                st.error("Please fill in all fields")
            else:
                with st.spinner("Authenticating..."):
                    response = client.login(email, password)
                    
                    if "access_token" in response:
                        st.session_state["token"] = response["access_token"]
                        
                        # Get user details
                        user = client.get_me()
                        st.session_state["user"] = user
                        
                        st.success("Login successful!")
                        time.sleep(1)
                        st.switch_page("app.py")
                    else:
                        st.error("Invalid credentials")

with tab2:
    st.header("Create Account")
    with st.form("signup_form"):
        new_email = st.text_input("Email")
        new_name = st.text_input("Full Name")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        signup_submit = st.form_submit_button("Sign Up", use_container_width=True)
        
        if signup_submit:
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif not new_email or not new_password:
                st.error("Please fill in all fields")
            else:
                with st.spinner("Creating account..."):
                    response = client.signup(new_email, new_password, new_name)
                    
                    if "id" in response:
                        st.success("Account created successfully! Please log in.")
                    else:
                        st.error("Registration failed. Email might be taken.")
