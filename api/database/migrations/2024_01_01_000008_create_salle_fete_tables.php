<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('event_clients', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('pos_id')->nullable()->index();
            $table->string('nom');
            $table->string('telephone')->nullable();
            $table->string('adresse')->nullable();
            $table->string('email')->nullable();
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('event_services', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('pos_id')->nullable()->index();
            $table->string('nom');
            $table->text('description')->nullable();
            $table->decimal('prix', 15, 2)->default(0);
            $table->string('unite')->nullable();
            $table->boolean('actif')->default(true);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('event_products', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('pos_id')->nullable()->index();
            $table->unsignedBigInteger('product_id')->nullable()->index();
            $table->boolean('is_available')->default(true);
            $table->decimal('custom_price', 15, 2)->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('event_reservations', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('pos_id')->nullable()->index();
            $table->unsignedBigInteger('client_id')->nullable()->index();
            $table->unsignedBigInteger('user_id')->nullable()->index();
            $table->string('reference')->nullable();
            $table->string('nom_evenement')->nullable();
            $table->timestamp('date_evenement')->nullable();
            $table->string('heure_debut')->nullable();
            $table->string('heure_fin')->nullable();
            $table->decimal('montant_total', 15, 2)->default(0);
            $table->decimal('montant_paye', 15, 2)->default(0);
            $table->decimal('remise', 15, 2)->default(0);
            $table->string('statut')->default('confirmee');
            $table->string('statut_paiement')->default('en_attente');
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('event_reservation_services', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('reservation_id')->index();
            $table->unsignedBigInteger('service_id')->nullable()->index();
            $table->decimal('quantite', 15, 3)->default(1);
            $table->decimal('prix_unitaire', 15, 2)->default(0);
            $table->decimal('remise', 15, 2)->default(0);
            $table->decimal('total', 15, 2)->default(0);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('event_reservation_products', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('reservation_id')->index();
            $table->unsignedBigInteger('product_id')->nullable()->index();
            $table->decimal('quantite', 15, 3)->default(1);
            $table->decimal('prix_unitaire', 15, 2)->default(0);
            $table->decimal('remise', 15, 2)->default(0);
            $table->decimal('total', 15, 2)->default(0);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('event_payments', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('reservation_id')->index();
            $table->unsignedBigInteger('payment_mode_id')->nullable()->index();
            $table->decimal('montant', 15, 2)->default(0);
            $table->string('reference')->nullable();
            $table->timestamp('date_paiement')->nullable();
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('event_stock_movements', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('reservation_id')->nullable()->index();
            $table->unsignedBigInteger('product_id')->nullable()->index();
            $table->unsignedBigInteger('warehouse_id')->nullable()->index();
            $table->decimal('quantite', 15, 3)->default(0);
            $table->string('type_mouvement')->default('sortie');
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('event_stock_movements');
        Schema::dropIfExists('event_payments');
        Schema::dropIfExists('event_reservation_products');
        Schema::dropIfExists('event_reservation_services');
        Schema::dropIfExists('event_reservations');
        Schema::dropIfExists('event_products');
        Schema::dropIfExists('event_services');
        Schema::dropIfExists('event_clients');
    }
};
