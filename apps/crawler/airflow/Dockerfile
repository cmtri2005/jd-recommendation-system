FROM apache/airflow:2.9.0

# Install Docker client và sudo để có thể chạy docker exec từ Airflow
USER root
RUN apt-get update && \
    apt-get install -y docker.io sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Thêm user airflow vào sudoers (không cần password)
    echo "airflow ALL=(ALL) NOPASSWD: /usr/bin/docker" >> /etc/sudoers && \
    # Tạo docker group và thêm user airflow vào
    groupadd -f -g 999 docker 2>/dev/null || true && \
    usermod -aG docker airflow
USER airflow

# Install Python packages for DAG dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

