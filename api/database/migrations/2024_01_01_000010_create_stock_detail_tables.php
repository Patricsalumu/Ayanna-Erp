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
            $table->bigIncrements('id');
            $table->unsignedBigInteger('product_id');
            $table->foreign('product_id')->references('id')->on('core_products')->cascadeOnDelete();
            $table->unsignedBigInteger('warehouse_id');
            $table->foreign('warehouse_id')->references('id')->on('stock_warehouses')->cascadeOnDelete();
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
            $table->bigIncrements('id');
            $table->unsignedBigInteger('product_id');
            $table->foreign('product_id')->references('id')->on('core_products')->cascadeOnDelete();
            $table->unsignedBigInteger('warehouse_id')->nullable();
            $table->unsignedBigInteger('product_warehouse_id')->nullable();
            $table->unsignedBigInteger('destination_warehouse_id')->nullable();
            $table->string('type_mouvement', 50)->nullable();
            $table->string('movement_type', 50)->nullable();
            $table->decimal('quantity', 15, 3);
            $table->decimal('unit_cost', 15, 2)->default(0);
            $table->string('reference_document', 100)->nullable();
            $table->string('reference', 100)->nullable();
            $table->string('type_document', 50)->nullable();
            $table->text('notes')->nullable();
            $table->text('description')->nullable();
            $table->unsignedBigInteger('user_id')->nullable();
            $table->string('user_name', 100)->nullable();
            $table->string('session_id', 100)->nullable();
            $table->timestamp('date_mouvement')->useCurrent();
            $table->timestamp('movement_date')->nullable();
            $table->timestamp('expiry_date')->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->foreign('warehouse_id')->references('id')->on('stock_warehouses')->nullOnDelete();
            $table->foreign('product_warehouse_id')->references('id')->on('stock_produits_entrepot')->nullOnDelete();
            $table->foreign('destination_warehouse_id')->references('id')->on('stock_warehouses')->nullOnDelete();
            $table->index(['product_id', 'warehouse_id']);
            $table->index('date_mouvement');
        });

        // Configuration par entreprise
        Schema::create('stock_config', function (Blueprint $table) {
            $table->bigIncrements('id');
            $table->unsignedBigInteger('entreprise_id')->nullable()->index();
            $table->unsignedBigInteger('default_warehouse_id')->nullable()->index();
            $table->boolean('allow_negative_stock')->default(false);
            $table->string('valuation_method', 20)->default('FIFO');
            $table->boolean('auto_reorder_enabled')->default(false);
            $table->timestamps();
            $table->softDeletes();
            $table->unique('entreprise_id');
        });

        // En-tête d'inventaire
        Schema::create('stock_inventaire', function (Blueprint $table) {
            $table->bigIncrements('id');
            $table->unsignedBigInteger('warehouse_id');
            $table->unsignedBigInteger('user_id')->nullable();
            $table->string('reference', 100)->nullable();
            $table->timestamp('date_inventaire')->useCurrent();
            $table->string('statut', 30)->default('brouillon');
            $table->text('notes')->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->foreign('warehouse_id')->references('id')->on('stock_warehouses')->cascadeOnDelete();
            $table->index('warehouse_id');
        });

        // Lignes d'inventaire
        Schema::create('stock_inventaire_items', function (Blueprint $table) {
            $table->bigIncrements('id');
            $table->unsignedBigInteger('inventaire_id');
            $table->unsignedBigInteger('product_id');
            $table->foreign('inventaire_id')->references('id')->on('stock_inventaire')->cascadeOnDelete();
            $table->foreign('product_id')->references('id')->on('core_products')->cascadeOnDelete();
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
