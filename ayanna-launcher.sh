#!/bin/bash
# Script de lancement global pour Ayanna ERP

AYANNA_DIR="/home/salumu/apps/ayanna ERP"

# Fonction d'aide
show_help() {
    echo "Ayanna ERP - Launcher"
    echo "Usage: ayanna [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start      Démarrer l'application (par défaut)"
    echo "  install    Installer/réinstaller l'application"
    echo "  demo       Générer des données de démonstration"
    echo "  shell      Ouvrir un shell avec environnement virtuel activé"
    echo "  update     Mettre à jour l'application"
    echo "  help       Afficher cette aide"
    echo ""
    echo "Examples:"
    echo "  ayanna            # Démarrer l'application"
    echo "  ayanna shell      # Shell avec venv activé"
    echo "  ayanna demo       # Ajouter des données de test"
}

# Vérifier que le répertoire existe
if [ ! -d "$AYANNA_DIR" ]; then
    echo "❌ Erreur: Répertoire Ayanna ERP non trouvé: $AYANNA_DIR"
    exit 1
fi

# Aller dans le répertoire
cd "$AYANNA_DIR"

# Traitement des commandes
case "${1:-start}" in
    "start")
        echo "🚀 Démarrage d'Ayanna ERP..."
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate && python main.py
        else
            python3 main.py
        fi
        ;;
    "install")
        echo "📦 Installation d'Ayanna ERP..."
        ./run.sh install
        ;;
    "demo")
        echo "🎭 Génération de données de démonstration..."
        ./run.sh demo
        ;;
    "shell")
        echo "🐚 Ouverture du shell avec environnement virtuel..."
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
            echo "✅ Environnement virtuel activé pour Ayanna ERP"
            echo "💡 Vous pouvez maintenant utiliser: python main.py"
            exec bash
        else
            echo "⚠️  Aucun environnement virtuel trouvé, ouverture du shell normal"
            exec bash
        fi
        ;;
    "update")
        echo "🔄 Mise à jour d'Ayanna ERP..."
        git pull 2>/dev/null || echo "⚠️  Git non disponible, mise à jour manuelle nécessaire"
        ./run.sh install
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Commande inconnue: $1"
        show_help
        exit 1
        ;;
esac
