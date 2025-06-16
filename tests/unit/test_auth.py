import unittest
from unittest.mock import patch, MagicMock

# Import the module to test
from app.auth import login, logout, render_login_page

class TestAuth(unittest.TestCase):
    """Unit tests for the authentication module"""

    @patch('streamlit.session_state', {})
    def setUp(self):
        """Set up test environment before each test"""
        # Clear session state before each test
        import streamlit as st
        if hasattr(st, 'session_state'):
            for key in list(st.session_state.keys()):
                del st.session_state[key]

    @patch('streamlit.session_state', {})
    def test_login_success(self):
        """Test successful login"""
        # Mock the database connection
        mock_db = MagicMock()
        mock_db.authenticate_user.return_value = (True, {"username": "test_user", "role": "Admin"})
        
        # Call the function
        result = login("test_user", "password", mock_db)
        
        # Verify the result
        self.assertTrue(result)
        self.assertTrue(st.session_state.authenticated)
        self.assertEqual(st.session_state.username, "test_user")
        self.assertEqual(st.session_state.role, "Admin")
        
        # Verify the database was called correctly
        mock_db.authenticate_user.assert_called_once_with("test_user", "password")

    @patch('streamlit.session_state', {})
    def test_login_failure(self):
        """Test failed login"""
        # Mock the database connection
        mock_db = MagicMock()
        mock_db.authenticate_user.return_value = (False, None)
        
        # Call the function
        result = login("test_user", "wrong_password", mock_db)
        
        # Verify the result
        self.assertFalse(result)
        self.assertFalse(hasattr(st.session_state, 'authenticated') or st.session_state.authenticated)
        
        # Verify the database was called correctly
        mock_db.authenticate_user.assert_called_once_with("test_user", "wrong_password")

    @patch('streamlit.session_state', {'authenticated': True, 'username': 'test_user', 'role': 'Admin', 'admin_demotion_votes': {'admin1': True}})
    def test_logout(self):
        """Test logout functionality"""
        # Call the function
        logout()
        
        # Verify session state was cleared
        self.assertFalse(st.session_state.authenticated)
        self.assertIsNone(st.session_state.username)
        self.assertIsNone(st.session_state.role)
        self.assertEqual(st.session_state.admin_demotion_votes, {})

    @patch('streamlit.form')
    @patch('streamlit.text_input')
    @patch('streamlit.form_submit_button')
    def test_render_login_page(self, mock_submit_button, mock_text_input, mock_form):
        """Test rendering of login page"""
        # Mock the form context manager
        mock_form.return_value.__enter__.return_value = None
        mock_form.return_value.__exit__.return_value = None
        
        # Mock form inputs
        mock_text_input.side_effect = ["test_user", "password"]
        mock_submit_button.return_value = False
        
        # Mock the database
        mock_db = MagicMock()
        
        # Call the function
        render_login_page(mock_db)
        
        # Verify streamlit components were called
        mock_form.assert_called_once_with("login_form")
        self.assertEqual(mock_text_input.call_count, 2)
        mock_submit_button.assert_called_once_with("Login")

if __name__ == '__main__':
    unittest.main()