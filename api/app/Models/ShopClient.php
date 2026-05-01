<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ShopClient extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'shop_clients';
    protected $fillable = ['id', 'pos_id', 'nom', 'telephone', 'adresse', 'email', 'note'];

    public function pos()     { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function paniers() { return $this->hasMany(ShopPanier::class, 'client_id'); }
}
