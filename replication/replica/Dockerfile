FROM postgres:latest

RUN apt-get update && apt-get install -y gosu && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
CMD ["postgres"]
