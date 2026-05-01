<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ShopPanier extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'shop_paniers';
    protected $fillable = [
        'id', 'pos_id', 'client_id', 'user_id', 'reference',
        'montant_total', 'montant_paye', 'remise', 'statut',
        'date_vente', 'note',
    ];
    protected $casts = [
        'montant_total' => 'decimal:2', 'montant_paye' => 'decimal:2',
        'remise' => 'decimal:2', 'date_vente' => 'datetime',
    ];

    public function pos()      { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function client()   { return $this->belongsTo(ShopClient::class, 'client_id'); }
    public function user()     { return $this->belongsTo(User::class, 'user_id'); }
    public function produits() { return $this->hasMany(ShopPanierProduct::class, 'panier_id'); }
    public function services() { return $this->hasMany(ShopPanierService::class, 'panier_id'); }
    public function paiements(){ return $this->hasMany(ShopPayment::class, 'panier_id'); }
}
