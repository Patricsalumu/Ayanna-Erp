<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class StockInventaireItem extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'stock_inventaire_items';
    protected $fillable = ['id', 'inventaire_id', 'product_id', 'quantite_theorique', 'quantite_reelle', 'ecart', 'unit_cost', 'notes'];
    protected $casts = ['quantite_theorique' => 'decimal:3', 'quantite_reelle' => 'decimal:3', 'ecart' => 'decimal:3', 'unit_cost' => 'decimal:2'];

    public function inventaire() { return $this->belongsTo(StockInventaire::class, 'inventaire_id'); }
    public function produit()    { return $this->belongsTo(CoreProduct::class, 'product_id'); }
}
