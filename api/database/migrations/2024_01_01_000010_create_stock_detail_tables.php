<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Liaison produit ↔ entrepôt avec quantités agrégées
        Schema::create('stock_produits_entrepot', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('product_id')->constrained('core_products')->cascadeOnDelete();
            $table->foreignUuid('warehouse_id')->constrained('stock_warehouses')->cascadeOnDelete();
            $table->decimal('quantity', 15, 3)->default(0);
            $table->decimal('reserved_quantity', 15, 3)->default(0);
            $table->decimal('unit_cost', 15, 2)->default(0);
            $table->decimal('total_cost', 15, 2)->default(0);
            $table->decimal('min_stock_level', 15, 3)->default(0);
            $table->timestamp('last_movement_date')->nullable();
            $table->string('location', 100)->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->unique(['product_id', 'warehouse_id'], 'spe_product_warehouse_unique');
            $table->index('warehouse_id');
            $table->index('product_id');
        });

        // Mouvements de stock (entrées / sorties / transferts)
        Schema::create('stock_mouvements', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('product_id')->constrained('core_products')->cascadeOnDelete();
            $table->foreignUuid('warehouse_id')->constrained('stock_warehouses')->cascadeOnDelete();
            $table->foreignUuid('product_warehouse_id')
                  ->nullable()
                  ->constrained('stock_produits_entrepot')
                  ->nullOnDelete();
            $table->string('type_mouvement', 50);   // entree, sortie, transfert, inventaire
            $table->decimal('quantity', 15, 3);
            $table->decimal('unit_cost', 15, 2)->default(0);
            $table->string('reference_document', 100)->nullable();
            $table->string('type_document', 50)->nullable();
            $table->text('notes')->nullable();
            $table->foreignUuid('user_id')->nullable()->constrained('core_users')->nullOnDelete();
            $table->timestamp('date_mouvement')->useCurrent();
            $table->timestamps();
            $table->softDeletes();
            $table->index(['product_id', 'warehouse_id']);
            $table->index('date_mouvement');
        });

        // Configuration par entreprise
        Schema::create('stock_config', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('enterprise_id')->constrained('core_enterprises')->cascadeOnDelete();
            $table->foreignUuid('default_warehouse_id')
                  ->nullable()
                  ->constrained('stock_warehouses')
                  ->nullOnDelete();
            $table->boolean('allow_negative_stock')->default(false);
            $table->string('valuation_method', 20)->default('FIFO'); // FIFO, LIFO, CMUP
            $table->boolean('auto_reorder_enabled')->default(false);
            $table->timestamps();
            $table->softDeletes();
            $table->unique('enterprise_id');
        });

        // En-tête d'inventaire
        Schema::create('stock_inventaire', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('warehouse_id')->constrained('stock_warehouses')->cascadeOnDelete();
            $table->foreignUuid('user_id')->nullable()->constrained('core_users')->nullOnDelete();
            $table->string('reference', 100)->nullable();
            $table->timestamp('date_inventaire')->useCurrent();
            $table->string('statut', 30)->default('brouillon'); // brouillon, valide, annule
            $table->text('notes')->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->index('warehouse_id');
        });

        // Lignes d'inventaire
        Schema::create('stock_inventaire_items', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('inventaire_id')->constrained('stock_inventaire')->cascadeOnDelete();
            $table->foreignUuid('product_id')->constrained('core_products')->cascadeOnDelete();
            $table->decimal('quantite_theorique', 15, 3)->default(0);
            $table->decimal('quantite_reelle', 15, 3)->default(0);
            $table->decimal('ecart', 15, 3)->default(0);
            $table->decimal('unit_cost', 15, 2)->default(0);
            $table->text('notes')->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->index(['inventaire_id', 'product_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('stock_inventaire_items');
        Schema::dropIfExists('stock_inventaire');
        Schema::dropIfExists('stock_config');
        Schema::dropIfExists('stock_mouvements');
        Schema::dropIfExists('stock_produits_entrepot');
    }
};
