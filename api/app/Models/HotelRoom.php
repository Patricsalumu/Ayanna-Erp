<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class HotelRoom extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'hotel_rooms';
    protected $fillable = ['id', 'pos_id', 'category_id', 'numero', 'nom', 'etage', 'statut', 'actif', 'note'];
    protected $casts = ['actif' => 'boolean'];

    public function pos()           { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function category()      { return $this->belongsTo(HotelCategory::class, 'category_id'); }
    public function reservations()  { return $this->hasMany(HotelReservation::class, 'room_id'); }
}
