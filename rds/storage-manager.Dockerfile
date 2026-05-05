FROM alpine:latest
RUN apk update && apk add --no-cache util-linux e2fsprogs e2fsprogs-extra
ENTRYPOINT ["sh", "/scripts/storage-manager.sh"]
