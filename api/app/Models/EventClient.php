<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class EventClient extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'event_clients';
    protected $fillable = ['id', 'pos_id', 'nom', 'telephone', 'adresse', 'email', 'note'];

    public function pos()          { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function reservations() { return $this->hasMany(EventReservation::class, 'client_id'); }
}
