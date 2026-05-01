<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class CoreProduct extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'core_products';
    protected $fillable = [
        'id', 'enterprise_id', 'category_id', 'code', 'name', 'description',
        'image', 'barcode', 'cost', 'price_unit', 'unit',
        'compte_produit_id', 'compte_charge_id', 'is_active',
    ];
    protected $casts = ['cost' => 'decimal:2', 'price_unit' => 'decimal:2', 'is_active' => 'boolean'];

    public function enterprise()     { return $this->belongsTo(Entreprise::class, 'enterprise_id'); }
    public function category()       { return $this->belongsTo(CoreProductCategory::class, 'category_id'); }
    public function compteProduit()  { return $this->belongsTo(ComptaComptes::class, 'compte_produit_id'); }
    public function compteCharge()   { return $this->belongsTo(ComptaComptes::class, 'compte_charge_id'); }
    public function posAccesses()    { return $this->hasMany(POSProductAccess::class, 'product_id'); }
    public function stockEntrepots() { return $this->hasMany(StockProduitEntrepot::class, 'product_id'); }
}
