<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ShopClient extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'shop_clients';
    protected $fillable = [
        'id', 'pos_id', 'nom', 'prenom', 'telephone', 'email', 'adresse',
        'ville', 'code_postal', 'date_naissance', 'type_client',
        'credit_limit', 'balance', 'note',
        'pays', 'carte_identite', 'type_carte', 'is_active',
    ];

    public function pos()     { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function paniers() { return $this->hasMany(ShopPanier::class, 'client_id'); }
}
