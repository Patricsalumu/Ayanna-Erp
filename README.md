# 🏢 Ayanna ERP

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green.svg)](https://pypi.org/project/PyQt6/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://sqlalchemy.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Système de Gestion Intégré (ERP) Desktop en Python avec PyQt6**

Ayanna ERP est une solution complète de gestion d'entreprise qui intègre plusieurs modules métier dans une seule application desktop moderne.

## 🌟 Fonctionnalités

### 📦 Modules Intégrés
- **🎪 Salle de Fête** - Gestion des événements et réservations
- **🛒 Boutique/Pharmacie** - Point de vente et gestion des produits
- **🏨 Hôtel** - Gestion hôtelière complète avec réservations
- **🍽️ Restaurant/Bar** - POS avec gestion des tables et commandes
- **📦 Achats** - Gestion des commandes fournisseurs
- **📊 Stock/Inventaire** - Suivi des stocks et mouvements
- **💰 Comptabilité SYSCOHADA** - Système comptable intégré

### ⚡ Caractéristiques Techniques
- ✅ Interface utilisateur moderne avec PyQt6
- ✅ Base de données SQLite intégrée avec SQLAlchemy
- ✅ Gestion multi-modules avec POS dédiés
- ✅ Système de comptabilité SYSCOHADA complet
- ✅ Gestion des utilisateurs et authentification sécurisée
- ✅ Moyens de paiement configurables
- ✅ Rapports et statistiques intégrés
- ✅ Architecture modulaire et extensible

## 🚀 Installation Rapide

### Prérequis
- **Python 3.8+** 
- **Système d'exploitation**: Linux, Windows, macOS
- **Mémoire**: 2GB RAM minimum
- **Espace disque**: 500MB minimum

### Installation en Une Commande

```bash
# Cloner le repository
git clone https://github.com/Patricsalumu/Ayanna-Erp.git
cd Ayanna-Erp

# Installation automatique (crée un environnement virtuel)
./run.sh install
```

### Démarrage

```bash
# Lancer l'application
./run.sh start

# Ou avec l'alias (après installation)
ayanna
```

## 🔑 Accès par Défaut

- **Email**: `admin@ayanna.com`
- **Mot de passe**: `admin123`

⚠️ **Important**: Changez ces identifiants après la première connexion !

## 📖 Documentation

### Scripts Utilitaires

```bash
./run.sh install   # Installation/réinstallation
./run.sh demo      # Générer des données de démonstration
./run.sh start     # Démarrer l'application
./run.sh help      # Afficher l'aide
```

### Architecture du Projet

```
Ayanna-Erp/
├── ayanna_erp/           # Code source principal
│   ├── core/             # Configuration et utilitaires
│   ├── database/         # Modèles et gestionnaire DB
│   ├── ui/              # Interface utilisateur
│   └── modules/         # Modules métier
├── install.py           # Script d'installation
├── main.py             # Point d'entrée principal
├── run.sh              # Script de lancement
└── README.md           # Documentation
```

## 🛠️ Développement

### Installation pour Développement

```bash
# Environnement virtuel manuel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialiser la base de données
python install.py
```

### Tests

```bash
# Vérifier l'installation
python test.py

# Générer des données de test
python demo.py
```

## 📋 Modules Détaillés

### 🎪 Salle de Fête
- Création de services et produits personnalisés
- Gestion complète des réservations (draft → confirmed → paid)
- Facturation et paiements multiples
- Génération automatique d'écritures comptables
- Rapports de chiffre d'affaires et marges

### 🛒 Boutique/Pharmacie
- Gestion catalogue produits/services
- Point de vente (POS) avec panier intelligent
- Pavé numérique pour saisie rapide
- Gestion clients et crédits
- Impression de factures et reçus

### 🏨 Hôtel
- Gestion des chambres (types, capacités, tarifs)
- Système de réservations avec check-in/out
- Services additionnels personnalisables
- Calcul automatique des séjours
- Rapports d'occupation et revenus

### 🍽️ Restaurant/Bar
- Configuration multi-salles et tables
- Tables interactives (forme, position, capacité)
- Gestion des commandes par table
- Menu dynamique et personnalisable
- Intégration comptable automatique

### 📦 Achats & 📊 Stock
- Commandes fournisseurs complètes
- Réception automatique en stock
- Mouvements de stock temps réel
- Alertes de rupture et seuils
- Valorisation comptable du stock

### 💰 Comptabilité SYSCOHADA
- Plan comptable SYSCOHADA intégré
- Journaux comptables automatiques
- Écritures débit/crédit automatiques
- Rapports financiers et bilans
- Intégration totale avec tous les modules

## 🤝 Contribution

Les contributions sont les bienvenues ! Voici comment contribuer :

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👤 Auteur

**Patric Salumu** - [@Patricsalumu](https://github.com/Patricsalumu)

## 🙏 Remerciements

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) pour l'interface utilisateur
- [SQLAlchemy](https://sqlalchemy.org/) pour l'ORM
- [Python](https://python.org) pour le langage
- [SYSCOHADA](https://syscohada.org) pour le référentiel comptable

---

⭐ **Si ce projet vous aide, n'hésitez pas à lui donner une étoile !**
