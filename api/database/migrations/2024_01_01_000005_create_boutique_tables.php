<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // ──── Boutique / Shop ────────────────────────────────────────────────
        Schema::create('shop_clients', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('pos_id')->nullable()->index();
            $table->string('nom');
            $table->string('prenom')->nullable();
            $table->string('telephone')->nullable();
            $table->string('email')->nullable();
            $table->text('adresse')->nullable();
            $table->string('ville', 100)->nullable();
            $table->string('code_postal', 10)->nullable();
            $table->date('date_naissance')->nullable();
            $table->string('type_client', 50)->default('Particulier');
            $table->decimal('credit_limit', 15, 2)->default(0);
            $table->decimal('balance', 15, 2)->default(0);
            $table->text('note')->nullable();
            $table->string('pays', 100)->nullable();
            $table->string('carte_identite', 100)->nullable();
            $table->string('type_carte', 50)->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('shop_services', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('pos_id')->nullable()->index();
            $table->string('nom');
            $table->text('description')->nullable();
            $table->decimal('prix', 15, 2)->default(0);
            $table->string('unite')->nullable();
            $table->boolean('actif')->default(true);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('shop_paniers', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('pos_id')->nullable()->index();
            $table->uuid('client_id')->nullable()->index();
            $table->uuid('user_id')->nullable()->index();
            $table->string('reference')->nullable();
            $table->decimal('montant_total', 15, 2)->default(0);
            $table->decimal('montant_paye', 15, 2)->default(0);
            $table->decimal('remise', 15, 2)->default(0);
            $table->string('statut')->default('ouvert');
            $table->timestamp('date_vente')->nullable();
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('shop_panier_products', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('panier_id')->index();
            $table->uuid('product_id')->nullable()->index();
            $table->decimal('quantite', 15, 3)->default(1);
            $table->decimal('prix_unitaire', 15, 2)->default(0);
            $table->decimal('remise', 15, 2)->default(0);
            $table->decimal('total', 15, 2)->default(0);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('shop_panier_services', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('panier_id')->index();
            $table->uuid('service_id')->nullable()->index();
            $table->decimal('quantite', 15, 3)->default(1);
            $table->decimal('prix_unitaire', 15, 2)->default(0);
            $table->decimal('remise', 15, 2)->default(0);
            $table->decimal('total', 15, 2)->default(0);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('shop_payments', function (Blueprint $table) {
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

        Schema::create('shop_expenses', function (Blueprint $table) {
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
    }

    public function down(): void
    {
        Schema::dropIfExists('shop_expenses');
        Schema::dropIfExists('shop_payments');
        Schema::dropIfExists('shop_panier_services');
        Schema::dropIfExists('shop_panier_products');
        Schema::dropIfExists('shop_paniers');
        Schema::dropIfExists('shop_services');
        Schema::dropIfExists('shop_clients');
    }
};
