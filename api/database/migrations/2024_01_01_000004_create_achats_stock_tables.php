<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('core_fournisseurs', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('nom', 200);
            $table->string('telephone', 20)->nullable();
            $table->text('adresse')->nullable();
            $table->string('email', 100)->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('stock_warehouses', function (Blueprint $table) {
            $table->bigIncrements('id');
            $table->unsignedBigInteger('entreprise_id')->nullable()->index();
            $table->string('code', 50)->unique();
            $table->string('name', 255);
            $table->string('type', 50)->default('Principal');
            $table->text('description')->nullable();
            $table->text('address')->nullable();
            $table->string('contact_person', 255)->nullable();
            $table->string('contact_phone', 50)->nullable();
            $table->string('contact_email', 255)->nullable();
            $table->boolean('is_default')->default(false);
            $table->boolean('is_active')->default(true);
            $table->decimal('capacity_limit', 15, 2)->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('achat_commandes', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('numero', 50)->unique();
            $table->foreignUuid('fournisseur_id')->nullable()->constrained('core_fournisseurs')->nullOnDelete();
            $table->unsignedBigInteger('entrepot_id');
            $table->foreignUuid('utilisateur_id')->constrained('core_users');
            $table->timestamp('date_commande')->useCurrent();
            $table->decimal('remise_global', 12, 2)->default(0);
            $table->decimal('montant_total', 12, 2);
            $table->enum('etat', ['encours', 'annule', 'valide', 'receptionne'])->default('encours');
            $table->string('statut_paiement', 20)->default('non_paye');
            $table->timestamps();
            $table->softDeletes();
            $table->foreign('entrepot_id')->references('id')->on('stock_warehouses')->cascadeOnDelete();
            $table->index(['fournisseur_id', 'etat']);
        });

        Schema::create('achat_commande_lignes', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('bon_commande_id')->constrained('achat_commandes')->cascadeOnDelete();
            $table->unsignedBigInteger('produit_id');
            $table->foreign('produit_id')->references('id')->on('core_products');
            $table->decimal('quantite', 12, 2);
            $table->decimal('prix_unitaire', 12, 2);
            $table->decimal('remise_ligne', 12, 2)->default(0);
            $table->decimal('total_ligne', 12, 2);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('achat_depenses', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('bon_commande_id')->constrained('achat_commandes')->cascadeOnDelete();
            $table->decimal('montant', 12, 2);
            $table->string('mode_paiement', 50)->nullable();
            $table->string('description', 100)->nullable();
            $table->timestamp('date_paiement')->useCurrent();
            $table->string('reference', 100)->nullable();
            $table->timestamps();
            $table->softDeletes();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('achat_depenses');
        Schema::dropIfExists('achat_commande_lignes');
        Schema::dropIfExists('achat_commandes');
        Schema::dropIfExists('stock_warehouses');
        Schema::dropIfExists('core_fournisseurs');
    }
};
