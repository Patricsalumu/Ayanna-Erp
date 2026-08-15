<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        $dropConstraints = [
            'compta_ecritures' => ['compta_ecritures_journal_id_foreign', 'compta_ecritures_compte_comptable_id_foreign'],
            'compta_journaux' => ['compta_journaux_enterprise_id_foreign', 'compta_journaux_user_id_foreign'],
            'compta_config' => [
                'compta_config_enterprise_id_foreign', 'compta_config_pos_id_foreign',
                'compta_config_compte_caisse_id_foreign', 'compta_config_compte_banque_id_foreign',
                'compta_config_compte_stock_id_foreign', 'compta_config_compte_variation_stock_id_foreign',
                'compta_config_compte_client_id_foreign', 'compta_config_compte_fournisseur_id_foreign',
                'compta_config_compte_fournisseur_debiteur_id_foreign', 'compta_config_compte_vente_id_foreign',
                'compta_config_compte_achat_id_foreign', 'compta_config_compte_tva_id_foreign',
                'compta_config_compte_remise_id_foreign',
            ],
            'compta_comptes' => ['compta_comptes_classe_comptable_id_foreign'],
            'compta_classes' => ['compta_classes_enterprise_id_foreign'],
            'core_pos_points' => ['core_pos_points_enterprise_id_foreign', 'core_pos_points_module_id_foreign'],
            'core_users' => ['core_users_enterprise_id_foreign'],
            'core_payment_modes' => ['core_payment_modes_enterprise_id_foreign', 'core_payment_modes_compte_id_foreign'],
            'core_fournisseurs' => [],
            'achat_commandes' => ['achat_commandes_entrepot_id_foreign', 'achat_commandes_fournisseur_id_foreign', 'achat_commandes_utilisateur_id_foreign'],
            'achat_commande_lignes' => ['achat_commande_lignes_bon_commande_id_foreign', 'achat_commande_lignes_produit_id_foreign'],
            'achat_depenses' => ['achat_depenses_bon_commande_id_foreign'],
            'pos_product_access' => ['pos_product_access_pos_id_foreign'],
        ];

        foreach ($dropConstraints as $table => $constraints) {
            if (!Schema::hasTable($table)) {
                continue;
            }
            foreach ($constraints as $constraint) {
                try {
                    DB::statement(sprintf('ALTER TABLE `%s` DROP FOREIGN KEY `%s`', $table, $constraint));
                } catch (\Throwable $e) {
                    // ignore if absent
                }
            }
        }

        $typeFixes = [
            ['core_enterprises', 'ALTER TABLE `core_enterprises` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['modules', 'ALTER TABLE `modules` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['core_users', 'ALTER TABLE `core_users` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['core_users', 'ALTER TABLE `core_users` MODIFY `enterprise_id` BIGINT UNSIGNED NOT NULL'],
            ['core_pos_points', 'ALTER TABLE `core_pos_points` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['core_pos_points', 'ALTER TABLE `core_pos_points` MODIFY `enterprise_id` BIGINT UNSIGNED NOT NULL'],
            ['core_pos_points', 'ALTER TABLE `core_pos_points` MODIFY `module_id` BIGINT UNSIGNED NOT NULL'],
            ['core_payment_modes', 'ALTER TABLE `core_payment_modes` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['core_payment_modes', 'ALTER TABLE `core_payment_modes` MODIFY `enterprise_id` BIGINT UNSIGNED NOT NULL'],
            ['core_payment_modes', 'ALTER TABLE `core_payment_modes` MODIFY `compte_id` BIGINT UNSIGNED NULL'],
            ['core_fournisseurs', 'ALTER TABLE `core_fournisseurs` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['compta_classes', 'ALTER TABLE `compta_classes` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['compta_classes', 'ALTER TABLE `compta_classes` MODIFY `enterprise_id` BIGINT UNSIGNED NOT NULL'],
            ['compta_comptes', 'ALTER TABLE `compta_comptes` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['compta_comptes', 'ALTER TABLE `compta_comptes` MODIFY `classe_comptable_id` BIGINT UNSIGNED NOT NULL'],
            ['compta_journaux', 'ALTER TABLE `compta_journaux` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['compta_journaux', 'ALTER TABLE `compta_journaux` MODIFY `enterprise_id` BIGINT UNSIGNED NOT NULL'],
            ['compta_journaux', 'ALTER TABLE `compta_journaux` MODIFY `user_id` BIGINT UNSIGNED NOT NULL'],
            ['compta_ecritures', 'ALTER TABLE `compta_ecritures` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['compta_ecritures', 'ALTER TABLE `compta_ecritures` MODIFY `journal_id` BIGINT UNSIGNED NOT NULL'],
            ['compta_ecritures', 'ALTER TABLE `compta_ecritures` MODIFY `compte_comptable_id` BIGINT UNSIGNED NOT NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `enterprise_id` BIGINT UNSIGNED NOT NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `pos_id` BIGINT UNSIGNED NOT NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_caisse_id` BIGINT UNSIGNED NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_banque_id` BIGINT UNSIGNED NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_stock_id` BIGINT UNSIGNED NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_variation_stock_id` BIGINT UNSIGNED NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_client_id` BIGINT UNSIGNED NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_fournisseur_id` BIGINT UNSIGNED NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_fournisseur_debiteur_id` BIGINT UNSIGNED NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_vente_id` BIGINT UNSIGNED NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_achat_id` BIGINT UNSIGNED NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_tva_id` BIGINT UNSIGNED NULL'],
            ['compta_config', 'ALTER TABLE `compta_config` MODIFY `compte_remise_id` BIGINT UNSIGNED NULL'],
            ['achat_commandes', 'ALTER TABLE `achat_commandes` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['achat_commandes', 'ALTER TABLE `achat_commandes` MODIFY `fournisseur_id` BIGINT UNSIGNED NULL'],
            ['achat_commandes', 'ALTER TABLE `achat_commandes` MODIFY `utilisateur_id` BIGINT UNSIGNED NOT NULL'],
            ['achat_commandes', 'ALTER TABLE `achat_commandes` MODIFY `entrepot_id` BIGINT UNSIGNED NOT NULL'],
            ['achat_commande_lignes', 'ALTER TABLE `achat_commande_lignes` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['achat_commande_lignes', 'ALTER TABLE `achat_commande_lignes` MODIFY `bon_commande_id` BIGINT UNSIGNED NOT NULL'],
            ['achat_commande_lignes', 'ALTER TABLE `achat_commande_lignes` MODIFY `produit_id` BIGINT UNSIGNED NOT NULL'],
            ['achat_depenses', 'ALTER TABLE `achat_depenses` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT'],
            ['achat_depenses', 'ALTER TABLE `achat_depenses` MODIFY `bon_commande_id` BIGINT UNSIGNED NOT NULL'],
        ];

        foreach ($typeFixes as [$table, $sql]) {
            if (!Schema::hasTable($table)) {
                continue;
            }
            try {
                DB::statement($sql);
            } catch (\Throwable $e) {
                // ignore if already normalized or if DB is empty and constraints block the change
            }
        }

        $recreateConstraints = [
            'core_users' => ['ALTER TABLE `core_users` ADD CONSTRAINT `core_users_enterprise_id_foreign` FOREIGN KEY (`enterprise_id`) REFERENCES `core_enterprises` (`id`) ON DELETE CASCADE'],
            'core_pos_points' => [
                'ALTER TABLE `core_pos_points` ADD CONSTRAINT `core_pos_points_enterprise_id_foreign` FOREIGN KEY (`enterprise_id`) REFERENCES `core_enterprises` (`id`) ON DELETE CASCADE',
                'ALTER TABLE `core_pos_points` ADD CONSTRAINT `core_pos_points_module_id_foreign` FOREIGN KEY (`module_id`) REFERENCES `modules` (`id`) ON DELETE CASCADE',
            ],
            'core_payment_modes' => [
                'ALTER TABLE `core_payment_modes` ADD CONSTRAINT `core_payment_modes_enterprise_id_foreign` FOREIGN KEY (`enterprise_id`) REFERENCES `core_enterprises` (`id`) ON DELETE CASCADE',
                'ALTER TABLE `core_payment_modes` ADD CONSTRAINT `core_payment_modes_compte_id_foreign` FOREIGN KEY (`compte_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
            ],
            'compta_classes' => ['ALTER TABLE `compta_classes` ADD CONSTRAINT `compta_classes_enterprise_id_foreign` FOREIGN KEY (`enterprise_id`) REFERENCES `core_enterprises` (`id`) ON DELETE CASCADE'],
            'compta_comptes' => ['ALTER TABLE `compta_comptes` ADD CONSTRAINT `compta_comptes_classe_comptable_id_foreign` FOREIGN KEY (`classe_comptable_id`) REFERENCES `compta_classes` (`id`) ON DELETE CASCADE'],
            'compta_journaux' => [
                'ALTER TABLE `compta_journaux` ADD CONSTRAINT `compta_journaux_enterprise_id_foreign` FOREIGN KEY (`enterprise_id`) REFERENCES `core_enterprises` (`id`) ON DELETE CASCADE',
                'ALTER TABLE `compta_journaux` ADD CONSTRAINT `compta_journaux_user_id_foreign` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`)',
            ],
            'compta_ecritures' => [
                'ALTER TABLE `compta_ecritures` ADD CONSTRAINT `compta_ecritures_journal_id_foreign` FOREIGN KEY (`journal_id`) REFERENCES `compta_journaux` (`id`) ON DELETE CASCADE',
                'ALTER TABLE `compta_ecritures` ADD CONSTRAINT `compta_ecritures_compte_comptable_id_foreign` FOREIGN KEY (`compte_comptable_id`) REFERENCES `compta_comptes` (`id`)',
            ],
            'compta_config' => [
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_enterprise_id_foreign` FOREIGN KEY (`enterprise_id`) REFERENCES `core_enterprises` (`id`) ON DELETE CASCADE',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_pos_id_foreign` FOREIGN KEY (`pos_id`) REFERENCES `core_pos_points` (`id`) ON DELETE CASCADE',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_caisse_id_foreign` FOREIGN KEY (`compte_caisse_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_banque_id_foreign` FOREIGN KEY (`compte_banque_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_stock_id_foreign` FOREIGN KEY (`compte_stock_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_variation_stock_id_foreign` FOREIGN KEY (`compte_variation_stock_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_client_id_foreign` FOREIGN KEY (`compte_client_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_fournisseur_id_foreign` FOREIGN KEY (`compte_fournisseur_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_fournisseur_debiteur_id_foreign` FOREIGN KEY (`compte_fournisseur_debiteur_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_vente_id_foreign` FOREIGN KEY (`compte_vente_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_achat_id_foreign` FOREIGN KEY (`compte_achat_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_tva_id_foreign` FOREIGN KEY (`compte_tva_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `compta_config` ADD CONSTRAINT `compta_config_compte_remise_id_foreign` FOREIGN KEY (`compte_remise_id`) REFERENCES `compta_comptes` (`id`) ON DELETE SET NULL',
            ],
            'achat_commandes' => [
                'ALTER TABLE `achat_commandes` ADD CONSTRAINT `achat_commandes_entrepot_id_foreign` FOREIGN KEY (`entrepot_id`) REFERENCES `stock_warehouses` (`id`) ON DELETE CASCADE',
                'ALTER TABLE `achat_commandes` ADD CONSTRAINT `achat_commandes_fournisseur_id_foreign` FOREIGN KEY (`fournisseur_id`) REFERENCES `core_fournisseurs` (`id`) ON DELETE SET NULL',
                'ALTER TABLE `achat_commandes` ADD CONSTRAINT `achat_commandes_utilisateur_id_foreign` FOREIGN KEY (`utilisateur_id`) REFERENCES `core_users` (`id`)',
            ],
            'achat_commande_lignes' => [
                'ALTER TABLE `achat_commande_lignes` ADD CONSTRAINT `achat_commande_lignes_bon_commande_id_foreign` FOREIGN KEY (`bon_commande_id`) REFERENCES `achat_commandes` (`id`) ON DELETE CASCADE',
                'ALTER TABLE `achat_commande_lignes` ADD CONSTRAINT `achat_commande_lignes_produit_id_foreign` FOREIGN KEY (`produit_id`) REFERENCES `core_products` (`id`)',
            ],
            'achat_depenses' => ['ALTER TABLE `achat_depenses` ADD CONSTRAINT `achat_depenses_bon_commande_id_foreign` FOREIGN KEY (`bon_commande_id`) REFERENCES `achat_commandes` (`id`) ON DELETE CASCADE'],
            'pos_product_access' => ['ALTER TABLE `pos_product_access` ADD CONSTRAINT `pos_product_access_pos_id_foreign` FOREIGN KEY (`pos_id`) REFERENCES `core_pos_points` (`id`) ON DELETE CASCADE'],
        ];

        foreach ($recreateConstraints as $table => $sqls) {
            if (!Schema::hasTable($table)) {
                continue;
            }
            foreach ($sqls as $sql) {
                try {
                    DB::statement($sql);
                } catch (\Throwable $e) {
                    // ignore if constraint already exists/failed on empty rows
                }
            }
        }
    }

    public function down(): void
    {
        // no-op; schema normalization is intentionally one-way
    }
};
