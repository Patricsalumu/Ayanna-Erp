<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ShopService extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'shop_services';
    protected $fillable = ['id', 'pos_id', 'nom', 'description', 'prix', 'actif'];
    protected $casts = ['prix' => 'decimal:2', 'actif' => 'boolean'];

    public function pos() { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function panierServices() { return $this->hasMany(ShopPanierService::class, 'service_id'); }
}
