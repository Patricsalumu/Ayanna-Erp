<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (Schema::hasTable('restau_produit_panier') && !Schema::hasColumn('restau_produit_panier', 'price')) {
            Schema::table('restau_produit_panier', function (Blueprint $table) {
                $table->decimal('price', 15, 2)->default(0)->after('quantity');
            });
            DB::table('restau_produit_panier')->where('price', 0)->whereNotNull('prix_unitaire')->update(['price' => DB::raw('prix_unitaire')]);
            DB::table('restau_produit_panier')->where('price', 0)->whereNotNull('price_unit')->update(['price' => DB::raw('price_unit')]);
        }

        if (Schema::hasTable('event_payments')) {
            $columnsToAdd = [
                ['payment_method', 'string', '50', 'nullable'],
                ['amount', 'decimal', '15,2', 'default:0'],
                ['payment_date', 'timestamp', null, 'nullable'],
                ['status', 'string', '50', "default:'validated'"],
                ['user_id', 'unsignedBigInteger', null, 'nullable'],
                ['notes', 'text', null, 'nullable'],
                ['journal_id', 'unsignedBigInteger', null, 'nullable'],
            ];

            foreach ($columnsToAdd as [$name, $type, $params, $mode]) {
                if (!Schema::hasColumn('event_payments', $name)) {
                    Schema::table('event_payments', function (Blueprint $table) use ($name, $type, $params, $mode) {
                        if ($type === 'string') {
                            $table->string($name, (int) $params)->nullable();
                        } elseif ($type === 'decimal') {
                            $table->decimal($name, 15, 2)->default(0);
                        } elseif ($type === 'timestamp') {
                            $table->timestamp($name)->nullable();
                        } elseif ($type === 'unsignedBigInteger') {
                            $table->unsignedBigInteger($name)->nullable();
                        } elseif ($type === 'text') {
                            $table->text($name)->nullable();
                        }
                    });
                }
            }

            if (Schema::hasColumn('event_payments', 'payment_method') && Schema::hasColumn('event_payments', 'payment_mode_id')) {
                DB::table('event_payments')->whereNull('payment_method')->whereNotNull('payment_mode_id')->update(['payment_method' => DB::raw('payment_mode_id')]);
            }
            if (Schema::hasColumn('event_payments', 'amount') && Schema::hasColumn('event_payments', 'montant')) {
                DB::table('event_payments')->where('amount', 0)->whereNotNull('montant')->update(['amount' => DB::raw('montant')]);
            }
            if (Schema::hasColumn('event_payments', 'payment_date') && Schema::hasColumn('event_payments', 'date_paiement')) {
                DB::table('event_payments')->whereNull('payment_date')->whereNotNull('date_paiement')->update(['payment_date' => DB::raw('date_paiement')]);
            }
            if (Schema::hasColumn('event_payments', 'status')) {
                DB::table('event_payments')->whereNull('status')->update(['status' => 'validated']);
            }
            if (Schema::hasColumn('event_payments', 'notes') && Schema::hasColumn('event_payments', 'note')) {
                DB::table('event_payments')->whereNull('notes')->whereNotNull('note')->update(['notes' => DB::raw('note')]);
            }
        }
    }

    public function down(): void
    {
        foreach (['restau_produit_panier', 'event_payments'] as $table) {
            if (!Schema::hasTable($table)) {
                continue;
            }

            foreach (['price', 'payment_method', 'amount', 'payment_date', 'status', 'user_id', 'notes', 'journal_id'] as $column) {
                if (Schema::hasColumn($table, $column)) {
                    Schema::table($table, function (Blueprint $table) use ($column) {
                        $table->dropColumn($column);
                    });
                }
            }
        }
    }
};
