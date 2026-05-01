<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class RestauProduitPanier extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'restau_produit_panier';
    protected $fillable = ['id', 'panier_id', 'product_id', 'quantite', 'prix_unitaire', 'remise', 'total', 'statut', 'note'];
    protected $casts = ['quantite' => 'decimal:3', 'prix_unitaire' => 'decimal:2', 'remise' => 'decimal:2', 'total' => 'decimal:2'];

    public function panier()  { return $this->belongsTo(RestauPanier::class, 'panier_id'); }
    public function product() { return $this->belongsTo(CoreProduct::class, 'product_id'); }
}
