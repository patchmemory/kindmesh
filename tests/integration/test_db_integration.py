import unittest
import os
import uuid
from datetime import datetime

# Import the module to test
from app.utils.graph import GraphDatabase

class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests for the GraphDatabase class with a real Neo4j database"""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment once before all tests"""
        # Use environment variables or default test values
        cls.uri = os.environ.get("TEST_NEO4J_URI", "bolt://localhost:7687")
        cls.user = os.environ.get("TEST_NEO4J_USER", "neo4j")
        cls.password = os.environ.get("TEST_NEO4J_PASSWORD", "kindmesh")
        
        # Create a unique prefix for test data to avoid conflicts
        cls.test_prefix = f"test_{uuid.uuid4().hex[:8]}_"
        
        # Connect to the database
        cls.db = GraphDatabase(uri=cls.uri, user=cls.user, password=cls.password)
        
        # Verify connection
        if not cls.db.driver:
            raise ConnectionError("Could not connect to Neo4j database for integration tests")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run"""
        # Delete all test data
        if cls.db and cls.db.driver:
            with cls.db.driver.session() as session:
                # Delete test users
                session.run(f"""
                MATCH (u:User)
                WHERE u.username STARTS WITH $prefix
                DETACH DELETE u
                """, prefix=cls.test_prefix)
                
                # Delete test recipients
                session.run(f"""
                MATCH (r:Recipient)
                WHERE r.key STARTS WITH $prefix
                DETACH DELETE r
                """, prefix=cls.test_prefix)
                
                # Delete test interactions
                session.run(f"""
                MATCH (i:Interaction)
                WHERE i.test_id STARTS WITH $prefix
                DETACH DELETE i
                """, prefix=cls.test_prefix)
            
            # Close the connection
            cls.db.close()
    
    def test_user_creation_and_authentication(self):
        """Test creating a user and authenticating with the created credentials"""
        # Generate unique username for this test
        username = f"{self.test_prefix}user_{uuid.uuid4().hex[:8]}"
        password = "TestPassword123!"
        
        # Create the user
        result = self.db.create_user(username, password, "Friend", "integration_test")
        self.assertTrue(result, "User creation should succeed")
        
        # Authenticate with the created user
        success, user_data = self.db.authenticate_user(username, password)
        self.assertTrue(success, "Authentication should succeed with correct credentials")
        self.assertEqual(user_data["username"], username)
        self.assertEqual(user_data["role"], "Friend")
        
        # Try authenticating with wrong password
        success, _ = self.db.authenticate_user(username, "WrongPassword")
        self.assertFalse(success, "Authentication should fail with incorrect password")
    
    def test_recipient_management(self):
        """Test creating and retrieving recipients"""
        # Generate unique recipient key for this test
        recipient_key = f"{self.test_prefix}rec_{uuid.uuid4().hex[:8]}"
        pseudonym = "Test Recipient"
        
        # Create the recipient
        result = self.db.create_recipient(recipient_key, pseudonym)
        self.assertTrue(result, "Recipient creation should succeed")
        
        # Retrieve the recipient
        recipient = self.db.get_recipient(recipient_key)
        self.assertIsNotNone(recipient, "Should be able to retrieve created recipient")
        self.assertEqual(recipient["key"], recipient_key)
        self.assertEqual(recipient["pseudonym"], pseudonym)
        
        # Get all recipient keys
        all_keys = self.db.get_all_recipient_keys()
        self.assertIn(recipient_key, all_keys, "Created recipient key should be in the list of all keys")
    
    def test_interaction_logging_and_retrieval(self):
        """Test logging interactions and retrieving them"""
        # Create test user and recipient
        username = f"{self.test_prefix}user_{uuid.uuid4().hex[:8]}"
        self.db.create_user(username, "password", "Friend", "integration_test")
        
        recipient_key = f"{self.test_prefix}rec_{uuid.uuid4().hex[:8]}"
        self.db.create_recipient(recipient_key, "Test Recipient")
        
        # Log an interaction
        interaction_type = "Food"
        notes = f"Test interaction {datetime.now().isoformat()}"
        
        # Add a test_id to the interaction for cleanup
        with self.db.driver.session() as session:
            result = session.run("""
            MATCH (u:User {username: $username})
            MATCH (r:Recipient {key: $recipient_key})
            
            CREATE (i:Interaction {
                timestamp: datetime(),
                type: $interaction_type,
                notes: $notes,
                test_id: $test_id
            })
            
            CREATE (u)-[:LOGGED]->(i)
            CREATE (i)-[:INVOLVES]->(r)
            
            RETURN i
            """, username=username, recipient_key=recipient_key, 
                 interaction_type=interaction_type, notes=notes,
                 test_id=self.test_prefix)
            
            self.assertIsNotNone(result.single(), "Interaction should be created")
        
        # Retrieve interactions
        interactions = self.db.get_interactions(limit=100)
        
        # Find our test interaction
        found = False
        for interaction in interactions:
            if interaction["notes"] == notes:
                found = True
                self.assertEqual(interaction["type"], interaction_type)
                self.assertEqual(interaction["logged_by"], username)
                self.assertEqual(interaction["recipient_key"], recipient_key)
                break
        
        self.assertTrue(found, "Should be able to retrieve the logged interaction")
        
        # Test retrieving interactions for a specific recipient
        recipient_interactions = self.db.get_interactions(limit=100, recipient_key=recipient_key)
        self.assertTrue(len(recipient_interactions) > 0, "Should find interactions for the recipient")
        
        found = False
        for interaction in recipient_interactions:
            if interaction["notes"] == notes:
                found = True
                break
        
        self.assertTrue(found, "Should find the specific interaction for the recipient")
    
    def test_summary_stats(self):
        """Test retrieving summary statistics"""
        # Get summary stats
        stats = self.db.get_summary_stats()
        
        # Basic validation of the stats structure
        self.assertIn("total_interactions", stats)
        self.assertIn("total_recipients", stats)
        self.assertIn("interaction_types", stats)
        
        # Verify the stats are numeric
        self.assertIsInstance(stats["total_interactions"], int)
        self.assertIsInstance(stats["total_recipients"], int)
        
        # Verify interaction types is a list of dictionaries
        if stats["interaction_types"]:
            self.assertIsInstance(stats["interaction_types"], list)
            self.assertIsInstance(stats["interaction_types"][0], dict)
            self.assertIn("type", stats["interaction_types"][0])
            self.assertIn("count", stats["interaction_types"][0])

if __name__ == '__main__':
    unittest.main()