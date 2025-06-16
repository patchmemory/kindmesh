# KindMesh Backup and Recovery Guide

This guide provides instructions for backing up and restoring the Neo4j database used by KindMesh.

## Backup Procedures

### Automated Backups

For production environments, it's recommended to set up automated backups using the following approach:

#### 1. Create a Backup Script

Create a file named `backup_neo4j.sh` with the following content:

```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/path/to/backups"
CONTAINER_NAME="kindmesh-neo4j-1"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILENAME="neo4j_backup_${DATE}.dump"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create backup
echo "Creating Neo4j backup: $BACKUP_FILENAME"
docker exec $CONTAINER_NAME neo4j-admin dump --database=neo4j --to=/tmp/$BACKUP_FILENAME

# Copy backup from container to host
echo "Copying backup to host"
docker cp $CONTAINER_NAME:/tmp/$BACKUP_FILENAME $BACKUP_DIR/

# Remove backup from container
docker exec $CONTAINER_NAME rm /tmp/$BACKUP_FILENAME

# Rotate backups (keep last 7 daily backups)
echo "Rotating backups"
ls -tp $BACKUP_DIR/neo4j_backup_* | grep -v '/$' | tail -n +8 | xargs -I {} rm -- {}

echo "Backup completed: $BACKUP_DIR/$BACKUP_FILENAME"
```

Make the script executable:

```bash
chmod +x backup_neo4j.sh
```

#### 2. Schedule Regular Backups

Add the script to crontab to run daily:

```bash
crontab -e
```

Add the following line to run the backup daily at 2 AM:

```
0 2 * * * /path/to/backup_neo4j.sh >> /path/to/backup.log 2>&1
```

### Manual Backups

You can also create manual backups when needed:

1. **Using Neo4j Admin Tool**:

   ```bash
   docker exec kindmesh-neo4j-1 neo4j-admin dump --database=neo4j --to=/tmp/neo4j_backup.dump
   docker cp kindmesh-neo4j-1:/tmp/neo4j_backup.dump /path/to/save/backup/
   ```

2. **Using Docker Volume Backup**:

   ```bash
   docker run --rm -v kindmesh_neo4j_data:/data -v $(pwd):/backup alpine tar -czf /backup/neo4j_data_backup.tar.gz /data
   ```

## Recovery Procedures

### Restoring from a Backup

#### 1. Using Neo4j Admin Tool

1. Stop the Neo4j container:

   ```bash
   docker-compose stop neo4j
   ```

2. Copy the backup file to the container:

   ```bash
   docker cp /path/to/backup/neo4j_backup.dump kindmesh-neo4j-1:/tmp/
   ```

3. Restore the database:

   ```bash
   docker exec kindmesh-neo4j-1 neo4j-admin load --database=neo4j --from=/tmp/neo4j_backup.dump --force
   ```

4. Start the Neo4j container:

   ```bash
   docker-compose start neo4j
   ```

#### 2. Restoring from a Volume Backup

1. Stop all containers:

   ```bash
   docker-compose down
   ```

2. Remove the existing volume:

   ```bash
   docker volume rm kindmesh_neo4j_data
   ```

3. Create a new volume:

   ```bash
   docker volume create kindmesh_neo4j_data
   ```

4. Restore from the backup:

   ```bash
   docker run --rm -v kindmesh_neo4j_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar -xzf /backup/neo4j_data_backup.tar.gz --strip 1"
   ```

5. Start the containers:

   ```bash
   docker-compose up -d
   ```

## Disaster Recovery Plan

### 1. Preparation

- Maintain regular backups as described above
- Store backups in multiple locations (local and remote)
- Document the recovery procedures and test them regularly
- Keep a copy of the docker-compose.yml file and environment variables

### 2. Recovery Steps

In case of a complete system failure:

1. Set up a new server with Docker and Docker Compose
2. Clone the KindMesh repository
3. Copy the most recent backup to the new server
4. Follow the restoration procedures above
5. Verify the application is working correctly

### 3. Verification

After recovery, verify the system by:

1. Checking that all users can log in
2. Verifying that all data is accessible
3. Testing key functionality (logging interactions, viewing data, etc.)

## Best Practices

1. **Regular Testing**: Test the backup and recovery procedures regularly to ensure they work as expected.

2. **Off-site Storage**: Store backups in multiple locations, including off-site or cloud storage.

3. **Encryption**: Consider encrypting sensitive backup data, especially if stored off-site.

4. **Documentation**: Keep this guide updated with any changes to the backup or recovery procedures.

5. **Monitoring**: Set up monitoring to alert you if backups fail or are not created as scheduled.