<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class HotelReservation extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'hotel_reservations';
    protected $fillable = [
        'id', 'pos_id', 'room_id', 'user_id', 'reference',
        'client_nom', 'client_telephone', 'client_adresse',
        'date_arrivee', 'date_depart', 'nombre_nuits',
        'prix_par_nuit', 'montant_total', 'montant_paye',
        'remise', 'statut', 'statut_paiement', 'note',
    ];
    protected $casts = [
        'date_arrivee' => 'datetime', 'date_depart' => 'datetime',
        'prix_par_nuit' => 'decimal:2', 'montant_total' => 'decimal:2',
        'montant_paye' => 'decimal:2', 'remise' => 'decimal:2',
    ];

    public function pos()       { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function room()      { return $this->belongsTo(HotelRoom::class, 'room_id'); }
    public function user()      { return $this->belongsTo(User::class, 'user_id'); }
    public function paiements() { return $this->hasMany(HotelPayment::class, 'reservation_id'); }
}
