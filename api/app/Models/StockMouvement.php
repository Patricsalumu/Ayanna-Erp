<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class StockMouvement extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'stock_mouvements';
    protected $fillable = [
        'id', 'product_id', 'warehouse_id', 'product_warehouse_id',
        'type_mouvement', 'quantity', 'unit_cost', 'reference_document',
        'type_document', 'notes', 'user_id', 'date_mouvement',
    ];
    protected $casts = ['quantity' => 'decimal:3', 'unit_cost' => 'decimal:2', 'date_mouvement' => 'datetime'];

    public function product()         { return $this->belongsTo(CoreProduct::class, 'product_id'); }
    public function warehouse()       { return $this->belongsTo(StockWarehouse::class, 'warehouse_id'); }
    public function productWarehouse(){ return $this->belongsTo(StockProduitEntrepot::class, 'product_warehouse_id'); }
    public function user()            { return $this->belongsTo(User::class, 'user_id'); }
}
