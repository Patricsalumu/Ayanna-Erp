# Ayanna ERP

**Système de Gestion Intégré (ERP) Desktop en Python avec PyQt6**

Ayanna ERP est une solution complète de gestion d'entreprise qui intègre plusieurs modules métier dans une seule application desktop.

## 🚀 Fonctionnalités

### Modules Disponibles
- **🎪 Salle de Fête** - Gestion des événements et réservations
- **🛒 Boutique/Pharmacie** - Point de vente et gestion des produits
- **🏨 Hôtel** - Gestion hôtelière complète avec réservations
- **🍽️ Restaurant/Bar** - POS avec gestion des tables et commandes
- **📦 Achats** - Gestion des commandes fournisseurs
- **📊 Stock/Inventaire** - Suivi des stocks et mouvements
- **💰 Comptabilité SYSCOHADA** - Système comptable intégré

### Caractéristiques Principales
- ✅ Interface utilisateur moderne avec PyQt6
- ✅ Base de données SQLite intégrée
- ✅ Gestion multi-modules avec POS dédiés
- ✅ Système de comptabilité SYSCOHADA
- ✅ Gestion des utilisateurs et authentification
- ✅ Moyens de paiement configurables
- ✅ Rapports et statistiques
- ✅ Intégration entre modules

## 📋 Prérequis

- **Python 3.8+** 
- **Système d'exploitation**: Linux, Windows, macOS
- **Mémoire**: 2GB RAM minimum
- **Espace disque**: 500MB minimum

## 🛠️ Installation

### Installation Automatique (Recommandée)

Le script d'installation gère automatiquement la création d'un environnement virtuel Python pour éviter les conflits avec votre système :

1. **Cloner ou télécharger le projet**
   ```bash
   cd "/home/salumu/apps/ayanna ERP"
   ```

2. **Exécuter l'installation**
   ```bash
   # Rendre le script exécutable (si nécessaire)
   chmod +x run.sh
   
   # Installation complète
   ./run.sh install
   ```
   
   Ou directement avec Python :
   ```bash
   python3 install.py
   ```
   
   Ce script va automatiquement :
   - Créer un environnement virtuel Python (si nécessaire)
   - Installer toutes les dépendances Python
   - Créer et initialiser la base de données
   - Créer un utilisateur administrateur par défaut
   - Créer un raccourci sur le bureau (optionnel)

### Installation Manuelle

Si vous préférez gérer l'environnement vous-même :

```bash
# 1. Créer un environnement virtuel
python3 -m venv venv

# 2. Activer l'environnement virtuel
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Initialiser la base de données
python install.py
```

### Problèmes d'Installation Courants

#### Erreur "externally-managed-environment"

Sur Ubuntu/Debian récents, Python utilise des environnements gérés externalement. Le script d'installation résout automatiquement ce problème en créant un environnement virtuel.

Si vous voyez cette erreur :
```
error: externally-managed-environment
× This environment is externally managed
```

**Solution automatique :** Utilisez `./run.sh install` ou `python3 install.py` qui créeront automatiquement un environnement virtuel.

**Solution manuelle :**
```bash
# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Installer les dépendances
pip install PyQt6 SQLAlchemy bcrypt reportlab Pillow python-dotenv
```

#### Dépendances Système Manquantes

Si l'installation de PyQt6 échoue, installez les dépendances système :

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-venv python3-dev build-essential

# Pour PyQt6 (optionnel, utilisé automatiquement si disponible)
sudo apt install python3-pyqt6 python3-pyqt6-dev
```

## 🎯 Démarrage

### Lancement de l'Application

**Méthode recommandée (avec environnement virtuel) :**
```bash
./run.sh start
```

**Ou directement avec l'environnement virtuel :**
```bash
source venv/bin/activate && python main.py
```

**Ou sans environnement virtuel (si installé système) :**
```bash
python3 main.py
```

### Scripts Utilitaires

```bash
# Installation/réinstallation
./run.sh install

# Générer des données de démonstration
./run.sh demo

# Démarrer l'application
./run.sh start

# Aide
./run.sh help
```

### Première Connexion

**Identifiants par défaut :**
- **Email**: `admin@ayanna.com`
- **Mot de passe**: `admin123`

⚠️ **Important**: Changez ces identifiants après la première connexion !

## 📖 Utilisation

### Interface Principale

1. **Connexion** - Authentifiez-vous avec vos identifiants
2. **Tableau de bord** - Vue d'ensemble avec accès aux modules
3. **Modules** - Cliquez sur un module pour l'ouvrir
4. **Navigation** - Utilisez les onglets pour naviguer dans chaque module

### Modules Détaillés

#### 🎪 Module Salle de Fête
- **Calendrier** - Vue d'ensemble des événements
- **Réservations** - Créer et gérer les réservations
- **Services** - Configurer les services proposés
- **Produits** - Gérer les produits événementiels
- **Clients** - Base de données clients
- **Paiements** - Gestion des encaissements

#### 🛒 Module Boutique/Pharmacie
- **POS** - Point de vente avec catalogue et panier
- **Produits** - Gestion du catalogue produits
- **Services** - Services proposés
- **Ventes** - Historique des ventes
- **Clients** - Gestion clientèle
- **Rapports** - Analyses de ventes

#### 🏨 Module Hôtel
- **Tableau de bord** - Occupancy et statistiques
- **Réservations** - Système de réservation
- **Chambres** - Gestion des chambres
- **Check-in/Check-out** - Processus d'arrivée/départ
- **Services** - Services hôteliers

#### 🍽️ Module Restaurant/Bar
- **POS** - Point de vente avec plan des tables
- **Salles** - Configuration des espaces
- **Tables** - Gestion des tables
- **Menu** - Carte et tarifs
- **Commandes** - Suivi des commandes

### Configuration

#### Entreprise
- Configurer les informations de votre entreprise
- Logo, coordonnées, devise

#### Utilisateurs
- Créer des comptes utilisateurs
- Définir les rôles et permissions

#### Moyens de Paiement
- Configurer les moyens de paiement par module
- Associer aux comptes comptables

## 🗃️ Structure du Projet

```
ayanna ERP/
├── main.py                     # Point d'entrée principal
├── install.py                  # Script d'installation
├── requirements.txt            # Dépendances Python
├── .env                       # Configuration
└── ayanna_erp/
    ├── __init__.py
    ├── core/                  # Fonctionnalités centrales
    ├── database/              # Gestion base de données
    │   ├── database_manager.py
    │   └── models/
    ├── ui/                    # Interface utilisateur
    │   ├── login_window.py
    │   └── main_window.py
    └── modules/               # Modules métier
        ├── salle_fete/
        ├── boutique/
        ├── hotel/
        ├── restaurant/
        ├── achats/
        ├── stock/
        └── comptabilite/
```

## 🗄️ Base de Données

### Tables Principales

#### Tables Centrales
- `core_enterprises` - Informations entreprise
- `core_users` - Utilisateurs système
- `core_partners` - Clients/Fournisseurs
- `core_pos_points` - Points de vente
- `modules` - Modules disponibles

#### Comptabilité SYSCOHADA
- `classes_comptables` - Classes comptables
- `comptes_comptables` - Plan comptable
- `journal_comptables` - Journaux comptables
- `ecritures_comptables` - Écritures comptables

#### Modules Métier
- Tables spécifiques pour chaque module
- Relations avec la comptabilité
- Gestion des stocks et mouvements

## 🔧 Développement

### Architecture

- **Framework UI**: PyQt6
- **Base de données**: SQLAlchemy + SQLite
- **Architecture**: Modulaire avec séparation des responsabilités
- **Modèle**: MVC (Model-View-Controller)

### Ajouter un Module

1. Créer le dossier du module dans `ayanna_erp/modules/`
2. Implémenter la fenêtre principale héritant de `QMainWindow`
3. Créer les modèles de données SQLAlchemy
4. Ajouter l'import dans `main_window.py`

### Contribution

1. Fork du projet
2. Créer une branche feature
3. Commits avec messages clairs
4. Pull request avec description

## 🆘 Support

### Problèmes Courants

**Erreur de dépendances**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Problème de base de données**
```bash
# Supprimer la base existante
rm ayanna_erp.db
# Relancer l'installation
python3 install.py
```

**Erreurs d'interface graphique**
- Vérifiez l'installation de PyQt6
- Assurez-vous d'avoir un serveur X11 (Linux)

### Contact

- **Email**: support@ayanna-solutions.com
- **Site web**: www.ayanna-solutions.com
- **Documentation**: docs.ayanna-solutions.com

## 📄 Licence

Copyright © 2024 Ayanna Solutions. Tous droits réservés.

Ce logiciel est propriétaire et protégé par les lois sur le droit d'auteur.

## 🔄 Changelog

### Version 1.0.0 (2024-08-14)
- ✅ Version initiale
- ✅ Modules principaux implémentés
- ✅ Interface PyQt6 complète
- ✅ Base de données SQLAlchemy
- ✅ Comptabilité SYSCOHADA
- ✅ Système d'authentification
- ✅ Documentation complète

---

**Ayanna ERP** - *Votre partenaire ERP de confiance* 🚀
