<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class StockInventaire extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'stock_inventaire';
    protected $fillable = ['id', 'warehouse_id', 'user_id', 'reference', 'date_inventaire', 'statut', 'notes'];
    protected $casts = ['date_inventaire' => 'datetime'];

    public function warehouse() { return $this->belongsTo(StockWarehouse::class, 'warehouse_id'); }
    public function user()      { return $this->belongsTo(User::class, 'user_id'); }
    public function items()     { return $this->hasMany(StockInventaireItem::class, 'inventaire_id'); }
}
