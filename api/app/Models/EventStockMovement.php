<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class EventStockMovement extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'event_stock_movements';
    protected $fillable = ['id', 'reservation_id', 'product_id', 'warehouse_id', 'quantite', 'type_mouvement', 'note'];
    protected $casts = ['quantite' => 'decimal:3'];

    public function reservation() { return $this->belongsTo(EventReservation::class, 'reservation_id'); }
    public function product()     { return $this->belongsTo(CoreProduct::class, 'product_id'); }
    public function warehouse()   { return $this->belongsTo(StockWarehouse::class, 'warehouse_id'); }
}
