FROM golang:1.25-alpine AS server
RUN go install github.com/minio/minio@latest

FROM minio/mc AS client

FROM alpine:latest AS final

# Install wget for healthcheck
RUN apk add --no-cache wget

# Copy binaries
COPY --from=server /go/bin/minio /usr/bin/minio
COPY --from=client /usr/bin/mc /usr/bin/mc
#COPY --from=client /etc/ssl/certs/ /etc/ssl/certs/

# Copy the script
COPY create_bucket.sh /usr/bin/create_bucket.sh
RUN chmod +x /usr/bin/create_bucket.sh

# ENTRYPOINT executes the script
ENTRYPOINT ["/usr/bin/create_bucket.sh"]
