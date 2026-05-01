<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('hotel_categories', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('pos_id')->nullable()->index();
            $table->string('nom');
            $table->text('description')->nullable();
            $table->decimal('prix_par_nuit', 15, 2)->default(0);
            $table->boolean('actif')->default(true);
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('hotel_rooms', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('pos_id')->nullable()->index();
            $table->uuid('category_id')->nullable()->index();
            $table->string('numero');
            $table->string('nom')->nullable();
            $table->string('etage')->nullable();
            $table->string('statut')->default('disponible');
            $table->boolean('actif')->default(true);
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('hotel_reservations', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('pos_id')->nullable()->index();
            $table->uuid('room_id')->nullable()->index();
            $table->uuid('user_id')->nullable()->index();
            $table->string('reference')->nullable();
            $table->string('client_nom');
            $table->string('client_telephone')->nullable();
            $table->string('client_adresse')->nullable();
            $table->timestamp('date_arrivee')->nullable();
            $table->timestamp('date_depart')->nullable();
            $table->integer('nombre_nuits')->default(1);
            $table->decimal('prix_par_nuit', 15, 2)->default(0);
            $table->decimal('montant_total', 15, 2)->default(0);
            $table->decimal('montant_paye', 15, 2)->default(0);
            $table->decimal('remise', 15, 2)->default(0);
            $table->string('statut')->default('confirmee');
            $table->string('statut_paiement')->default('en_attente');
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('hotel_payments', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('reservation_id')->index();
            $table->uuid('payment_mode_id')->nullable()->index();
            $table->decimal('montant', 15, 2)->default(0);
            $table->string('reference')->nullable();
            $table->timestamp('date_paiement')->nullable();
            $table->text('note')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('hotel_payments');
        Schema::dropIfExists('hotel_reservations');
        Schema::dropIfExists('hotel_rooms');
        Schema::dropIfExists('hotel_categories');
    }
};
