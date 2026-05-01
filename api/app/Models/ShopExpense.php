<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ShopExpense extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'shop_expenses';
    protected $fillable = ['id', 'pos_id', 'user_id', 'libelle', 'montant', 'date_depense', 'note'];
    protected $casts = ['montant' => 'decimal:2', 'date_depense' => 'datetime'];

    public function pos()  { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function user() { return $this->belongsTo(User::class, 'user_id'); }
}
