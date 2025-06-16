# kindmesh

A lightweight, secure, browser-based app for a small nonprofit that distributes resources to people in need.

## Overview

kindmesh is a simple application that allows nonprofit organizations to:

- Track semi-anonymous interactions where community members receive aid (e.g., food, services)
- Avoid personal identifiers unless explicitly added, instead using key-based lookups or pseudonyms
- Log what was accessed, by whom (by key), and when

## System Architecture

The application consists of:

- **Neo4j Community Edition** (Dockerized) as a backend graph database, with APOC libraries installed
- **Streamlit** frontend for data entry and visualization
- A simple role-based login system, integrated directly into the Neo4j graph

### Data Model

The Neo4j graph database uses the following schema:

- `(User {username, password_hash, role})`: Represents system users
- `(Interaction {timestamp, type, notes})`: Represents resource distribution events
- `(Recipient {key, pseudonym})`: Represents recipients of resources (semi-anonymous)
- Relationships:
  - `(:User)-[:CREATED]->(:User)`: Tracks user creation
  - `(:User)-[:LOGGED]->(:Interaction)`: Tracks who logged an interaction
  - `(:Interaction)-[:INVOLVES]->(:Recipient)`: Links interactions to recipients
  - `(:User)-[:PROMOTED]->(:User)`: Tracks admin promotions
  - `(:User)-[:DEMOTED]->(:User)`: Tracks admin demotions

## Role-Based Access

The system has three roles:

1. **Greeter**: The initial user (username: Hello, password: World!) who can only create new users
2. **Admin**: Users who can manage other users, log interactions, and export data
3. **Friend**: Regular users who can log interactions and view basic data

The first user created after the Greeter automatically becomes an Admin. All subsequent users default to the Friend role unless explicitly promoted.

## Setup Instructions

There are two ways to run kindmesh:
1. Using Docker (recommended for most users)
2. Local installation (for development or if Docker is not available)

### Option 1: Using Docker (Recommended)

#### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (version 19.03 or later)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 1.27 or later)
- Git (for cloning the repository)

#### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/kindmesh.git
   cd kindmesh
   ```

2. You can start the application in one of two ways:

   **Option A: Using the provided scripts (recommended for first-time users)**

   Make the startup scripts executable:
   ```
   chmod +x start.sh stop.sh
   ```

   Start the application using the provided script:
   ```
   ./start.sh
   ```
   This script will:
   - Check if Docker and Docker Compose are installed
   - Start the Neo4j database and Streamlit application
   - Provide instructions for accessing the application

   **Option B: Using Docker Compose directly**

   Start the Neo4j database and Streamlit application:
   ```
   docker compose up -d
   ```
   This command starts all services defined in the docker-compose.yml file in detached mode.

3. Access the application:
   - Open your browser and navigate to `http://localhost:8501`
   - Log in with the default credentials:
     - Username: `Hello`
     - Password: `World!`

5. Create your first user:
   - This user will automatically become an Admin
   - Use this Admin account to create additional users

#### Stopping the Application

You can stop the application in one of two ways:

**Option A: Using the provided script**
```
./stop.sh
```

**Option B: Using Docker Compose directly**
```
docker compose down
```

To stop and remove all data (including the database), run:
```
docker compose down -v
```

### Option 3: Local Installation

#### Prerequisites

- Python 3.12 or later (required for latest Streamlit features)
- pip (Python package manager)
- Neo4j Community Edition (installed separately)

### Option 2: Using Singularity

Singularity is a container platform designed for scientific computing and high-performance computing (HPC) environments. This option is useful for users who need to run Neo4j in environments where Docker is not available or not allowed.

#### Prerequisites

- [Singularity](https://sylabs.io/guides/latest/user-guide/quick_start.html) (version 3.5 or later)
- Git (for cloning the repository)

#### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/kindmesh.git
   cd kindmesh
   ```

2. Make the Singularity scripts executable:
   ```
   chmod +x singularity_build.sh singularity_start.sh
   ```

3. Build the Singularity container:
   ```
   ./singularity_build.sh
   ```
   This script will:
   - Check if Singularity is installed
   - Build a Singularity container for Neo4j based on the neo4j.def definition file

4. Start the Neo4j Singularity container:
   ```
   ./singularity_start.sh
   ```
   This script will:
   - Check if the Singularity container exists
   - Create directories for data persistence
   - Start the container with the appropriate bind mounts
   - Provide instructions for accessing Neo4j

5. Access Neo4j:
   - Open your browser and navigate to `http://localhost:7474`
   - Log in with the default credentials:
     - Username: `neo4j`
     - Password: `kindmesh`

6. Start the Streamlit application separately:
   ```
   ./local_setup.sh
   ./local_start.sh
   ```
   This will set up the Python environment and start the Streamlit application.

#### Stopping the Container

To stop the Singularity container, run:
```
singularity instance stop neo4j
```

### Option 3: Local Installation

#### Prerequisites

- Python 3.12 or later (required for latest Streamlit features)
- pip (Python package manager)
- Neo4j Community Edition (installed separately)

#### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/kindmesh.git
   cd kindmesh
   ```

2. Make the setup scripts executable:
   ```
   chmod +x local_setup.sh local_start.sh
   ```

3. Run the setup script to create a virtual environment and install dependencies:
   ```
   ./local_setup.sh
   ```

   If you encounter any package compatibility issues, you can run the setup script with the clean option:
   ```
   ./local_setup.sh --clean
   ```
   This will remove the existing virtual environment and create a fresh one.

4. Install and configure Neo4j:
   - Download and install [Neo4j Community Edition](https://neo4j.com/download/)
   - Set the Neo4j password to `kindmesh`
   - Install APOC libraries for Neo4j
   - Run the initialization script in `scripts/init-db.cypher`

5. Start the application:
   ```
   ./local_start.sh
   ```

6. Access the application:
   - Open your browser and navigate to `http://localhost:8501`
   - Log in with the default credentials:
     - Username: `Hello`
     - Password: `World!`

#### Stopping the Application

To stop the locally running application, press `Ctrl+C` in the terminal where it's running.

## Usage Guide

### Initial Login

1. Log in with the default Greeter account:
   - Username: `Hello`
   - Password: `World!`
2. Create your first user (will automatically become an Admin)
3. Log out and log in with your new Admin account

### Admin Functions

As an Admin, you can:

1. **Manage Users**:
   - Create new users (Friend or Admin role)
   - Promote Friends to Admins
   - Demote Admins to Friends (requires at least 2 Admins to confirm)

2. **Log Interactions**:
   - Record resource distributions using recipient keys
   - Optionally add pseudonyms for recipients
   - Specify the type of resource and add notes

3. **View Data**:
   - See summary statistics
   - View recent interactions
   - Analyze resource distribution by type

4. **Export Data**:
   - Download interaction data as CSV or JSON
   - Use for reporting or further analysis

### Friend Functions

As a Friend, you can:

1. **Log Interactions**:
   - Record resource distributions
   - Add notes and recipient information

2. **View Basic Data**:
   - See summary statistics
   - View recent interactions

3. **Batch Entry**:
   - Import multiple interactions from a spreadsheet
   - Automatically detect sections in the spreadsheet
   - Select which sections to import
   - Map spreadsheet columns to required fields
   - Process and import data in bulk

4. **Whole Person Approach Questionnaire**:
   - Complete comprehensive assessments for recipients
   - Track needs across multiple life domains
   - Save and resume questionnaires
   - View summary of completed assessments

## Batch Entry Guide

The Batch Entry feature allows Friends to import multiple interactions from a spreadsheet. This is useful for organizations that collect data in spreadsheets before entering it into kindmesh.

### Supported Spreadsheet Formats

- Excel (.xlsx, .xls)
- CSV (.csv)

### Expected Spreadsheet Structure

The spreadsheet can have multiple sections, each with its own set of columns. A typical spreadsheet might include:

1. **Main section** with columns like:
   - ID # (used as Recipient Key)
   - Name (can be used as Recipient Pseudonym)
   - Date
   - Agency
   - Additional Family
   - Address
   - City
   - Phone #
   - Referrals
   - Notes

2. **Special sections** that start with keywords like:
   - "Yearly Follow-Up Calls"
   - "Pledge Letters"
   - "Additional Notes"
   - Rows starting with "Update:" or "Referred:"

### Using the Batch Entry Feature

1. Navigate to the "Batch Entry" tab in the Friend interface
2. Upload your spreadsheet using the file uploader
3. Review the preview of your data
4. The system will automatically detect sections in your spreadsheet
5. Select which sections you want to import
6. For each selected section:
   - Map the columns to the required fields (Recipient Key is required)
   - Set a default Interaction Type if not mapped to a column
7. Click "Process and Import Data" to start the import
8. Review the results, including the number of successfully imported interactions and any errors

### Tips for Successful Imports

- Make sure your spreadsheet has a column that can be used as a Recipient Key
- If your spreadsheet has multiple sections, make sure they're clearly separated
- For sections with only a few rows, you can still import them by mapping the relevant columns
- If you encounter errors, check the error messages for specific information about what went wrong

## Whole Person Approach Questionnaire Guide

The Whole Person Approach Questionnaire feature allows Friends to conduct comprehensive assessments of recipients' needs across multiple life domains. This feature implements the holistic intake process described in the organization's approach to helping individuals and families.

### Questionnaire Sections

The questionnaire is divided into the following sections, based on the social determinants of health:

1. **Financial Assessment**
   - Ability to pay bills
   - Utility service status

2. **Employment Assessment**
   - Current employment status
   - Education level

3. **Transportation Assessment**
   - Access to transportation for medical appointments
   - Impact of transportation limitations

4. **Food, Clothing, and Furniture Assessment**
   - Food security
   - Resource sustainability

5. **Child Care, Elder Care, Sick Spouse or Partner Assessment**
   - Challenges with dependent care

6. **Medical and Dental Care Assessment**
   - Persistent pain or illness
   - Access to healthcare

7. **Federal and State Benefits Assessment**
   - Veteran status
   - Assistance program participation

8. **Mental Health Assessment**
   - Psychological symptoms
   - Emotional well-being

9. **Housing/Safe Shelter Assessment**
   - Housing stability
   - Living conditions

10. **Legal Services Assessment**
    - Legal needs across various domains

11. **Relationships Assessment**
    - Family dynamics
    - Safety concerns

12. **Community Involvement Assessment**
    - Participation in community activities

13. **Mentor Assessment**
    - Support network

14. **Spiritual Focused Care Assessment**
    - Spiritual support resources

### Using the Questionnaire Feature

1. Navigate to the "Questionnaire" tab in the Friend interface
2. Enter the recipient's key identifier (required) and optional pseudonym
3. If the recipient has existing questionnaire responses, you can view or edit them
4. Complete each section of the questionnaire, saving as you go
5. Navigate between sections using the "Back" and "Continue" buttons
6. At any point, you can save your progress without moving to the next section
7. After completing all sections, you'll see a summary of all completed assessments
8. From the summary page, you can start a new questionnaire or edit the current one

### Tips for Effective Assessments

- Complete all sections for a comprehensive view of the recipient's needs
- Pay special attention to sections where the recipient indicates significant challenges
- Use the questionnaire as a starting point for developing a holistic assistance plan
- Review previous questionnaire responses to track changes over time
- Consider the interconnections between different life domains when planning assistance

## Security Considerations

- Passwords are hashed using bcrypt
- No personal identifiers are required for recipients
- The application runs in a containerized environment
- Role-based access control limits user capabilities

## Development

### Project Structure

```
kindmesh/
├── app/
│   ├── app.py              # Main Streamlit application
│   └── utils/
│       └── graph.py        # Neo4j database interaction module
├── scripts/
│   ├── init-db.cypher      # Database initialization script
│   ├── generate_password_hash.py  # Utility to generate password hashes
│   └── test_setup.sh       # Test script for Docker setup
├── start.sh                # Script to start the application with Docker
├── stop.sh                 # Script to stop the Docker containers
├── local_setup.sh          # Script to set up local development environment
├── local_start.sh          # Script to start the application locally
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Application container definition
├── requirements.txt        # Python dependencies
└── README.md               # This documentation
```

### Extending the Application

To add new features:

1. Modify `app/utils/graph.py` to add new database interactions
2. Update `app/app.py` to add new UI components
3. Rebuild the Docker containers:
   ```
   docker-compose up -d --build
   ```

## Troubleshooting

### Common Issues

1. **Can't connect to Neo4j**:
   - Ensure the Neo4j container is running: `docker ps`
   - Check Neo4j logs: `docker-compose logs neo4j`

2. **Login issues**:
   - Verify you're using the correct credentials
   - Check if the database was initialized properly

3. **Data not showing up**:
   - Ensure interactions are being logged correctly
   - Check database connection in the application logs

4. **Package compatibility issues**:
   - If you see errors like `numpy.dtype size changed, may indicate binary incompatibility`, run:
     ```
     ./local_setup.sh --clean
     ```
   - This error typically occurs when there's a mismatch between numpy and pandas versions
   - The clean option will create a fresh virtual environment with compatible package versions

5. **Missing Altair module error**:
   - If you see an error like `ModuleNotFoundError: No module named 'altair.vegalite.v4'`, run:
     ```
     ./local_setup.sh --clean
     ```
   - This error occurs because Streamlit requires a specific version of Altair (4.2.0)
   - The clean option will ensure all dependencies are correctly installed

6. **Streamlit cache_resource error**:
   - If you see an error like `AttributeError: module 'streamlit' has no attribute 'cache_resource'`, this is because the application is using Streamlit 1.15.1 which doesn't support this feature
   - The application has been updated to use Streamlit 1.32.0 which supports `st.cache_resource`
   - If you're still seeing this error, make sure you're using the latest version of the code and have updated your dependencies with `pip install -r requirements.txt`

7. **Neo4j GraphDatabase name conflict error**:
   - If you see an error like `AttributeError: type object 'GraphDatabase' has no attribute 'driver'`, this is due to a name conflict between the imported Neo4j GraphDatabase class and the custom GraphDatabase class
   - The application has been updated to use an alias for the imported class to avoid this conflict
   - If you're still seeing this error, make sure you're using the latest version of the code

8. **Coroutine 'expire_cache' was never awaited warning**:
   - If you see a warning like `RuntimeWarning: coroutine 'expire_cache' was never awaited`, this is related to how Streamlit handles cache expiration
   - The application has been updated to include a TTL (Time To Live) parameter for the cache_resource decorator and to enable tracemalloc for better debugging
   - These changes should resolve the warning and improve cache handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Neo4j for the graph database
- Streamlit for the web interface
- The nonprofit community for their valuable feedback
