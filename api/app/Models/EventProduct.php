<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class EventProduct extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'event_products';
    protected $fillable = ['id', 'pos_id', 'product_id', 'is_available', 'custom_price'];
    protected $casts = ['is_available' => 'boolean', 'custom_price' => 'decimal:2'];

    public function pos()     { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function product() { return $this->belongsTo(CoreProduct::class, 'product_id'); }
}
