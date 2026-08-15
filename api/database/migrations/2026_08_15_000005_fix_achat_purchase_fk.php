<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (!Schema::hasTable('achat_commandes') || !Schema::hasTable('achat_commande_lignes')) {
            return;
        }

        // Remove the child constraints so we can align the FK types with the Python ORM.
        try {
            DB::statement('ALTER TABLE `achat_commande_lignes` DROP FOREIGN KEY `achat_commande_lignes_bon_commande_id_foreign`');
        } catch (\Throwable $e) {
        }

        try {
            DB::statement('ALTER TABLE `achat_depenses` DROP FOREIGN KEY `achat_depenses_bon_commande_id_foreign`');
        } catch (\Throwable $e) {
        }

        // Convert the purchase command ID to integer/bigint, matching the ORM used by the ERP app.
        try {
            DB::statement('ALTER TABLE `achat_commandes` MODIFY `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT');
        } catch (\Throwable $e) {
            throw $e;
        }

        try {
            DB::statement('ALTER TABLE `achat_commande_lignes` MODIFY `bon_commande_id` BIGINT UNSIGNED NOT NULL');
        } catch (\Throwable $e) {
            throw $e;
        }

        try {
            DB::statement('ALTER TABLE `achat_depenses` MODIFY `bon_commande_id` BIGINT UNSIGNED NOT NULL');
        } catch (\Throwable $e) {
            throw $e;
        }

        // Recreate the FK constraints with the repaired integer IDs.
        try {
            DB::statement('ALTER TABLE `achat_commande_lignes` ADD CONSTRAINT `achat_commande_lignes_bon_commande_id_foreign` FOREIGN KEY (`bon_commande_id`) REFERENCES `achat_commandes` (`id`) ON DELETE CASCADE');
        } catch (\Throwable $e) {
        }

        try {
            DB::statement('ALTER TABLE `achat_depenses` ADD CONSTRAINT `achat_depenses_bon_commande_id_foreign` FOREIGN KEY (`bon_commande_id`) REFERENCES `achat_commandes` (`id`) ON DELETE CASCADE');
        } catch (\Throwable $e) {
        }
    }

    public function down(): void
    {
        if (!Schema::hasTable('achat_commandes') || !Schema::hasTable('achat_commande_lignes')) {
            return;
        }

        try {
            DB::statement('ALTER TABLE `achat_commande_lignes` DROP FOREIGN KEY `achat_commande_lignes_bon_commande_id_foreign`');
        } catch (\Throwable $e) {
        }

        try {
            DB::statement('ALTER TABLE `achat_depenses` DROP FOREIGN KEY `achat_depenses_bon_commande_id_foreign`');
        } catch (\Throwable $e) {
        }

        try {
            DB::statement('ALTER TABLE `achat_commandes` MODIFY `id` CHAR(36) NOT NULL');
        } catch (\Throwable $e) {
        }

        try {
            DB::statement('ALTER TABLE `achat_commande_lignes` MODIFY `bon_commande_id` CHAR(36) NOT NULL');
        } catch (\Throwable $e) {
        }

        try {
            DB::statement('ALTER TABLE `achat_depenses` MODIFY `bon_commande_id` CHAR(36) NOT NULL');
        } catch (\Throwable $e) {
        }
    }
};
