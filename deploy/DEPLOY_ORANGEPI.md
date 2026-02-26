# 🍊 Deploy en OrangePi 5 Plus con Cloudflare Tunnel

## Arquitectura
```
Internet → Cloudflare Tunnel → OrangePi 5 Plus (8 cores, 16GB RAM)
                                    ├── Docker Compose
                                    │   ├── neural_saas_app (FastAPI + Streamlit)
                                    │   ├── PostgreSQL
                                    │   └── Redis
                                    └── cloudflared (tunnel)
```

## Beneficios
- ✅ **Cero puertos abiertos** - Cloudflare maneja todo
- ✅ **SSL automático** - Certificados de Cloudflare
- ✅ **DDoS protection** - Incluido gratis
- ✅ **Secretos en systemd** - Fuera del código
- ✅ **Persisten entre reinicios** - Environment files
- ✅ **Hardware aprovechado** - 8 cores ARM para IA

---

## 1. Preparar Secretos (UNA VEZ)

```bash
# Crear directorio de secretos
sudo mkdir -p /etc/neural-saas
sudo chmod 700 /etc/neural-saas

# Generar claves seguras
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_SALT=$(python3 -c "import secrets; print(secrets.token_hex(16))")
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

# Crear archivo de secretos
sudo tee /etc/neural-saas/secrets.env > /dev/null << EOF
# Generado automáticamente - NO COMMITEAR
APP_ENV=production
ENCRYPTION_KEY=${ENCRYPTION_KEY}
ENCRYPTION_SALT=${ENCRYPTION_SALT}
JWT_SECRET_KEY=${JWT_SECRET}
POSTGRES_PASSWORD=${DB_PASSWORD}
DATABASE_URL=postgresql+asyncpg://neural_user:${DB_PASSWORD}@db:5432/neural_saas_db
GEMINI_API_KEY=TU_API_KEY_AQUI
EOF

sudo chmod 600 /etc/neural-saas/secrets.env
```

---

## 2. Archivo docker-compose.prod.yml

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: neural_saas_app
    restart: always
    env_file:
      - /etc/neural-saas/secrets.env
    environment:
      - APP_ENV=production
      - POSTGRES_HOST=db
      - REDIS_HOST=redis
    ports:
      - "127.0.0.1:8501:8501"  # Solo localhost (Cloudflare accede via tunnel)
      - "127.0.0.1:8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '6'      # 6 de 8 cores para la app
          memory: 12G    # 12 de 16GB para la app

  db:
    image: postgres:15-alpine
    container_name: neural_saas_db
    restart: always
    env_file:
      - /etc/neural-saas/secrets.env
    environment:
      - POSTGRES_USER=neural_user
      - POSTGRES_DB=neural_saas_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U neural_user -d neural_saas_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: neural_saas_redis
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

---

## 3. Servicio Systemd

```bash
# /etc/systemd/system/neural-saas.service
sudo tee /etc/systemd/system/neural-saas.service > /dev/null << 'EOF'
[Unit]
Description=Neural SaaS Platform
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/neural-saas
EnvironmentFile=/etc/neural-saas/secrets.env
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
ExecReload=/usr/bin/docker compose -f docker-compose.prod.yml restart

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable neural-saas
```

---

## 4. Cloudflare Tunnel

```bash
# Instalar cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared
sudo mv cloudflared /usr/local/bin/
sudo chmod +x /usr/local/bin/cloudflared

# Autenticar (abre navegador)
cloudflared tunnel login

# Crear tunnel
cloudflared tunnel create neural-saas

# Configurar
sudo mkdir -p /etc/cloudflared
sudo tee /etc/cloudflared/config.yml > /dev/null << EOF
tunnel: neural-saas
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: app.tudominio.com
    service: http://localhost:8501
  - hostname: api.tudominio.com
    service: http://localhost:8000
  - service: http_status:404
EOF

# Instalar como servicio
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

---

## 5. Deploy Completo

```bash
# En tu OrangePi
cd /opt
sudo git clone https://github.com/tu-usuario/neural-saas.git
cd neural-saas

# Copiar compose de producción
sudo cp deploy/docker-compose.prod.yml ./docker-compose.prod.yml

# Iniciar
sudo systemctl start neural-saas

# Verificar
sudo docker compose -f docker-compose.prod.yml logs -f
```

---

## 6. Comandos Útiles

```bash
# Estado
sudo systemctl status neural-saas
sudo systemctl status cloudflared

# Logs
sudo docker compose -f docker-compose.prod.yml logs -f app

# Reiniciar
sudo systemctl restart neural-saas

# Actualizar
cd /opt/neural-saas
sudo git pull
sudo docker compose -f docker-compose.prod.yml build --no-cache
sudo systemctl restart neural-saas

# Backup DB
sudo docker exec neural_saas_db pg_dump -U neural_user neural_saas_db > backup_$(date +%Y%m%d).sql
```

---

## Recursos Estimados (OrangePi 5 Plus)

| Componente | CPU | RAM |
|------------|-----|-----|
| FastAPI + Streamlit | 2-4 cores | 4-8 GB |
| PostgreSQL | 1 core | 1-2 GB |
| Redis | 0.5 core | 512 MB |
| cloudflared | 0.5 core | 256 MB |
| **Total** | ~6 cores | ~10 GB |
| **Disponible** | 2 cores | 6 GB |

✅ Tu OrangePi tiene recursos de sobra para este stack.

---

## Seguridad Checklist

- [ ] Secretos en `/etc/neural-saas/secrets.env` (chmod 600)
- [ ] Puertos solo en localhost (127.0.0.1)
- [ ] Cloudflare Tunnel activo
- [ ] APP_ENV=production
- [ ] Firewall: solo SSH (si es necesario)
- [ ] Backups automáticos de PostgreSQL
