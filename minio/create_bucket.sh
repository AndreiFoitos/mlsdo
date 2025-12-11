#!/bin/sh

# 1. Start MinIO in the background
minio server /data --console-address ":9001" --address ":9000" &

# 2. Wait for MinIO to start
echo "Waiting for MinIO to start..."
until wget --no-verbose --tries=1 --spider http://localhost:9000/minio/health/live; do
    sleep 1
done

# 3. Configure Client
# We login as the root user (minio) to perform admin tasks
mc alias set local http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

# 4. Create the 'mlflow' user and attach the base policy
# (Tutorial Step: Create user and policy)
echo "Setting up mlflow user..."
mc admin policy create local mlflow-base /policies/mlflow-base-access.json
mc admin user add local mlflow mlflowpass
mc admin policy attach local mlflow-base --user mlflow

# 5. Create the Service Account with FIXED keys
# (Tutorial Step: Create service account)
# We remove it first to ensure idempotency (if you restart the container)
echo "Setting up Service Account..."
mc admin user svcacct rm local mlflow_access_key 2>/dev/null || true

mc admin user svcacct add \
    --access-key "mlflow_access_key" \
    --secret-key "mlflow_secret_key" \
    --policy /policies/mlflow-store-access.json \
    local mlflow

# 6. Create the Bucket
echo "Creating bucket..."
mc mb --ignore-existing local/mlflow-artefact-store

# 7. Keep container running
wait
