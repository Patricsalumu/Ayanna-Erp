<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class StockProduitEntrepot extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'stock_produits_entrepot';
    protected $fillable = [
        'id', 'product_id', 'warehouse_id', 'quantity', 'reserved_quantity',
        'unit_cost', 'total_cost', 'min_stock_level', 'last_movement_date', 'location',
    ];
    protected $casts = [
        'quantity' => 'decimal:3', 'reserved_quantity' => 'decimal:3',
        'unit_cost' => 'decimal:2', 'total_cost' => 'decimal:2', 'last_movement_date' => 'datetime',
    ];

    public function product()   { return $this->belongsTo(CoreProduct::class, 'product_id'); }
    public function warehouse() { return $this->belongsTo(StockWarehouse::class, 'warehouse_id'); }
    public function mouvements(){ return $this->hasMany(StockMouvement::class, 'product_warehouse_id'); }
}
