<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Ajoute les colonnes manquantes côté MySQL pour rester compatible avec
     * les modèles Python et les modules restaurant / vente / stock / compta.
     */
    public function up(): void
    {
        // core_product_categories
        if (Schema::hasTable('core_product_categories') && !Schema::hasColumn('core_product_categories', 'entreprise_id')) {
            Schema::table('core_product_categories', function (Blueprint $table) {
                $table->unsignedInteger('entreprise_id')->nullable()->after('id');
            });
            DB::table('core_product_categories')->whereNull('entreprise_id')->update(['entreprise_id' => 1]);
        }

        // core_products
        if (Schema::hasTable('core_products') && !Schema::hasColumn('core_products', 'entreprise_id')) {
            Schema::table('core_products', function (Blueprint $table) {
                $table->unsignedBigInteger('entreprise_id')->nullable()->after('id');
            });
            DB::statement('UPDATE core_products SET `entreprise_id` = CAST(`enterprise_id` AS UNSIGNED) WHERE `entreprise_id` IS NULL AND `enterprise_id` IS NOT NULL');
        }

        // shop_clients
        if (Schema::hasTable('shop_clients') && !Schema::hasColumn('shop_clients', 'notes')) {
            Schema::table('shop_clients', function (Blueprint $table) {
                $table->text('notes')->nullable()->after('balance');
            });
        }
        if (Schema::hasTable('shop_clients') && !Schema::hasColumn('shop_clients', 'pays')) {
            Schema::table('shop_clients', function (Blueprint $table) {
                $table->string('pays', 100)->nullable()->after('notes');
            });
        }
        if (Schema::hasTable('shop_clients') && !Schema::hasColumn('shop_clients', 'carte_identite')) {
            Schema::table('shop_clients', function (Blueprint $table) {
                $table->string('carte_identite', 100)->nullable()->after('pays');
            });
        }
        if (Schema::hasTable('shop_clients') && !Schema::hasColumn('shop_clients', 'type_carte')) {
            Schema::table('shop_clients', function (Blueprint $table) {
                $table->string('type_carte', 50)->nullable()->after('carte_identite');
            });
        }

        // shop_paniers compatibility with the Python ERP naming
        if (Schema::hasTable('shop_paniers') && !Schema::hasColumn('shop_paniers', 'numero_commande')) {
            Schema::table('shop_paniers', function (Blueprint $table) {
                $table->string('numero_commande', 50)->nullable()->after('client_id');
                $table->string('status', 50)->nullable()->after('numero_commande');
                $table->string('payment_method', 50)->nullable()->after('status');
                $table->decimal('subtotal', 15, 2)->default(0)->after('payment_method');
                $table->decimal('remise_amount', 15, 2)->default(0)->after('subtotal');
                $table->decimal('total_final', 15, 2)->default(0)->after('remise_amount');
                $table->boolean('pret')->default(false)->after('total_final');
                $table->boolean('livre')->default(false)->after('pret');
                $table->text('notes')->nullable()->after('livre');
                $table->timestamp('validated_at')->nullable()->after('notes');
            });

            if (Schema::hasColumn('shop_paniers', 'reference')) {
                DB::table('shop_paniers')->whereNull('numero_commande')->update(['numero_commande' => DB::raw('reference')]);
            }
            if (Schema::hasColumn('shop_paniers', 'statut')) {
                DB::table('shop_paniers')->whereNull('status')->update(['status' => DB::raw('statut')]);
            }
            if (Schema::hasColumn('shop_paniers', 'note')) {
                DB::table('shop_paniers')->whereNull('notes')->update(['notes' => DB::raw('note')]);
            }
            if (Schema::hasColumn('shop_paniers', 'montant_total')) {
                DB::table('shop_paniers')->whereNull('subtotal')->update(['subtotal' => DB::raw('montant_total')]);
                DB::table('shop_paniers')->whereNull('total_final')->update(['total_final' => DB::raw('montant_total - remise')]);
            }
            if (Schema::hasColumn('shop_paniers', 'remise')) {
                DB::table('shop_paniers')->whereNull('remise_amount')->update(['remise_amount' => DB::raw('remise')]);
            }
            DB::table('shop_paniers')->whereNull('payment_method')->update(['payment_method' => 'non_paye']);
        }

        if (Schema::hasTable('shop_panier_products') && !Schema::hasTable('shop_paniers_products')) {
            Schema::create('shop_paniers_products', function (Blueprint $table) {
                $table->id();
                $table->unsignedBigInteger('panier_id');
                $table->unsignedBigInteger('product_id');
                $table->decimal('quantity', 15, 2)->default(1);
                $table->decimal('price_unit', 15, 2)->default(0);
                $table->decimal('total_price', 15, 2)->default(0);
                $table->timestamps();
            });
            DB::statement('INSERT INTO shop_paniers_products (panier_id, product_id, quantity, price_unit, total_price, created_at, updated_at) SELECT panier_id, product_id, quantite, prix_unitaire, total, created_at, updated_at FROM shop_panier_products');
        }

        if (Schema::hasTable('shop_panier_services') && !Schema::hasTable('shop_paniers_services')) {
            Schema::create('shop_paniers_services', function (Blueprint $table) {
                $table->id();
                $table->unsignedBigInteger('panier_id');
                $table->unsignedBigInteger('service_id');
                $table->decimal('quantity', 15, 2)->default(1);
                $table->decimal('price_unit', 15, 2)->default(0);
                $table->decimal('total_price', 15, 2)->default(0);
                $table->timestamps();
            });
            DB::statement('INSERT INTO shop_paniers_services (panier_id, service_id, quantity, price_unit, total_price, created_at, updated_at) SELECT panier_id, service_id, quantite, prix_unitaire, total, created_at, updated_at FROM shop_panier_services');
        }

        if (Schema::hasTable('shop_payments') && !Schema::hasColumn('shop_payments', 'payment_method')) {
            Schema::table('shop_payments', function (Blueprint $table) {
                $table->string('payment_method', 50)->nullable()->after('payment_mode_id');
            });
        }
        if (Schema::hasTable('shop_payments') && !Schema::hasColumn('shop_payments', 'amount')) {
            Schema::table('shop_payments', function (Blueprint $table) {
                $table->decimal('amount', 15, 2)->default(0)->after('payment_method');
                $table->timestamp('payment_date')->nullable()->after('amount');
            });
            DB::table('shop_payments')->whereNull('amount')->update(['amount' => DB::raw('montant')]);
            DB::table('shop_payments')->whereNull('payment_date')->update(['payment_date' => DB::raw('date_paiement')]);
        }
        if (Schema::hasTable('shop_payments') && !Schema::hasColumn('shop_payments', 'notes') && Schema::hasColumn('shop_payments', 'note')) {
            Schema::table('shop_payments', function (Blueprint $table) {
                $table->text('notes')->nullable()->after('payment_date');
            });
            DB::table('shop_payments')->whereNull('notes')->update(['notes' => DB::raw('note')]);
        }

        // restaurant compatibility
        if (Schema::hasTable('restau_salles') && !Schema::hasColumn('restau_salles', 'entreprise_id')) {
            Schema::table('restau_salles', function (Blueprint $table) {
                $table->unsignedInteger('entreprise_id')->nullable()->after('id');
            });
            DB::table('restau_salles')->whereNull('entreprise_id')->update(['entreprise_id' => 1]);
        }
        if (Schema::hasTable('restau_salles') && !Schema::hasColumn('restau_salles', 'name') && Schema::hasColumn('restau_salles', 'nom')) {
            Schema::table('restau_salles', function (Blueprint $table) {
                $table->string('name', 200)->nullable()->after('id');
            });
            DB::table('restau_salles')->whereNotNull('nom')->whereNull('name')->update(['name' => DB::raw('nom')]);
        }

        if (Schema::hasTable('restau_paniers') && !Schema::hasColumn('restau_paniers', 'client_id')) {
            Schema::table('restau_paniers', function (Blueprint $table) {
                $table->unsignedBigInteger('client_id')->nullable()->after('table_id');
            });
        }
        if (Schema::hasTable('restau_paniers') && !Schema::hasColumn('restau_paniers', 'serveuse_id')) {
            Schema::table('restau_paniers', function (Blueprint $table) {
                $table->unsignedBigInteger('serveuse_id')->nullable()->after('client_id');
            });
        }
        if (Schema::hasTable('restau_paniers') && !Schema::hasColumn('restau_paniers', 'entreprise_id')) {
            Schema::table('restau_paniers', function (Blueprint $table) {
                $table->unsignedBigInteger('entreprise_id')->nullable()->after('id');
            });
            DB::table('restau_paniers')->whereNull('entreprise_id')->update(['entreprise_id' => 1]);
        }

        if (Schema::hasTable('restau_paniers') && !Schema::hasColumn('restau_paniers', 'subtotal')) {
            Schema::table('restau_paniers', function (Blueprint $table) {
                $table->decimal('subtotal', 15, 2)->default(0)->after('user_id');
                $table->decimal('remise_amount', 15, 2)->default(0)->after('subtotal');
                $table->decimal('total_final', 15, 2)->default(0)->after('remise_amount');
                $table->string('payment_method', 100)->nullable()->after('total_final');
                $table->string('status', 50)->nullable()->after('payment_method');
                $table->boolean('pret')->default(false)->after('status');
                $table->boolean('livre')->default(false)->after('pret');
                $table->text('notes')->nullable()->after('livre');
            });

            if (Schema::hasColumn('restau_paniers', 'montant_total')) {
                DB::table('restau_paniers')->whereNull('subtotal')->update(['subtotal' => DB::raw('montant_total')]);
                DB::table('restau_paniers')->whereNull('total_final')->update(['total_final' => DB::raw('montant_total - remise')]);
            }
            if (Schema::hasColumn('restau_paniers', 'remise')) {
                DB::table('restau_paniers')->whereNull('remise_amount')->update(['remise_amount' => DB::raw('remise')]);
            }
            if (Schema::hasColumn('restau_paniers', 'statut')) {
                DB::table('restau_paniers')->whereNull('status')->update(['status' => DB::raw('statut')]);
            }
            if (Schema::hasColumn('restau_paniers', 'note')) {
                DB::table('restau_paniers')->whereNull('notes')->update(['notes' => DB::raw('note')]);
            }
            DB::table('restau_paniers')->whereNull('payment_method')->update(['payment_method' => 'non_paye']);
        }

        if (Schema::hasTable('restau_produit_panier') && !Schema::hasColumn('restau_produit_panier', 'quantity')) {
            Schema::table('restau_produit_panier', function (Blueprint $table) {
                $table->decimal('quantity', 15, 3)->default(1)->after('product_id');
                $table->decimal('price_unit', 15, 2)->default(0)->after('quantity');
                $table->decimal('total_price', 15, 2)->default(0)->after('price_unit');
            });
            DB::table('restau_produit_panier')->whereNull('quantity')->update(['quantity' => DB::raw('quantite')]);
            DB::table('restau_produit_panier')->whereNull('price_unit')->update(['price_unit' => DB::raw('prix_unitaire')]);
            DB::table('restau_produit_panier')->whereNull('total_price')->update(['total_price' => DB::raw('total')]);
        }

        if (Schema::hasTable('restau_produit_panier') && !Schema::hasColumn('restau_produit_panier', 'price')) {
            Schema::table('restau_produit_panier', function (Blueprint $table) {
                $table->decimal('price', 15, 2)->default(0)->after('quantity');
            });
            DB::table('restau_produit_panier')->where('price', 0)->whereNotNull('prix_unitaire')->update(['price' => DB::raw('prix_unitaire')]);
            DB::table('restau_produit_panier')->where('price', 0)->whereNotNull('price_unit')->update(['price' => DB::raw('price_unit')]);
        }

        if (Schema::hasTable('restau_payments') && !Schema::hasColumn('restau_payments', 'amount')) {
            Schema::table('restau_payments', function (Blueprint $table) {
                $table->decimal('amount', 15, 2)->default(0)->after('payment_mode_id');
                $table->string('payment_method', 100)->nullable()->after('amount');
                $table->unsignedBigInteger('user_id')->nullable()->after('payment_method');
                $table->timestamp('payment_date')->nullable()->after('user_id');
            });
            DB::table('restau_payments')->whereNull('amount')->update(['amount' => DB::raw('montant')]);
            DB::table('restau_payments')->whereNull('payment_method')->update(['payment_method' => DB::raw('payment_mode_id')]);
            DB::table('restau_payments')->whereNull('payment_date')->update(['payment_date' => DB::raw('date_paiement')]);
        }

        if (Schema::hasTable('restau_payments') && Schema::hasColumn('restau_payments', 'user_id')) {
            DB::statement('ALTER TABLE restau_payments MODIFY COLUMN user_id BIGINT UNSIGNED NULL');
        }

        if (Schema::hasTable('restau_tables') && !Schema::hasColumn('restau_tables', 'number')) {
            Schema::table('restau_tables', function (Blueprint $table) {
                $table->string('number', 50)->nullable()->after('salle_id');
                $table->string('name', 200)->nullable()->after('number');
                $table->integer('pos_x')->default(0)->after('name');
                $table->integer('pos_y')->default(0)->after('pos_x');
                $table->integer('width')->default(80)->after('pos_y');
                $table->integer('height')->default(80)->after('width');
                $table->string('shape', 50)->default('rectangle')->after('height');
            });
            if (Schema::hasColumn('restau_tables', 'numero')) {
                DB::table('restau_tables')->whereNotNull('numero')->whereNull('number')->update(['number' => DB::raw('numero')]);
            }
            if (Schema::hasColumn('restau_tables', 'nom')) {
                DB::table('restau_tables')->whereNotNull('nom')->whereNull('name')->update(['name' => DB::raw('nom')]);
            }
        }

        if (Schema::hasTable('restau_printed_invoices') && !Schema::hasColumn('restau_printed_invoices', 'entreprise_id')) {
            Schema::table('restau_printed_invoices', function (Blueprint $table) {
                $table->unsignedInteger('entreprise_id')->nullable()->after('id');
            });
            DB::table('restau_printed_invoices')->whereNull('entreprise_id')->update(['entreprise_id' => 1]);
        }
        if (Schema::hasTable('restau_printed_invoices') && !Schema::hasColumn('restau_printed_invoices', 'total_items_quantity')) {
            Schema::table('restau_printed_invoices', function (Blueprint $table) {
                $table->unsignedInteger('total_items_quantity')->default(0)->after('entreprise_id');
            });
        }
        if (Schema::hasTable('restau_printed_invoices') && !Schema::hasColumn('restau_printed_invoices', 'product_lines_count')) {
            Schema::table('restau_printed_invoices', function (Blueprint $table) {
                $table->unsignedInteger('product_lines_count')->default(0)->after('total_items_quantity');
            });
        }
        if (Schema::hasTable('restau_printed_invoices') && !Schema::hasColumn('restau_printed_invoices', 'total_amount')) {
            Schema::table('restau_printed_invoices', function (Blueprint $table) {
                $table->decimal('total_amount', 15, 2)->default(0)->after('product_lines_count');
            });
        }
        if (Schema::hasTable('restau_printed_invoices') && !Schema::hasColumn('restau_printed_invoices', 'products_snapshot')) {
            Schema::table('restau_printed_invoices', function (Blueprint $table) {
                $table->text('products_snapshot')->nullable()->after('total_amount');
            });
        }
        if (Schema::hasTable('restau_printed_invoices') && !Schema::hasColumn('restau_printed_invoices', 'printed_by_user_id')) {
            Schema::table('restau_printed_invoices', function (Blueprint $table) {
                $table->unsignedBigInteger('printed_by_user_id')->nullable()->after('products_snapshot');
            });
        }
        if (Schema::hasTable('restau_printed_invoices') && Schema::hasColumn('restau_printed_invoices', 'printed_by_user_id')) {
            DB::statement('ALTER TABLE restau_printed_invoices MODIFY COLUMN printed_by_user_id BIGINT UNSIGNED NULL');
        }
        if (Schema::hasTable('restau_printed_invoices') && !Schema::hasColumn('restau_printed_invoices', 'printed_at')) {
            Schema::table('restau_printed_invoices', function (Blueprint $table) {
                $table->timestamp('printed_at')->nullable()->after('printed_by_user_id');
            });
        }

        // salle de fete / event
        if (Schema::hasTable('event_services') && !Schema::hasColumn('event_services', 'name') && Schema::hasColumn('event_services', 'nom')) {
            Schema::table('event_services', function (Blueprint $table) {
                $table->string('name', 200)->nullable()->after('id');
            });
            DB::table('event_services')->whereNotNull('nom')->whereNull('name')->update(['name' => DB::raw('nom')]);
        }
        if (Schema::hasTable('event_services') && !Schema::hasColumn('event_services', 'cost')) {
            Schema::table('event_services', function (Blueprint $table) {
                $table->decimal('cost', 15, 2)->default(0)->after('description');
            });
            DB::table('event_services')->where('cost', 0)->whereNotNull('prix')->update(['cost' => DB::raw('prix')]);
        }
        if (Schema::hasTable('event_services') && !Schema::hasColumn('event_services', 'price')) {
            Schema::table('event_services', function (Blueprint $table) {
                $table->decimal('price', 15, 2)->default(0)->after('cost');
            });
            DB::table('event_services')->where('price', 0)->whereNotNull('prix')->update(['price' => DB::raw('prix')]);
        }

        if (Schema::hasTable('event_payments') && !Schema::hasColumn('event_payments', 'payment_method')) {
            Schema::table('event_payments', function (Blueprint $table) {
                $table->string('payment_method', 50)->nullable()->after('payment_mode_id');
                $table->decimal('amount', 15, 2)->default(0)->after('payment_method');
                $table->timestamp('payment_date')->nullable()->after('amount');
                $table->string('status', 50)->default('validated')->after('payment_date');
                $table->unsignedBigInteger('user_id')->nullable()->after('status');
                $table->text('notes')->nullable()->after('user_id');
                $table->unsignedBigInteger('journal_id')->nullable()->after('notes');
            });
            DB::table('event_payments')->whereNull('payment_method')->whereNotNull('payment_mode_id')->update(['payment_method' => DB::raw('payment_mode_id')]);
            DB::table('event_payments')->where('amount', 0)->whereNotNull('montant')->update(['amount' => DB::raw('montant')]);
            DB::table('event_payments')->whereNull('payment_date')->whereNotNull('date_paiement')->update(['payment_date' => DB::raw('date_paiement')]);
            DB::table('event_payments')->whereNull('status')->update(['status' => 'validated']);
            DB::table('event_payments')->whereNull('notes')->whereNotNull('note')->update(['notes' => DB::raw('note')]);
        }

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

        // stock
        if (Schema::hasTable('stock_mouvements') && !Schema::hasColumn('stock_mouvements', 'total_cost')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->decimal('total_cost', 15, 2)->default(0)->after('unit_cost');
            });
            DB::statement('UPDATE stock_mouvements SET total_cost = quantity * unit_cost WHERE total_cost IS NULL OR total_cost = 0');
        }

        if (Schema::hasTable('stock_mouvements') && !Schema::hasColumn('stock_mouvements', 'warehouse_id_depart')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->unsignedBigInteger('warehouse_id_depart')->nullable()->after('warehouse_id');
            });
            DB::statement('UPDATE stock_mouvements SET warehouse_id_depart = warehouse_id WHERE warehouse_id_depart IS NULL');
        }

        if (Schema::hasTable('stock_mouvements') && !Schema::hasColumn('stock_mouvements', 'warehouse_id_destination')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->unsignedBigInteger('warehouse_id_destination')->nullable()->after('warehouse_id_depart');
            });
            DB::statement('UPDATE stock_mouvements SET warehouse_id_destination = destination_warehouse_id WHERE warehouse_id_destination IS NULL');
        }

        if (Schema::hasTable('stock_mouvements') && !Schema::hasColumn('stock_mouvements', 'quantity_before')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->decimal('quantity_before', 15, 3)->nullable()->after('total_cost');
            });
        }

        if (Schema::hasTable('stock_mouvements') && !Schema::hasColumn('stock_mouvements', 'quantity_after')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->decimal('quantity_after', 15, 3)->nullable()->after('quantity_before');
            });
        }

        if (Schema::hasTable('stock_mouvements') && !Schema::hasColumn('stock_mouvements', 'movement_type')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->string('movement_type', 50)->nullable()->after('user_id');
            });
            DB::table('stock_mouvements')->whereNull('movement_type')->whereNotNull('type_mouvement')->update(['movement_type' => DB::raw('type_mouvement')]);
            DB::table('stock_mouvements')->whereNull('movement_type')->update(['movement_type' => 'AJUSTEMENT']);
        }
        if (Schema::hasTable('stock_mouvements') && !Schema::hasColumn('stock_mouvements', 'movement_date')) {
            Schema::table('stock_mouvements', function (Blueprint $table) {
                $table->timestamp('movement_date')->nullable()->after('user_id');
            });
            DB::table('stock_mouvements')->whereNull('movement_date')->whereNotNull('date_mouvement')->update(['movement_date' => DB::raw('date_mouvement')]);
            DB::table('stock_mouvements')->whereNull('movement_date')->update(['movement_date' => DB::raw('created_at')]);
        }

        // compta
        if (Schema::hasTable('compta_classes') && !Schema::hasColumn('compta_classes', 'date_creation')) {
            Schema::table('compta_classes', function (Blueprint $table) {
                $table->timestamp('date_creation')->nullable()->after('enterprise_id');
                $table->timestamp('date_modification')->nullable()->after('date_creation');
            });
            DB::table('compta_classes')->whereNull('date_creation')->update(['date_creation' => DB::raw('created_at')]);
            DB::table('compta_classes')->whereNull('date_modification')->update(['date_modification' => DB::raw('updated_at')]);
        }

        if (Schema::hasTable('compta_comptes') && !Schema::hasColumn('compta_comptes', 'date_creation')) {
            Schema::table('compta_comptes', function (Blueprint $table) {
                $table->timestamp('date_creation')->nullable()->after('classe_comptable_id');
                $table->timestamp('date_modification')->nullable()->after('date_creation');
            });
            DB::table('compta_comptes')->whereNull('date_creation')->update(['date_creation' => DB::raw('created_at')]);
            DB::table('compta_comptes')->whereNull('date_modification')->update(['date_modification' => DB::raw('updated_at')]);
        }

        if (Schema::hasTable('compta_journaux') && !Schema::hasColumn('compta_journaux', 'date_creation')) {
            Schema::table('compta_journaux', function (Blueprint $table) {
                $table->timestamp('date_creation')->nullable()->after('user_id');
                $table->timestamp('date_modification')->nullable()->after('date_creation');
            });
            DB::table('compta_journaux')->whereNull('date_creation')->update(['date_creation' => DB::raw('created_at')]);
            DB::table('compta_journaux')->whereNull('date_modification')->update(['date_modification' => DB::raw('updated_at')]);
        }
    }

    public function down(): void
    {
        $tables = [
            'core_product_categories',
            'shop_clients',
            'restau_salles',
            'restau_printed_invoices',
            'event_services',
            'stock_mouvements',
            'compta_comptes',
            'compta_journaux',
        ];

        foreach ($tables as $tableName) {
            if (!Schema::hasTable($tableName)) {
                continue;
            }

            $columns = [
                'entreprise_id',
                'notes',
                'pays',
                'carte_identite',
                'type_carte',
                'name',
                'movement_date',
                'date_creation',
                'date_modification',
            ];

            foreach ($columns as $column) {
                if (Schema::hasColumn($tableName, $column)) {
                    Schema::table($tableName, function (Blueprint $table) use ($column) {
                        $table->dropColumn($column);
                    });
                }
            }
        }
    }
};
