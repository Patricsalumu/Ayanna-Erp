<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class StockConfig extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'stock_config';
    protected $fillable = ['id', 'enterprise_id', 'default_warehouse_id', 'allow_negative_stock', 'valuation_method', 'auto_reorder_enabled'];
    protected $casts = ['allow_negative_stock' => 'boolean', 'auto_reorder_enabled' => 'boolean'];

    public function enterprise()       { return $this->belongsTo(Entreprise::class, 'enterprise_id'); }
    public function defaultWarehouse() { return $this->belongsTo(StockWarehouse::class, 'default_warehouse_id'); }
}
