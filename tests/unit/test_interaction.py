import unittest
from unittest.mock import patch, MagicMock

# Import the module to test
from app.interaction import log_interaction_form

class TestInteraction(unittest.TestCase):
    """Unit tests for the interaction module"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create patchers for Streamlit components
        self.subheader_patcher = patch('streamlit.subheader')
        self.form_patcher = patch('streamlit.form')
        self.selectbox_patcher = patch('streamlit.selectbox')
        self.text_input_patcher = patch('streamlit.text_input')
        self.text_area_patcher = patch('streamlit.text_area')
        self.form_submit_button_patcher = patch('streamlit.form_submit_button')
        self.success_patcher = patch('streamlit.success')
        self.error_patcher = patch('streamlit.error')
        self.warning_patcher = patch('streamlit.warning')
        
        # Start all patchers
        self.mock_subheader = self.subheader_patcher.start()
        self.mock_form = self.form_patcher.start()
        self.mock_selectbox = self.selectbox_patcher.start()
        self.mock_text_input = self.text_input_patcher.start()
        self.mock_text_area = self.text_area_patcher.start()
        self.mock_form_submit_button = self.form_submit_button_patcher.start()
        self.mock_success = self.success_patcher.start()
        self.mock_error = self.error_patcher.start()
        self.mock_warning = self.warning_patcher.start()
        
        # Set up form context manager
        self.mock_form.return_value.__enter__.return_value = None
        self.mock_form.return_value.__exit__.return_value = None
    
    def tearDown(self):
        """Clean up after each test"""
        # Stop all patchers
        self.subheader_patcher.stop()
        self.form_patcher.stop()
        self.selectbox_patcher.stop()
        self.text_input_patcher.stop()
        self.text_area_patcher.stop()
        self.form_submit_button_patcher.stop()
        self.success_patcher.stop()
        self.error_patcher.stop()
        self.warning_patcher.stop()
    
    def test_log_interaction_form_with_recipients(self):
        """Test interaction form with existing recipients"""
        # Mock database
        mock_db = MagicMock()
        mock_db.get_all_recipient_keys.return_value = ["REC123", "REC456"]
        mock_db.get_recipient.return_value = {"key": "REC123", "pseudonym": "Test Recipient"}
        mock_db.log_interaction.return_value = True
        
        # Mock form inputs
        self.mock_selectbox.return_value = "REC123"
        self.mock_text_input.return_value = "Test Recipient"
        self.mock_selectbox.side_effect = ["REC123", "Food"]  # recipient_key, interaction_type
        self.mock_text_area.return_value = "Test notes"
        self.mock_form_submit_button.return_value = True
        
        # Call the function
        log_interaction_form(mock_db, "test_user")
        
        # Verify the database was called correctly
        mock_db.get_all_recipient_keys.assert_called_once()
        mock_db.get_recipient.assert_called_once_with("REC123")
        mock_db.log_interaction.assert_called_once_with(
            logged_by="test_user",
            recipient_key="REC123",
            interaction_type="Food",
            notes="Test notes",
            recipient_pseudonym="Test Recipient"
        )
        
        # Verify success message was shown
        self.mock_success.assert_called_once_with("Interaction logged successfully")
    
    def test_log_interaction_form_no_recipients(self):
        """Test interaction form with no existing recipients"""
        # Mock database
        mock_db = MagicMock()
        mock_db.get_all_recipient_keys.return_value = []
        mock_db.log_interaction.return_value = True
        
        # Mock form inputs
        self.mock_text_input.side_effect = ["REC789", "New Recipient"]  # recipient_key, recipient_pseudonym
        self.mock_selectbox.return_value = "Food"  # interaction_type
        self.mock_text_area.return_value = "Test notes"
        self.mock_form_submit_button.return_value = True
        
        # Call the function
        log_interaction_form(mock_db, "test_user")
        
        # Verify the warning was shown
        self.mock_warning.assert_called_once_with("No recipients found. Please create recipients in the Recipient panel first.")
        
        # Verify the database was called correctly
        mock_db.get_all_recipient_keys.assert_called_once()
        mock_db.log_interaction.assert_called_once_with(
            logged_by="test_user",
            recipient_key="REC789",
            interaction_type="Food",
            notes="Test notes",
            recipient_pseudonym="New Recipient"
        )
        
        # Verify success message was shown
        self.mock_success.assert_called_once_with("Interaction logged successfully")
    
    def test_log_interaction_form_missing_recipient_key(self):
        """Test interaction form with missing recipient key"""
        # Mock database
        mock_db = MagicMock()
        mock_db.get_all_recipient_keys.return_value = ["REC123", "REC456"]
        
        # Mock form inputs
        self.mock_selectbox.return_value = ""  # Empty recipient_key
        self.mock_text_input.return_value = ""
        self.mock_selectbox.side_effect = ["", "Food"]  # recipient_key, interaction_type
        self.mock_text_area.return_value = "Test notes"
        self.mock_form_submit_button.return_value = True
        
        # Call the function
        log_interaction_form(mock_db, "test_user")
        
        # Verify error message was shown
        self.mock_error.assert_called_once_with("Recipient Key is required")
        
        # Verify the database was not called to log interaction
        mock_db.log_interaction.assert_not_called()
    
    def test_log_interaction_form_failed_logging(self):
        """Test interaction form with failed logging"""
        # Mock database
        mock_db = MagicMock()
        mock_db.get_all_recipient_keys.return_value = ["REC123", "REC456"]
        mock_db.get_recipient.return_value = {"key": "REC123", "pseudonym": "Test Recipient"}
        mock_db.log_interaction.return_value = False  # Logging fails
        
        # Mock form inputs
        self.mock_selectbox.return_value = "REC123"
        self.mock_text_input.return_value = "Test Recipient"
        self.mock_selectbox.side_effect = ["REC123", "Food"]  # recipient_key, interaction_type
        self.mock_text_area.return_value = "Test notes"
        self.mock_form_submit_button.return_value = True
        
        # Call the function
        log_interaction_form(mock_db, "test_user")
        
        # Verify error message was shown
        self.mock_error.assert_called_once_with("Failed to log interaction")

if __name__ == '__main__':
    unittest.main()