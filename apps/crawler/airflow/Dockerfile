FROM apache/airflow:2.9.0

# Install Docker CLI (latest version) and sudo
USER root
RUN apt-get update && \
    apt-get install -y ca-certificates curl gnupg sudo && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bullseye stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Add airflow user to sudoers (no password required)
    echo "airflow ALL=(ALL) NOPASSWD: /usr/bin/docker" >> /etc/sudoers && \
    # Create docker group and add airflow user
    groupadd -f -g 999 docker 2>/dev/null || true && \
    usermod -aG docker airflow
USER airflow

# Install Python packages for DAG dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
