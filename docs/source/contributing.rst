Contributing
===========

Thank you for considering contributing to kindmesh! This document provides guidelines for contributing to the project.

Code of Conduct
--------------

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

Getting Started
--------------

1. Fork the repository on GitHub
2. Clone your fork locally:

   .. code-block:: bash

       git clone https://github.com/yourusername/kindmesh.git
       cd kindmesh

3. Set up the development environment:

   .. code-block:: bash

       ./local_setup.sh

4. Install development dependencies:

   .. code-block:: bash

       pip install -r requirements-dev.txt

Development Workflow
------------------

1. Create a branch for your changes:

   .. code-block:: bash

       git checkout -b feature/your-feature-name

2. Make your changes
3. Run the tests to ensure your changes don't break existing functionality:

   .. code-block:: bash

       pytest

4. Format your code:

   .. code-block:: bash

       black kindmesh tests
       isort kindmesh tests

5. Run linting:

   .. code-block:: bash

       flake8 kindmesh tests

6. Commit your changes:

   .. code-block:: bash

       git add .
       git commit -m "Add your descriptive commit message here"

7. Push to your fork:

   .. code-block:: bash

       git push origin feature/your-feature-name

8. Submit a pull request through the GitHub website

Pull Request Guidelines
---------------------

1. Include tests for any new functionality
2. Update documentation for any changed functionality
3. Ensure all tests pass
4. Follow the code style of the project
5. Keep pull requests focused on a single topic

Testing
------

We use pytest for testing. To run the tests:

.. code-block:: bash

    pytest

To run tests with coverage:

.. code-block:: bash

    pytest --cov=kindmesh

Documentation
------------

We use Sphinx for documentation. To build the documentation:

.. code-block:: bash

    cd docs
    make html

The documentation will be built in ``docs/build/html``.

Versioning
---------

We use semantic versioning. Please ensure that version numbers are updated appropriately when making changes.