ARG image
FROM $image

ARG app_root
ARG redis_data_dir

ENV REDIS_DATA_DIR=$redis_data_dir

EXPOSE 6379
EXPOSE 8001

COPY stack.conf /redis-stack.conf

CMD ["redis-server"]
