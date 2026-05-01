<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class PaymentMode extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'core_payment_modes';
    protected $fillable = [
        'id', 'enterprise_id', 'code', 'label', 'description',
        'compte_id', 'compte_label', 'is_default', 'is_active', 'sort_order',
    ];
    protected $casts = ['is_default' => 'boolean', 'is_active' => 'boolean'];

    public function enterprise() { return $this->belongsTo(Entreprise::class, 'enterprise_id'); }
    public function compte()     { return $this->belongsTo(ComptaComptes::class, 'compte_id'); }
}
