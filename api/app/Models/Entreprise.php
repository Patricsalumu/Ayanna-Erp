<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class Entreprise extends Model
{
    use HasUuids, SoftDeletes;

    protected $table = 'core_enterprises';

    protected $fillable = [
        'id', 'name', 'address', 'phone', 'email', 'rccm', 'id_nat',
        'logo', 'slogan', 'currency', 'taux_de_change',
    ];

    protected $hidden = ['logo'];

    protected $casts = ['taux_de_change' => 'decimal:4'];

    public function users()         { return $this->hasMany(User::class, 'enterprise_id'); }
    public function posPoints()     { return $this->hasMany(POSPoint::class, 'enterprise_id'); }
    public function products()      { return $this->hasMany(CoreProduct::class, 'enterprise_id'); }
    public function paymentModes()  { return $this->hasMany(PaymentMode::class, 'enterprise_id'); }
}
