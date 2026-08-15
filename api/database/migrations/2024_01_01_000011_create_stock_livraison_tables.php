<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Bon de livraison interne (transfert multi-produits entre entrepôts)
        Schema::create('stock_livraisons', function (Blueprint $table) {
            $table->bigIncrements('id');
            $table->string('numero', 50)->unique();
            $table->unsignedBigInteger('entreprise_id')->nullable()->index();
            $table->unsignedBigInteger('entrepot_depart_id');
            $table->unsignedBigInteger('entrepot_arrivee_id');
            $table->string('statut', 30)->default('brouillon');
            $table->decimal('valeur_totale', 15, 2)->default(0);
            $table->unsignedBigInteger('utilisateur_id')->nullable();
            $table->string('utilisateur_nom', 100)->nullable();
            $table->timestamp('date_creation')->useCurrent();
            $table->timestamp('date_livraison')->nullable();
            $table->timestamp('date_reception')->nullable();
            $table->text('notes')->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->foreign('entrepot_depart_id')->references('id')->on('stock_warehouses')->cascadeOnDelete();
            $table->foreign('entrepot_arrivee_id')->references('id')->on('stock_warehouses')->cascadeOnDelete();
            $table->index('statut');
        });

        // Lignes d'un bon de livraison
        Schema::create('stock_livraison_items', function (Blueprint $table) {
            $table->bigIncrements('id');
            $table->unsignedBigInteger('livraison_id');
            $table->unsignedBigInteger('product_id');
            $table->foreign('livraison_id')->references('id')->on('stock_livraisons')->cascadeOnDelete();
            $table->foreign('product_id')->references('id')->on('core_products')->cascadeOnDelete();
            $table->string('product_name', 200)->nullable();
            $table->string('product_code', 50)->nullable();
            $table->decimal('quantite', 15, 3);
            $table->decimal('cout_unitaire', 15, 2)->default(0);
            $table->decimal('total_ligne', 15, 2)->default(0);
            $table->timestamps();
            $table->softDeletes();
            $table->index('livraison_id');
            $table->index('product_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('stock_livraison_items');
        Schema::dropIfExists('stock_livraisons');
    }
};
