<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class POSProductAccess extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'pos_product_access';
    protected $fillable = ['id', 'pos_id', 'product_id', 'custom_price', 'custom_cost', 'is_available', 'display_order'];
    protected $casts = ['is_available' => 'boolean', 'custom_price' => 'decimal:2', 'custom_cost' => 'decimal:2'];

    public function pos()     { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function product() { return $this->belongsTo(CoreProduct::class, 'product_id'); }
}
