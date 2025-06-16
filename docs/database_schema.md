# KindMesh Database Schema Documentation

## Overview

KindMesh uses Neo4j, a graph database, to store and manage all application data. This document provides detailed information about the database schema, including node types, relationships, properties, and constraints.

## Node Types

### User

Represents a user of the KindMesh application.

**Properties:**
- `username` (string): Unique identifier for the user
- `password_hash` (string): Bcrypt-hashed password
- `role` (string): User's role in the system (Admin, Greeter, or Friend)
- `created_at` (datetime): When the user was created

**Constraints:**
- Unique constraint on `username`

### Recipient

Represents a recipient of resources.

**Properties:**
- `key` (string): Unique identifier for the recipient (non-PII)
- `pseudonym` (string, optional): Optional nickname or identifier
- `created_at` (datetime): When the recipient was first created

**Constraints:**
- Unique constraint on `key`

### Interaction

Represents a resource distribution event.

**Properties:**
- `timestamp` (datetime): When the interaction occurred
- `type` (string): Type of resource distributed (e.g., Food, Clothing)
- `notes` (string, optional): Additional information about the interaction

### Survey

Represents a questionnaire template.

**Properties:**
- `id` (string): Unique identifier for the survey (UUID)
- `name` (string): Name of the survey
- `description` (string): Description of the survey's purpose
- `sections` (JSON): Array of section objects defining the survey structure
- `created_at` (datetime): When the survey was created
- `created_by` (string): Username of the user who created the survey

**Constraints:**
- Unique constraint on `id`

### QuestionnaireResponse

Represents a completed section of a questionnaire for a recipient.

**Properties:**
- `section` (string): The section of the questionnaire (e.g., "financial", "housing")
- `responses` (JSON): The answers provided for this section
- `created_at` (datetime): When the response was first created
- `updated_at` (datetime, optional): When the response was last updated
- `survey_id` (string, optional): Reference to the survey template, if applicable

## Relationships

### CREATED

Connects a user who created another user.

**Properties:**
- None

**Direction:**
- `(:User)-[:CREATED]->(:User)`

### LOGGED

Connects a user to an interaction they recorded.

**Properties:**
- None

**Direction:**
- `(:User)-[:LOGGED]->(:Interaction)`

### INVOLVES

Connects an interaction to the recipient who received resources.

**Properties:**
- None

**Direction:**
- `(:Interaction)-[:INVOLVES]->(:Recipient)`

### PROMOTED

Connects a user who promoted another user to Admin.

**Properties:**
- `timestamp` (datetime): When the promotion occurred

**Direction:**
- `(:User)-[:PROMOTED]->(:User)`

### DEMOTED

Connects a user who voted to demote an Admin.

**Properties:**
- `timestamp` (datetime): When the demotion vote occurred

**Direction:**
- `(:User)-[:DEMOTED]->(:User)`

### COMPLETED

Connects a user to a questionnaire response they submitted.

**Properties:**
- `timestamp` (datetime): When the questionnaire was completed

**Direction:**
- `(:User)-[:COMPLETED]->(:QuestionnaireResponse)`

### ABOUT

Connects a questionnaire response to the recipient it concerns.

**Properties:**
- None

**Direction:**
- `(:QuestionnaireResponse)-[:ABOUT]->(:Recipient)`

## Example Queries

### Get all interactions for a specific recipient

```cypher
MATCH (i:Interaction)-[:INVOLVES]->(r:Recipient {key: $recipient_key})
MATCH (u:User)-[:LOGGED]->(i)
RETURN i.timestamp AS timestamp, i.type AS type, i.notes AS notes, 
       u.username AS logged_by, r.key AS recipient_key, r.pseudonym AS recipient_pseudonym
ORDER BY i.timestamp DESC
```

### Get all questionnaire responses for a recipient

```cypher
MATCH (q:QuestionnaireResponse)-[:ABOUT]->(r:Recipient {key: $recipient_key})
OPTIONAL MATCH (u:User)-[:COMPLETED]->(q)
RETURN q.section AS section, q.responses AS responses, 
       q.created_at AS created_at, q.updated_at AS updated_at,
       u.username AS completed_by
ORDER BY q.created_at DESC
```

### Get user activity statistics

```cypher
MATCH (u:User {username: $username})-[:LOGGED]->(i:Interaction)
RETURN count(i) AS total_interactions,
       count(DISTINCT date(i.timestamp)) AS active_days,
       min(i.timestamp) AS first_interaction,
       max(i.timestamp) AS last_interaction
```

## Database Initialization

When the application is first started, the database is initialized with:

1. Constraints on unique properties
2. The initial Greeter user (username: Hello, password: World!)

The initialization script can be found in `scripts/init-db.cypher`.

## Best Practices

### Working with Timestamps

All timestamps in the database are stored as Neo4j DateTime objects. When retrieving these values, they are converted to Python datetime objects. When storing timestamps, use the Neo4j `datetime()` function to ensure proper formatting.

### Handling JSON Data

For properties that store JSON data (like survey sections and questionnaire responses), the data is stored as serialized JSON strings in Neo4j and automatically converted to/from Python dictionaries when accessed through the GraphDatabase class.

### Recipient Privacy

To maintain recipient privacy:
- Never store personally identifiable information (PII) in the `key` or `pseudonym` fields
- Use non-identifying codes or reference numbers as recipient keys
- Be mindful of what information is included in interaction notes