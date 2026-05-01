<?php

namespace App\Services;

use App\Models\SyncAuditLog;
use Carbon\Carbon;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

/**
 * SyncService — handles push/pull synchronisation.
 *
 * Strategy: CLIENT ALWAYS WINS (last-write-wins).
 * All overwrite conflicts are logged in sync_audit_logs.
 */
class SyncService
{
    /**
     * Map of table name → Eloquent model class.
     * Add every syncable table here.
     */
    protected array $tableMap = [
        'core_enterprises'          => \App\Models\Entreprise::class,
        'core_users'                => \App\Models\User::class,
        'modules'                   => \App\Models\Module::class,
        'core_pos_points'           => \App\Models\POSPoint::class,
        'core_payment_modes'        => \App\Models\PaymentMode::class,
        'core_product_categories'   => \App\Models\CoreProductCategory::class,
        'core_products'             => \App\Models\CoreProduct::class,
        'pos_product_access'        => \App\Models\POSProductAccess::class,
        'compta_classes'            => \App\Models\ComptaClasses::class,
        'compta_comptes'            => \App\Models\ComptaComptes::class,
        'compta_journaux'           => \App\Models\ComptaJournaux::class,
        'compta_ecritures'          => \App\Models\ComptaEcritures::class,
        'compta_config'             => \App\Models\ComptaConfig::class,
        'core_fournisseurs'         => \App\Models\CoreFournisseur::class,
        'stock_warehouses'          => \App\Models\StockWarehouse::class,
        'achat_commandes'           => \App\Models\AchatCommande::class,
        'achat_commande_lignes'     => \App\Models\AchatCommandeLigne::class,
        'achat_depenses'            => \App\Models\AchatDepense::class,
        'stock_produits_entrepot'   => \App\Models\StockProduitEntrepot::class,
        'stock_mouvements'          => \App\Models\StockMouvement::class,
        'stock_config'              => \App\Models\StockConfig::class,
        'stock_inventaire'          => \App\Models\StockInventaire::class,
        'stock_inventaire_items'    => \App\Models\StockInventaireItem::class,
        'shop_clients'              => \App\Models\ShopClient::class,
        'shop_services'             => \App\Models\ShopService::class,
        'shop_paniers'              => \App\Models\ShopPanier::class,
        'shop_panier_products'      => \App\Models\ShopPanierProduct::class,
        'shop_panier_services'      => \App\Models\ShopPanierService::class,
        'shop_payments'             => \App\Models\ShopPayment::class,
        'shop_expenses'             => \App\Models\ShopExpense::class,
        'restau_salles'             => \App\Models\RestauSalle::class,
        'restau_tables'             => \App\Models\RestauTable::class,
        'restau_paniers'            => \App\Models\RestauPanier::class,
        'restau_produit_panier'     => \App\Models\RestauProduitPanier::class,
        'restau_payments'           => \App\Models\RestauPayment::class,
        'restau_expenses'           => \App\Models\RestauExpense::class,
        'restau_printed_invoices'   => \App\Models\RestauPrintedInvoice::class,
        'hotel_categories'          => \App\Models\HotelCategory::class,
        'hotel_rooms'               => \App\Models\HotelRoom::class,
        'hotel_reservations'        => \App\Models\HotelReservation::class,
        'hotel_payments'            => \App\Models\HotelPayment::class,
        'event_clients'             => \App\Models\EventClient::class,
        'event_services'            => \App\Models\EventService::class,
        'event_products'            => \App\Models\EventProduct::class,
        'event_reservations'        => \App\Models\EventReservation::class,
        'event_reservation_services'=> \App\Models\EventReservationService::class,
        'event_reservation_products'=> \App\Models\EventReservationProduct::class,
        'event_payments'            => \App\Models\EventPayment::class,
        'event_stock_movements'     => \App\Models\EventStockMovement::class,
        'licences'                  => \App\Models\Licence::class,
    ];

    /**
     * Process a batch of push operations from the client.
     *
     * @param  array  $operations  Each item: { table, operation, data, client_updated_at }
     * @param  string $syncedBy    UUID of the authenticated user
     * @return array               { success: int, errors: [] }
     */
    public function push(array $operations, string $syncedBy): array
    {
        $successCount = 0;
        $errors = [];

        DB::transaction(function () use ($operations, $syncedBy, &$successCount, &$errors) {
            foreach ($operations as $op) {
                try {
                    $this->applyOperation($op, $syncedBy);
                    $successCount++;
                } catch (\Throwable $e) {
                    $errors[] = [
                        'table'     => $op['table'] ?? '?',
                        'id'        => $op['data']['id'] ?? null,
                        'operation' => $op['operation'] ?? '?',
                        'error'     => $e->getMessage(),
                    ];
                }
            }
        });

        return ['success' => $successCount, 'errors' => $errors];
    }

    /**
     * Pull all records modified after $lastSync across all syncable tables.
     *
     * @param  Carbon $lastSync
     * @return array  { table => [records…] }
     */
    public function pull(Carbon $lastSync): array
    {
        $result = [];

        foreach ($this->tableMap as $table => $modelClass) {
            $model = new $modelClass;

            $records = $modelClass::withTrashed()
                ->where(function ($q) use ($lastSync) {
                    $q->where('updated_at', '>', $lastSync)
                      ->orWhere('created_at', '>', $lastSync)
                      ->orWhere('deleted_at', '>', $lastSync);
                })
                ->get();

            if ($records->isNotEmpty()) {
                $result[$table] = $records->toArray();
            }
        }

        return $result;
    }

    // ─── Private Helpers ─────────────────────────────────────────────────────

    private function applyOperation(array $op, string $syncedBy): void
    {
        $table     = $op['table']     ?? null;
        $operation = strtoupper($op['operation'] ?? '');
        $data      = $op['data']      ?? [];
        $clientUpdatedAt = isset($op['client_updated_at'])
            ? Carbon::parse($op['client_updated_at'])
            : now();

        if (! $table || ! isset($this->tableMap[$table])) {
            throw new \InvalidArgumentException("Table inconnue : {$table}");
        }

        $modelClass = $this->tableMap[$table];
        $id         = $data['id'] ?? null;

        if (! $id) {
            throw new \InvalidArgumentException("Champ 'id' manquant pour la table {$table}.");
        }

        $existing = $modelClass::withTrashed()->find($id);

        switch ($operation) {
            case 'INSERT':
                if ($existing) {
                    // Record already exists — log conflict, overwrite
                    $this->logAudit($table, $id, $operation, $data, $existing->toArray(), true, $clientUpdatedAt, $syncedBy);
                    $existing->fill($data)->save();
                } else {
                    $modelClass::create($data);
                }
                break;

            case 'UPDATE':
                if ($existing) {
                    $this->logAudit($table, $id, $operation, $data, $existing->toArray(), false, $clientUpdatedAt, $syncedBy);
                    $existing->fill($data)->save();
                } else {
                    // Client has a record server doesn't — create it
                    $modelClass::create($data);
                }
                break;

            case 'DELETE':
                if ($existing && ! $existing->trashed()) {
                    $this->logAudit($table, $id, $operation, $data, $existing->toArray(), false, $clientUpdatedAt, $syncedBy);
                    $existing->delete();
                }
                break;

            default:
                throw new \InvalidArgumentException("Opération inconnue : {$operation}");
        }
    }

    private function logAudit(
        string $table,
        string $recordId,
        string $operation,
        array  $clientData,
        array  $serverDataBefore,
        bool   $conflictResolved,
        Carbon $clientUpdatedAt,
        string $syncedBy
    ): void {
        SyncAuditLog::create([
            'table_name'        => $table,
            'record_id'         => $recordId,
            'operation'         => $operation,
            'client_data'       => $clientData,
            'server_data_before'=> $serverDataBefore,
            'conflict_resolved' => $conflictResolved,
            'client_updated_at' => $clientUpdatedAt,
            'synced_by'         => $syncedBy,
        ]);
    }
}
