<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class StockWarehouse extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'stock_warehouses';
    protected $fillable = [
        'id', 'entreprise_id', 'code', 'name', 'type', 'description', 'address',
        'contact_person', 'contact_phone', 'contact_email',
        'is_default', 'is_active', 'capacity_limit',
    ];
    protected $casts = ['is_default' => 'boolean', 'is_active' => 'boolean', 'capacity_limit' => 'decimal:2'];

    public function stockProduits() { return $this->hasMany(StockProduitEntrepot::class, 'warehouse_id'); }
    public function mouvements()    { return $this->hasMany(StockMouvement::class, 'warehouse_id'); }
    public function inventaires()   { return $this->hasMany(StockInventaire::class, 'warehouse_id'); }
}
