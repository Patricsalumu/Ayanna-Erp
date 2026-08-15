-- -----------------------------------------------------------------------------
-- Ayanna ERP - Default MySQL seed
-- -----------------------------------------------------------------------------
-- Import with:
--   mysql -u <user> -p <database_name> < mysql_default_seed.sql
--
-- This file contains the default enterprise, admin account, modules, POS,
-- payment modes, and accounting classes/accounts/config needed by Ayanna ERP.
-- -----------------------------------------------------------------------------

SET FOREIGN_KEY_CHECKS = 0;

-- 1) Enterprise
INSERT INTO core_enterprises (
    id, name, address, phone, email, rccm, id_nat, slogan, currency, taux_de_change,
    created_at, updated_at
) VALUES (
    1,
    'Ayanna Solutions',
    'Adresse par défaut',
    '+243 000 000 000',
    'contact@ayanna.com',
    NULL,
    NULL,
    'Excellence en gestion d\'entreprise',
    'USD',
    NULL,
    NOW(),
    NOW()
) ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    address = VALUES(address),
    phone = VALUES(phone),
    email = VALUES(email),
    slogan = VALUES(slogan),
    currency = VALUES(currency),
    updated_at = NOW();

-- 2) Default admin user
INSERT INTO core_users (
    id, enterprise_id, name, email, password, role, modules,
    created_at, updated_at
) VALUES (
    1,
    1,
    'Super Administrateur',
    'admin@ayanna.com',
    '$2b$12$Lx5ocQ9yUkBs/IYq8CIF9u9eatHdei45tIhHQAGv7WibckdSrtEO6',
    'super_admin',
    '["SalleFete","Vente","Pharmacie","Restaurant","Hotel","Achats","Stock","Comptabilite","Fabrication"]',
    NOW(),
    NOW()
) ON DUPLICATE KEY UPDATE
    enterprise_id = VALUES(enterprise_id),
    name = VALUES(name),
    email = VALUES(email),
    password = VALUES(password),
    role = VALUES(role),
    modules = VALUES(modules),
    updated_at = NOW();

-- 3) Default modules
INSERT INTO modules (id, name, description, created_at, updated_at) VALUES
    (1, 'SalleFete', 'Gestion des salles de fête et événements', NOW(), NOW()),
    (2, 'Vente', 'Gestion des ventes des Produits et services', NOW(), NOW()),
    (3, 'Pharmacie', 'Gestion de pharmacie', NOW(), NOW()),
    (4, 'Restaurant', 'Gestion de restaurant et bar', NOW(), NOW()),
    (5, 'Hotel', 'Gestion d\'hôtel', NOW(), NOW()),
    (6, 'Achats', 'Gestion des achats fournisseurs', NOW(), NOW()),
    (7, 'Stock', 'Gestion des stocks et inventaires', NOW(), NOW()),
    (8, 'Comptabilite', 'Comptabilité SYSCOHADA', NOW(), NOW()),
    (9, 'Fabrication', 'Gestion de la production et fabrication', NOW(), NOW())
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    updated_at = NOW();

-- 4) Default POS points
INSERT INTO core_pos_points (id, enterprise_id, module_id, name, created_at, updated_at) VALUES
    (1, 1, 1, 'POS Salle de Fête Principale', NOW(), NOW()),
    (2, 1, 2, 'POS Vente Centrale', NOW(), NOW()),
    (3, 1, 3, 'POS Pharmacie', NOW(), NOW()),
    (4, 1, 4, 'POS Restaurant Principal', NOW(), NOW()),
    (5, 1, 5, 'POS Hôtel', NOW(), NOW()),
    (6, 1, 6, 'POS Achats', NOW(), NOW()),
    (7, 1, 7, 'POS Stock Central', NOW(), NOW()),
    (8, 1, 8, 'POS Comptabilité', NOW(), NOW()),
    (9, 1, 9, 'POS Fabrication', NOW(), NOW())
ON DUPLICATE KEY UPDATE
    enterprise_id = VALUES(enterprise_id),
    module_id = VALUES(module_id),
    name = VALUES(name),
    updated_at = NOW();

-- 5) Default payment modes
INSERT INTO core_payment_modes (
    id, enterprise_id, code, label, description, compte_id, compte_label,
    is_default, is_active, sort_order, created_at, updated_at
) VALUES
    (1, 1, 'cash', 'Espèces', NULL, NULL, NULL, 1, 1, 1, NOW(), NOW()),
    (2, 1, 'banque', 'Banque', NULL, NULL, NULL, 1, 1, 2, NOW(), NOW()),
    (3, 1, 'mobile_money', 'Mobile Money', NULL, NULL, NULL, 1, 1, 3, NOW(), NOW()),
    (4, 1, 'credit', 'Crédit', NULL, NULL, NULL, 1, 1, 4, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    enterprise_id = VALUES(enterprise_id),
    code = VALUES(code),
    label = VALUES(label),
    is_default = VALUES(is_default),
    is_active = VALUES(is_active),
    sort_order = VALUES(sort_order),
    updated_at = NOW();

-- 6) Default accounting classes
INSERT INTO compta_classes (
    id, code, nom, libelle, type, document, enterprise_id, actif,
    created_at, updated_at
) VALUES
    (1, '1', 'COMPTES DE RESSOURCES DURABLES', 'Comptes de ressources durables', 'passif', 'bilan', 1, 1, NOW(), NOW()),
    (2, '2', 'COMPTES D\'ACTIF IMMOBILISE', 'Comptes d\'actif immobilisé', 'actif', 'bilan', 1, 1, NOW(), NOW()),
    (3, '3', 'COMPTES DE STOCKS', 'Comptes de stocks', 'actif', 'bilan', 1, 1, NOW(), NOW()),
    (4, '4', 'COMPTES DE TIERS', 'Comptes de tiers', 'mixte', 'bilan', 1, 1, NOW(), NOW()),
    (5, '5', 'COMPTES DE TRESORERIE', 'Comptes de trésorerie', 'actif', 'bilan', 1, 1, NOW(), NOW()),
    (6, '6', 'COMPTES DE CHARGES', 'Comptes de charges', 'charge', 'resultat', 1, 1, NOW(), NOW()),
    (7, '7', 'COMPTES DE PRODUITS', 'Comptes de produits', 'produit', 'resultat', 1, 1, NOW(), NOW()),
    (8, '8', 'COMPTES DES AUTRES CHARGES ET DES AUTRES PRODUITS', 'Autres charges et produits', 'mixte', 'resultat', 1, 1, NOW(), NOW()),
    (9, '44', 'COMPTES DE TAXES', 'Comptes de taxes', 'mixte', 'bilan', 1, 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    nom = VALUES(nom),
    libelle = VALUES(libelle),
    type = VALUES(type),
    document = VALUES(document),
    enterprise_id = VALUES(enterprise_id),
    actif = VALUES(actif),
    updated_at = NOW();

-- 7) Default accounting accounts
INSERT INTO compta_comptes (
    id, numero, nom, libelle, actif, is_default, classe_comptable_id,
    created_at, updated_at
) VALUES
    (101, '101', 'Capital social', 'Capital social souscrit et appelé', 1, 1, 1, NOW(), NOW()),
    (102, '102', 'Apports des associés', 'Comptes courants d\'associés et apports en compte', 1, 1, 1, NOW(), NOW()),
    (111, '111', 'Réserve légale', 'Réserve légale constituée (5% du bénéfice)', 1, 1, 1, NOW(), NOW()),
    (120, '120', 'Report à nouveau (créditeur)', 'Report à nouveau bénéficiaire', 1, 1, 1, NOW(), NOW()),
    (129, '129', 'Report à nouveau (débiteur)', 'Report à nouveau déficitaire', 1, 1, 1, NOW(), NOW()),
    (130, '130', 'Résultat net - Bénéfice', 'Résultat net de l\'exercice (bénéfice)', 1, 1, 1, NOW(), NOW()),
    (139, '139', 'Résultat net - Perte', 'Résultat net de l\'exercice (perte)', 1, 1, 1, NOW(), NOW()),
    (162, '162', 'Emprunts bancaires', 'Emprunts auprès des établissements de crédit', 1, 1, 1, NOW(), NOW()),
    (164, '164', 'Comptes courants d\'associés', 'Avances et prêts des associés à la société', 1, 1, 1, NOW(), NOW()),
    (211, '211', 'Terrains', 'Terrains nus, agricoles et de plantation', 1, 1, 2, NOW(), NOW()),
    (213, '213', 'Bâtiments (terrain propre)', 'Bâtiments et constructions sur terrain propre', 1, 1, 2, NOW(), NOW()),
    (2135, '2135', 'Bâtiments (terrain d\'autrui)', 'Bâtiments construits sur terrain d\'autrui', 1, 1, 2, NOW(), NOW()),
    (228, '228', 'Aménagements et installations de bureau', 'Aménagements, installations et agencements de bureaux', 1, 1, 2, NOW(), NOW()),
    (231, '231', 'Matériel de transport', 'Véhicules, motocycles et matériel de transport', 1, 1, 2, NOW(), NOW()),
    (241, '241', 'Mobilier de bureau', 'Meubles, armoires, rayonnages corporels de bureau', 1, 1, 2, NOW(), NOW()),
    (2442, '2442', 'Matériel de bureau (chaises et tables)', 'Chaises, tables et sièges de bureau', 1, 1, 2, NOW(), NOW()),
    (2443, '2443', 'Matériel informatique', 'Ordinateurs, imprimantes, serveurs et périphériques', 1, 1, 2, NOW(), NOW()),
    (2444, '2444', 'Logiciels et site web', 'Logiciels, progiciels, site web (immobilisations incorporelles)', 1, 1, 2, NOW(), NOW()),
    (245, '245', 'Brevets et licences', 'Brevets, licences, marques et droits similaires', 1, 1, 2, NOW(), NOW()),
    (246, '246', 'Congélateurs et équipements frigorigènes', 'Congélateurs, réfrigérateurs et équipements de froid', 1, 1, 2, NOW(), NOW()),
    (247, '247', 'Chaises et tables de terrasse', 'Mobilier de terrasse et d\'espace client', 1, 1, 2, NOW(), NOW()),
    (2813, '2813', 'Amortissement des bâtiments', 'Amortissements cumulés des bâtiments', 1, 1, 2, NOW(), NOW()),
    (2831, '2831', 'Amortissement du matériel de transport', 'Amortissements cumulés du matériel de transport', 1, 1, 2, NOW(), NOW()),
    (2841, '2841', 'Amortissement du mobilier de bureau', 'Amortissements cumulés du mobilier de bureau', 1, 1, 2, NOW(), NOW()),
    (2843, '2843', 'Amortissement du matériel informatique', 'Amortissements cumulés du matériel informatique', 1, 1, 2, NOW(), NOW()),
    (2844, '2844', 'Amortissement des logiciels', 'Amortissements cumulés des logiciels et site web', 1, 1, 2, NOW(), NOW()),
    (2846, '2846', 'Amortissement des congélateurs', 'Amortissements cumulés des congélateurs et équipements de froid', 1, 1, 2, NOW(), NOW()),
    (301, '301', 'Stocks de marchandises', 'Stocks de marchandises destinées à la revente', 1, 1, 3, NOW(), NOW()),
    (321, '321', 'Matières premières', 'Matières premières et fournitures liées à la production', 1, 1, 3, NOW(), NOW()),
    (341, '341', 'Produits finis', 'Produits finis issus de la production propre', 1, 1, 3, NOW(), NOW()),
    (401, '401', 'Fournisseurs (créditeurs)', 'Dettes fournisseurs et comptes rattachés', 1, 1, 4, NOW(), NOW()),
    (409, '409', 'Fournisseurs débiteurs (avances)', 'Avances et acomptes versés sur commandes fournisseurs', 1, 1, 4, NOW(), NOW()),
    (411, '411', 'Clients débiteurs', 'Créances clients et comptes rattachés', 1, 1, 4, NOW(), NOW()),
    (419, '419', 'Clients créditeurs (avances reçues)', 'Avances et acomptes reçus sur commandes clients', 1, 1, 4, NOW(), NOW()),
    (421, '421', 'Personnel - Rémunérations dues', 'Salaires et traitements dus au personnel', 1, 1, 4, NOW(), NOW()),
    (431, '431', 'Sécurité sociale (INSS/CNSS)', 'Cotisations de sécurité sociale et charges INSS', 1, 1, 4, NOW(), NOW()),
    (441, '441', 'État - Impôts et taxes divers', 'Impôts directs, taxes et contributions diverses', 1, 1, 4, NOW(), NOW()),
    (4431, '4431', 'TVA collectée', 'TVA collectée sur les ventes', 1, 1, 4, NOW(), NOW()),
    (4432, '4432', 'TVA déductible', 'TVA déductible sur les achats', 1, 1, 4, NOW(), NOW()),
    (444, '444', 'État - Impôt sur les bénéfices (IBP)', 'Impôt sur les bénéfices professionnels (IBP/IS)', 1, 1, 4, NOW(), NOW()),
    (461, '461', 'Associé - Compte courant débiteur', 'Associé ayant reçu une avance ou pris de l\'argent', 1, 1, 4, NOW(), NOW()),
    (462, '462', 'Associé - Compte courant créditeur', 'Associé ayant prêté de l\'argent à l\'entreprise', 1, 1, 4, NOW(), NOW()),
    (465, '465', 'Avances reçues - Associés', 'Avances et acomptes reçus des associés', 1, 1, 4, NOW(), NOW()),
    (466, '466', 'Avances versées - Associés', 'Avances et acomptes versés aux associés', 1, 1, 4, NOW(), NOW()),
    (471, '471', 'Débiteurs divers', 'Autres débiteurs divers', 1, 1, 4, NOW(), NOW()),
    (472, '472', 'Créditeurs divers', 'Autres créditeurs divers', 1, 1, 4, NOW(), NOW()),
    (477, '477', 'Dépôts et cautionnements reçus', 'Cautions et garanties reçues de tiers', 1, 1, 4, NOW(), NOW()),
    (478, '478', 'Dépôts et cautionnements versés', 'Cautions et garanties versées à des tiers', 1, 1, 4, NOW(), NOW()),
    (521, '521', 'Banque USD (compte courant)', 'Compte courant bancaire en dollars américains (USD)', 1, 1, 5, NOW(), NOW()),
    (522, '522', 'Banque CDF (compte courant)', 'Compte courant bancaire en francs congolais (CDF)', 1, 1, 5, NOW(), NOW()),
    (531, '531', 'Mobile Money', 'M-Pesa, Airtel Money, Orange Money et autres', 1, 1, 5, NOW(), NOW()),
    (542, '542', 'Chèques et virements à encaisser', 'Chèques reçus en attente d\'encaissement', 1, 1, 5, NOW(), NOW()),
    (571, '571', 'Caisse principale USD', 'Caisse en espèces dollars américains', 1, 1, 5, NOW(), NOW()),
    (572, '572', 'Caisse principale CDF', 'Caisse en espèces francs congolais', 1, 1, 5, NOW(), NOW()),
    (601, '601', 'Achats de marchandises', 'Achats de marchandises destinées à la revente', 1, 1, 6, NOW(), NOW()),
    (602, '602', 'Achats de matières premières', 'Achats de matières premières et fournitures de production', 1, 1, 6, NOW(), NOW()),
    (605, '605', 'Achats de carburant et lubrifiants', 'Carburant, huiles moteur et lubrifiants', 1, 1, 6, NOW(), NOW()),
    (606, '606', 'Achats de crédit téléphonique', 'Achats de crédit téléphonique et recharges', 1, 1, 6, NOW(), NOW()),
    (611, '611', 'Frais de transport', 'Transport sur achats, ventes et déplacements', 1, 1, 6, NOW(), NOW()),
    (621, '621', 'Salaires et traitements du personnel', 'Rémunérations brutes du personnel (salaires fixes)', 1, 1, 6, NOW(), NOW()),
    (622, '622', 'Honoraires et services externes', 'Honoraires, rémunérations d\'intermédiaires et consultants', 1, 1, 6, NOW(), NOW()),
    (623, '623', 'Formation du personnel', 'Frais de formation et perfectionnement du personnel', 1, 1, 6, NOW(), NOW()),
    (626, '626', 'Connexion internet et téléphonie', 'Abonnements internet, mobile et téléphonie fixe', 1, 1, 6, NOW(), NOW()),
    (6271, '6271', 'Électricité (SNEL)', 'Charges d\'électricité (SNEL/fournisseur électricité)', 1, 1, 6, NOW(), NOW()),
    (6272, '6272', 'Eau (REGIDESO)', 'Charges d\'eau (REGIDESO/fournisseur d\'eau)', 1, 1, 6, NOW(), NOW()),
    (629, '629', 'Produits d\'entretien et nettoyage', 'Produits d\'entretien, ménage et nettoyage des locaux', 1, 1, 6, NOW(), NOW()),
    (631, '631', 'Frais et commissions bancaires', 'Frais de tenue de compte et commissions bancaires', 1, 1, 6, NOW(), NOW()),
    (632, '632', 'Intérêts bancaires', 'Intérêts sur retraits, dépôts et tenue de compte bancaire', 1, 1, 6, NOW(), NOW()),
    (641, '641', 'Charges sociales patronales (INSS)', 'Cotisations patronales INSS/CNSS à la charge de l\'entreprise', 1, 1, 6, NOW(), NOW()),
    (651, '651', 'Pertes sur créances / Abandons', 'Abandon de créances clients et pertes sur créances irrécouvrables', 1, 1, 6, NOW(), NOW()),
    (661, '661', 'Charges imprévues et exceptionnelles', 'Dépenses imprévues, extraordinaires et exceptionnelles', 1, 1, 6, NOW(), NOW()),
    (671, '671', 'Dotations aux amortissements', 'Dotations aux amortissements et dépréciations des immobilisations', 1, 1, 6, NOW(), NOW()),
    (681, '681', 'Marketing et publicité', 'Frais de marketing, publicité et communication', 1, 1, 6, NOW(), NOW()),
    (682, '682', 'Remises accordées aux clients', 'Remises, ristournes et rabais accordés aux clients', 1, 1, 6, NOW(), NOW()),
    (683, '683', 'Maintenance et réparations', 'Entretien, maintenance et réparations des équipements', 1, 1, 6, NOW(), NOW()),
    (691, '691', 'Impôts et taxes (IBP, DI, patente)', 'Impôts sur bénéfices, droits d\'entrée et patentes diverses', 1, 1, 6, NOW(), NOW()),
    (701, '701', 'Ventes de marchandises', 'Chiffre d\'affaires - Ventes de marchandises', 1, 1, 7, NOW(), NOW()),
    (706, '706', 'Prestations de services', 'Chiffre d\'affaires - Prestations de services facturées', 1, 1, 7, NOW(), NOW()),
    (711, '711', 'Variation de stocks de produits finis', 'Variation des stocks de produits finis et en-cours', 1, 1, 7, NOW(), NOW()),
    (770, '770', 'Produits financiers (intérêts reçus)', 'Intérêts créditeurs et produits financiers reçus de la banque', 1, 1, 7, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    nom = VALUES(nom),
    libelle = VALUES(libelle),
    actif = VALUES(actif),
    is_default = VALUES(is_default),
    classe_comptable_id = VALUES(classe_comptable_id),
    updated_at = NOW();

-- 8) Default stock warehouses
INSERT INTO stock_warehouses (
    id, entreprise_id, code, name, type, description, address, contact_person,
    contact_phone, contact_email, is_default, is_active, capacity_limit,
    created_at, updated_at
) VALUES
    (1, 1, 'POS_2', 'Entrepôt Vente', 'Principal', 'Entrepôt principal pour la vente', NULL, NULL, NULL, NULL, 1, 1, NULL, NOW(), NOW()),
    (2, 1, 'POS_3', 'Entrepôt Pharmacie', 'Principal', 'Entrepôt principal pour la pharmacie', NULL, NULL, NULL, NULL, 0, 1, NULL, NOW(), NOW()),
    (3, 1, 'POS_4', 'Entrepôt Restaurant', 'Principal', 'Entrepôt principal pour le restaurant', NULL, NULL, NULL, NULL, 0, 1, NULL, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    entreprise_id = VALUES(entreprise_id),
    code = VALUES(code),
    name = VALUES(name),
    type = VALUES(type),
    description = VALUES(description),
    is_default = VALUES(is_default),
    is_active = VALUES(is_active),
    updated_at = NOW();

-- 9) Default accounting config by POS
INSERT INTO compta_config (
    id, enterprise_id, pos_id, compte_caisse_id, compte_banque_id, compte_stock_id,
    compte_variation_stock_id, compte_client_id, compte_fournisseur_id,
    compte_fournisseur_debiteur_id, compte_vente_id, compte_achat_id,
    compte_tva_id, compte_remise_id, created_at, updated_at
) VALUES
    (1, 1, 1, 571, 521, 301, NULL, 411, 401, 409, 701, 601, 4431, 682, NOW(), NOW()),
    (2, 1, 2, 571, 521, 301, NULL, 411, 401, 409, 701, 601, 4431, 682, NOW(), NOW()),
    (3, 1, 3, 571, 521, 301, NULL, 411, 401, 409, 701, 601, 4431, 682, NOW(), NOW()),
    (4, 1, 4, 571, 521, 301, NULL, 411, 401, 409, 701, 601, 4431, 682, NOW(), NOW()),
    (5, 1, 5, 571, 521, 301, NULL, 411, 401, 409, 701, 601, 4431, 682, NOW(), NOW()),
    (6, 1, 6, 571, 521, 301, NULL, 411, 401, 409, 701, 601, 4431, 682, NOW(), NOW()),
    (7, 1, 7, 571, 521, 301, NULL, 411, 401, 409, 701, 601, 4431, 682, NOW(), NOW()),
    (8, 1, 8, 571, 521, 301, NULL, 411, 401, 409, 701, 601, 4431, 682, NOW(), NOW()),
    (9, 1, 9, 571, 521, 301, NULL, 411, 401, 409, 701, 601, 4431, 682, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    compte_caisse_id = VALUES(compte_caisse_id),
    compte_banque_id = VALUES(compte_banque_id),
    compte_stock_id = VALUES(compte_stock_id),
    compte_variation_stock_id = VALUES(compte_variation_stock_id),
    compte_client_id = VALUES(compte_client_id),
    compte_fournisseur_id = VALUES(compte_fournisseur_id),
    compte_fournisseur_debiteur_id = VALUES(compte_fournisseur_debiteur_id),
    compte_vente_id = VALUES(compte_vente_id),
    compte_achat_id = VALUES(compte_achat_id),
    compte_tva_id = VALUES(compte_tva_id),
    compte_remise_id = VALUES(compte_remise_id),
    updated_at = NOW();

SET FOREIGN_KEY_CHECKS = 1;
