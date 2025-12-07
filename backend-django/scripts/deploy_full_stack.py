import paramiko
import time
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

# --- Configurations ---

BACKEND_DOCKERFILE = """
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
# Migrations and collectstatic should ideally be run at container startup, not build
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn openehrcore.wsgi:application --bind 0.0.0.0:8000"]
"""

FRONTEND_DOCKERFILE = """
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""

NGINX_CONF = """
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://django:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /fhir/ {
        proxy_pass http://hapi-fhir:8080/fhir/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Prefix /fhir;
    }
}
"""

DOCKER_COMPOSE_FULL = """
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: openehr_postgres
    environment:
      POSTGRES_DB: hapi_fhir
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_MULTIPLE_DATABASES: keycloak,mattermost
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U postgres -d hapi_fhir" ]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - openehr_network

  hapi-fhir:
    image: hapiproject/hapi:v7.2.0
    container_name: openehr_hapi_fhir
    environment:
      hapi.fhir.fhir_version: R4
      hapi.fhir.validation.enabled: "true"
      hapi.fhir.narrative_enabled: "true"
      server.compression.enabled: "true"
      spring.datasource.url: jdbc:postgresql://postgres:5432/hapi_fhir
      spring.datasource.username: ${POSTGRES_USER}
      spring.datasource.password: ${POSTGRES_PASSWORD}
      spring.datasource.driver-class-name: org.postgresql.Driver
      spring.jpa.database-platform: org.hibernate.dialect.PostgreSQLDialect
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - openehr_network
    restart: unless-stopped

  keycloak:
    image: quay.io/keycloak/keycloak:26.0.0
    container_name: openehr_keycloak
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: ${POSTGRES_USER}
      KC_DB_PASSWORD: ${POSTGRES_PASSWORD}
      KC_HOSTNAME_STRICT: "false"
      KC_PROXY: "edge"
      KC_HTTP_ENABLED: "true"
    ports:
      - "8180:8080"
    depends_on:
      postgres:
        condition: service_healthy
    command: start-dev
    networks:
      - openehr_network
    restart: unless-stopped

  django:
    build:
      context: ../backend-django
      dockerfile: Dockerfile
    container_name: openehr_django
    environment:
      DEBUG: "False"
      ALLOWED_HOSTS: "*"
      CSRF_TRUSTED_ORIGINS: "http://45.151.122.234,http://localhost"
      FHIR_SERVER_URL: http://hapi-fhir:8080/fhir
      KEYCLOAK_URL: http://keycloak:8080
      POSTGRES_NAME: hapi_fhir
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
    ports:
      - "8000:8000"
    depends_on:
      - hapi-fhir
      - keycloak
      - postgres
    networks:
      - openehr_network

  frontend:
    build:
      context: ../frontend-pwa
      dockerfile: Dockerfile
    container_name: openehr_frontend
    ports:
      - "80:80"
    depends_on:
      - django
    networks:
      - openehr_network

  mattermost:
    image: mattermost/mattermost-team-edition:latest
    container_name: mattermost
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    pids_limit: 200
    read_only: false
    tmpfs:
      - /tmp
    volumes:
      - ./volumes/mattermost/config:/mattermost/config:rw
      - ./volumes/mattermost/data:/mattermost/data:rw
      - ./volumes/mattermost/logs:/mattermost/logs:rw
      - ./volumes/mattermost/plugins:/mattermost/plugins:rw
      - ./volumes/mattermost/client/plugins:/mattermost/client/plugins:rw
      - /etc/localtime:/etc/localtime:ro
    environment:
      - MM_SQLSETTINGS_DRIVERNAME=postgres
      - MM_SQLSETTINGS_DATASOURCE=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/mattermost?sslmode=disable&connect_timeout=10
      - MM_BLEVESTTINGS_INDEXDIR=/mattermost/bleve-indexes
      - MM_SERVICESETTINGS_SITEURL=http://localhost:8065
      - MM_SERVICESETTINGS_ALLOWCORSFROM=*
      - MM_SECURITYSETTINGS_CONTENTSECURITYPOLICY=frame-ancestors 'self' http://localhost:5173 http://localhost:3000
    ports:
      - "8065:8065"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - openehr_network

volumes:
  postgres_data:
    driver: local

networks:
  openehr_network:
    driver: bridge
"""

def simple_exec(client, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"Error ({exit_status}): {stderr.read().decode()}")
        return False
    return True

def create_remote_file(client, path, content):
    print(f"Creating file: {path}")
    sftp = client.open_sftp()
    with sftp.file(path, 'w') as f:
        f.write(content)
    sftp.close()

def deploy_full():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS)
        print("Connected.")
        
        # 1. Write Backend Dockerfile
        create_remote_file(client, "/opt/openehrcore/backend-django/Dockerfile", BACKEND_DOCKERFILE)
        
        # 2. Write Frontend Dockerfile and Nginx Config
        create_remote_file(client, "/opt/openehrcore/frontend-pwa/Dockerfile", FRONTEND_DOCKERFILE)
        create_remote_file(client, "/opt/openehrcore/frontend-pwa/nginx.conf", NGINX_CONF)
        
        # 3. Overwrite docker-compose.yml
        create_remote_file(client, "/opt/openehrcore/docker/docker-compose.yml", DOCKER_COMPOSE_FULL)
        
        # 4. Pull/Build and Up
        print("Starting deploy (Build may take a few minutes)...")
        # Ensure .env is loaded
        deploy_cmd = "cd /opt/openehrcore && docker compose --env-file .env -f docker/docker-compose.yml up -d --build"
        
        # Stream output
        stdin, stdout, stderr = client.exec_command(deploy_cmd)
        
        while not stdout.channel.exit_status_ready():
            time.sleep(1)
            
        if stdout.channel.recv_exit_status() != 0:
            print("Deploy Failed:")
            print(stderr.read().decode())
        else:
            print("Deploy Successful!")
            print(stdout.read().decode())
            
        print("\nChecking containers...")
        _, stdout, _ = client.exec_command("docker ps")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    deploy_full()
