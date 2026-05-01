<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class HotelCategory extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'hotel_categories';
    protected $fillable = ['id', 'pos_id', 'nom', 'description', 'prix_par_nuit', 'actif'];
    protected $casts = ['prix_par_nuit' => 'decimal:2', 'actif' => 'boolean'];

    public function pos()    { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function rooms()  { return $this->hasMany(HotelRoom::class, 'category_id'); }
}
