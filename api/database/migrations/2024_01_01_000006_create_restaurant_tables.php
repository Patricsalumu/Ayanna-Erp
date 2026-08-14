<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('restau_salles', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('pos_id')->nullable()->index();
            $table->string('nom');
            $table->integer('capacite')->default(0);
            $table->boolean('actif')->default(true);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_bon_commandes', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('entreprise_id')->nullable()->index();
            $table->uuid('restau_panier_id')->nullable()->index();
            $table->string('numero_bon', 50)->nullable();
            $table->uuid('user_id')->nullable()->index();
            $table->uuid('client_id')->nullable()->index();
            $table->uuid('serveuse_id')->nullable()->index();
            $table->json('produits_json')->nullable();
            $table->decimal('montant_total', 15, 2)->default(0);
            $table->string('statut', 50)->default('valide');
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_tables', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('salle_id')->nullable()->index();
            $table->string('numero')->nullable();
            $table->string('nom')->nullable();
            $table->integer('capacite')->default(0);
            $table->string('statut')->default('libre');
            $table->boolean('actif')->default(true);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_paniers', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('pos_id')->nullable()->index();
            $table->uuid('table_id')->nullable()->index();
            $table->uuid('user_id')->nullable()->index();
            $table->string('reference')->nullable();
            $table->decimal('montant_total', 15, 2)->default(0);
            $table->decimal('montant_paye', 15, 2)->default(0);
            $table->decimal('remise', 15, 2)->default(0);
            $table->string('statut')->default('ouvert');
            $table->timestamp('date_ouverture')->nullable();
            $table->timestamp('date_fermeture')->nullable();
            $table->text('note')->nullable();
            $table->integer('nombre_couverts')->default(1);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_produit_panier', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('panier_id')->index();
            $table->uuid('product_id')->nullable()->index();
            $table->decimal('quantite', 15, 3)->default(1);
            $table->decimal('prix_unitaire', 15, 2)->default(0);
            $table->decimal('remise', 15, 2)->default(0);
            $table->decimal('total', 15, 2)->default(0);
            $table->string('statut')->default('en_attente');
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_payments', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('panier_id')->index();
            $table->uuid('payment_mode_id')->nullable()->index();
            $table->decimal('montant', 15, 2)->default(0);
            $table->string('reference')->nullable();
            $table->timestamp('date_paiement')->nullable();
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_expenses', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('pos_id')->nullable()->index();
            $table->uuid('user_id')->nullable()->index();
            $table->string('libelle');
            $table->decimal('montant', 15, 2)->default(0);
            $table->timestamp('date_depense')->nullable();
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_printed_invoices', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('panier_id')->index();
            $table->uuid('user_id')->nullable()->index();
            $table->timestamp('printed_at')->nullable();
            $table->decimal('montant_total', 15, 2)->default(0);
            $table->decimal('montant_paye', 15, 2)->default(0);
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('restau_printed_invoices');
        Schema::dropIfExists('restau_expenses');
        Schema::dropIfExists('restau_payments');
        Schema::dropIfExists('restau_produit_panier');
        Schema::dropIfExists('restau_paniers');
        Schema::dropIfExists('restau_bon_commandes');
        Schema::dropIfExists('restau_tables');
        Schema::dropIfExists('restau_salles');
    }
};
