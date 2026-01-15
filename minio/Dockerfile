FROM golang:1.25-alpine AS server
RUN go install github.com/minio/minio@latest

FROM minio/mc AS client

FROM alpine:latest AS final

RUN apk add --no-cache wget

COPY --from=server /go/bin/minio /usr/bin/minio
COPY --from=client /usr/bin/mc /usr/bin/mc

COPY create_bucket.sh /usr/bin/create_bucket.sh
RUN chmod +x /usr/bin/create_bucket.sh

ENTRYPOINT ["/usr/bin/create_bucket.sh"]
