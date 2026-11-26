# Optional local laboratory. Not a production-hardened deployment.
FROM apache/airflow:3.3.1-python3.12
USER airflow
RUN pip install --no-cache-dir 'pandas>=2.2,<3' 'requests>=2.32,<3' 'duckdb>=1.1,<2'
