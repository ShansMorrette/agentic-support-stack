#!/bin/bash
# setup-orangepi.sh
# Script de setup para OrangePi 5 Plus con Cloudflare Tunnel
# Ejecutar como root: sudo bash setup-orangepi.sh

set -e

echo "🍊 Neural SaaS - Setup para OrangePi 5 Plus"
echo "============================================"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Ejecutar como root: sudo bash setup-orangepi.sh${NC}"
    exit 1
fi

# 1. Crear directorio de secretos
echo -e "\n${YELLOW}📁 Creando directorio de secretos...${NC}"
mkdir -p /etc/neural-saas
chmod 700 /etc/neural-saas

# 2. Generar claves seguras
echo -e "${YELLOW}🔐 Generando claves de encriptación...${NC}"
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_SALT=$(python3 -c "import secrets; print(secrets.token_hex(16))")
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

# 3. Solicitar API Key de Gemini
echo -e "\n${YELLOW}🔑 Ingresa tu GEMINI_API_KEY:${NC}"
read -r GEMINI_KEY

if [ -z "$GEMINI_KEY" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY es requerida${NC}"
    exit 1
fi

# 4. Crear archivo de secretos
echo -e "${YELLOW}📝 Creando archivo de secretos...${NC}"
cat > /etc/neural-saas/secrets.env << EOF
# Neural SaaS - Secretos de Producción
# Generado: $(date)
# ⚠️ NO COMMITEAR ESTE ARCHIVO

APP_ENV=production

# Encriptación
ENCRYPTION_KEY=${ENCRYPTION_KEY}
ENCRYPTION_SALT=${ENCRYPTION_SALT}

# JWT
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Base de datos PostgreSQL
POSTGRES_USER=neural_user
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=neural_saas_db
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://neural_user:${DB_PASSWORD}@db:5432/neural_saas_db

# Gemini API
GEMINI_API_KEY=${GEMINI_KEY}
GEMINI_MODEL=gemini-2.5-flash

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# CORS (ajustar según tu dominio)
ALLOWED_ORIGINS=https://app.tudominio.com,https://api.tudominio.com
EOF

chmod 600 /etc/neural-saas/secrets.env
echo -e "${GREEN}✅ Secretos guardados en /etc/neural-saas/secrets.env${NC}"

# 5. Crear directorio de la aplicación
echo -e "\n${YELLOW}📂 Preparando directorio de aplicación...${NC}"
mkdir -p /opt/neural-saas
mkdir -p /opt/neural-saas/backups

# 6. Crear servicio systemd
echo -e "${YELLOW}⚙️ Creando servicio systemd...${NC}"
cat > /etc/systemd/system/neural-saas.service << 'EOF'
[Unit]
Description=Neural SaaS Platform
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/neural-saas
EnvironmentFile=/etc/neural-saas/secrets.env
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d --build
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
ExecReload=/usr/bin/docker compose -f docker-compose.prod.yml restart

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable neural-saas
echo -e "${GREEN}✅ Servicio neural-saas habilitado${NC}"

# 7. Crear script de backup
echo -e "${YELLOW}💾 Creando script de backup...${NC}"
cat > /opt/neural-saas/backup.sh << 'EOF'
#!/bin/bash
# Backup diario de PostgreSQL
BACKUP_DIR="/opt/neural-saas/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker exec neural_saas_db pg_dump -U neural_user neural_saas_db > "${BACKUP_DIR}/backup_${DATE}.sql"
# Mantener solo últimos 7 días
find ${BACKUP_DIR} -name "backup_*.sql" -mtime +7 -delete
echo "Backup completado: backup_${DATE}.sql"
EOF
chmod +x /opt/neural-saas/backup.sh

# Agregar cron para backup diario a las 3am
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/neural-saas/backup.sh >> /var/log/neural-saas-backup.log 2>&1") | crontab -
echo -e "${GREEN}✅ Backup diario configurado (3:00 AM)${NC}"

# 8. Resumen
echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Setup completado!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "📋 ${YELLOW}Próximos pasos:${NC}"
echo ""
echo "1. Clonar el repositorio:"
echo "   cd /opt/neural-saas"
echo "   git clone https://github.com/tu-usuario/neural-saas.git ."
echo ""
echo "2. Copiar docker-compose de producción:"
echo "   cp deploy/docker-compose.prod.yml ."
echo ""
echo "3. Iniciar la aplicación:"
echo "   systemctl start neural-saas"
echo ""
echo "4. Configurar Cloudflare Tunnel:"
echo "   cloudflared tunnel login"
echo "   cloudflared tunnel create neural-saas"
echo ""
echo -e "📁 ${YELLOW}Archivos creados:${NC}"
echo "   /etc/neural-saas/secrets.env (secretos)"
echo "   /etc/systemd/system/neural-saas.service"
echo "   /opt/neural-saas/backup.sh"
echo ""
echo -e "🔐 ${RED}IMPORTANTE: Guarda estas claves en un lugar seguro${NC}"
echo "   ENCRYPTION_KEY: ${ENCRYPTION_KEY:0:20}..."
echo "   JWT_SECRET: ${JWT_SECRET:0:20}..."
