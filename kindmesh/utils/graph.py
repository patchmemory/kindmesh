"""
Neo4j Graph Database Interaction Module for kindmesh

This module handles all interactions with the Neo4j graph database, including:
- Connection management
- User authentication and management
- CRUD operations for interactions and recipients
- Data export functionality
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

import bcrypt
from neo4j import GraphDatabase as Neo4jGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from neo4j.time import DateTime as Neo4jDateTime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphDatabase:
    """
    Handles all interactions with the Neo4j graph database.
    """

    @staticmethod
    def _convert_neo4j_datetime(value: Any) -> Any:
        """
        Convert Neo4j DateTime objects to Python datetime objects.

        Args:
            value: Value to convert

        Returns:
            Converted value
        """
        if isinstance(value, Neo4jDateTime):
            # Convert Neo4j DateTime to Python datetime
            return datetime(
                value.year, value.month, value.day,
                value.hour, value.minute, value.second,
                value.nanosecond // 1000  # Convert nanoseconds to microseconds
            )
        return value

    @classmethod
    def _process_record(cls, record: Dict) -> Dict:
        """
        Process a Neo4j record to convert DateTime objects to Python datetime objects.

        Args:
            record: Neo4j record as dictionary

        Returns:
            Processed record
        """
        result = {}
        for key, value in record.items():
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                result[key] = cls._process_record(value)
            elif isinstance(value, list):
                # Recursively process lists
                result[key] = [
                    cls._process_record(item) if isinstance(item, dict)
                    else cls._convert_neo4j_datetime(item)
                    for item in value
                ]
            else:
                # Convert value if it's a Neo4j DateTime
                result[key] = cls._convert_neo4j_datetime(value)
        return result

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize the database connection.

        Args:
            uri: Neo4j connection URI (default: environment variable NEO4J_URI)
            user: Neo4j username (default: environment variable NEO4J_USER)
            password: Neo4j password (default: environment variable NEO4J_PASSWORD)
        """
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.environ.get("NEO4J_USER", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "kindmesh")
        self.driver = None
        self.connect()

    def connect(self) -> bool:
        """
        Establish connection to the Neo4j database.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.driver = Neo4jGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j database")
            return True
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            return False

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j database connection")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # User Management Methods

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Authenticate a user with username and password.

        Args:
            username: User's username
            password: User's password

        Returns:
            Tuple containing:
                - bool: True if authentication successful, False otherwise
                - Optional[Dict]: User data if authentication successful, None otherwise
        """
        query = """
        MATCH (u:User {username: $username})
        RETURN u.username AS username, u.password_hash AS password_hash, u.role AS role
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, username=username)
                user_record = result.single()

                if not user_record:
                    logger.warning(f"Authentication failed: User {username} not found")
                    return False, None

                stored_hash = user_record["password_hash"]

                # Check password
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    user_data = {
                        "username": user_record["username"],
                        "role": user_record["role"]
                    }
                    logger.info(f"User {username} authenticated successfully")
                    return True, user_data
                else:
                    logger.warning(f"Authentication failed: Invalid password for user {username}")
                    return False, None

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False, None

    def create_user(self, username: str, password: str, role: str = "Friend", created_by: str = None) -> bool:
        """
        Create a new user in the database.

        Args:
            username: New user's username
            password: New user's password
            role: User's role (default: "Friend")
            created_by: Username of the user creating this account

        Returns:
            bool: True if user created successfully, False otherwise

        Raises:
            ValueError: If the password does not meet the security requirements
        """
        # Import here to avoid circular imports
        from kindmesh.password_policy import validate_password

        # Validate the password
        is_valid, errors = validate_password(password)
        if not is_valid:
            error_msg = "; ".join(errors)
            logger.warning(f"Password validation failed for new user: {error_msg}")
            raise ValueError(f"Password does not meet security requirements: {error_msg}")

        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Check if this is the first user being created (after Hello)
        if role == "Friend":
            query_check = """
            MATCH (u:User)
            WHERE u.username <> 'Hello'
            RETURN count(u) as user_count
            """

            try:
                with self.driver.session() as session:
                    result = session.run(query_check)
                    user_count = result.single()["user_count"]

                    # If this is the first user after Hello, make them an Admin
                    if user_count == 0:
                        role = "Admin"
                        logger.info(f"First user after Hello: {username} will be created as Admin")
            except Exception as e:
                logger.error(f"Error checking user count: {str(e)}")
                return False

        # Create user query
        query = """
        CREATE (u:User {
            username: $username,
            password_hash: $password_hash,
            role: $role,
            created_at: datetime()
        })
        RETURN u
        """

        # Add relationship if created_by is provided
        if created_by:
            query = """
            MATCH (creator:User {username: $created_by})
            CREATE (creator)-[:CREATED]->(u:User {
                username: $username,
                password_hash: $password_hash,
                role: $role,
                created_at: datetime()
            })
            RETURN u
            """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    username=username,
                    password_hash=password_hash,
                    role=role,
                    created_by=created_by
                )

                if result.single():
                    logger.info(f"User {username} created successfully with role {role}")
                    return True
                return False

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return False

    def get_all_users(self) -> List[Dict]:
        """
        Get all users from the database.

        Returns:
            List[Dict]: List of user dictionaries
        """
        query = """
        MATCH (u:User)
        RETURN u.username AS username, u.role AS role, u.created_at AS created_at
        ORDER BY u.created_at
        """

        try:
            with self.driver.session() as session:
                result = session.run(query)
                # Process records to convert Neo4j DateTime objects to Python datetime objects
                return [self._process_record(dict(record)) for record in result]
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return []

    def promote_user(self, username: str, promoted_by: str) -> bool:
        """
        Promote a user to Admin role.

        Args:
            username: Username to promote
            promoted_by: Username of admin performing the promotion

        Returns:
            bool: True if promotion successful, False otherwise
        """
        query = """
        MATCH (promoter:User {username: $promoted_by})
        MATCH (u:User {username: $username})
        WHERE promoter.role = 'Admin' AND u.username <> promoter.username
        SET u.role = 'Admin'
        CREATE (promoter)-[:PROMOTED {timestamp: datetime()}]->(u)
        RETURN u
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, username=username, promoted_by=promoted_by)
                if result.single():
                    logger.info(f"User {username} promoted to Admin by {promoted_by}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error promoting user: {str(e)}")
            return False

    def demote_admin(self, username: str, demoted_by: List[str]) -> bool:
        """
        Demote an admin to Friend role. Requires at least 2 admins to confirm.

        Args:
            username: Username to demote
            demoted_by: List of admin usernames performing the demotion

        Returns:
            bool: True if demotion successful, False otherwise
        """
        # Check if we have at least 2 admins confirming
        if len(demoted_by) < 2:
            logger.warning("Admin demotion requires at least 2 admins to confirm")
            return False

        # Check if all users in demoted_by are admins
        check_query = """
        MATCH (u:User)
        WHERE u.username IN $demoted_by AND u.role = 'Admin'
        RETURN count(u) as admin_count
        """

        try:
            with self.driver.session() as session:
                result = session.run(check_query, demoted_by=demoted_by)
                admin_count = result.single()["admin_count"]

                if admin_count < 2:
                    logger.warning("Not enough admins to confirm demotion")
                    return False

                # Perform the demotion
                demote_query = """
                MATCH (u:User {username: $username})
                WHERE u.role = 'Admin'
                SET u.role = 'Friend'
                WITH u
                UNWIND $demoted_by AS demoter_name
                MATCH (demoter:User {username: demoter_name})
                CREATE (demoter)-[:DEMOTED {timestamp: datetime()}]->(u)
                RETURN u
                """

                result = session.run(demote_query, username=username, demoted_by=demoted_by)
                if result.single():
                    logger.info(f"Admin {username} demoted by {', '.join(demoted_by)}")
                    return True
                return False

        except Exception as e:
            logger.error(f"Error demoting admin: {str(e)}")
            return False

    def delete_user(self, username: str) -> bool:
        """
        Delete a user from the database.

        Args:
            username: Username to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        query = """
        MATCH (u:User {username: $username})
        DETACH DELETE u
        RETURN count(u) as deleted_count
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, username=username)
                deleted_count = result.single()["deleted_count"]

                if deleted_count > 0:
                    logger.info(f"User {username} deleted successfully")
                    return True
                logger.warning(f"User {username} not found for deletion")
                return False
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False

    # Interaction and Recipient Methods

    def get_all_recipient_keys(self) -> List[str]:
        """
        Get all recipient keys from the database.

        Returns:
            List[str]: List of all recipient keys
        """
        query = """
        MATCH (r:Recipient)
        RETURN r.key AS key
        ORDER BY r.key
        """

        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [record["key"] for record in result]
        except Exception as e:
            logger.error(f"Error getting recipient keys: {str(e)}")
            return []

    def create_recipient(self, key: str, pseudonym: str = None) -> bool:
        """
        Create a new recipient.

        Args:
            key: Key identifier for the recipient
            pseudonym: Optional pseudonym for the recipient

        Returns:
            bool: True if recipient created successfully, False otherwise
        """
        query = """
        MERGE (r:Recipient {key: $key})
        ON CREATE SET r.created_at = datetime()
        """

        if pseudonym:
            query += ", r.pseudonym = $pseudonym"

        query += """
        RETURN r
        """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    key=key,
                    pseudonym=pseudonym
                )

                if result.single():
                    logger.info(f"Recipient {key} created successfully")
                    return True
                return False

        except Exception as e:
            logger.error(f"Error creating recipient: {str(e)}")
            return False

    def save_questionnaire(self, recipient_key: str, section: str, responses: Dict, survey_id: str = None, username: str = None) -> bool:
        """
        Save survey responses for a recipient.

        Args:
            recipient_key: Key identifier for the recipient
            section: Section of the survey response (e.g., "Financial", "Employment")
            responses: Dictionary of question-answer pairs
            survey_id: Optional ID of the survey this response is based on
            username: Username of the user submitting the response

        Returns:
            bool: True if responses saved successfully, False otherwise
        """
        # Convert responses to JSON string to ensure Neo4j can store it properly
        import json
        responses_json = json.dumps(responses)

        if survey_id and username:
            query = """
            MATCH (u:User {username: $username})
            MATCH (s:Survey {id: $survey_id})
            MERGE (r:Recipient {key: $recipient_key})
            ON CREATE SET r.created_at = datetime()
            MERGE (q:SurveyResponse {section: $section, recipient_key: $recipient_key})
            ON CREATE SET q.created_at = datetime(), q.responses_json = $responses_json, q.survey_id = $survey_id, q.submitted_by = $username
            ON MATCH SET q.updated_at = datetime(), q.responses_json = $responses_json, q.survey_id = $survey_id, q.submitted_by = $username
            MERGE (r)-[:RESPONDED_TO]->(s)
            MERGE (s)-[:HAS_RESPONSE]->(q)
            MERGE (r)-[:PROVIDED]->(q)
            RETURN q
            """
        elif survey_id:
            query = """
            MATCH (s:Survey {id: $survey_id})
            MERGE (r:Recipient {key: $recipient_key})
            ON CREATE SET r.created_at = datetime()
            MERGE (q:SurveyResponse {section: $section, recipient_key: $recipient_key})
            ON CREATE SET q.created_at = datetime(), q.responses_json = $responses_json, q.survey_id = $survey_id
            ON MATCH SET q.updated_at = datetime(), q.responses_json = $responses_json, q.survey_id = $survey_id
            MERGE (r)-[:RESPONDED_TO]->(s)
            MERGE (s)-[:HAS_RESPONSE]->(q)
            MERGE (r)-[:PROVIDED]->(q)
            RETURN q
            """
        else:
            query = """
            MERGE (r:Recipient {key: $recipient_key})
            ON CREATE SET r.created_at = datetime()
            MERGE (q:SurveyResponse {section: $section, recipient_key: $recipient_key})
            ON CREATE SET q.created_at = datetime(), q.responses_json = $responses_json
            ON MATCH SET q.updated_at = datetime(), q.responses_json = $responses_json
            MERGE (r)-[:PROVIDED]->(q)
            RETURN q
            """

        try:
            with self.driver.session() as session:
                # Only include survey_id and username in params if they're provided
                params = {
                    "recipient_key": recipient_key,
                    "section": section,
                    "responses_json": responses_json
                }
                if survey_id:
                    params["survey_id"] = survey_id
                if username:
                    params["username"] = username

                result = session.run(query, **params)

                if result.single():
                    logger.info(f"Survey responses saved for recipient {recipient_key}, section {section}")
                    return True
                return False

        except Exception as e:
            logger.error(f"Error saving survey responses: {str(e)}")
            return False

    def get_questionnaire(self, recipient_key: str, section: str = None) -> List[Dict]:
        """
        Get survey responses for a recipient.

        Args:
            recipient_key: Key identifier for the recipient
            section: Optional section to filter by

        Returns:
            List[Dict]: List of survey response dictionaries
        """
        if section:
            query = """
            MATCH (q:SurveyResponse {recipient_key: $recipient_key, section: $section})
            RETURN q.section AS section, q.responses_json AS responses_json, q.responses AS responses, 
                   q.created_at AS created_at, q.updated_at AS updated_at,
                   q.survey_id AS survey_id, q.submitted_by AS submitted_by
            """
            params = {"recipient_key": recipient_key, "section": section}
        else:
            query = """
            MATCH (q:SurveyResponse {recipient_key: $recipient_key})
            RETURN q.section AS section, q.responses_json AS responses_json, q.responses AS responses, 
                   q.created_at AS created_at, q.updated_at AS updated_at,
                   q.survey_id AS survey_id, q.submitted_by AS submitted_by
            """
            params = {"recipient_key": recipient_key}

        try:
            with self.driver.session() as session:
                result = session.run(query, **params)
                # Process records to convert Neo4j DateTime objects to Python datetime objects
                records = [self._process_record(dict(record)) for record in result]

                # Convert responses_json back to dictionary if it exists
                import json
                for record in records:
                    if 'responses_json' in record and record['responses_json']:
                        record['responses'] = json.loads(record['responses_json'])
                        del record['responses_json']  # Remove the JSON string from the result
                    elif 'responses' not in record or not record['responses']:
                        record['responses'] = {}  # Default to empty dict if no responses

                return records
        except Exception as e:
            logger.error(f"Error getting survey responses: {str(e)}")
            return []

    def log_interaction(self, logged_by: str, recipient_key: str, 
                       interaction_type: str, notes: str = None,
                       recipient_pseudonym: str = None) -> bool:
        """
        Log an interaction between a user and a recipient.

        Args:
            logged_by: Username of the user logging the interaction
            recipient_key: Key identifier for the recipient
            interaction_type: Type of interaction (e.g., "food", "services")
            notes: Optional notes about the interaction
            recipient_pseudonym: Optional pseudonym for the recipient

        Returns:
            bool: True if interaction logged successfully, False otherwise
        """
        # Choose the appropriate query based on whether a pseudonym is provided
        if recipient_pseudonym:
            # Query with pseudonym handling
            query = """
            MATCH (u:User {username: $logged_by})
            MERGE (r:Recipient {key: $recipient_key})
            ON CREATE SET r.created_at = datetime()
            ON MATCH SET r.pseudonym = $recipient_pseudonym

            CREATE (i:Interaction {
                timestamp: datetime(),
                type: $interaction_type,
                notes: $notes
            })

            CREATE (u)-[:LOGGED]->(i)
            CREATE (i)-[:INVOLVES]->(r)

            RETURN i
            """
        else:
            # Query without pseudonym handling
            query = """
            MATCH (u:User {username: $logged_by})
            MERGE (r:Recipient {key: $recipient_key})
            ON CREATE SET r.created_at = datetime()

            CREATE (i:Interaction {
                timestamp: datetime(),
                type: $interaction_type,
                notes: $notes
            })

            CREATE (u)-[:LOGGED]->(i)
            CREATE (i)-[:INVOLVES]->(r)

            RETURN i
            """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    logged_by=logged_by,
                    recipient_key=recipient_key,
                    interaction_type=interaction_type,
                    notes=notes,
                    recipient_pseudonym=recipient_pseudonym
                )

                if result.single():
                    logger.info(f"Interaction logged by {logged_by} with recipient {recipient_key}")
                    return True
                return False

        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")
            return False

    def get_interactions(self, limit: int = 100, *, recipient_key: str = None) -> List[Dict]:
        """
        Get recent interactions from the database.

        Args:
            limit: Maximum number of interactions to return
            recipient_key: Optional recipient key to filter interactions by

        Returns:
            List[Dict]: List of interaction dictionaries
        """
        if recipient_key:
            query = """
            MATCH (u:User)-[:LOGGED]->(i:Interaction)-[:INVOLVES]->(r:Recipient)
            WHERE r.key = $recipient_key
            RETURN 
                i.timestamp AS timestamp,
                i.type AS type,
                i.notes AS notes,
                u.username AS logged_by,
                r.key AS recipient_key,
                r.pseudonym AS recipient_pseudonym
            ORDER BY i.timestamp DESC
            LIMIT $limit
            """
            params = {"limit": limit, "recipient_key": recipient_key}
        else:
            query = """
            MATCH (u:User)-[:LOGGED]->(i:Interaction)-[:INVOLVES]->(r:Recipient)
            RETURN 
                i.timestamp AS timestamp,
                i.type AS type,
                i.notes AS notes,
                u.username AS logged_by,
                r.key AS recipient_key,
                r.pseudonym AS recipient_pseudonym
            ORDER BY i.timestamp DESC
            LIMIT $limit
            """
            params = {"limit": limit}

        try:
            with self.driver.session() as session:
                result = session.run(query, **params)
                # Process records to convert Neo4j DateTime objects to Python datetime objects
                return [self._process_record(dict(record)) for record in result]
        except Exception as e:
            logger.error(f"Error getting interactions: {str(e)}")
            return []

    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics about interactions and recipients.

        Returns:
            Dict: Dictionary containing summary statistics
        """
        query = """
        MATCH (i:Interaction)
        WITH count(i) AS total_interactions

        MATCH (r:Recipient)
        WITH total_interactions, count(r) AS total_recipients

        MATCH (i:Interaction)
        WITH 
            total_interactions, 
            total_recipients,
            i.type AS interaction_type, 
            count(i) AS type_count

        RETURN 
            total_interactions,
            total_recipients,
            collect({type: interaction_type, count: type_count}) AS interaction_types
        """

        try:
            with self.driver.session() as session:
                result = session.run(query)
                record = result.single()
                if record:
                    return {
                        "total_interactions": record["total_interactions"],
                        "total_recipients": record["total_recipients"],
                        "interaction_types": record["interaction_types"]
                    }
                return {
                    "total_interactions": 0,
                    "total_recipients": 0,
                    "interaction_types": []
                }
        except Exception as e:
            logger.error(f"Error getting summary stats: {str(e)}")
            return {
                "total_interactions": 0,
                "total_recipients": 0,
                "interaction_types": []
            }

    def export_interactions_data(self) -> List[Dict]:
        """
        Export all interaction data for reporting.

        Returns:
            List[Dict]: List of all interactions with related data
        """
        query = """
        MATCH (u:User)-[:LOGGED]->(i:Interaction)-[:INVOLVES]->(r:Recipient)
        RETURN 
            i.timestamp AS timestamp,
            i.type AS type,
            i.notes AS notes,
            u.username AS logged_by,
            r.key AS recipient_key,
            r.pseudonym AS recipient_pseudonym
        ORDER BY i.timestamp
        """

        try:
            with self.driver.session() as session:
                result = session.run(query)
                # Process records to convert Neo4j DateTime objects to Python datetime objects
                return [self._process_record(dict(record)) for record in result]
        except Exception as e:
            logger.error(f"Error exporting interaction data: {str(e)}")
            return []

    # Survey Management Methods

    def create_survey(self, name: str, description: str, sections: List[Dict], created_by: str) -> str:
        """
        Create a new survey with sections and questions.

        Args:
            name: Name of the survey
            description: Description of the survey
            sections: List of section dictionaries, each containing:
                - name: Section name
                - questions: List of question dictionaries, each containing:
                    - text: Question text
                    - type: Question type (e.g., "text", "radio", "checkbox")
                    - options: List of options for radio/checkbox questions
            created_by: Username of the user creating the survey

        Returns:
            str: ID of the created survey, or None if creation failed
        """
        # Generate a unique ID for the survey
        survey_id = str(uuid.uuid4())

        # Convert sections to JSON string to ensure Neo4j can store it properly
        import json
        sections_json = json.dumps(sections)

        query = """
        MERGE (creator:User {username: $created_by})
        CREATE (s:Survey {
            id: $survey_id,
            name: $name,
            description: $description,
            sections_json: $sections_json,
            created_at: datetime(),
            created_by: $created_by
        })
        CREATE (creator)-[:CREATED]->(s)
        RETURN s.id AS id
        """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    survey_id=survey_id,
                    name=name,
                    description=description,
                    sections_json=sections_json,
                    created_by=created_by
                )
                record = result.single()
                if record:
                    logger.info(f"Survey '{name}' created with ID {survey_id} by {created_by}")
                    return survey_id
                return None

        except Exception as e:
            logger.error(f"Error creating survey: {str(e)}")
            return None

    def get_all_surveys(self) -> List[Dict]:
        """
        Get all surveys from the database.

        Returns:
            List[Dict]: List of survey dictionaries
        """
        query = """
        MATCH (s:Survey)
        RETURN 
            s.id AS id,
            s.name AS name,
            s.description AS description,
            s.sections_json AS sections_json,
            s.created_at AS created_at,
            s.created_by AS created_by
        ORDER BY s.created_at DESC
        """

        try:
            with self.driver.session() as session:
                result = session.run(query)
                surveys = []
                import json
                for record in result:
                    # Process record to convert Neo4j DateTime objects to Python datetime objects
                    survey = self._process_record(dict(record))
                    # Parse the JSON string back to a Python object
                    if 'sections_json' in survey and survey['sections_json']:
                        survey['sections'] = json.loads(survey['sections_json'])
                        del survey['sections_json']  # Remove the JSON string from the result
                    else:
                        survey['sections'] = []  # Default to empty list if no sections
                    surveys.append(survey)
                return surveys
        except Exception as e:
            logger.error(f"Error getting surveys: {str(e)}")
            return []

    def get_survey(self, survey_id: str) -> Dict:
        """
        Get a specific survey by ID.

        Args:
            survey_id: ID of the survey to retrieve

        Returns:
            Dict: Survey data, or None if not found
        """
        query = """
        MATCH (s:Survey {id: $survey_id})
        RETURN 
            s.id AS id,
            s.name AS name,
            s.description AS description,
            s.sections_json AS sections_json,
            s.created_at AS created_at,
            s.created_by AS created_by
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, survey_id=survey_id)
                record = result.single()
                if record:
                    # Process record to convert Neo4j DateTime objects to Python datetime objects
                    survey = self._process_record(dict(record))
                    # Parse the JSON string back to a Python object
                    import json
                    if 'sections_json' in survey and survey['sections_json']:
                        survey['sections'] = json.loads(survey['sections_json'])
                        del survey['sections_json']  # Remove the JSON string from the result
                    else:
                        survey['sections'] = []  # Default to empty list if no sections
                    return survey
                return None
        except Exception as e:
            logger.error(f"Error getting survey: {str(e)}")
            return None

    def update_survey(self, survey_id: str, name: str, description: str, sections: List[Dict]) -> bool:
        """
        Update an existing survey.

        Args:
            survey_id: ID of the survey to update
            name: New name for the survey
            description: New description for the survey
            sections: New sections for the survey

        Returns:
            bool: True if update successful, False otherwise
        """
        # Convert sections to JSON string to ensure Neo4j can store it properly
        import json
        sections_json = json.dumps(sections)

        query = """
        MATCH (s:Survey {id: $survey_id})
        SET 
            s.name = $name,
            s.description = $description,
            s.sections_json = $sections_json,
            s.updated_at = datetime()
        RETURN s
        """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    survey_id=survey_id,
                    name=name,
                    description=description,
                    sections_json=sections_json
                )
                if result.single():
                    logger.info(f"Survey {survey_id} updated successfully")
                    return True
                logger.warning(f"Survey {survey_id} not found for update")
                return False
        except Exception as e:
            logger.error(f"Error updating survey: {str(e)}")
            return False

    def delete_survey(self, survey_id: str) -> bool:
        """
        Delete a survey from the database.

        Args:
            survey_id: ID of the survey to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        query = """
        MATCH (s:Survey {id: $survey_id})
        DETACH DELETE s
        RETURN count(s) as deleted_count
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, survey_id=survey_id)
                deleted_count = result.single()["deleted_count"]

                if deleted_count > 0:
                    logger.info(f"Survey {survey_id} deleted successfully")
                    return True
                logger.warning(f"Survey {survey_id} not found for deletion")
                return False
        except Exception as e:
            logger.error(f"Error deleting survey: {str(e)}")
            return False

    def get_recipient(self, recipient_key: str) -> Dict:
        """
        Get a specific recipient by key.

        Args:
            recipient_key: Key of the recipient to retrieve

        Returns:
            Dict: Recipient data, or None if not found
        """
        query = """
        MATCH (r:Recipient {key: $recipient_key})
        RETURN 
            r.key AS key,
            r.pseudonym AS pseudonym,
            r.created_at AS created_at
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, recipient_key=recipient_key)
                record = result.single()
                if record:
                    # Process record to convert Neo4j DateTime objects to Python datetime objects
                    return self._process_record(dict(record))
                return None
        except Exception as e:
            logger.error(f"Error getting recipient: {str(e)}")
            return None

    def get_all_recipients(self) -> List[Dict]:
        """
        Get all recipients from the database.

        Returns:
            List[Dict]: List of recipient dictionaries
        """
        query = """
        MATCH (r:Recipient)
        RETURN 
            r.key AS key,
            r.pseudonym AS pseudonym,
            r.created_at AS created_at
        ORDER BY r.created_at DESC
        """

        try:
            with self.driver.session() as session:
                result = session.run(query)
                # Process records to convert Neo4j DateTime objects to Python datetime objects
                return [self._process_record(dict(record)) for record in result]
        except Exception as e:
            logger.error(f"Error getting recipients: {str(e)}")
            return []
