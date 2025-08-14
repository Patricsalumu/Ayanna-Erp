#!/bin/bash

# Script de lancement pour Ayanna ERP
# Usage: ./run.sh [install|demo|start]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages colorés
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier que Python 3 est installé
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 n'est pas installé"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Python détecté: $python_version"
}

# Fonction pour obtenir l'exécutable Python (venv ou système)
get_python_executable() {
    if [ -f "venv/bin/python" ]; then
        echo "venv/bin/python"
    else
        echo "python3"
    fi
}

# Fonction pour activer l'environnement virtuel si il existe
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        log_info "Activation de l'environnement virtuel"
        source venv/bin/activate
    fi
}

# Installation
install() {
    log_info "🚀 Installation d'Ayanna ERP"
    echo "= $(ls -1 | tr '\n' ' ')$(ls -1 | wc -l)"
    
    check_python
    
    log_info "Lancement du script d'installation..."
    python3 install.py
    
    if [ $? -eq 0 ]; then
        log_success "Installation terminée avec succès!"
    else
        log_error "Échec de l'installation"
        exit 1
    fi
}

# Génération de données de démonstration
demo() {
    log_info "🎭 Génération des données de démonstration"
    
    check_python
    python_exec=$(get_python_executable)
    activate_venv
    
    if [ ! -f "ayanna_erp.db" ]; then
        log_warning "Base de données non trouvée. Installation requise."
        install
    fi
    
    log_info "Génération des données de test..."
    $python_exec demo.py
}

# Démarrage de l'application
start() {
    log_info "🖥️  Démarrage d'Ayanna ERP"
    
    check_python
    python_exec=$(get_python_executable)
    activate_venv
    
    if [ ! -f "ayanna_erp.db" ]; then
        log_warning "Base de données non trouvée. Installation requise."
        install
    fi
    
    log_info "Lancement de l'application..."
    $python_exec main.py
}

# Affichage de l'aide
show_help() {
    echo "Ayanna ERP - Script de lancement"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  install    Installer Ayanna ERP et ses dépendances"
    echo "  demo       Générer des données de démonstration"
    echo "  start      Démarrer l'application (par défaut)"
    echo "  help       Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 install    # Installation complète"
    echo "  $0 demo       # Générer des données de test"
    echo "  $0            # Démarrer l'application"
}

# Menu principal
main() {
    case "${1:-start}" in
        "install")
            install
            ;;
        "demo")
            demo
            ;;
        "start")
            start
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Commande inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

# Exécution
main "$@"
