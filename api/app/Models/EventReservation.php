<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class EventReservation extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'event_reservations';
    protected $fillable = [
        'id', 'pos_id', 'client_id', 'user_id', 'reference',
        'nom_evenement', 'date_evenement', 'heure_debut', 'heure_fin',
        'montant_total', 'montant_paye', 'remise',
        'statut', 'statut_paiement', 'note',
    ];
    protected $casts = [
        'date_evenement' => 'datetime',
        'montant_total' => 'decimal:2', 'montant_paye' => 'decimal:2', 'remise' => 'decimal:2',
    ];

    public function pos()       { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function client()    { return $this->belongsTo(EventClient::class, 'client_id'); }
    public function user()      { return $this->belongsTo(User::class, 'user_id'); }
    public function services()  { return $this->hasMany(EventReservationService::class, 'reservation_id'); }
    public function produits()  { return $this->hasMany(EventReservationProduct::class, 'reservation_id'); }
    public function paiements() { return $this->hasMany(EventPayment::class, 'reservation_id'); }
    public function stockMovements() { return $this->hasMany(EventStockMovement::class, 'reservation_id'); }
}
