<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (!Schema::hasTable('core_product_categories')) {
            Schema::create('core_product_categories', function (Blueprint $table) {
                $table->id();
                $table->unsignedBigInteger('entreprise_id')->nullable()->index();
                $table->unsignedBigInteger('enterprise_id')->nullable()->index();
                $table->string('name', 100);
                $table->text('description')->nullable();
                $table->unsignedBigInteger('parent_id')->nullable()->index();
                $table->boolean('is_active')->default(true);
                $table->timestamps();
                $table->softDeletes();
            });
        }

        if (!Schema::hasTable('compta_classes')) {
            Schema::create('compta_classes', function (Blueprint $table) {
                $table->uuid('id')->primary();
                $table->string('code', 10);
                $table->string('nom', 100);
                $table->string('libelle', 255);
                $table->string('type', 20);   // actif, passif, charge, produit
                $table->string('document', 50); // bilan, resultat
                $table->foreignUuid('enterprise_id')->constrained('core_enterprises')->cascadeOnDelete();
                $table->boolean('actif')->default(true);
                $table->timestamps();
                $table->softDeletes();
                $table->unique(['code', 'enterprise_id']);
            });
        }

        if (!Schema::hasTable('compta_comptes')) {
            Schema::create('compta_comptes', function (Blueprint $table) {
                $table->uuid('id')->primary();
                $table->string('numero', 20);
                $table->string('nom', 255);
                $table->string('libelle', 255);
                $table->boolean('actif')->default(true);
                $table->boolean('is_default')->default(false);
                $table->foreignUuid('classe_comptable_id')->constrained('compta_classes')->cascadeOnDelete();
                $table->timestamps();
                $table->softDeletes();
                $table->index('numero');
            });
        }

        if (!Schema::hasTable('core_products')) {
            Schema::create('core_products', function (Blueprint $table) {
                $table->id();
                $table->unsignedBigInteger('entreprise_id')->nullable()->index();
                $table->unsignedBigInteger('enterprise_id')->nullable()->index();
                $table->unsignedBigInteger('category_id')->nullable()->index();
                $table->string('code', 50)->nullable();
                $table->string('name', 200);
                $table->text('description')->nullable();
                $table->text('image')->nullable();
                $table->string('barcode', 100)->nullable();
                $table->decimal('cost', 15, 2)->default(0);
                $table->decimal('price_unit', 15, 2)->default(0);
                $table->string('unit', 50)->default('pièce');
                $table->unsignedBigInteger('compte_produit_id')->nullable();
                $table->unsignedBigInteger('compte_charge_id')->nullable();
                $table->unsignedBigInteger('stock_account_id')->nullable();
                $table->string('product_type', 50)->default('resale_product');
                $table->boolean('is_active')->default(true);
                $table->timestamps();
                $table->softDeletes();
                $table->unique(['enterprise_id', 'code']);
                $table->index('barcode');
            });
        }

        if (!Schema::hasTable('core_payment_modes')) {
            Schema::create('core_payment_modes', function (Blueprint $table) {
                $table->uuid('id')->primary();
                $table->foreignUuid('enterprise_id')->constrained('core_enterprises')->cascadeOnDelete();
                $table->string('code', 50);
                $table->string('label', 150);
                $table->text('description')->nullable();
                $table->uuid('compte_id')->nullable();
                $table->foreign('compte_id')->references('id')->on('compta_comptes')->nullOnDelete();
                $table->string('compte_label', 200)->nullable();
                $table->boolean('is_default')->default(false);
                $table->boolean('is_active')->default(true);
                $table->integer('sort_order')->default(0);
                $table->timestamps();
                $table->softDeletes();
                $table->unique(['enterprise_id', 'code']);
            });
        }

        if (!Schema::hasTable('pos_product_access')) {
            Schema::create('pos_product_access', function (Blueprint $table) {
                $table->uuid('id')->primary();
                $table->foreignUuid('pos_id')->constrained('core_pos_points')->cascadeOnDelete();
                $table->unsignedBigInteger('product_id');
                $table->foreign('product_id')->references('id')->on('core_products')->cascadeOnDelete();
                $table->decimal('custom_price', 15, 2)->nullable();
                $table->decimal('custom_cost', 15, 2)->nullable();
                $table->boolean('is_available')->default(true);
                $table->integer('display_order')->default(0);
                $table->timestamps();
                $table->softDeletes();
                $table->unique(['pos_id', 'product_id']);
            });
        }

        if (!Schema::hasTable('licences')) {
            Schema::create('licences', function (Blueprint $table) {
                $table->uuid('id')->primary();
                $table->string('cle', 255)->unique();
                $table->string('type', 50);
                $table->timestamp('date_activation')->nullable();
                $table->timestamp('date_expiration')->nullable();
                $table->string('signature', 255);
                $table->boolean('active')->default(true);
                $table->foreignUuid('enterprise_id')->nullable()->constrained('core_enterprises')->nullOnDelete();
                $table->timestamps();
                $table->softDeletes();
            });
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('licences');
        Schema::dropIfExists('pos_product_access');
        Schema::dropIfExists('core_payment_modes');
        Schema::dropIfExists('core_products');
        Schema::dropIfExists('compta_comptes');
        Schema::dropIfExists('compta_classes');
        Schema::dropIfExists('core_product_categories');
    }
};
