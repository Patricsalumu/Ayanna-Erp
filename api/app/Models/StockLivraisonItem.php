<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class StockLivraisonItem extends Model
{
    use HasUuids, SoftDeletes;

    protected $table = 'stock_livraison_items';

    protected $fillable = [
        'id', 'livraison_id', 'product_id', 'product_name', 'product_code',
        'quantite', 'cout_unitaire', 'total_ligne',
    ];

    protected $casts = [
        'quantite'     => 'decimal:3',
        'cout_unitaire'=> 'decimal:2',
        'total_ligne'  => 'decimal:2',
    ];

    public function livraison() { return $this->belongsTo(StockLivraison::class, 'livraison_id'); }
    public function produit()   { return $this->belongsTo(CoreProduct::class, 'product_id'); }
}
