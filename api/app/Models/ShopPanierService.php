<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ShopPanierService extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'shop_panier_services';
    protected $fillable = ['id', 'panier_id', 'service_id', 'quantite', 'prix_unitaire', 'remise', 'total'];
    protected $casts = ['quantite' => 'decimal:3', 'prix_unitaire' => 'decimal:2', 'remise' => 'decimal:2', 'total' => 'decimal:2'];

    public function panier()  { return $this->belongsTo(ShopPanier::class, 'panier_id'); }
    public function service() { return $this->belongsTo(ShopService::class, 'service_id'); }
}
