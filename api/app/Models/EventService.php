<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class EventService extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'event_services';
    protected $fillable = ['id', 'pos_id', 'nom', 'description', 'prix', 'unite', 'actif'];
    protected $casts = ['prix' => 'decimal:2', 'actif' => 'boolean'];

    public function pos()                 { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function reservationServices() { return $this->hasMany(EventReservationService::class, 'service_id'); }
}
