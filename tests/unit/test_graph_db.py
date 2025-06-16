import unittest
from unittest.mock import patch, MagicMock, call
import bcrypt
from datetime import datetime

# Import the module to test
from app.utils.graph import GraphDatabase

class TestGraphDatabase(unittest.TestCase):
    """Unit tests for the GraphDatabase class"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create a patcher for the Neo4j driver
        self.driver_patcher = patch('neo4j.GraphDatabase')
        self.mock_neo4j_driver = self.driver_patcher.start()
        
        # Mock the driver and session
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_transaction = MagicMock()
        
        # Set up the mock chain
        self.mock_neo4j_driver.driver.return_value = self.mock_driver
        self.mock_driver.session.return_value.__enter__.return_value = self.mock_session
        self.mock_session.begin_transaction.return_value.__enter__.return_value = self.mock_transaction
        
        # Create an instance of GraphDatabase with mock driver
        self.db = GraphDatabase(uri="bolt://mock:7687", user="mock", password="mock")
    
    def tearDown(self):
        """Clean up after each test"""
        self.driver_patcher.stop()
    
    def test_connect(self):
        """Test database connection"""
        # Reset the mock to clear the call from __init__
        self.mock_neo4j_driver.reset_mock()
        
        # Call connect method
        result = self.db.connect()
        
        # Verify the result and that driver was created
        self.assertTrue(result)
        self.mock_neo4j_driver.driver.assert_called_once_with(
            "bolt://mock:7687", 
            auth=("mock", "mock")
        )
    
    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        # Mock the query result
        mock_record = {
            "username": "test_user",
            "password_hash": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "Admin"
        }
        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result
        
        # Call the method
        success, user_data = self.db.authenticate_user("test_user", "password")
        
        # Verify the result
        self.assertTrue(success)
        self.assertEqual(user_data["username"], "test_user")
        self.assertEqual(user_data["role"], "Admin")
        
        # Verify the query was executed
        self.mock_session.run.assert_called_once()
        query_args = self.mock_session.run.call_args[1]
        self.assertEqual(query_args["username"], "test_user")
    
    def test_authenticate_user_failure_wrong_password(self):
        """Test failed authentication with wrong password"""
        # Mock the query result
        mock_record = {
            "username": "test_user",
            "password_hash": bcrypt.hashpw("correct_password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "Admin"
        }
        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result
        
        # Call the method
        success, user_data = self.db.authenticate_user("test_user", "wrong_password")
        
        # Verify the result
        self.assertFalse(success)
        self.assertIsNone(user_data)
    
    def test_authenticate_user_failure_user_not_found(self):
        """Test failed authentication with non-existent user"""
        # Mock the query result
        mock_result = MagicMock()
        mock_result.single.return_value = None
        self.mock_session.run.return_value = mock_result
        
        # Call the method
        success, user_data = self.db.authenticate_user("nonexistent_user", "password")
        
        # Verify the result
        self.assertFalse(success)
        self.assertIsNone(user_data)
    
    def test_create_user(self):
        """Test user creation"""
        # Mock the query result for checking if first user
        mock_result_check = MagicMock()
        mock_result_check.single.return_value = None  # No users exist yet
        
        # Mock the query result for user creation
        mock_result_create = MagicMock()
        mock_result_create.single.return_value = {"username": "new_user"}
        
        # Set up the mock session to return different results for different queries
        self.mock_session.run.side_effect = [mock_result_check, mock_result_create]
        
        # Call the method
        result = self.db.create_user("new_user", "password", "Friend", "admin_user")
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the queries were executed
        self.assertEqual(self.mock_session.run.call_count, 2)
    
    def test_log_interaction(self):
        """Test logging an interaction"""
        # Mock the query result
        mock_result = MagicMock()
        mock_result.single.return_value = {"timestamp": datetime.now()}
        self.mock_session.run.return_value = mock_result
        
        # Call the method
        result = self.db.log_interaction(
            logged_by="test_user",
            recipient_key="REC123",
            interaction_type="Food",
            notes="Test notes",
            recipient_pseudonym="Test Recipient"
        )
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the query was executed
        self.mock_session.run.assert_called_once()
        query_args = self.mock_session.run.call_args[1]
        self.assertEqual(query_args["logged_by"], "test_user")
        self.assertEqual(query_args["recipient_key"], "REC123")
        self.assertEqual(query_args["interaction_type"], "Food")
        self.assertEqual(query_args["notes"], "Test notes")
        self.assertEqual(query_args["recipient_pseudonym"], "Test Recipient")
    
    def test_get_interactions(self):
        """Test retrieving interactions"""
        # Mock the query result
        mock_records = [
            {
                "timestamp": datetime.now(),
                "type": "Food",
                "notes": "Test notes 1",
                "logged_by": "test_user",
                "recipient_key": "REC123",
                "recipient_pseudonym": "Test Recipient"
            },
            {
                "timestamp": datetime.now(),
                "type": "Clothing",
                "notes": "Test notes 2",
                "logged_by": "test_user",
                "recipient_key": "REC456",
                "recipient_pseudonym": "Another Recipient"
            }
        ]
        mock_result = MagicMock()
        mock_result.__iter__.return_value = mock_records
        self.mock_session.run.return_value = mock_result
        
        # Call the method
        result = self.db.get_interactions(limit=10)
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "Food")
        self.assertEqual(result[1]["type"], "Clothing")
        
        # Verify the query was executed
        self.mock_session.run.assert_called_once()
        query_args = self.mock_session.run.call_args[1]
        self.assertEqual(query_args["limit"], 10)

if __name__ == '__main__':
    unittest.main()