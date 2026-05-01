<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class EventReservationService extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'event_reservation_services';
    protected $fillable = ['id', 'reservation_id', 'service_id', 'quantite', 'prix_unitaire', 'remise', 'total'];
    protected $casts = ['quantite' => 'decimal:3', 'prix_unitaire' => 'decimal:2', 'remise' => 'decimal:2', 'total' => 'decimal:2'];

    public function reservation() { return $this->belongsTo(EventReservation::class, 'reservation_id'); }
    public function service()     { return $this->belongsTo(EventService::class, 'service_id'); }
}
