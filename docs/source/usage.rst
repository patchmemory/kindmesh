Usage
=====

This guide provides instructions for using the kindmesh application.

Running the Application
----------------------

After installation, you can run the application using:

.. code-block:: bash

    # Start Neo4j database (required)
    # See Installation guide for Neo4j setup instructions

    # Run the application
    kindmesh

Or run directly with Python:

.. code-block:: bash

    python -m kindmesh.app

Using the Local Start Script
---------------------------

If you used the setup script, you can start the application with:

.. code-block:: bash

    ./local_start.sh

User Roles
---------

kindmesh has three user roles:

1. **Greeter**: Can create new users
2. **Friend**: Can log interactions and complete surveys
3. **Admin**: Has full access to all features

Logging In
---------

1. Open the application in your web browser
2. Enter your username and password
3. Click "Login"

Logging Interactions
------------------

To log a resource distribution:

1. Navigate to the "Log Interaction" tab
2. Select a recipient or create a new one
3. Select the resource type
4. Add any notes
5. Click "Log Interaction"

Managing Recipients
-----------------

To manage recipients:

1. Navigate to the "Manage Recipients" tab
2. To create a new recipient:
   - Enter a unique key
   - Optionally enter a pseudonym
   - Click "Create Recipient"
3. To view recipient details:
   - Select a recipient from the dropdown
   - View their details, survey responses, and interaction history

Completing Surveys
----------------

To complete a survey for a recipient:

1. Navigate to the "Log Survey" tab
2. Select a recipient
3. Select a survey
4. Complete the survey sections
5. Click "Submit Survey"

Viewing Data
----------

To view data and statistics:

1. Navigate to the "View Data" tab
2. View summary statistics and recent interactions
3. Administrators can see more detailed statistics and export data

User Management (Admin Only)
--------------------------

Administrators can manage users:

1. Navigate to the "Manage Users" tab
2. View all users
3. Promote users to Admin
4. Demote Admins to Friend (requires multiple votes)
5. Delete users
6. Create new users with specific roles