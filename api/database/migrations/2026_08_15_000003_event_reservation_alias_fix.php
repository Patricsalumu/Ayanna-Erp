<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (Schema::hasTable('event_reservations') && !Schema::hasColumn('event_reservations', 'event_date')) {
            Schema::table('event_reservations', function (Blueprint $table) {
                $table->timestamp('event_date')->nullable()->after('nom_evenement');
                $table->string('status', 50)->nullable()->after('statut');
                $table->text('notes')->nullable()->after('note');
                $table->decimal('total_amount', 15, 2)->default(0)->after('montant_total');
                $table->decimal('total_services', 15, 2)->default(0)->after('total_amount');
                $table->decimal('total_products', 15, 2)->default(0)->after('total_services');
                $table->decimal('discount_percent', 15, 2)->default(0)->after('total_products');
                $table->decimal('tax_rate', 15, 2)->default(0)->after('discount_percent');
                $table->decimal('tax_amount', 15, 2)->default(0)->after('tax_rate');
                $table->unsignedBigInteger('created_by')->nullable()->after('tax_amount');
                $table->timestamp('closed_at')->nullable()->after('created_by');
            });
            DB::table('event_reservations')->whereNull('event_date')->whereNotNull('date_evenement')->update(['event_date' => DB::raw('date_evenement')]);
            DB::table('event_reservations')->whereNull('status')->whereNotNull('statut')->update(['status' => DB::raw('statut')]);
            DB::table('event_reservations')->whereNull('notes')->whereNotNull('note')->update(['notes' => DB::raw('note')]);
            DB::table('event_reservations')->where('total_amount', 0)->whereNotNull('montant_total')->update(['total_amount' => DB::raw('montant_total')]);
            DB::table('event_reservations')->whereNull('created_by')->whereNotNull('user_id')->update(['created_by' => DB::raw('user_id')]);
        }

        if (Schema::hasTable('event_reservation_services') && !Schema::hasColumn('event_reservation_services', 'quantity')) {
            Schema::table('event_reservation_services', function (Blueprint $table) {
                $table->decimal('quantity', 15, 3)->default(1)->after('service_id');
                $table->decimal('unit_price', 15, 2)->default(0)->after('quantity');
                $table->decimal('line_total', 15, 2)->default(0)->after('unit_price');
                $table->decimal('line_cost', 15, 2)->default(0)->after('line_total');
            });
            DB::table('event_reservation_services')->where('quantity', 1)->whereNotNull('quantite')->update(['quantity' => DB::raw('quantite')]);
            DB::table('event_reservation_services')->where('unit_price', 0)->whereNotNull('prix_unitaire')->update(['unit_price' => DB::raw('prix_unitaire')]);
            DB::table('event_reservation_services')->where('line_total', 0)->whereNotNull('total')->update(['line_total' => DB::raw('total')]);
        }

        if (Schema::hasTable('event_reservation_products') && !Schema::hasColumn('event_reservation_products', 'quantity')) {
            Schema::table('event_reservation_products', function (Blueprint $table) {
                $table->decimal('quantity', 15, 3)->default(1)->after('product_id');
                $table->decimal('unit_price', 15, 2)->default(0)->after('quantity');
                $table->decimal('line_total', 15, 2)->default(0)->after('unit_price');
                $table->decimal('line_cost', 15, 2)->default(0)->after('line_total');
            });
            DB::table('event_reservation_products')->where('quantity', 1)->whereNotNull('quantite')->update(['quantity' => DB::raw('quantite')]);
            DB::table('event_reservation_products')->where('unit_price', 0)->whereNotNull('prix_unitaire')->update(['unit_price' => DB::raw('prix_unitaire')]);
            DB::table('event_reservation_products')->where('line_total', 0)->whereNotNull('total')->update(['line_total' => DB::raw('total')]);
        }
    }

    public function down(): void
    {
        foreach (['event_reservations', 'event_reservation_services', 'event_reservation_products'] as $table) {
            if (!Schema::hasTable($table)) {
                continue;
            }

            foreach (['event_date', 'status', 'notes', 'total_amount', 'total_services', 'total_products', 'discount_percent', 'tax_rate', 'tax_amount', 'created_by', 'closed_at', 'quantity', 'unit_price', 'line_total', 'line_cost'] as $column) {
                if (Schema::hasColumn($table, $column)) {
                    Schema::table($table, function (Blueprint $table) use ($column) {
                        $table->dropColumn($column);
                    });
                }
            }
        }
    }
};
