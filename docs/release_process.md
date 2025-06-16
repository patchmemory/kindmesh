# KindMesh Release Process

This document outlines the process for preparing and executing a release of the KindMesh application.

## Release Preparation

### 1. Version Update

1. Update the version number in the following files:
   - `VERSION` file
   - `app/app.py` (in the docstring)
   - `CHANGELOG.md` (add a new version section)

2. Ensure the version follows [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):
   - MAJOR: Incompatible API changes
   - MINOR: Add functionality in a backward-compatible manner
   - PATCH: Backward-compatible bug fixes

### 2. Update Changelog

1. Add a new section to `CHANGELOG.md` with the new version number and release date
2. Document all significant changes since the last release, categorized as:
   - Added: New features
   - Changed: Changes to existing functionality
   - Deprecated: Features that will be removed in upcoming releases
   - Removed: Features removed in this release
   - Fixed: Bug fixes
   - Security: Security improvements or vulnerability fixes

### 3. Code Freeze

1. Announce a code freeze to all developers
2. No new features should be merged into the main branch during this period
3. Only critical bug fixes should be allowed

### 4. Testing

1. Run all unit tests:
   ```bash
   cd /path/to/kindmesh
   python -m unittest discover tests/unit
   ```

2. Run all integration tests:
   ```bash
   cd /path/to/kindmesh
   python -m unittest discover tests/integration
   ```

3. Perform manual testing of critical user flows:
   - User authentication
   - User creation
   - Interaction logging
   - Data visualization
   - Export functionality

4. Test the application in different environments:
   - Docker deployment
   - Singularity deployment
   - Local installation

### 5. Documentation Review

1. Review and update all documentation:
   - README.md
   - User guides
   - API documentation
   - Installation instructions
   - Troubleshooting guide

2. Ensure all documentation is consistent with the new version

## Release Execution

### 1. Final Commit

1. Create a final commit with all release changes:
   ```bash
   git add VERSION app/app.py CHANGELOG.md
   git commit -m "Prepare release v[VERSION]"
   ```

### 2. Create Release Tag

1. Create a Git tag for the release:
   ```bash
   git tag -a v[VERSION] -m "Release v[VERSION]"
   ```

2. Push the tag to the remote repository:
   ```bash
   git push origin v[VERSION]
   ```

### 3. Build Release Artifacts

1. Build the Docker image:
   ```bash
   docker build -t kindmesh:v[VERSION] .
   ```

2. Build the Singularity container:
   ```bash
   ./singularity_build.sh
   ```

3. Create a release archive:
   ```bash
   git archive --format=zip --output=kindmesh-v[VERSION].zip v[VERSION]
   ```

### 4. Publish Release

1. Create a new release on GitHub:
   - Tag: v[VERSION]
   - Title: KindMesh v[VERSION]
   - Description: Copy the relevant section from CHANGELOG.md
   - Attach the release archive

2. Push the Docker image to a registry (if applicable):
   ```bash
   docker tag kindmesh:v[VERSION] registry.example.com/kindmesh:v[VERSION]
   docker push registry.example.com/kindmesh:v[VERSION]
   ```

### 5. Announce Release

1. Notify all stakeholders about the new release
2. Provide links to:
   - Release notes
   - Installation instructions
   - Upgrade instructions (if applicable)

## Post-Release

### 1. Version Bump

1. Update the version number to the next development version:
   ```bash
   # Example: After releasing 1.0.0, update to 1.1.0-dev
   echo "1.1.0-dev" > VERSION
   ```

2. Update the version in `app/app.py`

3. Commit the changes:
   ```bash
   git add VERSION app/app.py
   git commit -m "Bump version to [NEXT-VERSION]-dev"
   git push origin main
   ```

### 2. Release Retrospective

1. Hold a meeting to discuss:
   - What went well
   - What could be improved
   - Action items for the next release

2. Document the findings for future reference

### 3. Monitoring

1. Monitor the application for any issues after the release
2. Be prepared to release a patch version if critical issues are discovered

## Hotfix Process

If critical issues are discovered after a release:

1. Create a hotfix branch from the release tag:
   ```bash
   git checkout -b hotfix/v[VERSION].1 v[VERSION]
   ```

2. Fix the issue and commit the changes:
   ```bash
   git add [fixed-files]
   git commit -m "Fix [issue description]"
   ```

3. Update the version number and changelog:
   ```bash
   # Update VERSION file
   echo "[VERSION].1" > VERSION
   
   # Update app/app.py
   # Update CHANGELOG.md
   
   git add VERSION app/app.py CHANGELOG.md
   git commit -m "Prepare hotfix v[VERSION].1"
   ```

4. Create a tag for the hotfix:
   ```bash
   git tag -a v[VERSION].1 -m "Hotfix v[VERSION].1"
   git push origin v[VERSION].1
   ```

5. Follow the regular release process for building and publishing

6. Merge the hotfix back to the main branch:
   ```bash
   git checkout main
   git merge hotfix/v[VERSION].1
   git push origin main
   ```