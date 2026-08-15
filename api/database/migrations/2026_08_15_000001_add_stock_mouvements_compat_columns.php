<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (!Schema::hasTable('stock_mouvements')) {
            return;
        }

        if (!Schema::hasColumn('stock_mouvements', 'total_cost')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->decimal('total_cost', 15, 2)->default(0)->after('unit_cost');
            });
            DB::statement('UPDATE stock_mouvements SET total_cost = quantity * unit_cost WHERE total_cost IS NULL OR total_cost = 0');
        }

        if (!Schema::hasColumn('stock_mouvements', 'warehouse_id_depart')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->unsignedBigInteger('warehouse_id_depart')->nullable()->after('warehouse_id');
            });
            DB::statement('UPDATE stock_mouvements SET warehouse_id_depart = warehouse_id WHERE warehouse_id_depart IS NULL');
        }

        if (!Schema::hasColumn('stock_mouvements', 'warehouse_id_destination')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->unsignedBigInteger('warehouse_id_destination')->nullable()->after('warehouse_id_depart');
            });
            DB::statement('UPDATE stock_mouvements SET warehouse_id_destination = destination_warehouse_id WHERE warehouse_id_destination IS NULL');
        }

        if (!Schema::hasColumn('stock_mouvements', 'quantity_before')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->decimal('quantity_before', 15, 3)->nullable()->after('total_cost');
            });
        }

        if (!Schema::hasColumn('stock_mouvements', 'quantity_after')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->decimal('quantity_after', 15, 3)->nullable()->after('quantity_before');
            });
        }

        if (!Schema::hasColumn('stock_mouvements', 'movement_type')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->string('movement_type', 50)->nullable()->after('user_id');
            });
            DB::table('stock_mouvements')->whereNull('movement_type')->whereNotNull('type_mouvement')->update(['movement_type' => DB::raw('type_mouvement')]);
            DB::table('stock_mouvements')->whereNull('movement_type')->update(['movement_type' => 'AJUSTEMENT']);
        }

        if (!Schema::hasColumn('stock_mouvements', 'movement_date')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->timestamp('movement_date')->nullable()->after('user_id');
            });
            DB::table('stock_mouvements')->whereNull('movement_date')->whereNotNull('date_mouvement')->update(['movement_date' => DB::raw('date_mouvement')]);
            DB::table('stock_mouvements')->whereNull('movement_date')->update(['movement_date' => DB::raw('created_at')]);
        }

        if (!Schema::hasColumn('stock_mouvements', 'batch_number')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->string('batch_number', 50)->nullable()->after('session_id');
            });
        }
    }

    public function down(): void
    {
        if (!Schema::hasTable('stock_mouvements')) {
            return;
        }

        foreach (['total_cost', 'warehouse_id_depart', 'warehouse_id_destination', 'quantity_before', 'quantity_after', 'movement_type', 'movement_date', 'batch_number'] as $column) {
            if (Schema::hasColumn('stock_mouvements', $column)) {
                Schema::table('stock_mouvements', function (Blueprint $table) use ($column) {
                    $table->dropColumn($column);
                });
            }
        }
    }
};
