<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('restau_salles', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('entreprise_id')->nullable()->index();
            $table->unsignedBigInteger('pos_id')->nullable()->index();
            $table->string('nom');
            $table->string('name', 200)->nullable();
            $table->integer('capacite')->default(0);
            $table->boolean('actif')->default(true);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_bon_commandes', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('entreprise_id')->nullable()->index();
            $table->unsignedBigInteger('restau_panier_id')->nullable()->index();
            $table->string('numero_bon', 50)->nullable();
            $table->unsignedBigInteger('user_id')->nullable()->index();
            $table->unsignedBigInteger('client_id')->nullable()->index();
            $table->unsignedBigInteger('serveuse_id')->nullable()->index();
            $table->json('produits_json')->nullable();
            $table->decimal('montant_total', 15, 2)->default(0);
            $table->string('statut', 50)->default('valide');
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_tables', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('salle_id')->nullable()->index();
            $table->string('numero')->nullable();
            $table->string('number', 50)->nullable();
            $table->string('nom')->nullable();
            $table->string('name', 200)->nullable();
            $table->integer('capacite')->default(0);
            $table->integer('pos_x')->default(0);
            $table->integer('pos_y')->default(0);
            $table->integer('width')->default(80);
            $table->integer('height')->default(80);
            $table->string('shape', 50)->default('rectangle');
            $table->string('statut')->default('libre');
            $table->boolean('actif')->default(true);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_paniers', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('entreprise_id')->nullable()->index();
            $table->unsignedBigInteger('pos_id')->nullable()->index();
            $table->unsignedBigInteger('table_id')->nullable()->index();
            $table->unsignedBigInteger('client_id')->nullable()->index();
            $table->unsignedBigInteger('serveuse_id')->nullable()->index();
            $table->unsignedBigInteger('user_id')->nullable()->index();
            $table->string('reference')->nullable();
            $table->string('status', 50)->nullable()->default('en_cours');
            $table->string('payment_method', 100)->nullable()->default('non_paye');
            $table->decimal('subtotal', 15, 2)->default(0);
            $table->decimal('montant_total', 15, 2)->default(0);
            $table->decimal('montant_paye', 15, 2)->default(0);
            $table->decimal('remise', 15, 2)->default(0);
            $table->decimal('remise_amount', 15, 2)->default(0);
            $table->decimal('total_final', 15, 2)->default(0);
            $table->string('statut')->nullable()->default('ouvert');
            $table->timestamp('date_ouverture')->nullable();
            $table->timestamp('date_fermeture')->nullable();
            $table->boolean('pret')->default(false);
            $table->boolean('livre')->default(false);
            $table->text('note')->nullable();
            $table->text('notes')->nullable();
            $table->integer('nombre_couverts')->default(1);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_produit_panier', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('panier_id')->index();
            $table->unsignedBigInteger('product_id')->nullable()->index();
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
            $table->id();
            $table->unsignedBigInteger('panier_id')->index();
            $table->unsignedBigInteger('payment_mode_id')->nullable()->index();
            $table->string('payment_method', 100)->nullable();
            $table->decimal('amount', 15, 2)->default(0);
            $table->decimal('montant', 15, 2)->default(0);
            $table->string('reference')->nullable();
            $table->timestamp('payment_date')->nullable();
            $table->timestamp('date_paiement')->nullable();
            $table->text('note')->nullable();
            $table->text('notes')->nullable();
            $table->unsignedBigInteger('user_id')->nullable()->index();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_expenses', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('pos_id')->nullable()->index();
            $table->unsignedBigInteger('user_id')->nullable()->index();
            $table->string('libelle');
            $table->decimal('montant', 15, 2)->default(0);
            $table->timestamp('date_depense')->nullable();
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('restau_printed_invoices', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('panier_id')->index();
            $table->unsignedBigInteger('user_id')->nullable()->index();
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
