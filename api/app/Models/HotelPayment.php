<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class HotelPayment extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'hotel_payments';
    protected $fillable = ['id', 'reservation_id', 'payment_mode_id', 'montant', 'reference', 'date_paiement', 'note'];
    protected $casts = ['montant' => 'decimal:2', 'date_paiement' => 'datetime'];

    public function reservation() { return $this->belongsTo(HotelReservation::class, 'reservation_id'); }
    public function paymentMode() { return $this->belongsTo(PaymentMode::class, 'payment_mode_id'); }
}
