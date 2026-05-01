<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('compta_journaux', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->timestamp('date_operation')->useCurrent();
            $table->string('libelle', 255);
            $table->decimal('montant', 15, 2);
            $table->string('type_operation', 20); // entree, sortie, transfert
            $table->string('reference', 100)->nullable();
            $table->text('description')->nullable();
            $table->foreignUuid('enterprise_id')->constrained('core_enterprises')->cascadeOnDelete();
            $table->foreignUuid('user_id')->constrained('core_users');
            $table->boolean('valide')->default(false);
            $table->string('valide_by', 100)->nullable();
            $table->timestamp('date_validation')->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->index(['enterprise_id', 'date_operation']);
            $table->index('reference');
        });

        Schema::create('compta_ecritures', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('journal_id')->constrained('compta_journaux')->cascadeOnDelete();
            $table->foreignUuid('compte_comptable_id')->constrained('compta_comptes');
            $table->decimal('debit', 15, 2)->default(0);
            $table->decimal('credit', 15, 2)->default(0);
            $table->integer('ordre');
            $table->string('libelle', 255)->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->index('journal_id');
        });

        Schema::create('compta_config', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('enterprise_id')->constrained('core_enterprises')->cascadeOnDelete();
            $table->foreignUuid('pos_id')->constrained('core_pos_points')->cascadeOnDelete();
            $table->uuid('compte_caisse_id')->nullable();
            $table->uuid('compte_banque_id')->nullable();
            $table->uuid('compte_stock_id')->nullable();
            $table->uuid('compte_variation_stock_id')->nullable();
            $table->uuid('compte_client_id')->nullable();
            $table->uuid('compte_fournisseur_id')->nullable();
            $table->uuid('compte_fournisseur_debiteur_id')->nullable();
            $table->uuid('compte_vente_id')->nullable();
            $table->uuid('compte_achat_id')->nullable();
            $table->uuid('compte_tva_id')->nullable();
            $table->uuid('compte_remise_id')->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->unique('pos_id');
            foreach ([
                'compte_caisse_id', 'compte_banque_id', 'compte_stock_id',
                'compte_variation_stock_id', 'compte_client_id', 'compte_fournisseur_id',
                'compte_fournisseur_debiteur_id', 'compte_vente_id', 'compte_achat_id',
                'compte_tva_id', 'compte_remise_id',
            ] as $col) {
                $table->foreign($col)->references('id')->on('compta_comptes')->nullOnDelete();
            }
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('compta_config');
        Schema::dropIfExists('compta_ecritures');
        Schema::dropIfExists('compta_journaux');
    }
};
