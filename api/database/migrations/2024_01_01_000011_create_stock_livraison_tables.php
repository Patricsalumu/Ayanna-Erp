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
            $table->uuid('id')->primary();
            $table->string('numero', 50)->unique();
            $table->foreignUuid('entreprise_id')->constrained('core_enterprises')->cascadeOnDelete();
            $table->foreignUuid('entrepot_depart_id')->constrained('stock_warehouses');
            $table->foreignUuid('entrepot_arrivee_id')->constrained('stock_warehouses');
            $table->string('statut', 30)->default('brouillon'); // brouillon, livre, receptionne, annule
            $table->decimal('valeur_totale', 15, 2)->default(0);
            $table->foreignUuid('utilisateur_id')->nullable()->constrained('core_users')->nullOnDelete();
            $table->string('utilisateur_nom', 100)->nullable();
            $table->timestamp('date_creation')->useCurrent();
            $table->timestamp('date_livraison')->nullable();
            $table->timestamp('date_reception')->nullable();
            $table->text('notes')->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->index('entreprise_id');
            $table->index('statut');
        });

        // Lignes d'un bon de livraison
        Schema::create('stock_livraison_items', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('livraison_id')->constrained('stock_livraisons')->cascadeOnDelete();
            $table->foreignUuid('product_id')->constrained('core_products')->cascadeOnDelete();
            $table->string('product_name', 200)->nullable();  // dénormalisé
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
