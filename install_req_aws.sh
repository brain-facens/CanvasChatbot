pip install \
--platform manylinux2014_aarch64 \
--target=package \
--implementation cp \
--python-version 3.12 \
--only-binary=:all: --upgrade \
requests psycopg2-binary