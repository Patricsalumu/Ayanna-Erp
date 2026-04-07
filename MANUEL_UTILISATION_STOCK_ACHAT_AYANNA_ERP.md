# FORMATION - GESTION COMPTABLE NUMERISEE D'UNE ENTREPRISE DE RESTAURATION AVEC AYANNA ERP

## 0. Fiche de formation
- Intitule: Gestion comptable numerisee d'une entreprise de restauration avec Ayanna ERP
- Duree totale: 12h
- Rythmes proposes:
1. 3 seances de 4h
2. 6 seances de 2h
- Prerequis: maitrise de base de l'ordinateur et disponibilite en temps
- Public cible: gerants, caissiers, comptables, assistants administratifs, managers de salle
- Formateur: Patrick Salumu, Ingenieur Logiciel et Consultant PMEs

## 0.1 Objectifs pedagogiques globaux
A la fin de la formation, les participants doivent etre capables de:
1. Comprendre la logique economique d'une entreprise de restauration.
2. Comprendre la mecanique comptable (debit/credit, classes de comptes, etats financiers).
3. Utiliser Ayanna ERP pour gerer ventes, achats, stocks et caisse.
4. Configurer correctement les comptes comptables et les liaisons POS.
5. Lire le journal, le grand livre, le compte de resultat et le bilan.
6. Produire des rapports journaliers, hebdomadaires, mensuels et annuels.
7. Appliquer de bonnes pratiques de controle et de rigueur comptable.

---

# CHAPITRE 1 - PREMIER DEMARRAGE ET MISE EN ROUTE

## 1.1 Installation et premier lancement
### 1.1.1 Obtenir le lien de telechargement
1. Demander le lien officiel de telechargement au support Ayanna ERP.
2. Telecharger l'application.

[Capture d'ecran a inserer ici - Lien de telechargement]



### 1.1.2 Preparation du dossier local
1. Ouvrir le disque C.
2. Creer un dossier nomme Ayanna ERP.
3. Copier/placer le fichier telecharge dans C:\Ayanna ERP.

[Capture d'ecran a inserer ici - Dossier C Ayanna ERP]



### 1.1.3 Activation au premier demarrage
1. Lancer l'application.
2. A l'ecran de licence, saisir la cle d'essai: Qm3AYO.
3. Cliquer sur Activer.
4. Verifier le message de succes.

[Capture d'ecran a inserer ici - Ecran activation]



### 1.1.4 Connexion initiale
1. Login: admin@ayanna.com
2. Mot de passe: admin123
3. Cliquer sur Se connecter.

[Capture d'ecran a inserer ici - Connexion initiale]



## 1.2 Configuration de base entreprise et utilisateurs
### 1.2.1 Modifier les informations de l'entreprise
Chemin: Configuration > Entreprise

1. Ouvrir Configuration.
2. Mettre a jour nom, adresse, telephone, email, devise et informations legales.
3. Enregistrer.

[Capture d'ecran a inserer ici - Configuration entreprise]



### 1.2.2 Modifier l'utilisateur admin ou creer un utilisateur
Chemin: Configuration > Utilisateurs

1. Ouvrir l'utilisateur admin et changer les informations necessaires.
2. Ou cliquer sur Nouvel utilisateur.
3. Assigner un role et des droits.
4. Enregistrer.

[Capture d'ecran a inserer ici - Gestion utilisateurs]



---

# CHAPITRE 2 - MODULE RESTAURANT: DEMARRAGE OPERATIONNEL

## 2.1 Vue generale des onglets
Le module Restaurant comprend en pratique:
1. Point de Vente
2. Commandes
3. Categories
4. Produits
5. Salles
6. Clients
7. Caisse
8. Factures imprimees (selon role)

[Capture d'ecran a inserer ici - Onglets module restaurant]



## 2.2 Salles et tables
### 2.2.1 Creer une salle
1. Ouvrir l'onglet Salles.
2. Saisir le nom.
3. Cliquer sur Nouvelle salle.
4. Enregistrer.

### 2.2.2 Creer des tables dans chaque salle
1. Selectionner la salle.
2. Cliquer sur Ajouter table.
3. Saisir numero/nom et capacite.
4. Enregistrer.

[Capture d'ecran a inserer ici - Salles et tables]



## 2.3 Categories
1. Ouvrir Categories.
2. Cliquer sur Nouvelle categorie.
3. Saisir le nom (ex: Boissons, Plats, Desserts).
4. Enregistrer.
5. Pour modifier, selectionner puis cliquer l'icone sytlot à votre sur la ligne de la categorie.
6. Pour desactiver, utiliser l'action de desactivation si disponible.

[Capture d'ecran a inserer ici - Categories]



## 2.4 Produits
### 2.4.1 Creer un produit
1. Ouvrir Produits.
2. Cliquer sur Nouveau produit.
3. Remplir les informations generales (nom, code, categorie).
4. Completer prix de vente et cout.
5. Verifier les infos stock/comptables.
6. Enregistrer.

### 2.4.2 Naviguer les onglets de la fenetre modal produit
Procedure recommandee:
1. Onglet General: identite produit.
2. Onglet Prix: prix de vente, cout, marges.
3. Onglet Stock: unite, min stock, parametres.
4. Onglet Comptable: compte produit/charge si applicable.
5. Validation finale.

### 2.4.3 Modifier un produit
1. Selectionner le produit.
2. Cliquer Modifier.
3. Corriger les champs.
4. Enregistrer.

[Capture d'ecran a inserer ici - Produits]



## 2.5 Clients
1. Ouvrir Clients.
2. Cliquer Nouveau client.
3. Saisir informations client.
4. Enregistrer.
5. Pour modifier, selectionner puis Modifier.

[Capture d'ecran a inserer ici - Clients]



## 2.6 Point de Vente: cycle complet de vente
Precondition: salles, tables, categories et produits sont deja crees.

### 2.6.1 Demarrer une vente
1. Ouvrir Point de Vente.
2. Cliquer une table.
3. Selectionner un client si necessaire.
4. Ajouter les produits au panier.

### 2.6.2 Gerer le panier
1. Incrementer: cliquer +.
2. Decrementer: cliquer -.
3. Supprimer: cliquer l'action supprimer/poubelle.

### 2.6.3 Imprimer et encaisser
1. Cliquer Imprimer ticket/facture si necessaire.
2. Cliquer Payer.
3. Choisir mode de paiement.
4. Valider.

### 2.6.4 Paiement echoue (cas stock insuffisant)
Si la validation echoue a cause du stock:
1. Ouvrir Stock et verifier le produit.
2. Approvisionner via achat, entree ou transfert.
3. Revenir au POS et relancer le paiement.

[Capture d'ecran a inserer ici - Point de vente et panier]



## 2.7 Commandes et Caisse
### 2.7.1 Onglet Commandes
Permet de:
1. Filtrer les ventes/commandes par periode.
2. Exporter les commandes.
3. Exporter des rapports de periode.

### 2.7.2 Onglet Caisse
Permet de:
1. Enregistrer entrees/sorties.
2. Suivre le journal de caisse.
3. Faire des mouvements entre comptes selon droits et configuration.

[Capture d'ecran a inserer ici - Commandes et Caisse]



---

# CHAPITRE 3 - SEANCE 1: FONDEMENTS DE L'ENTREPRISE ET DE LA COMPTABILITE

## 3.1 Definition et role d'une entreprise
Une entreprise est une organisation economique autonome qui combine des ressources humaines, materielles et financieres pour produire ou vendre des biens/services dans le but de generer un profit.

Dans la restauration, les ressources principales sont:
1. Ressources humaines: gerant, manager, cuisiniers, barman, serveurs, caissiers, gardes, cleaners.
2. Ressources materielles: cuisine, tables, caisse, sonorisation, ordinateurs, TV.
3. Ressources financieres: capital, tresorerie, credit fournisseur.

Role d'une entreprise de restauration:
1. Repondre a un besoin client (se nourrir, se detendre, socialiser).
2. Creer de l'emploi.
3. Generer des revenus pour les proprietaires et l'Etat.
4. Contribuer a l'economie locale.

Point cle: une entreprise ne se limite pas a vendre. Elle doit organiser, controler et perenniser son activite pour produire du benefice.

## 3.2 Notion de benefice
Formule de base:

$$
Benefice = Produits - Charges
$$

Definitions:
1. Produits: ce que l'entreprise gagne (ventes repas, boissons, services).
2. Charges: ce que l'entreprise depense (marchandises, salaires, loyer, eau, electricite, internet, taxes, entretien).

Interpretation:
1. Si Produits > Charges: benefice.
2. Si Produits = Charges: equilibre.
3. Si Produits < Charges: perte.

Exemple simple (restaurant, 1 mois):
1. Ventes totales: 8 000
2. Cout marchandises: 3 200
3. Loyer: 900
4. Salaires: 2 000
5. Transport et nourriture: 400
6. Marketing: 240
7. Electricite/eau/internet: 500
8. Divers: 300
9. Imprevus: 160

Total charges: 7 700
Benefice: 8 000 - 7 700 = 300

A retenir:
1. Vendre beaucoup ne suffit pas.
2. Il faut maitriser les couts.
3. Il faut enregistrer chaque entree et chaque sortie.

## 3.3 Pourquoi la comptabilite est indispensable
La comptabilite est le systeme qui enregistre, classe, controle et presente les operations financieres.

Pourquoi elle est vitale:
1. Suivre l'argent entrant/sortant.
2. Mesurer la performance reelle.
3. Prevenir pertes, erreurs et fraudes.
4. Aider la decision manageriale.
5. Produire des documents fiables pour banque, fisc et investisseurs.

## 3.4 Objectifs et utilisateurs de la comptabilite
Objectifs:
1. Informer sur la sante financiere.
2. Controler les operations.
3. Faciliter budget et planification.
4. Respecter les obligations legales.
5. Appuyer la strategie.

Utilisateurs internes:
1. Dirigeant.
2. Responsable administratif/financier.
3. Gestionnaire de stock.
4. Manager de salle/production.

Utilisateurs externes:
1. Administration fiscale.
2. Banques.
3. Investisseurs et associes.
4. Fournisseurs majeurs.
5. Auditeurs.

## 3.5 Notions fondamentales de comptabilite
### 3.5.1 Plan comptable (classes 1 a 7)
1. Classe 1: capitaux.
2. Classe 2: immobilisations.
3. Classe 3: stocks.
4. Classe 4: tiers (clients, fournisseurs, Etat).
5. Classe 5: financiers (caisse, banque, mobile money).
6. Classe 6: charges.
7. Classe 7: produits.

### 3.5.2 Principe de la partie double
Chaque operation touche au moins deux comptes, avec egalite:

$$
Total des debits = Total des credits
$$

Exemple:
1. Achat marchandises a credit pour 300.
2. Debit Stock: 300.
3. Credit Fournisseurs: 300.

### 3.5.3 Etats financiers essentiels
1. Journal: enregistrement chronologique des operations.
2. Compte de resultat: performance de la periode (benefice/perte).
3. Bilan: situation patrimoniale a une date donnee.

---

# CHAPITRE 4 - SEANCE 2: PARAMETRAGE DU LOGICIEL POUR RESTAURANT

## 4.1 Check-list de parametrage initial
1. Activer la licence.
2. Verifier informations entreprise.
3. Verifier devise.
4. Configurer utilisateurs et droits.
5. Configurer plan des salles et tables.
6. Configurer categories et produits.
7. Configurer clients.
8. Faire une vente test.

## 4.2 Exercice pratique seance 2
Objectif: realiser une commande complete en simulation.

Etapes:
1. Creer 1 salle et 5 tables.
2. Creer 3 categories.
3. Creer 10 produits.
4. Creer 2 clients.
5. Ouvrir une table et enregistrer une vente.
6. Imprimer un ticket.
7. Valider un paiement.

Livrable:
1. Ticket imprime.
2. Commande visible dans l'onglet Commandes.

---

# CHAPITRE 5 - SEANCE 3: GESTION DES STOCKS ET ACHATS

## 5.1 Parametrage des entrepots
1. Stock > Entrepots > Nouvel entrepot.
2. Definir code, nom, type, actif.
3. Definir entrepot par defaut si necessaire.

## 5.2 Transfert entre entrepots
1. Stock > Transfert.
2. Choisir entrepot source.
3. Choisir entrepot destination.
4. Choisir produits et quantites.
5. Valider le transfert.

## 5.3 Definir stock minimum
1. Stock > consulter le produit.
2. Ouvrir detail par entrepot.
3. Definir minimum pour chaque entrepot.
4. Enregistrer.

## 5.4 Achat des produits
1. Achats > Fournisseurs > creer fournisseur.
2. Achats > Nouvelle commande.
3. Choisir entrepot de destination.
4. Ajouter produits, quantites et prix d'achat.
5. Creer la commande.
6. Receptionner la commande.
7. Payer total ou partiel.

## 5.5 Inventaire
1. Stock > Inventaire > Nouvelle session.
2. Choisir entrepot et type (complet/categorie/partiel).
3. Saisir comptages.
4. Sauvegarder.
5. Terminer l'inventaire (irreversible).

## 5.6 Exercice pratique seance 3
1. Creer 2 entrepots.
2. Enregistrer 1 achat fournisseur.
3. Receptionner l'achat.
4. Faire 1 transfert inter-entrepots.
5. Lancer 1 inventaire partiel sur 5 produits.
6. Finaliser et analyser les ecarts.

---

# CHAPITRE 6 - SEANCE 4: MECANISME DE LA COMPTABILITE

## 6.1 Plan comptable dans Ayanna ERP
Chemin: Comptabilite > Comptes comptables

1. Verifier les classes et comptes existants.
2. Creer les comptes manquants par classe.
3. Nommer clairement les comptes (ex: 571 Caisse principale, 101 Capital social, 607 Achats marchandises, 701 Ventes).

[Capture d'ecran a inserer ici - Comptes comptables]



## 6.2 Configuration comptable par point de vente
Chemin: Comptabilite > Comptes comptables > Configurer les comptes par point de vente

Configurer au minimum:
1. Compte caisse (classe 5)
2. Compte banque (classe 5)
3. Compte client (classe 4)
4. Compte fournisseur (classe 4)
5. Compte achat (classe 6)
6. Compte vente (classe 7)
7. Compte stock (classe 3)
8. Compte TVA/remise selon votre politique

[Capture d'ecran a inserer ici - Configuration comptes POS]



## 6.3 Lire le journal comptable
Chemin: Comptabilite > Journal comptable

1. Ouvrir la liste des journaux.
2. Cliquer une ligne pour voir les ecritures detaillees.
3. Verifier date, reference, comptes debites/credites, montant, libelle.
4. Exporter en PDF si necessaire.

Regle de controle:
1. Chaque operation doit etre equilibree en debit/credit.
2. Les references doivent pointer vers une operation reelle (vente, achat, caisse).

[Capture d'ecran a inserer ici - Journal comptable]



## 6.4 Lire le grand livre
Chemin: Comptabilite > Grand livre

1. Selectionner un compte.
2. Lire les mouvements debit/credit du compte.
3. Verifier le solde final.
4. Comparer avec les pieces justificatives.

## 6.5 Lire le compte de resultat
Chemin: Comptabilite > Compte de resultat

1. Choisir la periode (du/au).
2. Lancer le filtre.
3. Lire total produits et total charges.
4. Lire resultat net.

Interpretation:
1. Resultat net positif: activite rentable.
2. Resultat net negatif: activite deficitaire.

[Capture d'ecran a inserer ici - Compte de resultat]



## 6.6 Lire le bilan
Chemin: Comptabilite > Bilan

1. Choisir la periode.
2. Filtrer.
3. Lire total actif et total passif.
4. Verifier coherence generale.

[Capture d'ecran a inserer ici - Bilan]



## 6.7 Ecriture pratique: injection de capital social vers tresorerie
Contexte: demarrage d'une entreprise avec capital apporte en caisse.

Ecriture type:
1. Debit compte de tresorerie (classe 5, ex: 571 Caisse) montant X.
2. Credit compte capital social (classe 1, ex: 101 Capital social) montant X.

Procedure logicielle pratique:
1. Aller dans Comptabilite > Journal comptable.
2. Ouvrir Transfert de fonds.
3. Choisir compte a debiter (tresorerie/caisse selon flux).
4. Choisir compte a crediter (capital social).
5. Saisir montant et libelle (ex: Apport initial de l'exploitant).
6. Valider.
7. Verifier l'ecriture dans le journal.
8. Verifier impact dans Bilan (hausse tresorerie et capitaux propres).

Note pedagogique importante:
1. La logique economique doit etre validee par votre comptable/conseil fiscal local.
2. Si l'apport est bancaire au lieu de caisse, utiliser le compte banque au debit.

## 6.8 Limites du systeme manuel
1. Retards de saisie.
2. Erreurs de calcul.
3. Difficultes de controle.
4. Risques de pertes de documents.

---

# CHAPITRE 7 - SEANCE 5: COMPTABILITE NUMERISEE AVEC ERP

## 7.1 Definitions essentielles
1. Logiciel comptable: outil centre sur comptabilite.
2. ERP: systeme integre (vente, achat, stock, comptabilite, rapports).
3. Valeur ajoutee ERP: une seule source de verite, moins de doubles saisies.

## 7.2 Difference logiciel comptable vs ERP
1. Logiciel comptable: souvent posteriori et oriente ecritures.
2. ERP: operationnel + comptable en temps reel.

## 7.3 Fonctionnement d'Ayanna ERP dans un restaurant
1. Vente POS -> impact caisse + comptes de ventes.
2. Achat -> impact stock/fournisseur/paiement.
3. Inventaire -> impact correction de stock.
4. Caisse -> impact journal et soldes de comptes.
5. Comptabilite -> centralisation des ecritures et etats.

## 7.4 Parametrage comptable recommande (implementation terrain)
Ordre conseille:
1. Creer/verifier classes et comptes.
2. Configurer comptes par POS.
3. Verifier comptes produits (vente/charges si utile).
4. Tester une vente et un achat.
5. Verifier journal, resultat, bilan.

## 7.5 Exercice pratique seance 5
Scenario complet:
1. Enregistrer 5 ventes.
2. Enregistrer 1 achat fournisseur et reception.
3. Enregistrer 2 depenses caisse.
4. Faire 1 transfert de fonds.
5. Lire les impacts dans journal et compte de resultat.

---

# CHAPITRE 8 - SEANCE 6: RAPPORTS ET CONTROLE DE GESTION

## 8.1 Rapports de ventes
Chemin recommande: Restaurant > Commandes

Utiliser les filtres de dates:
1. Journalier: selectionner 1 jour.
2. Hebdomadaire: selectionner 7 jours.
3. Mensuel: selectionner debut/fin du mois.
4. Annuel: selectionner debut/fin d'annee.

Actions utiles:
1. Export commandes.
2. Export produits vendus.
3. Export rapport de periode.

[Capture d'ecran a inserer ici - Rapports commandes]



## 8.2 Rapport caisse
Chemin: Restaurant > Caisse

1. Ouvrir le journal de caisse.
2. Filtrer la periode.
3. Lire entrees, sorties, solde.
4. Identifier les depenses importantes.
5. Comparer avec le chiffre d'affaires de la meme periode.

[Capture d'ecran a inserer ici - Rapport caisse]



## 8.3 Generation des etats financiers
Chemin: Comptabilite

1. Journal comptable: verification des ecritures.
2. Grand livre: verification par compte.
3. Compte de resultat: performance de la periode.
4. Bilan: situation patrimoniale.

## 8.4 Introduction au controle de gestion
Objectif: piloter l'entreprise avec des chiffres fiables.

Indicateurs minimum a suivre chaque periode:
1. Chiffre d'affaires.
2. Cout marchandises.
3. Marge brute.
4. Charges fixes.
5. Resultat net.
6. Solde caisse/banque.
7. Rotation de stock et ruptures.

## 8.5 Bonnes pratiques et rigueur comptable
1. Cloturer la caisse chaque jour.
2. Eviter les ventes non enregistrees.
3. Conserver les justificatifs (factures, tickets, depenses).
4. Faire un inventaire periodique.
5. Verifier les ecarts stock et caisse.
6. Produire un rapport hebdomadaire et mensuel.
7. Valider les ecritures sensibles avec le comptable.

---

# CHAPITRE 9 - PLAN D'ANIMATION PEDAGOGIQUE (VERSION FORMATEUR)

## 9.1 Repartition horaire conseillee (6 x 2h)
1. Seance 1 (2h): fondements entreprise/comptabilite.
2. Seance 2 (2h): installation et parametrage restaurant.
3. Seance 3 (2h): stock, achats, inventaires.
4. Seance 4 (2h): mecanique comptable + lecture etats.
5. Seance 5 (2h): comptabilite numerisee + cas integre.
6. Seance 6 (2h): rapports et controle de gestion.

## 9.2 Evaluation finale (pratique)
Chaque participant doit realiser:
1. Une vente complete POS avec paiement.
2. Une commande achat receptionnee.
3. Une session inventaire finalisee.
4. Une configuration comptable POS.
5. Un transfert de fonds capital->tresorerie.
6. Une lecture commentee du journal, resultat, bilan.
7. Un rapport journalier et un rapport mensuel exportes.

---

# CHAPITRE 10 - ANNEXES PEDAGOGIQUES

## 10.1 Check-list operationnelle quotidienne
1. Verifier ouverture caisse.
2. Verifier disponibilite stock produits phares.
3. Enregistrer toutes les ventes dans POS.
4. Enregistrer toutes les sorties de caisse.
5. Verifier paiements en attente.
6. Cloturer caisse et verifier solde fin de journee.

## 10.2 Check-list hebdomadaire
1. Export rapport ventes semaine.
2. Controle depenses semaine.
3. Controle marge brute.
4. Verification ruptures stock.
5. Inventaire partiel sur produits sensibles.

## 10.3 Check-list mensuelle
1. Export rapport mensuel.
2. Rapprochement caisse/banque.
3. Lecture compte de resultat mensuel.
4. Lecture bilan mensuel.
5. Ajustements de prix, couts et achats.

[Capture d'ecran a inserer ici - Annexes check-lists]



Fin du manuel de formation.
