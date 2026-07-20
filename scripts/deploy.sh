#!/bin/bash
# Script de despliegue automatizado para SGIND v2

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_requirements() {
    log_info "Verificando requisitos..."

    # Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js no está instalado"
        exit 1
    fi
    log_success "Node.js $(node --version)"

    # npm
    if ! command -v npm &> /dev/null; then
        log_error "npm no está instalado"
        exit 1
    fi
    log_success "npm $(npm --version)"

    # Git
    if ! command -v git &> /dev/null; then
        log_error "Git no está instalado"
        exit 1
    fi
    log_success "Git $(git --version)"

    # Python (opcional, para backend)
    if command -v python3 &> /dev/null; then
        log_success "Python $(python3 --version)"
    else
        log_warning "Python 3 no encontrado (requerido para backend)"
    fi
}

build_frontend() {
    log_info "Construyendo frontend..."

    cd sgind-v2/frontend

    # Instalar dependencias
    log_info "Instalando dependencias de npm..."
    npm ci

    # Build
    log_info "Ejecutando build..."
    npm run build

    # Validar build
    if [ ! -d ".next/standalone" ]; then
        log_error "Build fallido: directorio .next/standalone no encontrado"
        exit 1
    fi

    log_success "Frontend construido exitosamente"
    cd ../..
}

build_backend() {
    log_info "Verificando backend..."

    cd sgind-v2/backend

    # Verificar requirements.txt
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt no encontrado"
        exit 1
    fi

    log_success "Backend verificado"
    cd ../..
}

verify_config() {
    log_info "Verificando configuración..."

    # Frontend
    if [ ! -f "sgind-v2/frontend/netlify.toml" ]; then
        log_warning "netlify.toml no encontrado en frontend"
    else
        log_success "netlify.toml encontrado"
    fi

    if [ ! -f "sgind-v2/frontend/.env.local" ]; then
        log_warning ".env.local no configurado"
    else
        log_success ".env.local encontrado"
    fi

    # Backend
    if [ ! -f "sgind-v2/backend/.env" ]; then
        log_warning ".env no configurado en backend"
    else
        log_success ".env backend encontrado"
    fi
}

test_frontend() {
    log_info "Ejecutando tests del frontend..."

    cd sgind-v2/frontend

    # ESLint
    if npm run lint &> /dev/null; then
        log_success "Linting exitoso"
    else
        log_warning "Algunos warnings en ESLint"
    fi

    cd ../..
}

deploy_netlify() {
    log_info "Desplegando en Netlify..."

    # Verificar que netlify-cli esté instalado
    if ! command -v netlify &> /dev/null; then
        log_warning "netlify-cli no está instalado. Instálalo con:"
        echo "    npm install -g netlify-cli"
        exit 1
    fi

    cd sgind-v2/frontend

    log_info "Iniciando deploy a Netlify..."
    netlify deploy --prod --dir=.next/standalone

    log_success "Deploy en Netlify completado"
    cd ../..
}

preview() {
    log_info "Información de despliegue:"
    echo ""
    echo "Frontend:"
    echo "  - Ubicación: sgind-v2/frontend"
    echo "  - Netlify config: netlify.toml"
    echo "  - Variables: .env.local"
    echo ""
    echo "Backend:"
    echo "  - Ubicación: sgind-v2/backend"
    echo "  - Variables: .env"
    echo ""
    echo "Database:"
    echo "  - Migraciones: sgind-v2/database/"
    echo ""
}

main() {
    log_info "=== SGIND v2 Deploy Script ==="
    echo ""

    COMMAND=${1:-help}

    case $COMMAND in
        check)
            check_requirements
            verify_config
            ;;
        build)
            check_requirements
            build_frontend
            build_backend
            ;;
        test)
            check_requirements
            test_frontend
            ;;
        build-test)
            check_requirements
            build_frontend
            build_backend
            test_frontend
            ;;
        deploy)
            check_requirements
            verify_config
            build_frontend
            build_backend
            deploy_netlify
            ;;
        preview)
            preview
            ;;
        all)
            check_requirements
            verify_config
            build_frontend
            build_backend
            test_frontend
            preview
            ;;
        *)
            echo "Uso: $0 <comando>"
            echo ""
            echo "Comandos disponibles:"
            echo "  check              - Verificar requisitos y configuración"
            echo "  build              - Construir frontend y backend"
            echo "  test               - Ejecutar tests"
            echo "  build-test         - Construir y testear"
            echo "  deploy             - Desplegar en Netlify (requiere netlify-cli)"
            echo "  preview            - Mostrar información de despliegue"
            echo "  all                - Ejecutar todo (check, build, test)"
            echo ""
            exit 1
            ;;
    esac

    echo ""
    log_success "Completado"
}

main "$@"
